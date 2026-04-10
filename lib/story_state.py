"""
Story state tracking for the runtime fields that actually shape sessions.
"""

from dataclasses import dataclass, field
from enum import Enum


class StoryAct(Enum):
    """Three-act structure for story pacing."""
    SETUP = 1
    CONFRONTATION = 2
    RESOLUTION = 3


@dataclass
class StorySegment:
    """A contribution to the story with lightweight metadata."""
    content: str
    author: str
    round_num: int
    word_count: int = 0

    def __post_init__(self):
        self.word_count = len(self.content.split())

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "author": self.author,
            "round_num": self.round_num,
            "word_count": self.word_count,
        }


@dataclass
class StoryState:
    """
    Shared runtime story state for pacing and recent context.

    The session currently tracks only the fields that are produced in runtime:
    premise, act, tension, pacing, word count, round count, and recent beats.
    """

    premise: str
    mode: str = "horror"
    current_act: StoryAct = StoryAct.SETUP
    story_segments: list = field(default_factory=list)
    tension_level: int = 3
    pacing: str = "steady"
    word_count: int = 0
    round_count: int = 0

    def add_segment(self, content: str, author: str, round_num: int):
        """Add a new story contribution."""
        segment = StorySegment(content=content, author=author, round_num=round_num)
        self.story_segments.append(segment)
        self.word_count += segment.word_count
        self.round_count = max(self.round_count, round_num)

    def update_tension(self, delta: int):
        """Adjust overall tension level."""
        self.tension_level = max(1, min(10, self.tension_level + delta))

    def advance_act(self):
        """Move to the next act if appropriate."""
        if self.current_act == StoryAct.SETUP:
            self.current_act = StoryAct.CONFRONTATION
        elif self.current_act == StoryAct.CONFRONTATION:
            self.current_act = StoryAct.RESOLUTION

    def get_story_needs(self) -> list:
        """Return a small set of honest pacing and escalation nudges."""
        if self.current_act == StoryAct.SETUP:
            if self.round_count <= 1:
                return ["Establish a concrete source of conflict or unease"]
            if self.tension_level < 4:
                return ["Raise the stakes before the setup stalls"]
            return ["Turn the setup into a concrete complication"]

        if self.current_act == StoryAct.CONFRONTATION:
            if self.tension_level < 6:
                return ["Increase tension and complications"]
            if self.tension_level > 8:
                return ["Give the story one brief breath before the next escalation"]
            return ["Drive the confrontation toward a decisive turn"]

        return ["Drive toward a decisive ending"]

    def to_prompt_context(self) -> str:
        """Generate a prompt-friendly summary for agents."""
        lines = [
            "=== THE CENTER TABLE: STORY STATE ===",
            f"Premise: {self.premise}",
            f"Mode: {self.mode.upper()}",
            f"Act: {self.current_act.name} ({self.current_act.value}/3)",
            f"Tension: {self.tension_level}/10 | Pacing: {self.pacing}",
            f"Rounds: {self.round_count} | Words: {self.word_count}",
            "",
        ]

        if self.story_segments:
            lines.append("RECENT STORY:")
            for segment in self.story_segments[-3:]:
                lines.append(f"  [{segment.author}]: {segment.content[:100]}...")
            lines.append("")

        lines.append(f"CURRENT FOCUS: {self.get_story_needs()[0]}")
        lines.append("=" * 40)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "premise": self.premise,
            "mode": self.mode,
            "current_act": self.current_act.value,
            "story_segments": [segment.to_dict() for segment in self.story_segments],
            "tension_level": self.tension_level,
            "pacing": self.pacing,
            "word_count": self.word_count,
            "round_count": self.round_count,
        }


