import json
from src.rag_models.retriever.retriever_factory import Retrieval_Factory
from src.rag_models.vectorestore.vectorstore_factory import VectorStoreFactory
from src.utils.prompts.prompt import general_prompt


class Chat:

    def __init__(
        self,
        model,
        vectorstore_type: str,
        collection_name: str,
        embedding_model_name: str,
        chunk_size: int,
        retriever_type:str,
    ):
        self.model = model
        self.prompt = general_prompt

        self.vectorstore = VectorStoreFactory(
            vectorstore_type,
            collection_name,
            embedding_model_name,
        ).get_vectorstore()

        self.retriever_type = retriever_type
        self.chunk_size = chunk_size

    async def ask_stream(self, query: str):
        try:
            retrieval_handler = Retrieval_Factory(
                llm=self.model,
                vectorstore=self.vectorstore,
                chunk_size=self.chunk_size,
            )

            retriever_methods = {
                "Similarity-research": retrieval_handler.answer_with_similarity,
                "Contextual-Compression": retrieval_handler.answer_with_compression,
                "Parent-document": retrieval_handler.answer_with_multiquery,
                "Hybrid-fusion": retrieval_handler.answer_with_hybrid,
            }

            method = retriever_methods.get(
                self.retriever_type, retrieval_handler.answer_with_similarity
            )

            async for letter in method(query, prompt_template=self.prompt):
                yield letter

        except Exception as error:
            yield json.dumps({"error": f"Error processing request: {error}"})
