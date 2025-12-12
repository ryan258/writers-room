#!/usr/bin/env python3
"""
Writers Room: The Mischief Engine

A chaotic AI writers room where three agents with wildly different
personalities collaborate (and argue) over creative prompts.
"""

import os
import sys
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


def main():
    """Main orchestrator for the Writers Room."""
    print_banner()

    # Check for API key
    if not os.getenv("OPENROUTER_API_KEY"):
        print(f"{Fore.RED}ERROR: OPENROUTER_API_KEY not found in environment.")
        print(f"{Fore.YELLOW}Please create a .env file with your OpenRouter API key.")
        print(f"{Fore.YELLOW}See .env.example for reference.")
        sys.exit(1)

    # Initialize the six agents
    print(f"{Fore.CYAN}🎬 Initializing legendary writers...\n")

    agent_serling = Agent(
        name="Rod Serling",
        model=RECOMMENDED_MODELS["rod_serling"],
        system_prompt=ROD_SERLING
    )

    agent_king = Agent(
        name="Stephen King",
        model=RECOMMENDED_MODELS["stephen_king"],
        system_prompt=STEPHEN_KING
    )

    agent_lovecraft = Agent(
        name="H.P. Lovecraft",
        model=RECOMMENDED_MODELS["hp_lovecraft"],
        system_prompt=HP_LOVECRAFT
    )

    agent_borges = Agent(
        name="Jorge Luis Borges",
        model=RECOMMENDED_MODELS["jorge_borges"],
        system_prompt=JORGE_BORGES
    )

    agent_stack = Agent(
        name="Robert Stack",
        model=RECOMMENDED_MODELS["robert_stack"],
        system_prompt=ROBERT_STACK
    )

    agent_rip = Agent(
        name="RIP Tequila Bot",
        model=RECOMMENDED_MODELS["marketing"],
        system_prompt=MARKETING_EXEC
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

    # Get user's starting prompt
    print(f"\n{Fore.CYAN}{'─'*60}")
    user_prompt = input(f"{Fore.WHITE}Enter your story prompt: {Style.RESET_ALL}").strip()

    if not user_prompt:
        print(f"{Fore.RED}No prompt provided. Exiting.")
        sys.exit(0)

    print(f"{Fore.CYAN}{'─'*60}\n")

    # Initialize conversation history
    conversation_history = [
        {"role": "user", "content": f"Write a scene about: {user_prompt}"}
    ]

    # Run 3 rounds of collaboration
    rounds = 3
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

    # Session complete
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}  SESSION COMPLETE")
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
