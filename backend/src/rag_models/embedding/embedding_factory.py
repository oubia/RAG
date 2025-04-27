import time
import logging
from src.config.settings import OLLAMA_EMBEDDINGS_ENDPOINT

class EmbeddingFactory:
    @staticmethod
    def _init_nomic_embedding_with_retry(model_name: str):
        try:
            from langchain_community.embeddings import OllamaEmbeddings

            logging.info("Attempting to initialize nomic embedding model '%s' with endpoint: %s", model_name, OLLAMA_EMBEDDINGS_ENDPOINT)
            embeddings = OllamaEmbeddings(model=model_name, show_progress=True, base_url=OLLAMA_EMBEDDINGS_ENDPOINT)
            logging.info("Nomic embedding model initialized successfully.")
            return embeddings
        except Exception as e:
            logging.error("Error initializing nomic embedding model (elapsed: %.0f sec): %s", elapsed, str(e))
            
    @staticmethod
    def get_embedding_model(model_name: str):
        model_name = model_name.lower()

        if model_name in "nomic-embed-text":
            return EmbeddingFactory._init_nomic_embedding_with_retry(model_name)
     
        else:
            raise ValueError(
                f"Unsupported embedding model: {model_name}. Supported models: "
                f"'amazon.titan-embed-text-v2:0', 'nomic-embed-text', 'text-embedding-3-small'."
            )
