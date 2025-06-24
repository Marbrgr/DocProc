#!/usr/bin/env python3

# Clear all environment variables that might interfere
import os
for key in list(os.environ.keys()):
    if 'proxy' in key.lower():
        print(f"Removing env var: {key}")
        del os.environ[key]

# Now try the simplest possible OpenAI creation
from openai import OpenAI

try:
    print("Creating OpenAI client with just api_key...")
    client = OpenAI(api_key="sk-test-fake-key-for-debugging")
    print("✅ Client created successfully (this should fail with auth error, not proxy error)")
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"❌ Error type: {type(e).__name__}") 