import json
from src.rag_models.retriever.retriever_factory import Retrieval_Factory
from src.rag_models.vectorestore.vectorstore_factory import VectorStoreFactory
from src.utils.prompts.prompt import general_prompt

class Chat:
    def __init__(self, model, vectorstore_type: str, collection_name: str, embedding_model_name: str, retriever_type: str = "combined"):
        self.model = model
        self.prompt = general_prompt
        self.vectorstore = VectorStoreFactory(
            vectorstore_type, 
            collection_name,
            embedding_model_name
        ).get_vectorstore()
        self.retriever_type = retriever_type.lower()  

    async def ask_stream(self, query):
        try:
            retrieval_qna_handler = Retrieval_Factory(self.model, self.vectorstore)
            
            retriever_methods = {
                "conversation": retrieval_qna_handler.get_retrieve_answer_conversation,
                "condense": retrieval_qna_handler.get_retrieve_answer_conversation_combiened
            }
            
            method = retriever_methods.get(self.retriever_type, retrieval_qna_handler.get_retrieve_answer_conversation_combiened)
            
            async for letter in method(query, prompt_template=self.prompt):
                yield letter

        except Exception as error:
            yield json.dumps({"error": f"Error processing request: {error}"})
