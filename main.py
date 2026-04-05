#!/usr/bin/env python3
"""
Writers Room: Collaborative Story Excellence Engine

An elite AI writers room where legendary authors collaborate around
a shared "Center Table" to create unforgettably potent stories.
"""

import os
import sys
import argparse
import json
import re
from datetime import datetime
from urllib import error as urllib_error
from urllib import request as urllib_request

try:
    from colorama import init, Fore, Style
except ImportError:  # pragma: no cover - exercised in thin local installs
    def init(*args, **kwargs):
        return None

    class _ColorFallback:
        BLACK = ""
        BLUE = ""
        CYAN = ""
        GREEN = ""
        MAGENTA = ""
        RED = ""
        WHITE = ""
        YELLOW = ""
        RESET_ALL = ""

    Fore = _ColorFallback()
    Style = _ColorFallback()

from lib.agents import Agent
from lib.story_state import StoryStateManager
from lib.personalities import (
    PRODUCER,
    STORY_MODES,
    DEFAULT_MODEL,
    get_agent_roster,
    get_producer_mode_criteria,
    get_session_opening_prompt,
    is_dnd_mode,
)
from lib.session_briefing import render_session_brief
from lib.session_turns import (
    build_dnd_story_context,
    generate_dnd_turn,
)

# Initialize colorama for cross-platform colored terminal output
init(autoreset=True)

CLI_COLOR_BY_HEX = {
    "#00FFFF": Fore.CYAN,
    "#FF0000": Fore.RED,
    "#FF00FF": Fore.MAGENTA,
    "#0000FF": Fore.BLUE,
    "#FFFFFF": Fore.WHITE,
    "#FFFF00": Fore.YELLOW,
    "#98C379": Fore.GREEN,
}


def print_banner():
    """Print the Writers Room banner."""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}    WRITERS ROOM: COLLABORATIVE STORY EXCELLENCE")
    print(f"{Fore.CYAN}{'='*60}\n")


def print_agent_response(agent_name: str, response: str, color: str):
    """
    Print an agent's response with colored formatting.

    Args:
        agent_name: Name of the agent
        response: The agent's response text
        color: Colorama color constant (e.g., Fore.GREEN)
    """
    print(f"\n{color}+-- {agent_name.upper()} {'-'*(55-len(agent_name))}")
    print(f"{color}|")
    # Wrap text for better readability
    for line in response.split('\n'):
        print(f"{color}|  {line}")
    print(f"{color}+{'-'*58}\n")


def save_transcript(prompt: str, conversation_history: list, story_state=None, filename: str = None):
    """
    Save the conversation to a transcript file.

    Args:
        prompt: The initial prompt
        conversation_history: List of all messages
        story_state: Optional StoryState object for metadata
        filename: Optional custom filename
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"transcripts/session_{timestamp}.txt"

    # Ensure directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, 'w') as f:
        f.write("="*60 + "\n")
        if story_state and is_dnd_mode(story_state.mode):
            f.write("WRITERS ROOM D&D TABLE TRANSCRIPT\n")
        else:
            f.write("WRITERS ROOM TRANSCRIPT\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        if story_state:
            f.write(f"Mode: {story_state.mode.upper()}\n")
            f.write(f"Final Act: {story_state.current_act.name}\n")
            f.write(f"Word Count: {story_state.word_count}\n")
        f.write("="*60 + "\n\n")

        if story_state and is_dnd_mode(story_state.mode):
            f.write(f"ADVENTURE HOOK: {prompt}\n\n")
            current_round = None
            for msg in conversation_history:
                if msg["role"] != "assistant":
                    continue
                msg_round = msg.get("round")
                if msg_round != current_round:
                    current_round = msg_round
                    f.write("-" * 60 + "\n")
                    f.write(f"ROUND {current_round}\n")
                    f.write("-" * 60 + "\n\n")
                f.write(f"{msg.get('name', 'AGENT')}: {msg['content']}\n\n")
        else:
            f.write(f"INITIAL PROMPT: {prompt}\n\n")
            f.write("-"*60 + "\n\n")

            for msg in conversation_history:
                if msg['role'] == 'user':
                    f.write(f"[USER]: {msg['content']}\n\n")
                elif msg['role'] == 'assistant':
                    f.write(f"{msg.get('name', 'AGENT')}: {msg['content']}\n\n")

            f.write("-"*60 + "\n")
            f.write("END OF TRANSCRIPT\n")

    print(f"{Fore.CYAN}Transcript saved to: {filename}")
    return filename


def validate_api_key():
    """Validate that the OpenRouter API key works."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return False, "OPENROUTER_API_KEY not found in environment"

    if not api_key.startswith("sk-or-"):
        return False, "API key format appears invalid (should start with 'sk-or-')"

    request = urllib_request.Request(
        "https://openrouter.ai/api/v1/key",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
        method="GET",
    )

    try:
        with urllib_request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib_error.HTTPError as exc:
        if exc.code == 401:
            return False, "API key is invalid or expired"
        if exc.code == 429:
            return False, "Rate limited - your API key may need credits"
        if exc.code == 404:
            return False, "OpenRouter key endpoint was not found"
        return False, f"OpenRouter validation failed ({exc.code})"
    except urllib_error.URLError as exc:
        reason = str(exc.reason)
        if "timed out" in reason.lower():
            return False, "Connection timeout - check your internet connection"
        return False, f"Network error - {reason}"
    except Exception as exc:
        return False, f"Validation failed: {str(exc)[:150]}"

    data = payload.get("data", {})
    if not data:
        return False, "Unexpected API response format"

    limit_remaining = data.get("limit_remaining")
    try:
        if limit_remaining is not None and float(limit_remaining) <= 0:
            return True, "Warning: API key is valid, but the current account limit is exhausted."
    except (TypeError, ValueError):
        pass

    return True, "API key validated successfully"


