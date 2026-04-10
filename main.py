#!/usr/bin/env python3
"""
Writers Room: Collaborative Story Excellence Engine

An elite AI writers room where legendary authors collaborate around
a shared "Center Table" to create unforgettably potent stories.
"""

import argparse
import json
import os
import sys
from typing import Any
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

from lib.pipeline import (
    generate_pipeline_report_from_draft,
    get_pipeline_failures,
    retry_failed_pipeline_items,
)
from lib.personalities import STORY_MODES, DEFAULT_MODEL, is_dnd_mode
from lib.session import SessionEvent, SessionOrchestrator

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

ACT_NAME_BY_VALUE = {
    1: "SETUP",
    2: "CONFRONTATION",
    3: "RESOLUTION",
}


def print_banner():
    """Print the Writers Room banner."""
    print(f"\n{Fore.CYAN}{'=' * 60}")
    print(f"{Fore.CYAN}    WRITERS ROOM: COLLABORATIVE STORY EXCELLENCE")
    print(f"{Fore.CYAN}{'=' * 60}\n")


def print_agent_response(agent_name: str, response: str, color: str):
    """
    Print an agent's response with colored formatting.

    Args:
        agent_name: Name of the agent
        response: The agent's response text
        color: Colorama color constant (e.g., Fore.GREEN)
    """
    print(f"\n{color}+-- {agent_name.upper()} {'-' * (55 - len(agent_name))}")
    print(f"{color}|")
    for line in response.split("\n"):
        print(f"{color}|  {line}")
    print(f"{color}+{'-' * 58}\n")


def display_leaderboard(leaderboard: list[dict[str, Any]], round_num: int | None = None):
    """Display the current leaderboard using orchestrator payload data."""
    print(f"\n{Fore.GREEN}{'=' * 60}")
    if round_num:
        print(f"{Fore.GREEN}  LEADERBOARD - After Round {round_num}")
    else:
        print(f"{Fore.GREEN}  FINAL LEADERBOARD")
    print(f"{Fore.GREEN}{'=' * 60}\n")

    for rank, entry in enumerate(leaderboard, 1):
        medal = "1st" if rank == 1 else "2nd" if rank == 2 else "3rd" if rank == 3 else f"{rank}th"
        agent_name = entry.get("name", "Agent")
        avg_score = entry.get("average", 0.0)
        scores = entry.get("scores") or []
        score_history = ", ".join(str(score) for score in scores)
        print(f"{Fore.GREEN}{medal} {agent_name}: {avg_score:.1f}/10 avg ({score_history})")

    print(f"{Fore.GREEN}{'=' * 60}\n")


def display_story_state(state_payload: dict[str, Any] | None):
    """Display the current story state from an orchestrator event payload."""
    if not state_payload:
        return

    mode = str(state_payload.get("mode", "horror"))
    act_value = state_payload.get("current_act")
    act_name = ACT_NAME_BY_VALUE.get(act_value, str(act_value or "UNKNOWN"))
    tension_level = state_payload.get("tension_level", 0)

    print(f"\n{Fore.MAGENTA}{'=' * 60}")
    print(f"{Fore.MAGENTA}  CENTER TABLE: STORY STATE")
    print(f"{Fore.MAGENTA}{'=' * 60}")
    print(f"{Fore.MAGENTA}Mode: {mode.upper()} | Act: {act_name} | Tension: {tension_level}/10")

    themes = state_payload.get("themes") or []
    if themes:
        print(f"{Fore.MAGENTA}Themes: {', '.join(themes[:3])}")

    if is_dnd_mode(mode):
        open_threads = state_payload.get("open_threads", 0)
        word_count = state_payload.get("word_count", 0)
        print(f"{Fore.MAGENTA}Open Threads: {open_threads} | Words: {word_count}")
    else:
        story_needs = state_payload.get("story_needs") or []
        if story_needs:
            print(f"{Fore.MAGENTA}Story needs: {story_needs[0]}")

    print(f"{Fore.MAGENTA}{'=' * 60}\n")


