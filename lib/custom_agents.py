"""
Custom Agents: User-defined agent personalities for Writers Room

Allows users to create their own collaborative agents with custom
specialties, guidance, and visual identity.
"""

import json
import uuid
from dataclasses import dataclass, asdict
from typing import Optional
from pathlib import Path


# Default directory for storing custom agents
AGENTS_DIR = Path(__file__).resolve().parents[1] / "agents"


@dataclass
class CustomAgent:
    """
    A user-defined agent with custom personality and appearance.

    Each custom agent has:
    - Unique identity (id, name)
    - Writing specialty and guidance
    - Visual identity (color, avatar emoji)
    - Voice settings (if TTS enabled)
    """
    id: str
    name: str
    specialty: str
    guidance: str
    voice_id: str = "alloy"  # OpenAI TTS voice
    color: str = "#888888"
    avatar_emoji: str = "pen"
    created_at: str = ""
    is_active: bool = True

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if not self.created_at:
            from datetime import datetime
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def to_system_prompt(self, story_context: str = "") -> str:
        """Generate the system prompt for this agent."""
        from .personalities import COLLABORATION_BASE

        return f"""{COLLABORATION_BASE}

YOUR SPECIALTY: {self.specialty}

{self.guidance}

{story_context}

OUTPUT ONLY YOUR NEW STORY CONTRIBUTION. No meta-commentary."""

    def save(self, directory: Optional[Path] = None) -> str:
        """
        Save this agent to a JSON file.
        """
        save_dir = directory or AGENTS_DIR
        save_dir.mkdir(parents=True, exist_ok=True)

        # Stable filename keyed by id to prevent orphaned files on rename
        filepath = save_dir / f"{self.id}.json"

        # Clean up any legacy filename variants (id_name.json)
        for legacy_path in save_dir.glob(f"{self.id}_*.json"):
            try:
                legacy_path.unlink()
            except OSError:
                pass

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)

        return str(filepath)

    @classmethod
    def load(cls, filepath: str) -> 'CustomAgent':
        """Load an agent from a JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)

    @classmethod
    def from_dict(cls, data: dict) -> 'CustomAgent':
        """Create an agent from a dictionary."""
        return cls(**data)


# =============================================================================
# AGENT TEMPLATES
# =============================================================================

AGENT_TEMPLATES = {
    "literary_master": CustomAgent(
        id="tmpl_lit",
        name="Literary Master",
        specialty="Prose excellence, metaphor, and thematic resonance",
        guidance="""Your expertise: Crafting sentences that sing. Finding the perfect word.
Use this when: The story needs elevated prose or deeper meaning.
Don't force it: If the scene needs action or dialogue, serve that need.
Your voice: Precise, evocative, every word chosen with care.""",
        color="#9B59B6",
        avatar_emoji="quill"
    ),
    "action_writer": CustomAgent(
        id="tmpl_act",
        name="Action Writer",
        specialty="Kinetic scenes, clear choreography, momentum",
        guidance="""Your expertise: Making things MOVE. Clear, punchy action.
Use this when: The story needs velocity, conflict, or physical stakes.
Don't force it: If the scene needs reflection or dialogue, step back.
Your voice: Short sentences. Active verbs. No fat.""",
        color="#E74C3C",
        avatar_emoji="explosion"
    ),
    "dialogue_specialist": CustomAgent(
        id="tmpl_dia",
        name="Dialogue Specialist",
        specialty="Authentic voices, subtext, character through speech",
        guidance="""Your expertise: Making characters speak with distinct, authentic voices.
