import litellm
import os

# Cloud API key comes from the environment; the placeholder below is
# intentionally not a real key. Set OPENAI_API_KEY before running.
os.environ.setdefault("OPENAI_API_KEY", "sk-your-key-here")


def hybrid_generate(prompt):
    """Try the cloud model first, fall back to a local engine when offline."""
    try:
        # The router tries the primary model first, then falls back
        response = litellm.completion(
            model="gpt-4o",  # Primary: Cloud
            messages=[{"role": "user", "content": prompt}],
            fallbacks=["ollama/llama3"],  # Fallback: Local offline engine
            timeout=3,  # If cloud doesn't respond in 3s, assume offline/bad connection
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"System completely offline and local engine failed: {e}"


if __name__ == "__main__":
    # If online, you get GPT-4o. If offline, LiteLLM transparently hands it to Llama 3.
    print(hybrid_generate("Analyze this system log for anomalies."))
