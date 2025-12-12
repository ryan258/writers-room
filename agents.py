"""
Agent class for Writers Room AI agents.
Each agent has a unique personality defined by its system prompt.
"""

import os
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class Agent:
    """An AI agent with a specific personality and model."""

    def __init__(self, name: str, model: str, system_prompt: str):
        """
        Initialize an AI agent.

        Args:
            name: The agent's name (e.g., "Cosmic Horror")
            model: The OpenRouter model ID (e.g., "mistralai/mistral-7b-instruct")
            system_prompt: The personality/instructions for this agent
        """
        self.name = name
        self.model = model
        self.system_prompt = system_prompt

        # Initialize OpenAI client pointing to OpenRouter
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )

    def generate_response(self, context: list[dict]) -> str:
        """
        Generate a response based on conversation context.

        Args:
            context: List of message dicts with 'role' and 'content' keys
                    representing the conversation history

        Returns:
            The agent's response as a string
        """
        # ULTRA-AGGRESSIVE SLIDING WINDOW: Only last 5 messages
        # Just enough to understand recent context without bloat
        recent_context = context[-5:] if len(context) > 5 else context

        # ULTRA-AGGRESSIVE TRUNCATION: Limit each message to 200 chars
        # Models keep echoing context, so we MUST keep it minimal
        safe_context = []
        for msg in recent_context:
            content = msg.get("content", "")
            if len(content) > 200:
                # Keep only the end for story flow
                content = "..." + content[-200:]
            safe_context.append({"role": msg["role"], "content": content})

        # Build the full message list
        # FIX: Move system prompt to User role for compatibility
        messages = [
            {"role": "user", "content": f"SYSTEM INSTRUCTIONS:\n{self.system_prompt}\n\n(End of instructions)"}
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
                    max_tokens=80,       # ULTRA-STRICT: One sentence only (~50 words = ~65 tokens)
                    presence_penalty=1.2, # MAXIMUM: Strongly discourage any repetition
                    frequency_penalty=1.0, # ANTI-ECHO: Penalize repeated tokens
                    temperature=0.9,      # High creativity to avoid formulaic responses
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
