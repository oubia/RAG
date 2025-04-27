import time
import logging
from src.utils.prompts.prompt import general_prompt

class LLMFactory:
    def __init__(self, model_name: str):
        self.model_name = model_name.lower()
        if self.model_name in "llamantino":
            self.llm = self._init_llamantino_with_retry()
        elif self.model_name in "llama":
            self.llm = self._init_llama_with_retry()
        elif self.model_name in "qwen":
            self.llm = self._init_qwen_with_retry()
        else:
            raise ValueError(f"Unsupported model name: {model_name}. Supported models: 'llama', 'aws_bedrock', 'deepseek'.")

    def _init_llamantino_with_retry(self):
        from langchain_ollama import OllamaLLM
        from src.config.settings import OLLAMA_LLM_ENDPOINT

        max_wait = 60 
        interval = 5   
        start_time = time.time()

        while True:
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
                elapsed = time.time() - start_time
                logging.error("Error initializing Llama LLM (elapsed: %.0f sec): %s", elapsed, str(e))
                if elapsed > max_wait:
                    logging.error("Timeout exceeded while waiting for Llama LLM.")
                    raise e
                time.sleep(interval)

    def _init_llama_with_retry(self):
        from langchain_ollama import OllamaLLM
        from src.config.settings import OLLAMA_LLM_ENDPOINT

        max_wait = 60 
        interval = 5   
        start_time = time.time()

        while True:
            try:
                logging.info("Attempting to initialize Llama LLM at endpoint: %s", OLLAMA_LLM_ENDPOINT)
                llm = OllamaLLM(
                    model="llama3.2:latest",  
                    temperature=0.2,
                    streaming=True,
                    verbose=True,
                    system=lama3_prompt,
                    base_url=OLLAMA_LLM_ENDPOINT
                )
                logging.info("Llama LLM initialized successfully.")
                return llm
            except Exception as e:
                elapsed = time.time() - start_time
                logging.error("Error initializing Llama LLM (elapsed: %.0f sec): %s", elapsed, str(e))
                if elapsed > max_wait:
                    logging.error("Timeout exceeded while waiting for Llama LLM.")
                    raise e
                time.sleep(interval)

    def _init_qwen_with_retry(self):
        from langchain_ollama import OllamaLLM
        from src.config.settings import OLLAMA_LLM_ENDPOINT
        
        max_wait = 60 
        interval = 5  
        start_time = time.time()

        while True:
            try:
                logging.info("Attempting to initialize Deepseek LLM at endpoint: %s", OLLAMA_LLM_ENDPOINT)
                llm = OllamaLLM(
                    model="qwen2.5:7b",
                    temperature=0.2,
                    streaming=True,
                    verbose=True,
                    system=deepseek_prompt,
                    base_url=OLLAMA_LLM_ENDPOINT
                )
                logging.info("Deepseek LLM initialized successfully.")
                return llm
            except Exception as e:
                elapsed = time.time() - start_time
                logging.error("Error initializing Deepseek LLM (elapsed: %.0f sec): %s", elapsed, str(e))
                if elapsed > max_wait:
                    logging.error("Timeout exceeded while waiting for Deepseek LLM.")
                    raise e
                time.sleep(interval)

    def get_llm(self):
        return self.llm