class CliSessionSink:
    """Render SessionOrchestrator events to the terminal."""

    def __init__(self):
        self.pending_story_state: dict[str, Any] | None = None
        self.latest_summary: dict[str, Any] | None = None
        self.error_messages: list[str] = []
        self._handlers = {
            SessionEvent.SESSION_STARTED: self._on_session_started,
            SessionEvent.SESSION_RESUMED: self._on_session_resumed,
            SessionEvent.STORY_STATE_UPDATE: self._on_story_state_update,
            SessionEvent.ROUND_STARTED: self._on_round_started,
            SessionEvent.AGENT_RESPONSE: self._on_agent_response,
            SessionEvent.PRODUCER_VERDICT: self._on_producer_verdict,
            SessionEvent.SESSION_COMPLETED: self._on_session_completed,
            SessionEvent.ERROR: self._on_error,
        }

    def __call__(self, event: str, payload: dict[str, Any]) -> None:
        handler = self._handlers.get(event)
        if handler is not None:
            handler(payload)

    @property
    def had_error(self) -> bool:
        return bool(self.error_messages)

    def print_final_summary(self, *, fire_worst: bool) -> None:
        """Print the final CLI summary from the last session completion payload."""
        summary = self.latest_summary or {}
        leaderboard = summary.get("leaderboard") or []
        winner = summary.get("winner")
        worst = summary.get("worst")

        if leaderboard:
            display_leaderboard(leaderboard)

        if winner:
            print(f"{Fore.GREEN}{'=' * 60}")
            print(f"{Fore.GREEN}   WINNER: {winner['name']} with {winner['average']:.1f}/10 average!")
            print(f"{Fore.GREEN}{'=' * 60}\n")

        if fire_worst and worst:
            print(f"{Fore.RED}{'=' * 60}")
            print(f"{Fore.RED}   {worst['name']} has been FIRED!")
            print(f"{Fore.RED}   (Lowest score: {worst['average']:.1f}/10)")
            print(f"{Fore.RED}{'=' * 60}\n")

        transcript_path = summary.get("transcript_path")
        if transcript_path:
            print(f"{Fore.CYAN}Transcript saved to: {transcript_path}")

        brief_path = summary.get("brief_path")
        if brief_path:
            print(f"{Fore.CYAN}Session brief saved to: {brief_path}")

    def _on_session_started(self, payload: dict[str, Any]) -> None:
        for agent in payload.get("agent_roster", []):
            color = CLI_COLOR_BY_HEX.get(agent.get("color"), Fore.WHITE)
            specialty = agent.get("specialty", "")
            print(f"{color}+ {agent.get('name', 'Agent')} ({specialty})")

        config = payload.get("config") or {}
        mode = payload.get("mode", "horror")
        if config.get("producer_enabled"):
            print(f"{Fore.GREEN}+ The Producer (Quality Evaluation)")
        elif is_dnd_mode(mode):
            print(f"{Fore.YELLOW}+ D&D mode runs without The Producer, leaderboard scoring, or story-needs prompts")

    def _on_session_resumed(self, payload: dict[str, Any]) -> None:
        self.latest_summary = None

    def _on_story_state_update(self, payload: dict[str, Any]) -> None:
        self.pending_story_state = payload.get("state")

    def _on_round_started(self, payload: dict[str, Any]) -> None:
        round_num = payload.get("round")
        print(f"{Fore.CYAN}{'─' * 60}")
        print(f"{Fore.CYAN}  ROUND {round_num}")
        print(f"{Fore.CYAN}{'─' * 60}")
        display_story_state(self.pending_story_state)
        self.pending_story_state = None

    def _on_agent_response(self, payload: dict[str, Any]) -> None:
        color = CLI_COLOR_BY_HEX.get(payload.get("color"), Fore.WHITE)
        print_agent_response(
            payload.get("agent", "Agent"),
            payload.get("response", ""),
            color,
        )

    def _on_producer_verdict(self, payload: dict[str, Any]) -> None:
        print(f"\n{Fore.GREEN}{'─' * 60}")
        print(f"{Fore.GREEN}  THE PRODUCER'S VERDICT")
        print(f"{Fore.GREEN}{'─' * 60}\n")
        print_agent_response("The Producer", payload.get("response", ""), Fore.GREEN)

        leaderboard = payload.get("leaderboard") or []
        if leaderboard:
            display_leaderboard(leaderboard, payload.get("round"))

    def _on_session_completed(self, payload: dict[str, Any]) -> None:
        self.latest_summary = payload

    def _on_error(self, payload: dict[str, Any]) -> None:
        message = payload.get("message", "Unknown error")
        self.error_messages.append(message)
        print(f"{Fore.RED}ERROR: {message}")


