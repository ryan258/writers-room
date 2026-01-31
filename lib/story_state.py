"""
Story State: The Center Table Architecture

This module implements the collaborative story state system where all agents
work together around a shared "Center Table" to create cohesive narratives.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class StoryAct(Enum):
    """Three-act structure for story pacing."""
    SETUP = 1           # Establish characters, setting, and initial conflict
    CONFRONTATION = 2   # Rising action, complications, and tension
    RESOLUTION = 3      # Climax and denouement


@dataclass
class Character:
    """A character in the story with their arc and current state."""
    name: str
    role: str  # protagonist, antagonist, supporting, etc.
    motivation: str = ""
    arc_stage: str = "introduced"  # introduced, developing, transformed
    last_action: str = ""
    emotional_state: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "role": self.role,
            "motivation": self.motivation,
            "arc_stage": self.arc_stage,
            "last_action": self.last_action,
            "emotional_state": self.emotional_state
        }


@dataclass
class PlotThread:
    """A narrative thread being developed in the story."""
    id: str
    description: str
    tension_level: int = 5  # 1-10 scale
    status: str = "active"  # active, resolved, abandoned
    introduced_by: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "tension_level": self.tension_level,
            "status": self.status,
            "introduced_by": self.introduced_by
        }


@dataclass
class StorySegment:
    """A contribution to the story with metadata."""
    content: str
    author: str
    round_num: int
    word_count: int = 0
    advances_plot: bool = True

    def __post_init__(self):
        self.word_count = len(self.content.split())

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "author": self.author,
            "round_num": self.round_num,
            "word_count": self.word_count,
            "advances_plot": self.advances_plot
        }


@dataclass
class StoryState:
    """
    The Center Table: shared story state that all agents can see and build upon.

    This is the heart of the collaborative system - instead of agents competing
    with their own styles, they all focus on what the story NEEDS next.
    """
    premise: str
    mode: str = "horror"  # horror, noir, comedy, sci-fi, literary, fantasy
    current_act: StoryAct = StoryAct.SETUP

    # Story elements
    characters: dict = field(default_factory=dict)  # name -> Character
    plot_threads: list = field(default_factory=list)  # List of PlotThread
    themes: list = field(default_factory=list)  # Concepts being developed

    # Scene tracking
    scene_beats: list = field(default_factory=list)  # What's happened in current scene
    story_segments: list = field(default_factory=list)  # All contributions

    # Story health metrics
    tension_level: int = 3  # Overall tension 1-10
    pacing: str = "steady"  # slow, steady, fast, frantic
    word_count: int = 0
    round_count: int = 0

    def add_segment(self, content: str, author: str, round_num: int):
        """Add a new story contribution."""
        segment = StorySegment(content=content, author=author, round_num=round_num)
        self.story_segments.append(segment)
        self.word_count += segment.word_count
        self.round_count = max(self.round_count, round_num)

    def add_character(self, name: str, role: str, motivation: str = ""):
        """Add or update a character."""
        if name not in self.characters:
            self.characters[name] = Character(name=name, role=role, motivation=motivation)
        else:
            char = self.characters[name]
            if motivation:
                char.motivation = motivation

    def add_plot_thread(self, thread_id: str, description: str, author: str, tension: int = 5):
        """Add a new plot thread."""
        thread = PlotThread(
            id=thread_id,
            description=description,
            tension_level=tension,
            introduced_by=author
        )
        self.plot_threads.append(thread)

    def resolve_plot_thread(self, thread_id: str):
        """Mark a plot thread as resolved."""
        for thread in self.plot_threads:
            if thread.id == thread_id:
                thread.status = "resolved"
                break

    def update_tension(self, delta: int):
        """Adjust overall tension level."""
        self.tension_level = max(1, min(10, self.tension_level + delta))

    def advance_act(self):
        """Move to the next act if appropriate."""
        if self.current_act == StoryAct.SETUP:
            self.current_act = StoryAct.CONFRONTATION
        elif self.current_act == StoryAct.CONFRONTATION:
            self.current_act = StoryAct.RESOLUTION

    def get_active_threads(self) -> list:
        """Get all active plot threads."""
        return [t for t in self.plot_threads if t.status == "active"]

    def get_story_needs(self) -> list:
        """Analyze what the story currently needs."""
        needs = []

        # Check character needs
        if not self.characters:
            needs.append("Introduce a compelling character")
        elif len(self.characters) == 1:
            needs.append("Add another character for conflict/interaction")

        # Check plot thread needs
        active_threads = self.get_active_threads()
        if not active_threads:
            needs.append("Establish a central conflict or mystery")
        elif len(active_threads) > 3:
            needs.append("Resolve or combine some plot threads")

        # Check pacing needs based on act
        if self.current_act == StoryAct.SETUP:
            if self.round_count > 2 and self.tension_level < 4:
                needs.append("Raise the stakes - something needs to go wrong")
        elif self.current_act == StoryAct.CONFRONTATION:
            if self.tension_level < 6:
                needs.append("Increase tension and complications")
            elif self.tension_level > 8:
                needs.append("Brief moment of relief before next escalation")
        elif self.current_act == StoryAct.RESOLUTION:
            if active_threads:
                needs.append(f"Resolve: {active_threads[0].description}")

        # Check for stagnation
        if len(self.story_segments) > 3:
            recent = self.story_segments[-3:]
            recent_authors = [s.author for s in recent]
            if len(set(recent_authors)) < len(recent_authors):
                needs.append("Fresh perspective needed")

        return needs if needs else ["Continue building momentum"]

    def to_prompt_context(self) -> str:
        """Generate a prompt-friendly summary for agents."""
        lines = []
        lines.append("=== THE CENTER TABLE: STORY STATE ===")
        lines.append(f"Premise: {self.premise}")
        lines.append(f"Mode: {self.mode.upper()}")
        lines.append(f"Act: {self.current_act.name} ({self.current_act.value}/3)")
        lines.append(f"Tension: {self.tension_level}/10 | Pacing: {self.pacing}")
        lines.append("")

        # Characters
        if self.characters:
            lines.append("CHARACTERS:")
            for name, char in self.characters.items():
                lines.append(f"  - {name} ({char.role}): {char.motivation or 'motivation unknown'}")
                if char.last_action:
                    lines.append(f"    Last: {char.last_action}")

        # Active plot threads
        active = self.get_active_threads()
        if active:
            lines.append("")
            lines.append("ACTIVE THREADS:")
            for thread in active[:3]:  # Limit to top 3
                lines.append(f"  - {thread.description} [tension: {thread.tension_level}]")

        # Themes
        if self.themes:
            lines.append("")
            lines.append(f"THEMES: {', '.join(self.themes[:3])}")

        # Recent story (last 3 segments)
        if self.story_segments:
            lines.append("")
            lines.append("RECENT STORY:")
            for segment in self.story_segments[-3:]:
                lines.append(f"  [{segment.author}]: {segment.content[:100]}...")

        # What the story needs
        needs = self.get_story_needs()
        lines.append("")
        lines.append("STORY NEEDS:")
        for need in needs[:2]:  # Top 2 needs
            lines.append(f"  >> {need}")

        lines.append("=" * 40)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "premise": self.premise,
            "mode": self.mode,
            "current_act": self.current_act.value,
            "characters": {k: v.to_dict() for k, v in self.characters.items()},
            "plot_threads": [t.to_dict() for t in self.plot_threads],
            "themes": self.themes,
            "scene_beats": self.scene_beats,
            "story_segments": [s.to_dict() for s in self.story_segments],
            "tension_level": self.tension_level,
            "pacing": self.pacing,
            "word_count": self.word_count,
            "round_count": self.round_count
        }


class StoryStateManager:
    """
    Manages story state updates and generates agent-specific guidance.

    This class processes contributions, extracts story elements,
    and provides tailored guidance to each agent based on their specialty.
    """

    def __init__(self, premise: str, mode: str = "horror"):
        self.state = StoryState(premise=premise, mode=mode)

    def process_contribution(self, content: str, author: str, round_num: int):
        """
        Process an agent's contribution and update story state.

        This is where we extract characters, plot developments, and
        other story elements from the contribution.
        """
        self.state.add_segment(content, author, round_num)

        # Simple heuristics for story analysis
        # In a production system, this could use NLP or an LLM
        content_lower = content.lower()

        # Detect tension changes
        tension_words = {
            "increase": ["scream", "blood", "terror", "horror", "panic", "death", "kill"],
            "decrease": ["calm", "peace", "relief", "safe", "escape", "hope"]
        }

        for word in tension_words["increase"]:
            if word in content_lower:
                self.state.update_tension(1)
                break

        for word in tension_words["decrease"]:
            if word in content_lower:
                self.state.update_tension(-1)
                break

        # Update pacing based on sentence length
        avg_sentence_len = len(content.split()) / max(1, content.count('.') + content.count('!') + content.count('?'))
        if avg_sentence_len < 8:
            self.state.pacing = "fast"
        elif avg_sentence_len > 20:
            self.state.pacing = "slow"
        else:
            self.state.pacing = "steady"

        # Check for act transitions
        if self.state.round_count >= 3 and self.state.current_act == StoryAct.SETUP:
            if self.state.tension_level >= 5:
                self.state.advance_act()
        elif self.state.round_count >= 6 and self.state.current_act == StoryAct.CONFRONTATION:
            if self.state.tension_level >= 8:
                self.state.advance_act()

    def get_agent_guidance(self, agent_specialty: str) -> str:
        """
        Generate specific guidance for an agent based on their specialty
        and what the story currently needs.
        """
        needs = self.state.get_story_needs()
        mode_context = self._get_mode_guidance()

        guidance_lines = [
            f"Story Mode: {self.state.mode.upper()}",
            mode_context,
            "",
            "What the story needs now:"
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
            "fantasy": "Atmosphere: Wonder and mythic resonance. Magic has rules and costs."
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
Active Plot Threads: {len(self.state.get_active_threads())}
Characters Established: {len(self.state.characters)}

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
        valid_modes = ["horror", "noir", "comedy", "sci-fi", "literary", "fantasy"]
        if mode.lower() in valid_modes:
            self.state.mode = mode.lower()

    def add_theme(self, theme: str):
        """Add a theme being explored."""
        if theme not in self.state.themes:
            self.state.themes.append(theme)