Use this when: The story needs conversation, revelation through speech, or conflict via dialogue.
Don't force it: If the scene needs description or action, let others lead.
Your voice: Each character sounds unique. What's unsaid matters.""",
        color="#3498DB",
        avatar_emoji="speech_balloon"
    ),
    "world_builder": CustomAgent(
        id="tmpl_wrld",
        name="World Builder",
        specialty="Setting, atmosphere, sensory immersion",
        guidance="""Your expertise: Making places REAL. Grounding the reader in space and time.
Use this when: The story needs grounding, atmosphere, or world detail.
Don't force it: If the scene needs character focus or action, support instead.
Your voice: Specific details. All five senses. The world as character.""",
        color="#2ECC71",
        avatar_emoji="globe_showing_americas"
    ),
    "tension_master": CustomAgent(
        id="tmpl_tens",
        name="Tension Master",
        specialty="Suspense, pacing, the art of withholding",
        guidance="""Your expertise: Making readers hold their breath. The power of the unseen.
Use this when: The story needs to ratchet up stakes or create unease.
Don't force it: If the scene needs release or resolution, allow it.
Your voice: What's coming? What's around the corner? The dread of waiting.""",
        color="#E67E22",
        avatar_emoji="hourglass_not_done"
    ),
    "heart_writer": CustomAgent(
        id="tmpl_heart",
        name="Heart Writer",
        specialty="Emotional truth, character interiority, human connection",
        guidance="""Your expertise: Making readers FEEL. The truth of human experience.
Use this when: The story needs emotional grounding or character depth.
Don't force it: If the scene needs plot momentum, let others drive.
Your voice: Vulnerability. Honesty. The ache of being human.""",
        color="#E91E63",
        avatar_emoji="heart"
    )
}


# =============================================================================
# AGENT MANAGEMENT
# =============================================================================

