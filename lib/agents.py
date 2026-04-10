"""
Agent class for Writers Room AI agents.
Each agent has a unique personality defined by its system prompt.
"""

from dataclasses import dataclass
import json
import time
from openai import OpenAI
from typing import Any, Optional

from .config import RuntimeConfig


@dataclass(frozen=True)
class AgentResult:
    """Structured result from a model call."""

    ok: bool
    content: str = ""
    error: Optional[str] = None

    @classmethod
    def success(cls, content: str) -> "AgentResult":
        return cls(ok=True, content=content)

    @classmethod
    def failure(cls, error: str) -> "AgentResult":
        return cls(ok=False, error=error)


def coerce_agent_result(value: Any) -> AgentResult:
    """Normalize legacy string test doubles into the structured result shape."""
    # TODO: Drop this once all test doubles and callsites return AgentResult.
    if isinstance(value, AgentResult):
        return value
    if value is None:
        return AgentResult.success("")
    return AgentResult.success(str(value))


class Agent:
    """An AI agent with a specific personality and model."""

    def __init__(
        self,
        name: str,
        model: str,
        system_prompt: str,
        temperature: float = 0.9,
        max_tokens: int = 300,
        window_size: int = 15,
        response_format: Optional[dict[str, Any]] = None,
        json_key: Optional[str] = None,
        runtime_config: Optional[RuntimeConfig] = None,
    ):
        """
        Initialize an AI agent.

        Args:
            name: The agent's name (e.g., "Cosmic Horror")
            model: The OpenRouter model ID (e.g., "mistralai/mistral-7b-instruct")
            system_prompt: The personality/instructions for this agent
            temperature: Sampling temperature (0.0-2.0, default: 0.9)
            max_tokens: Maximum tokens per response (default: 80 for one sentence)
            window_size: Number of recent messages to keep in context (default: 15)
            response_format: Optional OpenAI response_format dict (e.g. {"type": "json_object"})
            json_key: When response_format is set, extract this key from the JSON response
        """
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.window_size = window_size
        self.response_format = response_format
        self.json_key = json_key
        if runtime_config is None:
            raise ValueError("Agent requires a RuntimeConfig")
        self.runtime_config = runtime_config

        # Initialize OpenAI client pointing to OpenRouter
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=runtime_config.openrouter_api_key,
        )

    def generate_response(
        self,
        context: list[dict],
        story_context: Optional[str] = None,
    ) -> AgentResult:
        """
        Generate a response based on conversation context.

        Args:
            context: List of message dicts with 'role' and 'content' keys
                    representing the conversation history
            story_context: Optional story state context from StoryStateManager
                          This provides the agent with the "Center Table" view

        Returns:
            Structured success/failure information for the model response
        """
        # Keep system prompt pure (agent identity only).
        # Story context is injected as a separate user message below
        # to prevent table-talk contamination from causing role confusion.
        full_system_prompt = self.system_prompt

        # PRESERVE ORIGINAL PROMPT: Always keep the first message (user's story prompt)
        # Then apply sliding window to recent messages to maintain story context
        # This ensures agents never lose track of what they're writing about
        if len(context) > 0:
            original_prompt = context[0]  # The user's initial request

            # Take last N messages (not including original) to stay within token budget
            # By default (15), this is enough for ~2 full rounds of 6 writers
            if len(context) > self.window_size + 1:
                recent_messages = context[-self.window_size:]
            else:
                recent_messages = context[1:]  # Everything except the original prompt

            # Combine: original prompt + recent conversation
            # Filter out duplicate if original_prompt somehow appears in recent_messages
            recent_context = [original_prompt] + [msg for msg in recent_messages if msg.get("content") != original_prompt.get("content")]
        else:
            recent_context = context

        # ULTRA-AGGRESSIVE TRUNCATION: Limit each message to 500 chars
        # BUT: Don't truncate the original user prompt (keep it intact so context is clear)
        safe_context = []
        for i, msg in enumerate(recent_context):
            content = msg.get("content", "")
            # Keep first message (user prompt) intact, truncate the rest
            if i > 0 and len(content) > 500:
                # Keep only the end for story flow
                content = "..." + content[-500:]
            safe_context.append({"role": msg["role"], "content": content})

        # Build the full message list with proper system role for personality
        # System messages have higher priority and clearer separation from conversation
        messages = [
            {"role": "system", "content": full_system_prompt}
        ] + safe_context

        # Inject story context as a grounding user message at the end,
        # separate from the system prompt to avoid role confusion
        if story_context:
            messages.append({"role": "user", "content": story_context})

        max_retries = 3

        for attempt in range(max_retries):
            try:
                create_kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "extra_headers": {
                        "HTTP-Referer": self.runtime_config.site_url,
                        "X-Title": self.runtime_config.site_name,
                    },
                    "max_tokens": self.max_tokens,
                    "presence_penalty": 1.2,
                    "frequency_penalty": 1.0,
                    "temperature": self.temperature,
                }
                if self.response_format:
                    create_kwargs["response_format"] = self.response_format

                response = self.client.chat.completions.create(**create_kwargs)
                raw_response = response.choices[0].message.content.strip()

                # If structured output was requested, try to extract the target key
                if self.response_format and self.json_key:
                    extracted = self._extract_json_field(raw_response, self.json_key)
                    if extracted is not None:
                        return AgentResult.success(extracted)

                # POST-PROCESSING: Remove any echoed context
                # If the response starts with "..." it's likely echoing truncated context
                if raw_response.startswith("..."):
                    import re
                    sentences = re.split(r'(?<=[.!?])\s+', raw_response)
                    if len(sentences) > 1:
                        return AgentResult.success(sentences[-1])

                return AgentResult.success(raw_response)

            except Exception as e:
                error_str = str(e)
                # Check for rate limit or other transient errors
                if "429" in error_str or "Rate limit" in error_str:
                    if attempt < max_retries - 1:
                        sleep_time = 5 * (2 ** attempt)  # Exponential backoff: 5, 10, 20 seconds
                        print(f"    [Adjusting frequency for {self.name}... waiting {sleep_time}s]")
                        time.sleep(sleep_time)
                        continue

                # If we're out of retries or it's a different error, return the error message
                if attempt == max_retries - 1:
                    return AgentResult.failure(f"{self.name} failed to respond - {error_str}")

        return AgentResult.failure(f"{self.name} failed to respond")

    @staticmethod
    def _extract_json_field(raw: str, key: str) -> Optional[str]:
        """Try to parse JSON and return the value at *key*, or None on failure."""
        try:
            data = json.loads(raw)
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        except (json.JSONDecodeError, AttributeError, TypeError):
            pass
        return None

    @staticmethod
    def parse_json_response(raw: str) -> Optional[dict]:
        """Parse a full JSON response dict, or None on failure."""
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, AttributeError, TypeError):
            pass
        return None

    def update_system_prompt(self, new_prompt: str):
        """Update the agent's system prompt dynamically."""
        self.system_prompt = new_prompt

    def get_agent_key(self) -> str:
        """Get the agent key for looking up configs."""
        name_to_key = {
            "Rod Serling": "rod_serling",
            "Stephen King": "stephen_king",
            "H.P. Lovecraft": "hp_lovecraft",
            "Jorge Luis Borges": "jorge_borges",
            "Robert Stack": "robert_stack",
            "RIP Tequila Bot": "marketing",
            "The Producer": "producer"
        }
        return name_to_key.get(self.name, self.name.lower().replace(" ", "_"))
