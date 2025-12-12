#!/usr/bin/env python3
"""
Writers Room: The Mischief Engine

A chaotic AI writers room where three agents with wildly different
personalities collaborate (and argue) over creative prompts.
"""

import os
import sys
import argparse
from datetime import datetime
from colorama import init, Fore, Style

from agents import Agent
from personalities import (
    ROD_SERLING,
    STEPHEN_KING,
    HP_LOVECRAFT,
    JORGE_BORGES,
    ROBERT_STACK,
    MARKETING_EXEC,
    RECOMMENDED_MODELS
)

# Initialize colorama for cross-platform colored terminal output
init(autoreset=True)


def print_banner():
    """Print the Writers Room banner."""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}    AGENT SWARM WRITERS ROOM: THE MISCHIEF ENGINE")
    print(f"{Fore.CYAN}{'='*60}\n")


def print_agent_response(agent_name: str, response: str, color: str):
    """
    Print an agent's response with colored formatting.

    Args:
        agent_name: Name of the agent
        response: The agent's response text
        color: Colorama color constant (e.g., Fore.GREEN)
    """
    print(f"\n{color}╔══ {agent_name.upper()} {'═'*(55-len(agent_name))}")
    print(f"{color}║")
    # Wrap text for better readability
    for line in response.split('\n'):
        print(f"{color}║  {line}")
    print(f"{color}╚{'═'*58}\n")


