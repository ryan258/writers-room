"""
Session Orchestration for Writers Room.
"""
import threading
import re
from typing import Dict, Any, List, Optional, Callable

from .story_state import StoryStateManager
from .agents import Agent
from .custom_agents import CustomAgentManager
from .personalities import (
    ROD_SERLING, STEPHEN_KING, HP_LOVECRAFT, JORGE_BORGES, 
    ROBERT_STACK, MARKETING_EXEC, PRODUCER, 
    DEFAULT_MODEL, STORY_MODES, get_mode_prompt_context,
    get_producer_mode_criteria
)

# Optional voice support
try:
    from .voice import generate_agent_audio
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

class SessionEvent:
    SESSION_STARTED = "session_started"
    ROUND_STARTED = "round_started"
    STORY_STATE_UPDATE = "story_state_update"
    AGENT_THINKING = "agent_thinking"
    AGENT_RESPONSE = "agent_response"
    PRODUCER_THINKING = "producer_thinking"
    PRODUCER_VERDICT = "producer_verdict"
    ROUND_COMPLETED = "round_completed"
    SESSION_COMPLETED = "session_completed"
    ERROR = "error"

def parse_producer_scores(producer_response: str, agent_names: List[str]) -> Dict[str, int]:
    """Parse scores from Producer's response with robust fallbacks."""
    scores = {}

    # Define aliases for agents with complex names
    aliases = {
        "RIP Tequila Bot": ["TM Bot", "Tequila Bot", "Tequila", "RIP Tequila", "Marketing Exec"],
        "H.P. Lovecraft": ["HP Lovecraft", "Lovecraft"],
        "Jorge Luis Borges": ["Borges", "Jorge Borges"],
        "Rod Serling": ["Serling", "Rod"],
        "Stephen King": ["King", "Stephen"],
        "Robert Stack": ["Stack", "Robert"]
    }

    for agent_name in agent_names:
        names_to_check = [agent_name]
        if agent_name in aliases:
            names_to_check.extend(aliases[agent_name])

        found_score_for_agent = False

        for name_variant in names_to_check:
            if found_score_for_agent:
                break

            patterns = [
                rf"{re.escape(name_variant)}:\s*(\d+)\s*/\s*10",
                rf"{re.escape(name_variant)}.*?(\d+)\s*/\s*10",
                rf"{re.escape(name_variant)}.*?score.*?(\d+)",
                rf"{re.escape(name_variant)}.*?(\d+)\s*out of 10",
                rf"\*\*?{re.escape(name_variant)}\*\*?.*?(\d+)/10",
                rf"{re.escape(name_variant)}.*?(\d+)/10",
            ]

            for pattern in patterns:
                match = re.search(pattern, producer_response, re.IGNORECASE | re.DOTALL)
                if match:
                    try:
                        score = int(match.group(1))
                        # Clamp between 1-10
                        scores[agent_name] = max(1, min(10, score))
                        found_score_for_agent = True
                        break
                    except (ValueError, IndexError):
                        continue

    # Fallback patterns
    for i, agent_name in enumerate(agent_names):
        if agent_name not in scores:
            writer_patterns = [
                rf"Writer\s*#?{i+1}\s*.*?:.*?(\d+)/10",
                rf"Writer\s*#?{i+1}\s*.*?(\d+)\s*out of 10",
            ]
            for pattern in writer_patterns:
                match = re.search(pattern, producer_response, re.IGNORECASE)
                if match:
                    try:
                        score = int(match.group(1))
                        scores[agent_name] = max(1, min(10, score))
                        break
                    except ValueError:
                        continue

    # Fallback: assign neutral scores if absolutely nothing found
    if not scores and agent_names:
        scores = {name: 5 for name in agent_names}

    return scores

