import litellm
import os

# Set your cloud API key (used when online)
os.environ["OPENAI_API_KEY"] = "sk-your-key"

def hybrid_generate(prompt):
    try:
        # The router tries the primary model first, then falls back
        response = litellm.completion(
            model="gpt-4o", # Primary: Cloud
            messages=[{"role": "user", "content": prompt}],
            fallbacks=["ollama/llama3"], # Fallback: Local offline engine
            timeout=3 # If cloud doesn't respond in 3s, assume offline/bad connection
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"System completely offline and local engine failed: {e}"

# If online, you get GPT-4o. If offline, LiteLLM transparently hands it to Llama 3.
print(hybrid_generate("Analyze this system log for anomalies."))
