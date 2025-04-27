import time
import logging
from src.utils.prompts.prompt import general_prompt

class LLMFactory:
    def __init__(self, model_name: str):
        self.model_name = model_name.lower()

        if self.model_name in "llama":
            self.llm = self._init_llama_with_retry()
        else:
            raise ValueError(f"Unsupported model name: {model_name}. Supported models: 'llama'.")

    def _init_llama_with_retry(self):
        from langchain_ollama import OllamaLLM
        from src.config.settings import OLLAMA_LLM_ENDPOINT

        try:
            logging.info("Attempting to initialize Llama LLM at endpoint: %s", OLLAMA_LLM_ENDPOINT)
            llm = OllamaLLM(
                model="llama3.2:latest",  
                temperature=0.2,
                streaming=True,
                verbose=True,
                system=general_prompt,
                base_url=OLLAMA_LLM_ENDPOINT
            )
            logging.info("Llama LLM initialized successfully.")
            return llm
        except Exception as e:
            logging.error("Error initializing Llama LLM (elapsed: %.0f sec): %s", elapsed, str(e))
               

    def get_llm(self):
        return self.llm
