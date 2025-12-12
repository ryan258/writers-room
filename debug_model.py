import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


model = "mistralai/ministral-3b-2512"
context = [
    {"role": "user", "content": "SYSTEM INSTRUCTION: You are Rod Serling. You write introductions for The Twilight Zone.\n\nUSER PROMPT: Write an intro about a man who finds a shoe."}
]

print(f"Testing model: {model}")
print("Sending request...")

try:
    response = client.chat.completions.create(
        model=model,
        messages=context,
        extra_headers={
            "HTTP-Referer": "http://localhost",
            "X-Title": "DebugScript",
        },
        max_tokens=80,   # Ultra-strict: one sentence only
        presence_penalty=1.2,  # Maximum anti-repetition
        frequency_penalty=1.0, # Penalize echoing
        temperature=0.9,
    )

    print("\n--- RAW RESPONSE ---")
    print(response)
    print("\n--- CONTENT ---")
    print(f"'{response.choices[0].message.content}'")
    print("\n--- FINISH REASON ---")
    print(response.choices[0].finish_reason)

except Exception as e:
    print(f"Error: {e}")