def parse_producer_scores(producer_response: str, agent_names: list) -> dict:
    """
    Parse scores from Producer's response with robust fallbacks.

    Supports multiple formats:
    - "Agent Name: 7/10"
    - "Agent Name ... 7/10"
    - "Agent Name score: 7"
    - "Agent Name 7 out of 10"
    - "**Agent Name**: 7/10" (Markdown bold)
    - Also handles aliases for agents with complex names

    Args:
        producer_response: The Producer's evaluation text
        agent_names: List of agent names to look for

    Returns:
        Dictionary mapping agent names to scores (1-10)
    """
    import re
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
        # Build list of names to check (full name + aliases)
        names_to_check = [agent_name]
        if agent_name in aliases:
            names_to_check.extend(aliases[agent_name])

        found_score_for_agent = False

        for name_variant in names_to_check:
            if found_score_for_agent:
                break

            # Try multiple patterns to be robust
            patterns = [
                rf"{re.escape(name_variant)}:\s*(\d+)\s*/\s*10",  # "Name: 7/10"
                rf"{re.escape(name_variant)}.*?(\d+)\s*/\s*10",    # "Name ... 7/10"
                rf"{re.escape(name_variant)}.*?score.*?(\d+)",      # "Name score: 7"
                rf"{re.escape(name_variant)}.*?(\d+)\s*out of 10", # "Name 7 out of 10"
                rf"\*\*?{re.escape(name_variant)}\*\*?.*?(\d+)/10", # "**Name**: 7/10" (Markdown bold)
                rf"{re.escape(name_variant)}.*?(\d+)/10", # Generic catch-all near name
            ]

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

    # Fallback: Check for "Writer N" or "Writer #N" patterns if specific names aren't found
    for i, agent_name in enumerate(agent_names):
        if agent_name not in scores:
            # Look for "Writer {i+1}" or "Writer #{i+1}"
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

            if agent_name not in scores:
                print(f"{Fore.YELLOW}Warning: Could not parse score for {agent_name}")

    # Fallback: if no scores found, assign neutral scores
    if not scores and agent_names:
        print(f"{Fore.YELLOW}Warning: Could not parse any scores from Producer response")
        # Assign 5/10 to all agents as fallback
        scores = {name: 5 for name in agent_names}

    return scores