def save_transcript(prompt: str, conversation_history: list, filename: str = None):
    """
    Save the conversation to a transcript file.

    Args:
        prompt: The initial prompt
        conversation_history: List of all messages
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

    print(f"{Fore.CYAN}💾 Transcript saved to: {filename}")


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
            model="mistralai/ministral-3b-2512",
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
        help="Override model for all agents (e.g., 'mistralai/ministral-3b-2512')"
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
    return parser.parse_args()


def main():
    """Main orchestrator for the Writers Room."""
    args = parse_args()
    print_banner()

    # Validate API key
    if not args.skip_validation:
        print(f"{Fore.CYAN}🔑 Validating API key...")
        is_valid, message = validate_api_key()

        if not is_valid:
            print(f"{Fore.RED}❌ {message}")
            print(f"{Fore.YELLOW}Please check your .env file and ensure OPENROUTER_API_KEY is set.")
            print(f"{Fore.YELLOW}See .env.example for reference.")
            sys.exit(1)
        else:
            if "Warning" in message:
                print(f"{Fore.YELLOW}⚠️  {message}")
            else:
                print(f"{Fore.GREEN}✓ {message}")
    else:
        if not os.getenv("OPENROUTER_API_KEY"):
            print(f"{Fore.RED}ERROR: OPENROUTER_API_KEY not found in environment.")
            print(f"{Fore.YELLOW}Please create a .env file with your OpenRouter API key.")
            sys.exit(1)

    # Initialize the six agents
    print(f"{Fore.CYAN}🎬 Initializing legendary writers...\n")

    # Use model and temperature overrides if provided
    model_override = args.model
    temperature = args.temperature if args.temperature is not None else 0.9

    agent_serling = Agent(
        name="Rod Serling",
        model=model_override or RECOMMENDED_MODELS["rod_serling"],
        system_prompt=ROD_SERLING,
        temperature=temperature
    )

    agent_king = Agent(
        name="Stephen King",
        model=model_override or RECOMMENDED_MODELS["stephen_king"],
        system_prompt=STEPHEN_KING,
        temperature=temperature
    )

    agent_lovecraft = Agent(
        name="H.P. Lovecraft",
        model=model_override or RECOMMENDED_MODELS["hp_lovecraft"],
        system_prompt=HP_LOVECRAFT,
        temperature=temperature
    )

    agent_borges = Agent(
        name="Jorge Luis Borges",
        model=model_override or RECOMMENDED_MODELS["jorge_borges"],
        system_prompt=JORGE_BORGES,
        temperature=temperature
    )

    agent_stack = Agent(
        name="Robert Stack",
        model=model_override or RECOMMENDED_MODELS["robert_stack"],
        system_prompt=ROBERT_STACK,
        temperature=temperature
    )

    agent_rip = Agent(
        name="RIP Tequila Bot",
        model=model_override or RECOMMENDED_MODELS["marketing"],
        system_prompt=MARKETING_EXEC,
        temperature=temperature
    )

    agents = [
        (agent_serling, Fore.CYAN, "Rod Serling"),
        (agent_king, Fore.RED, "Stephen King"),
        (agent_lovecraft, Fore.MAGENTA, "H.P. Lovecraft"),
        (agent_borges, Fore.BLUE, "Jorge Luis Borges"),
        (agent_stack, Fore.WHITE, "Robert Stack"),
        (agent_rip, Fore.YELLOW, "RIP Tequila Bot")
    ]

    print(f"{Fore.CYAN}✓ Rod Serling (Twilight Zone)")
    print(f"{Fore.RED}✓ Stephen King (Character Horror)")
    print(f"{Fore.MAGENTA}✓ H.P. Lovecraft (Cosmic Horror)")
    print(f"{Fore.BLUE}✓ Jorge Luis Borges (Philosophical Fiction)")
    print(f"{Fore.WHITE}✓ Robert Stack (Unsolved Mysteries)")
    print(f"{Fore.YELLOW}✓ RIP Tequila Bot (Marketing Executive)")

    if model_override:
        print(f"\n{Fore.YELLOW}📌 Using custom model: {model_override}")

    if args.temperature is not None:
        print(f"{Fore.YELLOW}🌡️  Using custom temperature: {temperature}")

    # Get user's starting prompt
    print(f"\n{Fore.CYAN}{'─'*60}")
    user_prompt = input(f"{Fore.WHITE}Enter your story prompt: {Style.RESET_ALL}").strip()

    if not user_prompt:
        print(f"{Fore.RED}No prompt provided. Exiting.")
        sys.exit(0)

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
    print(f"{Fore.CYAN}🎭 Starting {rounds} rounds of creative chaos...\n")

    for round_num in range(1, rounds + 1):
        print(f"{Fore.CYAN}{'─'*60}")
        print(f"{Fore.CYAN}  ROUND {round_num}/{rounds}")
        print(f"{Fore.CYAN}{'─'*60}")

        # Each agent takes a turn
        for agent, color, display_name in agents:
            # Agent generates response based on full context
            response = agent.generate_response(conversation_history)

            # Print with color
            print_agent_response(display_name, response, color)

            # Add to conversation history
            conversation_history.append({
                "role": "assistant",
                "content": response,
                "name": display_name
            })

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
            print(f"\n{Fore.CYAN}🎭 Continuing with {additional_rounds} more round(s)...\n")
            current_round = rounds + 1

            for round_num in range(current_round, current_round + additional_rounds):
                print(f"{Fore.CYAN}{'─'*60}")
                print(f"{Fore.CYAN}  ROUND {round_num}")
                print(f"{Fore.CYAN}{'─'*60}")

                # Each agent takes a turn
                for agent, color, display_name in agents:
                    response = agent.generate_response(conversation_history)
                    print_agent_response(display_name, response, color)
                    conversation_history.append({
                        "role": "assistant",
                        "content": response,
                        "name": display_name
                    })

            rounds += additional_rounds
            print(f"\n{Fore.CYAN}{'='*60}")
            print(f"{Fore.CYAN}  ROUNDS COMPLETE (Total: {rounds})")
            print(f"{Fore.CYAN}{'='*60}\n")

    # Save transcript
    save_transcript(user_prompt, conversation_history)

    print(f"\n{Fore.GREEN}✨ The mischief is complete. Thank you for writing!\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}⚠️  Session interrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}❌ ERROR: {str(e)}")
        sys.exit(1)