class CustomAgentManager:
    """Manages custom agents - loading, saving, and listing."""

    def __init__(self, agents_dir: Optional[Path] = None):
        self.agents_dir = agents_dir or AGENTS_DIR
        self._cache: dict = {}

    def ensure_directory(self):
        """Create the agents directory if it doesn't exist."""
        self.agents_dir.mkdir(parents=True, exist_ok=True)

    def list_agents(self) -> list:
        """List all saved custom agents."""
        self.ensure_directory()
        agents = []

        for filepath in self.agents_dir.glob("*.json"):
            if filepath.name.startswith("."):
                continue
            try:
                agent = CustomAgent.load(str(filepath))
                agents.append(agent)
            except Exception:
                continue

        return sorted(agents, key=lambda a: a.name)

    def get_agent(self, agent_id: str) -> Optional[CustomAgent]:
        """Get an agent by ID."""
        # Check cache first
        if agent_id in self._cache:
            return self._cache[agent_id]

        if not agent_id or not agent_id.replace("-", "").isalnum():
            return None

        # Fast path: stable filename by id
        self.ensure_directory()
        direct_path = self.agents_dir / f"{agent_id}.json"
        if direct_path.exists():
            try:
                agent = CustomAgent.load(str(direct_path))
                self._cache[agent_id] = agent
                return agent
            except Exception:
                return None

        # Legacy fallback: id prefix match
        for filepath in self.agents_dir.glob(f"{agent_id}_*.json"):
            try:
                agent = CustomAgent.load(str(filepath))
                if agent.id == agent_id:
                    self._cache[agent_id] = agent
                    return agent
            except Exception:
                continue

        return None

    def save_agent(self, agent: CustomAgent) -> str:
        """Save an agent and return the filepath."""
        self.ensure_directory()
        filepath = agent.save(self.agents_dir)
        self._cache[agent.id] = agent
        return filepath

    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent by ID."""
        self.ensure_directory()

        if not agent_id or not agent_id.replace("-", "").isalnum():
            return False

        deleted = False

        direct_path = self.agents_dir / f"{agent_id}.json"
        if direct_path.exists():
            try:
                direct_path.unlink()
                deleted = True
            except OSError:
                return False

        for filepath in self.agents_dir.glob(f"{agent_id}_*.json"):
            try:
                filepath.unlink()
                deleted = True
            except OSError:
                return False

        if deleted and agent_id in self._cache:
            del self._cache[agent_id]
        if deleted:
            return True

        return False

    def create_from_template(self, template_key: str, name: str = None) -> Optional[CustomAgent]:
        """Create a new agent based on a template."""
        template = AGENT_TEMPLATES.get(template_key)
        if not template:
            return None

        # Create new agent with fresh ID
        agent = CustomAgent(
            id="",  # Will auto-generate
            name=name or template.name,
            specialty=template.specialty,
            guidance=template.guidance,
            color=template.color,
            avatar_emoji=template.avatar_emoji
        )

        return agent

    def get_active_agents(self) -> list:
        """Get all active custom agents."""
        return [a for a in self.list_agents() if a.is_active]


# Global manager instance
_manager: Optional[CustomAgentManager] = None


def get_agent_manager() -> CustomAgentManager:
    """Get or create the global CustomAgentManager instance."""
    global _manager
    if _manager is None:
        _manager = CustomAgentManager()
    return _manager


def list_templates() -> dict:
    """List available agent templates."""
    return {
        key: {
            "name": tmpl.name,
            "specialty": tmpl.specialty,
            "color": tmpl.color,
            "avatar_emoji": tmpl.avatar_emoji
        }
        for key, tmpl in AGENT_TEMPLATES.items()
    }


# =============================================================================
# CLI HELPERS
# =============================================================================

def interactive_create_agent() -> Optional[CustomAgent]:
    """Interactive CLI for creating a custom agent."""
    print("\n=== CREATE CUSTOM AGENT ===\n")

    # Show templates
    print("Available templates (or press Enter to create from scratch):")
    templates = list(AGENT_TEMPLATES.keys())
    for i, key in enumerate(templates, 1):
        tmpl = AGENT_TEMPLATES[key]
        print(f"  {i}. {tmpl.name} - {tmpl.specialty[:50]}...")

    print()
    choice = input("Choose template (1-6) or press Enter: ").strip()

    if choice and choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(templates):
            template_key = templates[idx]
            base = AGENT_TEMPLATES[template_key]
            print(f"\nUsing template: {base.name}")
        else:
            base = None
    else:
        base = None

    # Get agent details
    if base:
        name = input(f"Agent name [{base.name}]: ").strip() or base.name
        specialty = input(f"Specialty [{base.specialty[:50]}...]: ").strip() or base.specialty
        guidance = input("Custom guidance (or Enter for default): ").strip() or base.guidance
        color = input(f"Color hex [{base.color}]: ").strip() or base.color
        emoji = input(f"Avatar emoji [{base.avatar_emoji}]: ").strip() or base.avatar_emoji
    else:
        name = input("Agent name: ").strip()
        if not name:
            print("Name is required. Aborting.")
            return None

        specialty = input("Specialty (what are they good at?): ").strip()
        if not specialty:
            print("Specialty is required. Aborting.")
            return None

        print("\nGuidance template:")
        print("  Your expertise: [what they do]")
        print("  Use this when: [when to use specialty]")
        print("  Don't force it: [when to step back]")
        print("  Your voice: [writing style]")
        guidance = input("\nEnter guidance (or Enter for basic): ").strip()
        if not guidance:
            guidance = f"""Your expertise: {specialty}
Use this when: The story needs your particular skills.
Don't force it: If the scene needs something else, serve that need.
Your voice: Distinctive and purposeful."""

        color = input("Color hex [#888888]: ").strip() or "#888888"
        emoji = input("Avatar emoji [pen]: ").strip() or "pen"

    # Create the agent
    agent = CustomAgent(
        id="",  # Auto-generate
        name=name,
        specialty=specialty,
        guidance=guidance,
        color=color,
        avatar_emoji=emoji
    )

    # Save
    manager = get_agent_manager()
    filepath = manager.save_agent(agent)
    print(f"\nAgent saved to: {filepath}")
    print(f"Agent ID: {agent.id}")

    return agent