class StoryStateManager:
    """
    Manage runtime story state updates and guidance.

    This manager tracks pacing-oriented signals and recent beats rather than
    speculative character or plot-thread structures.
    """

    def __init__(self, premise: str, mode: str = "horror"):
        self.state = StoryState(premise=premise, mode=mode)

    def process_contribution(self, content: str, author: str, round_num: int):
        """Process an agent contribution and update story state."""
        self.state.add_segment(content, author, round_num)

        content_lower = content.lower()

        high_tension = [
            "scream", "blood", "terror", "horror", "panic", "death", "kill",
            "dark", "shadow", "threat", "danger", "fear", "dread", "howl",
            "shatter", "crash", "explode", "collapse", "trap", "curse",
            "devour", "sacrifice", "ritual", "corrupted", "infernal",
            "attack", "strike", "sword", "blade", "spell", "wound", "ambush",
            "charge", "flee", "combat", "battle", "fight", "slash", "stab",
            "damage", "hit", "initiative", "weapon", "arrow", "bolt",
            "grapple", "shove", "smite", "rage", "sneak",
            "hurry", "urgent", "countdown", "closing", "sealing",
            "grinding", "stalking", "cornered", "surrounded", "locked",
            "poison", "dying", "unconscious", "failed",
        ]
        low_tension = [
            "calm", "peace", "relief", "safe", "escape", "hope",
            "rest", "heal", "quiet", "steady", "breathe", "settle",
            "laugh", "joke", "relax", "camp",
        ]

        delta = 0
        for word in high_tension:
            if word in content_lower:
                delta += 1
        for word in low_tension:
            if word in content_lower:
                delta -= 1

        delta = max(-2, min(3, delta))
        if delta:
            self.state.update_tension(delta)

        round_floor = min(8, 2 + round_num)
        if self.state.tension_level < round_floor:
            self.state.update_tension(1)

        sentences = max(1, content.count(".") + content.count("!") + content.count("?"))
        avg_sentence_len = len(content.split()) / sentences
        exclamations = content.count("!")
        if avg_sentence_len < 8 or exclamations >= 2:
            self.state.pacing = "fast"
        elif avg_sentence_len > 20:
            self.state.pacing = "slow"
        else:
            self.state.pacing = "steady"

        if self.state.current_act == StoryAct.SETUP and self.state.round_count >= 2:
            if self.state.tension_level >= 4:
                self.state.advance_act()
        elif self.state.current_act == StoryAct.CONFRONTATION and self.state.round_count >= 5:
            if self.state.tension_level >= 7:
                self.state.advance_act()

    def get_agent_guidance(self, agent_specialty: str) -> str:
        """Generate specific guidance for an agent based on current pacing needs."""
        needs = self.state.get_story_needs()
        mode_context = self._get_mode_guidance()

        guidance_lines = [
            f"Story Mode: {self.state.mode.upper()}",
            mode_context,
            "",
            "What the story needs now:",
        ]

        for need in needs[:2]:
            guidance_lines.append(f"  - {need}")

        guidance_lines.append("")
        guidance_lines.append(f"Your specialty is: {agent_specialty}")
        guidance_lines.append("Use your specialty IF it serves the story's needs.")
        guidance_lines.append("If not, focus on what the story actually needs right now.")

        return "\n".join(guidance_lines)

    def _get_mode_guidance(self) -> str:
        """Get mode-specific atmosphere guidance."""
        mode_guides = {
            "horror": "Atmosphere: Dread, unease, psychological terror. Build tension through suggestion.",
            "noir": "Atmosphere: Shadows, moral ambiguity, cynical worldview. Trust no one.",
            "comedy": "Atmosphere: Timing is everything. Subvert expectations. Find absurdity.",
            "sci-fi": "Atmosphere: Wonder and consequence. What does this technology MEAN for humanity?",
            "literary": "Atmosphere: Prose excellence. Every word earns its place. Theme over plot.",
            "fantasy": "Atmosphere: Wonder and mythic resonance. Magic has rules and costs.",
            "dnd": "Atmosphere: Run the table honestly. Present a tactical choice, let actions have consequences, and keep the adventure moving.",
        }
        return mode_guides.get(self.state.mode, "Atmosphere: Serve the story above all.")

    def get_producer_context(self) -> str:
        """Get context for the Producer to evaluate contributions."""
        return f"""Story State Summary:
Mode: {self.state.mode.upper()}
Act: {self.state.current_act.name}
Tension: {self.state.tension_level}/10
Pacing: {self.state.pacing}
Word Count: {self.state.word_count}

Evaluation Focus for {self.state.mode} mode:
- Did the contribution serve the story's needs?
- Was it coherent with what came before?
- Did it advance plot or character appropriately?
- Did it maintain the {self.state.mode} atmosphere?
"""

    def get_state(self) -> StoryState:
        """Get the current story state."""
        return self.state

    def set_mode(self, mode: str):
        """Change the story mode."""
        valid_modes = ["horror", "noir", "comedy", "sci-fi", "literary", "fantasy", "dnd"]
        if mode.lower() in valid_modes:
            self.state.mode = mode.lower()