def display_leaderboard(agent_scores: dict, round_num: int = None):
    """
    Display the current leaderboard with agent scores.

    Args:
        agent_scores: Dictionary mapping agent names to list of scores
        round_num: Current round number (optional)
    """
    print(f"\n{Fore.GREEN}{'='*60}")
    if round_num:
        print(f"{Fore.GREEN}  LEADERBOARD - After Round {round_num}")
    else:
        print(f"{Fore.GREEN}  FINAL LEADERBOARD")
    print(f"{Fore.GREEN}{'='*60}\n")

    # Calculate averages and sort
    agent_averages = []
    for agent_name, scores in agent_scores.items():
        if scores:
            avg_score = sum(scores) / len(scores)
            agent_averages.append((agent_name, avg_score, scores))

    # Sort by average score (descending)
    agent_averages.sort(key=lambda x: x[1], reverse=True)

    # Display rankings
    for rank, (agent_name, avg_score, scores) in enumerate(agent_averages, 1):
        medal = "1st" if rank == 1 else "2nd" if rank == 2 else "3rd" if rank == 3 else f"{rank}th"
        score_history = ", ".join(str(s) for s in scores)
        print(f"{Fore.GREEN}{medal} {agent_name}: {avg_score:.1f}/10 avg ({score_history})")

    print(f"{Fore.GREEN}{'='*60}\n")


def display_story_state(story_manager: StoryStateManager):
    """Display the current story state."""
    state = story_manager.get_state()
    print(f"\n{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.MAGENTA}  CENTER TABLE: STORY STATE")
    print(f"{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.MAGENTA}Mode: {state.mode.upper()} | Act: {state.current_act.name} | Tension: {state.tension_level}/10")
    if state.themes:
        print(f"{Fore.MAGENTA}Themes: {', '.join(state.themes[:3])}")
    if is_dnd_mode(state.mode):
        active_threads = state.get_active_threads()
        print(f"{Fore.MAGENTA}Open Threads: {len(active_threads)} | Words: {state.word_count}")
    else:
        needs = state.get_story_needs()
        print(f"{Fore.MAGENTA}Story needs: {needs[0]}")
    print(f"{Fore.MAGENTA}{'='*60}\n")


def run_single_round(
    round_num: int,
    agents: list,
    conversation_history: list,
    user_prompt: str,
    producer_enabled: bool,
    agent_producer,
    agent_scores: dict,
    story_manager: StoryStateManager = None
):
    """
    Run a single round of the writers room.

    Args:
        round_num: Current round number
        agents: List of (agent, color, display_name) tuples
        conversation_history: Full conversation history (mutated in place)
        user_prompt: The original user prompt
        producer_enabled: Whether Producer is enabled
        agent_producer: The Producer agent instance (or None)
        agent_scores: Dictionary mapping agent names to list of scores (mutated in place)
        story_manager: Optional StoryStateManager for collaborative mode
    """
    # Print round header
    print(f"{Fore.CYAN}{'─'*60}")
    print(f"{Fore.CYAN}  ROUND {round_num}")
    print(f"{Fore.CYAN}{'─'*60}")

    # Display story state if available
    if story_manager:
        display_story_state(story_manager)

    # Each agent takes a turn
    for agent, color, display_name in agents:
        # Get story context for this agent if available
        story_context = None
        if story_manager:
            if is_dnd_mode(story_manager.state.mode):
                story_context = build_dnd_story_context(
                    story_manager,
                    conversation_history,
                    display_name,
                    round_num,
                )
            else:
                story_context = story_manager.state.to_prompt_context()

        if story_manager and is_dnd_mode(story_manager.state.mode):
            response = generate_dnd_turn(
                agent,
                conversation_history,
                story_context or "",
                display_name,
            )
        else:
            response = agent.generate_response(conversation_history, story_context=story_context)
        print_agent_response(display_name, response, color)

        # Add to conversation history
        conversation_history.append({
            "role": "assistant",
            "content": response,
            "name": display_name,
            "round": round_num,
        })

        # Update story state
        if story_manager:
            story_manager.process_contribution(response, display_name, round_num)

    # Producer evaluation after each round
    if producer_enabled and agent_producer:
        print(f"\n{Fore.GREEN}{'─'*60}")
        print(f"{Fore.GREEN}  THE PRODUCER'S VERDICT")
        print(f"{Fore.GREEN}{'─'*60}\n")

        # Build context for Producer with agent names prepended so Producer knows who wrote what
        round_context = []
        for msg in conversation_history:
            if msg['role'] == 'assistant' and 'name' in msg:
                # Create a copy with the name prepended
                new_msg = msg.copy()
                new_msg['content'] = f"{msg['name']}: {msg['content']}"
                round_context.append(new_msg)
            else:
                round_context.append(msg)

        # Add instruction for Producer at the end with explicit agent names
        agent_names = [name for _, _, name in agents]
        agent_names_str = ", ".join(agent_names)

        # Add mode-specific criteria if using story manager
        mode_criteria = ""
        if story_manager:
            mode_criteria = f"\n\nMode-specific criteria: {get_producer_mode_criteria(story_manager.state.mode)}"

        round_context.append({
            "role": "user",
            "content": f"Judge round {round_num}. Score these writers: [{agent_names_str}]. IMPORTANT: Use the EXACT names provided (e.g. 'Rod Serling: 7/10'). Do NOT use 'Writer 1' or aliases.{mode_criteria}"
        })

        # Get Producer context if available
        producer_story_context = None
        if story_manager:
            producer_story_context = story_manager.get_producer_context()

        producer_response = agent_producer.generate_response(round_context, story_context=producer_story_context)
        print_agent_response("The Producer", producer_response, Fore.GREEN)

        # Parse scores from Producer's response
        round_scores = parse_producer_scores(producer_response, agent_names)

        # Update score tracking
        for agent_name, score in round_scores.items():
            if agent_name in agent_scores:
                agent_scores[agent_name].append(score)

        # Display leaderboard if we got scores
        if round_scores:
            display_leaderboard(agent_scores, round_num)


