#!/usr/bin/env python3
"""
Writers Room Web Interface
Flask + SocketIO backend for real-time agent collaboration
"""

import os
import sys
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading

# Add parent directory to path to import our agents
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import Agent
from personalities import (
    ROD_SERLING,
    STEPHEN_KING,
    HP_LOVECRAFT,
    JORGE_BORGES,
    ROBERT_STACK,
    MARKETING_EXEC,
    PRODUCER,
    RECOMMENDED_MODELS
)

app = Flask(__name__)

# Security: Use environment variable for secret key in production
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-CHANGE-IN-PRODUCTION')

# CORS: Restrict origins in production
cors_origins = os.getenv('CORS_ORIGINS', '*').split(',') if os.getenv('CORS_ORIGINS') else "*"
CORS(app, origins=cors_origins)
socketio = SocketIO(app, cors_allowed_origins=cors_origins)

# Global session state
current_session = {
    'active': False,
    'agents': None,
    'producer': None,
    'conversation_history': [],
    'agent_scores': {},
    'config': {}
}


def initialize_agents(config):
    """Initialize all agents with given configuration."""
    model_override = config.get('model', None)  # None if no override specified
    temperature = config.get('temperature', 0.9)
    producer_enabled = config.get('producer_enabled', True)

    agents = []

    # Initialize the six writers
    agent_configs = [
        ('Rod Serling', ROD_SERLING, 'rod_serling', '#00FFFF'),  # Cyan
        ('Stephen King', STEPHEN_KING, 'stephen_king', '#FF0000'),  # Red
        ('H.P. Lovecraft', HP_LOVECRAFT, 'hp_lovecraft', '#FF00FF'),  # Magenta
        ('Jorge Luis Borges', JORGE_BORGES, 'jorge_borges', '#0000FF'),  # Blue
        ('Robert Stack', ROBERT_STACK, 'robert_stack', '#FFFFFF'),  # White
        ('RIP Tequila Bot', MARKETING_EXEC, 'marketing', '#FFFF00')  # Yellow
    ]

    for name, personality, model_key, color in agent_configs:
        agent = Agent(
            name=name,
            model=model_override if model_override else RECOMMENDED_MODELS[model_key],
            system_prompt=personality,
            temperature=temperature
        )
        agents.append({
            'agent': agent,
            'name': name,
            'color': color
        })

    # Initialize Producer if enabled
    producer = None
    if producer_enabled:
        try:
            producer = Agent(
                name="The Producer",
                model=model_override if model_override else RECOMMENDED_MODELS.get('producer', 'mistralai/ministral-3b-2512'),
                system_prompt=PRODUCER,
                temperature=0.7,
                max_tokens=300
            )
            print("✓ Producer agent initialized successfully")
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize Producer: {e}")
            print("   Session will continue without Producer/scoring")
            producer = None

    return agents, producer


def parse_producer_scores(producer_response, agent_names):
    """Parse scores from Producer's response with robust fallbacks."""
    import re
    scores = {}

    for agent_name in agent_names:
        # Try multiple patterns to be robust
        patterns = [
            rf"{re.escape(agent_name)}:\s*(\d+)\s*/\s*10",  # "Name: 7/10"
            rf"{re.escape(agent_name)}.*?(\d+)\s*/\s*10",    # "Name ... 7/10"
            rf"{re.escape(agent_name)}.*?score.*?(\d+)",      # "Name score: 7"
            rf"{re.escape(agent_name)}.*?(\d+)\s*out of 10", # "Name 7 out of 10"
        ]

        found_score_for_agent = False
        for pattern in patterns:
            match = re.search(pattern, producer_response, re.IGNORECASE | re.DOTALL)
            if match:
                try:
                    score = int(match.group(1))
                    scores[agent_name] = max(1, min(10, score))
                    found_score_for_agent = True
                    break  # Found a score, stop trying patterns
                except (ValueError, IndexError):
                    continue
        if not found_score_for_agent:
            print(f"⚠️  Warning: Could not parse score for {agent_name} in Producer response")

    # Fallback: if no scores found, assign neutral scores
    if not scores and agent_names:
        print(f"Warning: Could not parse scores from Producer response")
        print(f"Response was: {producer_response[:200]}...")
        # Assign 5/10 to all agents as fallback
        scores = {name: 5 for name in agent_names}

    return scores


