"""
Agent class for Writers Room AI agents.
Each agent has a unique personality defined by its system prompt.
"""

import os
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
        # Build the full message list with system prompt first
        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + context

        try:
            # Call OpenRouter API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                extra_headers={
                    "HTTP-Referer": os.getenv("YOUR_SITE_URL", "http://localhost"),
                    "X-Title": os.getenv("YOUR_SITE_NAME", "AgentSwarmLocal"),
                },
                max_tokens=300,  # Keep responses concise
                temperature=0.8,  # Add some creativity
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            return f"[ERROR: {self.name} failed to respond - {str(e)}]"
