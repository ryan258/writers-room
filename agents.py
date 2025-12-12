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
        # Build the full message list
        # FIX: Move system prompt to User role AND remove max_tokens for Nemotron compatibility
        messages = [
            {"role": "user", "content": f"SYSTEM INSTRUCTIONS:\n{self.system_prompt}\n\n(End of instructions)"}
        ] + context

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
                    # max_tokens=300,  # REMOVED: Causes empty response with Nemotron 12B
                    temperature=0.8,  # Add some creativity
                )

                return response.choices[0].message.content.strip()

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