def select_story_mode() -> str:
    """Let user select a story mode."""
    print(f"\n{Fore.CYAN}Available Story Modes:")
    modes = list(STORY_MODES.keys())
    for i, mode in enumerate(modes, 1):
        mode_info = STORY_MODES[mode]
        print(f"  {i}. {mode_info['name']}: {mode_info['description']}")

    print()
    choice = input(f"{Fore.WHITE}Select mode (1-{len(modes)}) or press Enter for Horror: {Style.RESET_ALL}").strip()

    if choice and choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(modes):
            return modes[idx]

    return "horror"


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Writers Room: AI agents collaborate on creative writing",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "-r", "--rounds",
        type=int,
        default=None,
        help="Number of rounds to run (default: prompt user)"
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default=None,
        help=f"Override model for all agents (default: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=list(STORY_MODES.keys()),
        default=None,
        help="Story mode (horror, noir, comedy, sci-fi, literary, fantasy, dnd)"
    )
    parser.add_argument(
        "--no-continue",
        action="store_true",
        help="Don't prompt to continue after rounds complete"
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip API key validation on startup (faster but riskier)"
    )
    parser.add_argument(
        "-t", "--temperature",
        type=float,
        default=None,
        help="Override temperature for all agents (0.0-2.0, default: 0.9)"
    )
    parser.add_argument(
        "--no-producer",
        action="store_true",
        help="Disable The Producer agent"
    )
    parser.add_argument(
        "--fire-worst",
        action="store_true",
        help="Producer fires the worst performer at the end (requires Producer)"
    )
    parser.add_argument(
        "--create-agent",
        action="store_true",
        help="Interactive mode to create a custom agent"
    )
    return parser.parse_args()