def _handle_pipeline_cli_result(pipeline_dir: str, *, action_label: str) -> None:
    """Print a CLI summary and exit non-zero if the pipeline still has failures."""
    failures = get_pipeline_failures(pipeline_dir)
    if not failures:
        print(f"{Fore.CYAN}{action_label} written to: {pipeline_dir}")
        return

    print(f"{Fore.YELLOW}{action_label} completed with failures in: {pipeline_dir}")
    if failures["status_failed"]:
        print(f"{Fore.YELLOW}- status.md is still pending")
    if failures["marketing_failed"]:
        failed_items = ", ".join(failures["marketing_failed"])
        print(f"{Fore.YELLOW}- marketing assets still pending: {failed_items}")
    print(
        f"{Fore.YELLOW}See {os.path.join(pipeline_dir, '.failures.json')} for the retry manifest."
    )
    sys.exit(1)


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
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-r", "--rounds",
        type=int,
        default=None,
        help="Number of rounds to run (default: prompt user)",
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default=None,
        help=f"Override model for all agents (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=list(STORY_MODES.keys()),
        default=None,
        help="Story mode (horror, noir, comedy, sci-fi, literary, fantasy, dnd)",
    )
    parser.add_argument(
        "--no-continue",
        action="store_true",
        help="Don't prompt to continue after rounds complete",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip API key validation on startup (faster but riskier)",
    )
    parser.add_argument(
        "-t", "--temperature",
        type=float,
        default=None,
        help="Override temperature for all agents (0.0-2.0, default: 0.9)",
    )
    parser.add_argument(
        "--no-producer",
        action="store_true",
        help="Disable The Producer agent",
    )
    parser.add_argument(
        "--fire-worst",
        action="store_true",
        help="Producer fires the worst performer at the end (requires Producer)",
    )
    parser.add_argument(
        "--create-agent",
        action="store_true",
        help="Interactive mode to create a custom agent",
    )
    parser.add_argument(
        "--run-pipeline",
        type=str,
        default=None,
        metavar="DRAFT_PATH",
        help=(
            "Regenerate the full pipelines/{YYMMDD}_{title-name}/ directory "
            "(status + all marketing assets) from an edited final draft"
        ),
    )
    parser.add_argument(
        "--retry-pipeline",
        type=str,
        default=None,
        metavar="DRAFT_PATH",
        help=(
            "Retry only the items recorded in "
            "pipelines/{YYMMDD}_{title-name}/.failures.json "
            "(no-op if the manifest is missing or empty)"
        ),
    )
    return parser.parse_args()


def _prompt_for_rounds(args: argparse.Namespace) -> int:
    """Return the requested number of rounds, prompting when needed."""
    if args.rounds:
        return args.rounds

    try:
        rounds_input = input(f"{Fore.WHITE}Number of rounds (default 3): {Style.RESET_ALL}").strip()
        rounds = int(rounds_input) if rounds_input else 3
        if rounds < 1:
            print(f"{Fore.YELLOW}Using minimum of 1 round.")
            return 1
        return rounds
    except ValueError:
        print(f"{Fore.YELLOW}Invalid input. Using 3 rounds.")
        return 3


def _build_cli_config(
    *,
    args: argparse.Namespace,
    prompt: str,
    rounds: int,
    story_mode: str,
    model_override: str,
    temperature: float,
) -> dict[str, Any]:
    """Build the session config used by the shared orchestrator."""
    return {
        "prompt": prompt,
        "rounds": rounds,
        "mode": story_mode,
        "model": model_override,
        "temperature": temperature,
        "producer_enabled": not args.no_producer and not is_dnd_mode(story_mode),
        "fire_worst": args.fire_worst,
        "voice_enabled": False,
        "include_custom_agents": False,
        "produce_final_draft": False,
    }


