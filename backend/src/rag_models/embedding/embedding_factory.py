import time
import logging
from src.config.settings import OLLAMA_EMBEDDINGS_ENDPOINT

class EmbeddingFactory:
    @staticmethod
    def _init_nomic_embedding_with_retry(model_name: str):
        max_wait = 60  
        interval = 5  
        start_time = time.time()

        while True:
            try:
                from langchain_community.embeddings import OllamaEmbeddings

                logging.info("Attempting to initialize nomic embedding model '%s' with endpoint: %s", model_name, OLLAMA_EMBEDDINGS_ENDPOINT)
                embeddings = OllamaEmbeddings(model=model_name, show_progress=True, base_url=OLLAMA_EMBEDDINGS_ENDPOINT)
                logging.info("Nomic embedding model initialized successfully.")
                return embeddings
            except Exception as e:
                elapsed = time.time() - start_time
                logging.error("Error initializing nomic embedding model (elapsed: %.0f sec): %s", elapsed, str(e))
                if elapsed > max_wait:
                    logging.error("Timeout exceeded while waiting for nomic embedding model.")
                    raise e
                time.sleep(interval)

    @staticmethod
    def get_embedding_model(model_name: str):
        model_name = model_name.lower()

        if model_name in "amazon.titan-embed-text-v2:0":
            from langchain.embeddings import BedrockEmbeddings
            from src.config.settings import AWS_PROFILE 
            return BedrockEmbeddings(
                model_id=model_name,
                credentials_profile_name=AWS_PROFILE
            )
        elif model_name in "nomic-embed-text":
            return EmbeddingFactory._init_nomic_embedding_with_retry(model_name)
        elif model_name in "text-embedding-3-small":
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(model=model_name)
        else:
            raise ValueError(
                f"Unsupported embedding model: {model_name}. Supported models: "
                f"'amazon.titan-embed-text-v2:0', 'nomic-embed-text', 'text-embedding-3-small'."
            )