def main():
    """Main orchestrator for the Writers Room."""
    args = parse_args()

    # Handle custom agent creation mode
    if args.create_agent:
        from custom_agents import interactive_create_agent
        interactive_create_agent()
        return

    print_banner()

    # Validate API key
    if not args.skip_validation:
        print(f"{Fore.CYAN}Validating API key...")
        is_valid, message = validate_api_key()

        if not is_valid:
            print(f"{Fore.RED}ERROR: {message}")
            print(f"{Fore.YELLOW}Please check your .env file and ensure OPENROUTER_API_KEY is set.")
            print(f"{Fore.YELLOW}See .env.example for reference.")
            sys.exit(1)
        else:
            if "Warning" in message:
                print(f"{Fore.YELLOW}Warning: {message}")
            else:
                print(f"{Fore.GREEN}OK: {message}")
    else:
        if not os.getenv("OPENROUTER_API_KEY"):
            print(f"{Fore.RED}ERROR: OPENROUTER_API_KEY not found in environment.")
            print(f"{Fore.YELLOW}Please create a .env file with your OpenRouter API key.")
            sys.exit(1)

    # Select story mode
    if args.mode:
        story_mode = args.mode
    else:
        story_mode = select_story_mode()

    mode_info = STORY_MODES.get(story_mode, STORY_MODES["horror"])
    print(f"\n{Fore.MAGENTA}Story Mode: {mode_info['name']}")
    print(f"{Fore.MAGENTA}{mode_info['atmosphere']}\n")

    # Initialize the session roster
    print(f"{Fore.CYAN}Initializing collaborative writers room...\n")

    # Use model and temperature overrides if provided
    model_override = args.model or DEFAULT_MODEL
    temperature = args.temperature if args.temperature is not None else 0.9

    agent_roster = get_agent_roster(story_mode)

    # The Producer is intentionally disabled for CLI D&D mode.
    producer_enabled = not args.no_producer and not is_dnd_mode(story_mode)
    agent_producer = None
    if producer_enabled:
        producer_prompt = PRODUCER + f"\n\nMode-specific focus: {get_producer_mode_criteria(story_mode)}"
        agent_producer = Agent(
            name="The Producer",
            model=model_override,
            system_prompt=producer_prompt,
            temperature=0.7,  # Lower temperature for more consistent judging
            max_tokens=300     # Producer needs more tokens to evaluate all 6 agents
        )

    agents = []
    for spec in agent_roster:
        max_tokens = 80
        window_size = 15
        if is_dnd_mode(story_mode):
            max_tokens = 120 if spec["name"] == "Dungeon Master" else 90
            window_size = 8
        agents.append(
            (
                Agent(
                    name=spec["name"],
                    model=model_override,
                    system_prompt=spec["system_prompt"],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    window_size=window_size,
                ),
                CLI_COLOR_BY_HEX.get(spec["color"], Fore.WHITE),
                spec["name"],
            )
        )

    # Initialize scoring system
    agent_scores = {spec["name"]: [] for spec in agent_roster}

    for spec in agent_roster:
        color = CLI_COLOR_BY_HEX.get(spec["color"], Fore.WHITE)
        print(f"{color}+ {spec['name']} ({spec['specialty']})")
    if producer_enabled:
        print(f"{Fore.GREEN}+ The Producer (Quality Evaluation)")
    elif is_dnd_mode(story_mode):
        print(f"{Fore.YELLOW}+ D&D mode runs without The Producer, leaderboard scoring, or story-needs prompts")

    print(f"\n{Fore.YELLOW}Model: {model_override}")

    if args.temperature is not None:
        print(f"{Fore.YELLOW}Temperature: {temperature}")

    # Get user's starting prompt
    print(f"\n{Fore.CYAN}{'─'*60}")
    user_prompt = input(f"{Fore.WHITE}Enter your story prompt: {Style.RESET_ALL}").strip()

    if not user_prompt:
        print(f"{Fore.RED}No prompt provided. Exiting.")
        sys.exit(0)

    # Initialize story state manager
    story_manager = StoryStateManager(premise=user_prompt, mode=story_mode)

    # Get number of rounds (from CLI or prompt user)
    if args.rounds:
        rounds = args.rounds
    else:
        try:
            rounds_input = input(f"{Fore.WHITE}Number of rounds (default 3): {Style.RESET_ALL}").strip()
            rounds = int(rounds_input) if rounds_input else 3
            if rounds < 1:
                print(f"{Fore.YELLOW}Using minimum of 1 round.")
                rounds = 1
        except ValueError:
            print(f"{Fore.YELLOW}Invalid input. Using 3 rounds.")
            rounds = 3

    print(f"{Fore.CYAN}{'─'*60}\n")

    # Initialize conversation history
    conversation_history = [
        {"role": "user", "content": get_session_opening_prompt(story_mode, user_prompt)}
    ]

    # Run rounds of collaboration
    print(f"{Fore.CYAN}Starting {rounds} rounds of collaborative storytelling...\n")

    for round_num in range(1, rounds + 1):
        run_single_round(
            round_num=round_num,
            agents=agents,
            conversation_history=conversation_history,
            user_prompt=user_prompt,
            producer_enabled=producer_enabled,
            agent_producer=agent_producer,
            agent_scores=agent_scores,
            story_manager=story_manager
        )

    # Initial rounds complete
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}  ROUNDS COMPLETE")
    print(f"{Fore.CYAN}{'='*60}\n")

    # Ask if user wants to continue (unless disabled)
    if not args.no_continue:
        while True:
            continue_choice = input(f"{Fore.WHITE}Continue with more rounds? (y/n or number of rounds): {Style.RESET_ALL}").strip().lower()

            if continue_choice in ['n', 'no']:
                break
            elif continue_choice in ['y', 'yes']:
                # Default to 1 more round
                additional_rounds = 1
            else:
                # Try to parse as number
                try:
                    additional_rounds = int(continue_choice)
                    if additional_rounds < 1:
                        print(f"{Fore.YELLOW}Please enter a valid number of rounds.")
                        continue
                except ValueError:
                    print(f"{Fore.YELLOW}Please enter 'y', 'n', or a number.")
                    continue

            # Run additional rounds
            print(f"\n{Fore.CYAN}Continuing with {additional_rounds} more round(s)...\n")
            current_round = rounds + 1

            for round_num in range(current_round, current_round + additional_rounds):
                run_single_round(
                    round_num=round_num,
                    agents=agents,
                    conversation_history=conversation_history,
                    user_prompt=user_prompt,
                    producer_enabled=producer_enabled,
                    agent_producer=agent_producer,
                    agent_scores=agent_scores,
                    story_manager=story_manager
                )

            rounds += additional_rounds
            print(f"\n{Fore.CYAN}{'='*60}")
            print(f"{Fore.CYAN}  ROUNDS COMPLETE (Total: {rounds})")
            print(f"{Fore.CYAN}{'='*60}\n")

    # Final results and winner declaration
    if producer_enabled and agent_producer:
        # Calculate final averages
        agent_averages = []
        for agent_name, scores in agent_scores.items():
            if scores:
                avg_score = sum(scores) / len(scores)
                agent_averages.append((agent_name, avg_score, scores))

        if agent_averages:
            # Sort by average score
            agent_averages.sort(key=lambda x: x[1], reverse=True)

            # Display final leaderboard
            display_leaderboard(agent_scores)

            # Declare winner
            winner_name, winner_score, _ = agent_averages[0]
            print(f"{Fore.GREEN}{'='*60}")
            print(f"{Fore.GREEN}   WINNER: {winner_name} with {winner_score:.1f}/10 average!")
            print(f"{Fore.GREEN}{'='*60}\n")

            # Optional: Fire worst performer
            if args.fire_worst and len(agent_averages) > 1:
                worst_name, worst_score, _ = agent_averages[-1]
                print(f"{Fore.RED}{'='*60}")
                print(f"{Fore.RED}   {worst_name} has been FIRED!")
                print(f"{Fore.RED}   (Lowest score: {worst_score:.1f}/10)")
                print(f"{Fore.RED}{'='*60}\n")

    # Save transcript with story state
    transcript_path = save_transcript(
        user_prompt,
        conversation_history,
        story_state=story_manager.state,
    )

    final_averages = []
    for agent_name, scores in agent_scores.items():
        if scores:
            avg_score = sum(scores) / len(scores)
            final_averages.append((agent_name, avg_score, scores))
    final_averages.sort(key=lambda item: item[1], reverse=True)
    leaderboard = [
        {
            "name": name,
            "average": round(avg_score, 1),
            "scores": scores,
        }
        for name, avg_score, scores in final_averages
    ]
    brief_path = render_session_brief(
        prompt=user_prompt,
        mode=story_mode,
        story_state=story_manager.state,
        conversation_history=conversation_history,
        leaderboard=leaderboard,
        transcript_path=transcript_path,
    )
    if brief_path:
        print(f"{Fore.CYAN}Session brief saved to: {brief_path}")

    print(f"\n{Fore.GREEN}The story is complete. Thank you for writing!\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Session interrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}ERROR: {str(e)}")
        sys.exit(1)