def run_session_thread(prompt, rounds, config):
    """Run the writers room session in a background thread."""
    global current_session

    try:
        current_session['active'] = True
        current_session['conversation_history'] = [
            {"role": "user", "content": f"Write a scene about: {prompt}"}
        ]

        # Initialize agent scores
        agent_scores = {agent['name']: [] for agent in current_session['agents']}
        current_session['agent_scores'] = agent_scores

        # Emit session started event
        socketio.emit('session_started', {
            'prompt': prompt,
            'rounds': rounds,
            'config': config
        })

        # Run rounds
        for round_num in range(1, rounds + 1):
            socketio.emit('round_started', {'round': round_num, 'total': rounds})

            # Each agent takes a turn
            for agent_info in current_session['agents']:
                agent = agent_info['agent']
                name = agent_info['name']
                color = agent_info['color']

                # Emit agent thinking
                socketio.emit('agent_thinking', {'agent': name, 'color': color})

                # Generate response
                response = agent.generate_response(current_session['conversation_history'])

                # Add to history
                current_session['conversation_history'].append({
                    "role": "assistant",
                    "content": response,
                    "name": name
                })

                # Emit response to UI
                socketio.emit('agent_response', {
                    'agent': name,
                    'response': response,
                    'color': color,
                    'round': round_num
                })

            # Producer evaluation after each round
            if current_session['producer']:
                try:
                    socketio.emit('producer_thinking', {'round': round_num})

                    # Build context for Producer
                    # Include the original prompt + recent rounds for full story context
                    # Producer's Agent.generate_response will apply its own windowing (preserves first message)
                    round_context = list(current_session['conversation_history'])

                    # Add instruction for Producer at the end
                    round_context.append({
                        "role": "user",
                        "content": f"Judge round {round_num}: Score each writer 1-10 with brief comments."
                    })

                    # Get Producer's verdict
                    producer_response = current_session['producer'].generate_response(round_context)

                    # Parse scores
                    agent_names = [a['name'] for a in current_session['agents']]
                    round_scores = parse_producer_scores(producer_response, agent_names)

                    # Update scores
                    for agent_name, score in round_scores.items():
                        if agent_name in agent_scores:
                            agent_scores[agent_name].append(score)
                except Exception as e:
                    print(f"⚠️  Producer evaluation failed for round {round_num}: {e}")
                    # Continue session without Producer verdict this round
                    socketio.emit('error', {'message': f'Producer evaluation failed: {str(e)[:100]}'})
                    round_scores = {}

                # Calculate leaderboard
                leaderboard = []
                for agent_name, scores in agent_scores.items():
                    if scores:
                        avg_score = sum(scores) / len(scores)
                        leaderboard.append({
                            'name': agent_name,
                            'average': round(avg_score, 1),
                            'scores': scores,
                            'total_rounds': len(scores)
                        })

                leaderboard.sort(key=lambda x: x['average'], reverse=True)

                # Emit Producer verdict
                socketio.emit('producer_verdict', {
                    'response': producer_response,
                    'scores': round_scores,
                    'leaderboard': leaderboard,
                    'round': round_num
                })

            socketio.emit('round_completed', {'round': round_num})

        # Final results
        if current_session['producer'] and agent_scores:
            leaderboard = []
            for agent_name, scores in agent_scores.items():
                if scores:
                    avg_score = sum(scores) / len(scores)
                    leaderboard.append({
                        'name': agent_name,
                        'average': round(avg_score, 1),
                        'scores': scores,
                        'total_rounds': len(scores)
                    })

            leaderboard.sort(key=lambda x: x['average'], reverse=True)

            winner = leaderboard[0] if leaderboard else None
            worst = leaderboard[-1] if len(leaderboard) > 1 and config.get('fire_worst', False) else None

            socketio.emit('session_completed', {
                'leaderboard': leaderboard,
                'winner': winner,
                'worst': worst if config.get('fire_worst', False) else None
            })
        else:
            socketio.emit('session_completed', {
                'leaderboard': [],
                'winner': None,
                'worst': None
            })

    except Exception as e:
        socketio.emit('error', {'message': str(e)})
    finally:
        current_session['active'] = False


@app.route('/')
def index():
    """Render the main UI."""
    return render_template('index.html')


@app.route('/api/start', methods=['POST'])
def start_session():
    """Start a new writers room session."""
    global current_session

    if current_session['active']:
        return jsonify({'error': 'Session already active'}), 400

    data = request.json
    prompt = data.get('prompt', '').strip()
    rounds = data.get('rounds', 3)

    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400

    config = {
        'model': data.get('model'),
        'temperature': float(data.get('temperature', 0.9)),
        'producer_enabled': data.get('producer_enabled', True),
        'fire_worst': data.get('fire_worst', False)
    }

    # Initialize agents
    agents, producer = initialize_agents(config)
    current_session['agents'] = agents
    current_session['producer'] = producer
    current_session['config'] = config

    # Start session in background thread
    thread = threading.Thread(
        target=run_session_thread,
        args=(prompt, rounds, config)
    )
    thread.daemon = True
    thread.start()

    return jsonify({'status': 'started'})


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current session status."""
    return jsonify({
        'active': current_session['active'],
        'config': current_session['config']
    })


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print('Client connected')
    emit('connected', {'status': 'connected'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print('Client disconnected')


if __name__ == '__main__':
    print("🌐 Starting Writers Room Web Interface...")
    print("📍 Navigate to: http://localhost:5001")
    print("🎬 Press Ctrl+C to stop\n")
    socketio.run(app, host='0.0.0.0', port=5001, debug=True, allow_unsafe_werkzeug=True)