class SessionOrchestrator:
    def __init__(self, event_callback: Callable[[str, Dict[str, Any]], None]):
        self.emit = event_callback
        self.active = False
        self.agents = []
        self.producer = None
        self.conversation_history = []
        self.agent_scores = {}
        self.config = {}
        self.story_manager = None
        self.voice_enabled = False
        self.stop_event = threading.Event()

    def initialize(self, prompt: str, config: Dict[str, Any]):
        self.config = config
        self.active = True
        self.stop_event.clear()
        self.conversation_history = [
            {"role": "user", "content": f"Write a scene about: {prompt}"}
        ]
        
        story_mode = config.get('mode', 'horror')
        self.story_manager = StoryStateManager(premise=prompt, mode=story_mode)
        
        self.agents, self.producer = self._initialize_agents(config)
        self.agent_scores = {agent['name']: [] for agent in self.agents}
        self.voice_enabled = config.get('voice_enabled', False) and VOICE_AVAILABLE
        
        # Initial emit
        self.emit(SessionEvent.SESSION_STARTED, {
            'prompt': prompt,
            'rounds': config.get('rounds', 3),
            'config': config,
            'mode': story_mode,
            'mode_info': STORY_MODES.get(story_mode, {})
        })

    def stop(self):
        self.active = False
        self.stop_event.set()

    def _initialize_agents(self, config):
        model_override = config.get('model') or DEFAULT_MODEL
        temperature = config.get('temperature', 0.9)
        producer_enabled = config.get('producer_enabled', True)
        story_mode = config.get('mode', 'horror')
        mode_context = get_mode_prompt_context(story_mode)
        include_custom_agents = config.get('include_custom_agents', True)
        
        agents = []
        agent_configs = [
            ('Rod Serling', ROD_SERLING, 'rod_serling', '#00FFFF'),
            ('Stephen King', STEPHEN_KING, 'stephen_king', '#FF0000'),
            ('H.P. Lovecraft', HP_LOVECRAFT, 'hp_lovecraft', '#FF00FF'),
            ('Jorge Luis Borges', JORGE_BORGES, 'jorge_borges', '#0000FF'),
            ('Robert Stack', ROBERT_STACK, 'robert_stack', '#FFFFFF'),
            ('RIP Tequila Bot', MARKETING_EXEC, 'marketing', '#FFFF00')
        ]
        
        for name, personality, model_key, color in agent_configs:
            agent = Agent(
                name=name,
                model=model_override,
                system_prompt=personality + mode_context,
                temperature=temperature
            )
            agents.append({'agent': agent, 'name': name, 'color': color, 'voice_id': None})

        # Append active custom agents if requested
        if include_custom_agents:
            manager = CustomAgentManager()
            for custom in manager.get_active_agents():
                custom_agent = Agent(
                    name=custom.name,
                    model=model_override,
                    system_prompt=custom.to_system_prompt(""),
                    temperature=temperature
                )
                agents.append({
                    'agent': custom_agent,
                    'name': custom.name,
                    'color': custom.color,
                    'voice_id': custom.voice_id
                })
            
        producer = None
        if producer_enabled:
             try:
                producer_prompt = PRODUCER + f"\n\nMode-specific focus: {get_producer_mode_criteria(story_mode)}"
                producer = Agent(
                    name="The Producer",
                    model=model_override,
                    system_prompt=producer_prompt,
                    temperature=0.7,
                    max_tokens=300
                )
             except Exception as e:
                self.emit(SessionEvent.ERROR, {'message': f"Could not initialize Producer: {e}"})
                producer = None
        return agents, producer

    def run_session(self, rounds: int):
        try:
            for round_num in range(1, rounds + 1):
                if self.stop_event.is_set(): break
                
                self._run_round(round_num, rounds)
                
            self._finalize_session()
        except Exception as e:
            self.emit(SessionEvent.ERROR, {'message': str(e)})
            import traceback
            traceback.print_exc()
        finally:
             self.active = False
             self.emit(SessionEvent.SESSION_COMPLETED, self._get_session_summary())

    def _run_round(self, round_num, total_rounds):
         state = self.story_manager.get_state()
         self.emit(SessionEvent.STORY_STATE_UPDATE, {
             'round': round_num,
             'state': state.to_dict()
         })
         
         self.emit(SessionEvent.ROUND_STARTED, {'round': round_num, 'total': total_rounds})
         
         # Agents turn
         for agent_info in self.agents:
             if self.stop_event.is_set(): return
             
             agent = agent_info['agent']
             name = agent_info['name']
             color = agent_info['color']
             
             self.emit(SessionEvent.AGENT_THINKING, {'agent': name, 'color': color})
             
             story_context = self.story_manager.state.to_prompt_context()
             response = agent.generate_response(
                 self.conversation_history,
                 story_context=story_context
             )
             
             self.story_manager.process_contribution(response, name, round_num)
             
             self.conversation_history.append({
                 "role": "assistant",
                 "content": response,
                 "name": name
             })
             
             audio_data = None
             if self.voice_enabled:
                 try:
                     audio_data = generate_agent_audio(
                         response,
                         name,
                         voice_id_override=agent_info.get('voice_id')
                     )
                 except Exception:
                     pass
                     
             self.emit(SessionEvent.AGENT_RESPONSE, {
                 'agent': name,
                 'response': response,
                 'color': color,
                 'round': round_num,
                 'audio': audio_data[0] if audio_data else None,
                 'audio_mime': audio_data[1] if audio_data else None
             })
             
         # Producer turn
         if self.producer:
             self._run_producer_turn(round_num)
             
         self.emit(SessionEvent.ROUND_COMPLETED, {'round': round_num})

    def _run_producer_turn(self, round_num):
         self.emit(SessionEvent.PRODUCER_THINKING, {'round': round_num})
         
         round_context = []
         for msg in self.conversation_history:
             if msg['role'] == 'assistant' and 'name' in msg:
                 new_msg = msg.copy()
                 new_msg['content'] = f"{msg['name']}: {msg['content']}"
                 round_context.append(new_msg)
             else:
                 round_context.append(msg)
                 
         agent_names = [a['name'] for a in self.agents]
         agent_names_str = ", ".join(agent_names)
         mode_criteria = get_producer_mode_criteria(self.config.get('mode', 'horror'))
         
         round_context.append({
             "role": "user",
             "content": f"Judge round {round_num}. Score these writers: [{agent_names_str}]. IMPORTANT: Use the EXACT names provided (e.g. 'Rod Serling: 7/10'). Do NOT use 'Writer 1' or aliases.\n\nMode-specific criteria: {mode_criteria}"
         })
         
         producer_story_context = self.story_manager.get_producer_context()
         producer_response = self.producer.generate_response(
             round_context,
             story_context=producer_story_context
         )
         
         round_scores = parse_producer_scores(producer_response, agent_names)
         for agent_name, score in round_scores.items():
            if agent_name in self.agent_scores:
                self.agent_scores[agent_name].append(score)
         
         # Calculate leaderboard
         leaderboard = self._calculate_leaderboard()
         
         producer_audio = None
         if self.voice_enabled:
             try:
                producer_audio = generate_agent_audio(producer_response, "The Producer")
             except Exception:
                pass
                
         self.emit(SessionEvent.PRODUCER_VERDICT, {
             'response': producer_response,
             'scores': round_scores,
             'leaderboard': leaderboard,
             'round': round_num,
             'audio': producer_audio[0] if producer_audio else None,
             'audio_mime': producer_audio[1] if producer_audio else None
         })

    def _calculate_leaderboard(self):
         leaderboard = []
         for agent_name, scores in self.agent_scores.items():
             if scores:
                 avg_score = sum(scores) / len(scores)
                 leaderboard.append({
                     'name': agent_name,
                     'average': round(avg_score, 1),
                     'scores': scores,
                     'total_rounds': len(scores)
                 })
         leaderboard.sort(key=lambda x: x['average'], reverse=True)
         return leaderboard

    def _finalize_session(self):
         # Logic for final cleanup or stats is handled in get_session_summary for the event
         pass

    def _get_session_summary(self):
        leaderboard = self._calculate_leaderboard()
        winner = leaderboard[0] if leaderboard else None
        worst = leaderboard[-1] if len(leaderboard) > 1 and self.config.get('fire_worst', False) else None
        final_state = self.story_manager.get_state()
        
        return {
            'leaderboard': leaderboard,
            'winner': winner,
            'worst': worst,
            'story_state': final_state.to_dict()
        }
