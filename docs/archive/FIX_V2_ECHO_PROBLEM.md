# Fix V2: The Echo Problem

## What Went Wrong

You were absolutely right - the first optimization didn't work. Here's what happened in the transcript:

```
Rod Serling: [writes one sentence] ✅

Stephen King: ...ng screen where the AI's voice... [REPEATS ROD'S ENTIRE OUTPUT] ❌
              [then adds nothing new]

H.P. Lovecraft: ...ng screen where the AI's voice... [REPEATS EVERYTHING AGAIN] ❌
                [then adds nothing new]
```

**The models were echoing the context instead of just adding new content.**

## Why This Happened

LLMs have a tendency to "complete" text by repeating what they see, especially when:
1. The context is truncated (starts with "...")
2. The instructions aren't explicit enough about NOT repeating
3. The model thinks it should show its work

Result: Each agent used their 120 tokens to **echo context** instead of creating new content.

## The Nuclear Option (Fix V2)

I've applied the most aggressive fixes possible:

### 1. Explicit Anti-Echo Prompts
```python
# Before
"You are Rod Serling. Add ONE sentence..."

# After
"OUTPUT ONLY YOUR NEW SENTENCE. Do not repeat what others wrote.
You are Rod Serling. Write ONE sentence..."
```

**Leading with the most important instruction: DON'T ECHO.**

### 2. Ultra-Minimal Context
```python
# Before
recent_context = context[-8:]    # Last 8 messages
content_limit = 400 chars

# After
recent_context = context[-5:]    # Only last 5 messages
content_limit = 200 chars        # Cut in half
```

**Less context = less to echo.**

### 3. Maximum Anti-Repetition Penalties
```python
max_tokens=80             # Down from 120
presence_penalty=1.2      # Up from 0.6 (maximum strength)
frequency_penalty=1.0     # NEW: Penalize any repeated tokens
temperature=0.9           # Higher for more creativity
```

**Making repetition mathematically painful for the model.**

### 4. Post-Processing Echo Removal
```python
# New safety net: If response starts with "..."
# Extract only the LAST sentence (the new content)
if raw_response.startswith("..."):
    sentences = re.split(r'(?<=[.!?])\s+', raw_response)
    return sentences[-1]  # Return only the new sentence
```

**Insurance policy: Strip echoes programmatically.**

## Expected Result

Now each agent should output **ONLY** their new sentence:

```
Rod Serling: The rain hammered against the window as Dr. Carter stared at the AI.

Stephen King: His hands shook as he remembered the nurse who'd left when he got sick.

H.P. Lovecraft: The machine whispered in a tongue that predated human language itself.

[etc - clean, one sentence per agent]
```

## Token Math (Revised)

### Per Agent Call:
- System prompt: ~25 tokens (ultra-concise)
- Context (5 msgs × 50 tokens): ~250 tokens
- Output (max_tokens): 80 tokens
- **Total: ~355 tokens/agent**

### Per Round (6 agents):
- 6 × 355 = **~2,100 tokens**

### Full Session (3 rounds):
- 2,100 × 3 = **~6,300 tokens**

**Cost estimate**: $0.01-$0.02 per session (99% reduction from original)

## Test It Now

```bash
python main.py
```

The transcript should now show:
- Clean, one-sentence responses
- No `...` echo prefixes
- Actual story progression

Check your OpenRouter dashboard - should see ~6-7k tokens instead of 150k+.

## If It STILL Echoes

Then we need to:
1. Try a different model (some models echo more than others)
2. Add even more aggressive post-processing
3. Change the architecture to use a different conversation pattern

But this should work. The combination of:
- Explicit "DON'T ECHO" instruction
- Minimal context
- Maximum penalties
- Post-processing safety net

Should finally kill the echo problem.
