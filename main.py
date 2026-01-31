#!/usr/bin/env python3
"""
Writers Room: Collaborative Story Excellence Engine

An elite AI writers room where legendary authors collaborate around
a shared "Center Table" to create unforgettably potent stories.
"""

import os
import sys
import argparse
from datetime import datetime
from colorama import init, Fore, Style

from lib.agents import Agent
from lib.story_state import StoryStateManager
from lib.personalities import (
    ROD_SERLING,
    STEPHEN_KING,
    HP_LOVECRAFT,
    JORGE_BORGES,
    ROBERT_STACK,
    MARKETING_EXEC,
    PRODUCER,
    RECOMMENDED_MODELS,
    STORY_MODES,
    DEFAULT_MODEL,
    build_agent_prompt,
    get_mode_prompt_context,
    get_producer_mode_criteria
)

# Initialize colorama for cross-platform colored terminal output
init(autoreset=True)


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
        f.write("WRITERS ROOM TRANSCRIPT\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        if story_state:
            f.write(f"Mode: {story_state.mode.upper()}\n")
            f.write(f"Final Act: {story_state.current_act.name}\n")
            f.write(f"Word Count: {story_state.word_count}\n")
        f.write("="*60 + "\n\n")
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


def validate_api_key():
    """Validate that the OpenRouter API key works."""
    from openai import OpenAI

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return False, "OPENROUTER_API_KEY not found in environment"

    if not api_key.startswith("sk-or-"):
        return False, "API key format appears invalid (should start with 'sk-or-')"

    # Try a minimal API call to validate the key
    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

        # Make a minimal request to test authentication
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1
        )

        # Only return True if we actually got a response
        if response and response.choices:
            return True, "API key validated successfully"
        else:
            return False, "Unexpected API response format"

    except Exception as e:
        error_str = str(e)
        # Check for specific known error types
        if "401" in error_str or "authentication" in error_str.lower() or "unauthorized" in error_str.lower():
            return False, "API key is invalid or expired"
        elif "429" in error_str or "rate limit" in error_str.lower():
            return False, "Rate limited - your API key may need credits"
        elif "404" in error_str or "not found" in error_str.lower():
            return False, "API endpoint not found - check OpenRouter URL"
        elif "timeout" in error_str.lower() or "timed out" in error_str.lower():
            return False, "Connection timeout - check your internet connection"
        elif "connection" in error_str.lower() or "network" in error_str.lower():
            return False, "Network error - check your internet connection"
        else:
            # Unknown error - fail safely and show the error
            return False, f"Validation failed: {error_str[:150]}"


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
    needs = state.get_story_needs()
    if needs:
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
            story_context = story_manager.state.to_prompt_context()

        response = agent.generate_response(conversation_history, story_context=story_context)
        print_agent_response(display_name, response, color)

        # Add to conversation history
        conversation_history.append({
            "role": "assistant",
            "content": response,
            "name": display_name
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
        help="Story mode (horror, noir, comedy, sci-fi, literary, fantasy)"
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

    # Initialize the six agents
    print(f"{Fore.CYAN}Initializing collaborative writers room...\n")

    # Use model and temperature overrides if provided
    model_override = args.model or DEFAULT_MODEL
    temperature = args.temperature if args.temperature is not None else 0.9

    # Get mode-specific context for prompts
    mode_context = get_mode_prompt_context(story_mode)

    agent_serling = Agent(
        name="Rod Serling",
        model=model_override,
        system_prompt=ROD_SERLING + mode_context,
        temperature=temperature
    )

    agent_king = Agent(
        name="Stephen King",
        model=model_override,
        system_prompt=STEPHEN_KING + mode_context,
        temperature=temperature
    )

    agent_lovecraft = Agent(
        name="H.P. Lovecraft",
        model=model_override,
        system_prompt=HP_LOVECRAFT + mode_context,
        temperature=temperature
    )

    agent_borges = Agent(
        name="Jorge Luis Borges",
        model=model_override,
        system_prompt=JORGE_BORGES + mode_context,
        temperature=temperature
    )

    agent_stack = Agent(
        name="Robert Stack",
        model=model_override,
        system_prompt=ROBERT_STACK + mode_context,
        temperature=temperature
    )

    agent_rip = Agent(
        name="RIP Tequila Bot",
        model=model_override,
        system_prompt=MARKETING_EXEC + mode_context,
        temperature=temperature
    )

    # The Producer Agent (unless disabled)
    producer_enabled = not args.no_producer
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

    agents = [
        (agent_serling, Fore.CYAN, "Rod Serling"),
        (agent_king, Fore.RED, "Stephen King"),
        (agent_lovecraft, Fore.MAGENTA, "H.P. Lovecraft"),
        (agent_borges, Fore.BLUE, "Jorge Luis Borges"),
        (agent_stack, Fore.WHITE, "Robert Stack"),
        (agent_rip, Fore.YELLOW, "RIP Tequila Bot")
    ]

    # Initialize scoring system
    agent_scores = {
        "Rod Serling": [],
        "Stephen King": [],
        "H.P. Lovecraft": [],
        "Jorge Luis Borges": [],
        "Robert Stack": [],
        "RIP Tequila Bot": []
    }

    print(f"{Fore.CYAN}+ Rod Serling (Irony & Moral Complexity)")
    print(f"{Fore.RED}+ Stephen King (Visceral Horror)")
    print(f"{Fore.MAGENTA}+ H.P. Lovecraft (Cosmic Dread)")
    print(f"{Fore.BLUE}+ Jorge Luis Borges (Paradox & Infinity)")
    print(f"{Fore.WHITE}+ Robert Stack (Mystery & Investigation)")
    print(f"{Fore.YELLOW}+ RIP Tequila Bot (Comic Relief)")
    if producer_enabled:
        print(f"{Fore.GREEN}+ The Producer (Quality Evaluation)")

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
        {"role": "user", "content": f"Write a scene about: {user_prompt}"}
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
    save_transcript(user_prompt, conversation_history, story_state=story_manager.state)

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
