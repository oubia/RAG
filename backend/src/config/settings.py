import os

CHROMA_DIR = "/Users/yasaman/Desktop/dataminin-project/RAG_Embeddings/Vectorestor"
#CHROMA_DIR = os.getenv("CHROMA_DIR")
OLLAMA_LLM_ENDPOINT = os.getenv("OLLAMA_LLM_ENDPOINT", "http://localhost:11434/")
OLLAMA_EMBEDDINGS_ENDPOINT = os.getenv("OLLAMA_EMBEDDINGS_ENDPOINT", "http://localhost:11434/")

 