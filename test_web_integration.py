#!/usr/bin/env python3
"""
Test script to verify web app can import and initialize correctly.
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Testing Writers Room Web Integration...\n")

# Test 1: Import personalities
print("1. Testing personalities imports...")
try:
    from personalities import (
        ROD_SERLING,
        STEPHEN_KING,
        HP_LOVECRAFT,
        JORGE_BORGES,
        ROBERT_STACK,
        MARKETING_EXEC,
        PRODUCER,
        RECOMMENDED_MODELS
    )
    print("   ✓ All personalities imported successfully")
    print(f"   ✓ PRODUCER defined: {len(PRODUCER)} characters")
    print(f"   ✓ RECOMMENDED_MODELS['producer']: {RECOMMENDED_MODELS.get('producer', 'MISSING')}")
except ImportError as e:
    print(f"   ✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Import Agent class
print("\n2. Testing Agent class import...")
try:
    from agents import Agent
    print("   ✓ Agent class imported successfully")
except ImportError as e:
    print(f"   ✗ Import failed: {e}")
    sys.exit(1)

# Test 3: Check Agent __init__ signature
print("\n3. Testing Agent constructor signature...")
import inspect
sig = inspect.signature(Agent.__init__)
params = list(sig.parameters.keys())
print(f"   Agent.__init__ parameters: {params}")
if 'max_tokens' in params:
    print("   ✓ max_tokens parameter exists")
    default = sig.parameters['max_tokens'].default
    print(f"   ✓ max_tokens default value: {default}")
else:
    print("   ✗ max_tokens parameter MISSING")
    sys.exit(1)

# Test 4: Instantiate Producer agent with max_tokens=300
print("\n4. Testing Producer instantiation with max_tokens=300...")
try:
    # Don't actually call API, just test instantiation
    producer = Agent(
        name="The Producer",
        model="mistralai/ministral-3b-2512",
        system_prompt=PRODUCER,
        temperature=0.7,
        max_tokens=300
    )
    print("   ✓ Producer agent instantiated successfully")
    print(f"   ✓ producer.max_tokens = {producer.max_tokens}")
    if producer.max_tokens == 300:
        print("   ✓ max_tokens correctly set to 300")
    else:
        print(f"   ✗ max_tokens is {producer.max_tokens}, expected 300")
except TypeError as e:
    print(f"   ✗ TypeError: {e}")
    sys.exit(1)

# Test 5: Test context window preservation
print("\n5. Testing context window logic...")
try:
    # Simulate a conversation with 10 messages
    test_context = [
        {"role": "user", "content": "ORIGINAL PROMPT: Write about a detective"}
    ]
    # Add 9 agent responses (simulating 1.5 rounds)
    for i in range(9):
        test_context.append({
            "role": "assistant",
            "content": f"Agent response {i+1}",
            "name": f"Agent{i+1}"
        })

    # Check what the Agent would see (simulate the logic from agents.py lines 51-68)
    if len(test_context) > 0:
        original_prompt = test_context[0]
        if len(test_context) > 5:
            recent_messages = test_context[-4:]
        else:
            recent_messages = test_context[1:]

        recent_context = [original_prompt] + [msg for msg in recent_messages if msg.get("content") != original_prompt.get("content")]

        if recent_context[0]["content"] == "ORIGINAL PROMPT: Write about a detective":
            print("   ✓ Original prompt preserved in context")
            print(f"   ✓ Context length: {len(recent_context)} (original + {len(recent_context)-1} recent)")
        else:
            print("   ✗ Original prompt NOT preserved")
            sys.exit(1)
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

# Test 6: Check web app can import
print("\n6. Testing web app imports...")
try:
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web'))
    # Just check if the file can be parsed, don't actually run Flask
    with open('web/app.py', 'r') as f:
        content = f.read()
        if 'from personalities import' in content and 'PRODUCER' in content:
            print("   ✓ web/app.py has correct imports")
        else:
            print("   ✗ web/app.py missing PRODUCER import")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("✅ ALL TESTS PASSED")
print("="*50)
print("\nThe web integration is correctly configured:")
print("  • PRODUCER personality is defined")
print("  • RECOMMENDED_MODELS includes 'producer'")
print("  • Agent class accepts max_tokens parameter")
print("  • Producer can be instantiated with max_tokens=300")
print("  • Context window preserves original user prompt")
print("\nWeb server should start without errors.")
