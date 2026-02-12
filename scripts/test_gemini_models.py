"""Test script to list available Gemini models."""

import os
import google.generativeai as genai

# Get API key from environment
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("ERROR: GEMINI_API_KEY environment variable not set")
    exit(1)

# Configure the API
genai.configure(api_key=api_key)

print("Fetching available Gemini models...\n")

# List all models
try:
    models = genai.list_models()

    print("=" * 80)
    print("ALL AVAILABLE MODELS:")
    print("=" * 80)

    for model in models:
        print(f"\nModel: {model.name}")
        print(f"  Display Name: {model.display_name}")
        print(f"  Description: {model.description}")
        print(f"  Supported methods: {model.supported_generation_methods}")

    print("\n" + "=" * 80)
    print("MODELS SUPPORTING generateContent:")
    print("=" * 80)

    generate_content_models = [
        m for m in genai.list_models()
        if 'generateContent' in m.supported_generation_methods
    ]

    for model in generate_content_models:
        print(f"\n✓ {model.name}")
        print(f"  Display: {model.display_name}")

    print("\n" + "=" * 80)
    print("MODELS SUPPORTING embedContent:")
    print("=" * 80)

    embed_models = [
        m for m in genai.list_models()
        if 'embedContent' in m.supported_generation_methods
    ]

    for model in embed_models:
        print(f"\n✓ {model.name}")
        print(f"  Display: {model.display_name}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