def main():
    """Main orchestrator for the Writers Room CLI."""
    args = parse_args()

    if args.create_agent:
        from lib.custom_agents import interactive_create_agent
        interactive_create_agent()
        return

    print_banner()

    if not args.skip_validation:
        print(f"{Fore.CYAN}Validating API key...")
        is_valid, message = validate_api_key()
        if not is_valid:
            print(f"{Fore.RED}ERROR: {message}")
            print(f"{Fore.YELLOW}Please check your .env file and ensure OPENROUTER_API_KEY is set.")
            print(f"{Fore.YELLOW}See .env.example for reference.")
            sys.exit(1)
        if "Warning" in message:
            print(f"{Fore.YELLOW}Warning: {message}")
        else:
            print(f"{Fore.GREEN}OK: {message}")
    else:
        if not os.getenv("OPENROUTER_API_KEY"):
            print(f"{Fore.RED}ERROR: OPENROUTER_API_KEY not found in environment.")
            print(f"{Fore.YELLOW}Please create a .env file with your OpenRouter API key.")
            sys.exit(1)

    if args.run_pipeline:
        pipeline_dir = generate_pipeline_report_from_draft(
            draft_path=args.run_pipeline,
            model=args.model or DEFAULT_MODEL,
        )
        _handle_pipeline_cli_result(
            pipeline_dir,
            action_label="Pipeline directory",
        )
        return

    if args.retry_pipeline:
        pipeline_dir = retry_failed_pipeline_items(
            draft_path=args.retry_pipeline,
            model=args.model or DEFAULT_MODEL,
        )
        _handle_pipeline_cli_result(
            pipeline_dir,
            action_label="Pipeline retry",
        )
        return

    story_mode = args.mode or select_story_mode()
    mode_info = STORY_MODES.get(story_mode, STORY_MODES["horror"])
    print(f"\n{Fore.MAGENTA}Story Mode: {mode_info['name']}")
    print(f"{Fore.MAGENTA}{mode_info['atmosphere']}\n")

    print(f"{Fore.CYAN}Initializing collaborative writers room...\n")

    model_override = args.model or DEFAULT_MODEL
    temperature = args.temperature if args.temperature is not None else 0.9

    user_prompt = input(f"{Fore.WHITE}Enter your story prompt: {Style.RESET_ALL}").strip()
    if not user_prompt:
        print(f"{Fore.RED}No prompt provided. Exiting.")
        sys.exit(0)

    rounds = _prompt_for_rounds(args)
    print(f"{Fore.CYAN}{'─' * 60}\n")

    sink = CliSessionSink()
    orchestrator = SessionOrchestrator(sink)
    config = _build_cli_config(
        args=args,
        prompt=user_prompt,
        rounds=rounds,
        story_mode=story_mode,
        model_override=model_override,
        temperature=temperature,
    )
    orchestrator.initialize(user_prompt, config)

    print(f"\n{Fore.YELLOW}Model: {model_override}")
    if args.temperature is not None:
        print(f"{Fore.YELLOW}Temperature: {temperature}")

    total_rounds = rounds
    print(f"\n{Fore.CYAN}Starting {rounds} rounds of collaborative storytelling...\n")
    orchestrator.run_session(rounds)
    if sink.had_error:
        sys.exit(1)

    print(f"\n{Fore.CYAN}{'=' * 60}")
    print(f"{Fore.CYAN}  ROUNDS COMPLETE")
    print(f"{Fore.CYAN}{'=' * 60}\n")

    if not args.no_continue:
        while True:
            continue_choice = input(
                f"{Fore.WHITE}Continue with more rounds? (y/n or number of rounds): {Style.RESET_ALL}"
            ).strip().lower()

            if continue_choice in ["n", "no"]:
                break
            if continue_choice in ["y", "yes"]:
                additional_rounds = 1
            else:
                try:
                    additional_rounds = int(continue_choice)
                    if additional_rounds < 1:
                        print(f"{Fore.YELLOW}Please enter a valid number of rounds.")
                        continue
                except ValueError:
                    print(f"{Fore.YELLOW}Please enter 'y', 'n', or a number.")
                    continue

            print(f"\n{Fore.CYAN}Continuing with {additional_rounds} more round(s)...\n")
            orchestrator.resume(additional_rounds)
            if sink.had_error:
                sys.exit(1)

            total_rounds += additional_rounds
            print(f"\n{Fore.CYAN}{'=' * 60}")
            print(f"{Fore.CYAN}  ROUNDS COMPLETE (Total: {total_rounds})")
            print(f"{Fore.CYAN}{'=' * 60}\n")

    sink.print_final_summary(fire_worst=args.fire_worst)
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
