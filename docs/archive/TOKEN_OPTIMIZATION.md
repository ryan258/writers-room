# Token Optimization Analysis

## The Problem

Original implementation was spending too many tokens despite having "fixes" in place.

## Root Causes

### 1. max_tokens Too High
- **Before**: 1000 tokens per response
- **Requirement**: ONE sentence (~70 tokens)
- **Waste**: 14x more tokens allocated than needed

### 2. Context Window Too Large
- **Before**: 15 messages in sliding window
- **With 6 agents**: That's 2.5 rounds of full history
- **Each message**: Up to 2000 chars (~500 tokens)
- **Total context**: ~7,500 tokens per call

### 3. Verbose System Prompts
- **Before**: ~200 tokens per system prompt
- **Sent**: With EVERY API call
- **Impact**: 6 calls × 200 tokens = 1,200 tokens/round just for instructions

## Token Math

### Before Optimization
```
Per agent call:
  - System prompt: ~200 tokens
  - Context (15 msgs × 500 tokens): ~7,500 tokens
  - Output (max_tokens): 1,000 tokens
  - Total: ~8,700 tokens/agent

Per round (6 agents):
  - 6 × 8,700 = ~52,000 tokens

Full session (3 rounds):
  - 52,000 × 3 = ~156,000 tokens
```

**Cost estimate**: $0.15-$0.50 per session (depending on model pricing)

### After Optimization
```
Per agent call:
  - System prompt: ~35 tokens (condensed)
  - Context (8 msgs × 100 tokens): ~800 tokens
  - Output (max_tokens): 120 tokens
  - Total: ~955 tokens/agent

Per round (6 agents):
  - 6 × 955 = ~5,700 tokens

Full session (3 rounds):
  - 5,700 × 3 = ~17,000 tokens
```

**Cost estimate**: $0.02-$0.05 per session

## Optimizations Applied

### 1. Reduced max_tokens
```python
# Before
max_tokens=1000

# After
max_tokens=120  # ONE sentence = ~70 tokens + small buffer
```

### 2. Aggressive Context Window
```python
# Before
recent_context = context[-15:]
content_limit = 2000 chars

# After
recent_context = context[-8:]  # Just enough for 1 round + some history
content_limit = 400 chars      # 1-2 sentences max
```

### 3. Condensed System Prompts
```python
# Before (200 tokens)
"""You are Rod Serling.
GAME: We are writing a collaborative MICROFICTION.
RULES:
1. Read the story so far.
2. Add EXACTLY ONE SENTENCE (max 280 chars).
3. Do NOT rewrite the previous text.
4. Maintain a tone of irony and moral weight.
5. End with a twist or a thought-provoking observation if possible.
"""

# After (35 tokens)
"""You are Rod Serling writing microfiction. Add ONE sentence (max 280 chars)
with irony and moral weight. Focus on twists. Don't rewrite previous text."""
```

## Results

- **Token reduction**: 89% fewer tokens (~156k → ~17k)
- **Cost reduction**: ~90% cheaper per session
- **Quality**: Should remain the same or better (agents forced to be concise)
- **Speed**: Faster responses due to smaller context windows

## Recommendations

1. Monitor actual token usage in OpenRouter dashboard
2. If agents still produce bloated responses, reduce max_tokens further (to 80-100)
3. If story continuity suffers, increase window to 10 messages
4. Consider adding a post-processing step to enforce 280 char limit

## Testing

Run a test session and check:
1. Are responses actually one sentence?
2. Do agents maintain story continuity?
3. What's the actual token count in OpenRouter logs?

Compare to this estimate to validate the optimization.
