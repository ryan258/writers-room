"""
Agent class for Writers Room AI agents.
Each agent has a unique personality defined by its system prompt.
"""

import os
import time
from openai import OpenAI
from dotenv import load_dotenv
from typing import Optional

load_dotenv()


class Agent:
    """An AI agent with a specific personality and model."""

    def __init__(self, name: str, model: str, system_prompt: str, temperature: float = 0.9, max_tokens: int = 80, window_size: int = 15):
        """
        Initialize an AI agent.

        Args:
            name: The agent's name (e.g., "Cosmic Horror")
            model: The OpenRouter model ID (e.g., "mistralai/mistral-7b-instruct")
            system_prompt: The personality/instructions for this agent
            temperature: Sampling temperature (0.0-2.0, default: 0.9)
            max_tokens: Maximum tokens per response (default: 80 for one sentence)
            window_size: Number of recent messages to keep in context (default: 15)
        """
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.window_size = window_size

        # Initialize OpenAI client pointing to OpenRouter
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )

    def generate_response(self, context: list[dict], story_context: Optional[str] = None) -> str:
        """
        Generate a response based on conversation context.

        Args:
            context: List of message dicts with 'role' and 'content' keys
                    representing the conversation history
            story_context: Optional story state context from StoryStateManager
                          This provides the agent with the "Center Table" view

        Returns:
            The agent's response as a string
        """
        # Build the system prompt, incorporating story context if provided
        if story_context:
            # Inject story state into the system prompt
            full_system_prompt = f"{self.system_prompt}\n\n{story_context}"
        else:
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

        max_retries = 3

        for attempt in range(max_retries):
            try:
                # Call OpenRouter API
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    extra_headers={
                        "HTTP-Referer": os.getenv("YOUR_SITE_URL", "http://localhost"),
                        "X-Title": "YOUR_SITE_NAME",
                    },
                    max_tokens=self.max_tokens,  # Configurable token limit (80 for writers, 300 for Producer)
                    presence_penalty=1.2, # MAXIMUM: Strongly discourage any repetition
                    frequency_penalty=1.0, # ANTI-ECHO: Penalize repeated tokens
                    temperature=self.temperature,  # Configurable creativity level
                )

                raw_response = response.choices[0].message.content.strip()

                # POST-PROCESSING: Remove any echoed context
                # If the response starts with "..." it's likely echoing truncated context
                if raw_response.startswith("..."):
                    # Find the last occurrence of a sentence-ending pattern
                    # Then return everything after it
                    import re
                    # Look for the last complete sentence boundary after ellipsis
                    sentences = re.split(r'(?<=[.!?])\s+', raw_response)
                    if len(sentences) > 1:
                        # Return only the last sentence (the new content)
                        return sentences[-1]

                return raw_response

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
                    return f"[ERROR: {self.name} failed to respond - {error_str}]"

        return f"[ERROR: {self.name} failed to respond]"

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
