import chromadb
from chromadb.utils import embedding_functions

# 1. Initialize persistent local storage (survives reboots)
client = chromadb.PersistentClient(path="./ai_memory_db")

# 2. Use the offline embedding model
# This downloads a tiny ~90MB model on first run, then works 100% offline
sentence_transformer_ef = embedding_functions.DefaultEmbeddingFunction()

# 3. Create or load the memory collection
memory_bank = client.get_or_create_collection(
    name="general_knowledge",
    embedding_function=sentence_transformer_ef
)

def learn_information(text, source_type, doc_id):
    """Saves a new memory to the database."""
    memory_bank.upsert(
        documents=[text],
        metadatas=[{"source": source_type}], # e.g., "user_input" or "web_scrape"
        ids=[doc_id]
    )
    print(f"Stored in memory: {text[:30]}...")

def recall_relevant_context(query, max_results=2):
    """Searches the database for memories related to the query."""
    results = memory_bank.query(
        query_texts=[query],
        n_results=max_results
    )
    # Extract just the text documents from the result
    return results['documents'][0] if results['documents'] else []

# --- Example Usage ---

# 1. AI learns a user fact
learn_information("User prefers Python scripts to be modular and concise.", "user_preference", "pref_001")

# 2. AI learns something from the internet (assume we scraped this)
learn_information("OpenCV 5.0 introduces better CUDA acceleration for drones.", "web_article", "tech_001")

# 3. Later, the user asks a question
user_query = "Write a script for my drone camera."
relevant_memories = recall_relevant_context(user_query)

# 4. Inject into the LLM prompt
system_prompt = f"""
You are a helpful AI. Use these retrieved memories to personalize your answer:
{relevant_memories}

User Query: {user_query}
"""

print("\n--- Final Prompt Sent to LLM ---")
print(system_prompt)
