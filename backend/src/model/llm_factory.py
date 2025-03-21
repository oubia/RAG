import time
import logging
from src.utils.prompts.prompt import prompt_bedrock, lama3_prompt, deepseek_prompt

class LLMFactory:
    def __init__(self, model_name: str):
        self.model_name = model_name.lower()
        if self.model_name in "bedrock":
            self.llm = self._init_aws_bedrock()
        elif self.model_name in "llama":
            self.llm = self._init_llama_with_retry()
        elif self.model_name in "deepseek":
            self.llm = self._init_deepseek_with_retry()
        else:
            raise ValueError(f"Unsupported model name: {model_name}. Supported models: 'llama', 'aws_bedrock', 'deepseek'.")

    def _init_aws_bedrock(self):
        from langchain_aws import ChatBedrock
        from src.config.settings import AWS_PROFILE
        
        try:
            return ChatBedrock(
                credentials_profile_name=AWS_PROFILE,
                model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",  
                model_kwargs={"temperature": 0},
                streaming=True,
                system_prompt_with_tools=prompt_bedrock,
            )
        except Exception as e:
            logging.info("Error initializing ChatBedrock: %s", str(e))
            raise

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
                    model="llama3:8b",  
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

    def _init_deepseek_with_retry(self):
        from langchain_ollama import OllamaLLM
        from src.config.settings import OLLAMA_LLM_ENDPOINT
        
        max_wait = 60 
        interval = 5  
        start_time = time.time()

        while True:
            try:
                logging.info("Attempting to initialize Deepseek LLM at endpoint: %s", OLLAMA_LLM_ENDPOINT)
                llm = OllamaLLM(
                    model="deepseek-r1:8b",
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
