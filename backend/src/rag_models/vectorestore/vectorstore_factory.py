from src.rag_models.embedding.embedding_factory import EmbeddingFactory
from src.config.settings import QDRANT_URL,QDRANT_API_KEY
class VectorStoreFactory:
    def __init__(self, vectorstore_type: str, collection_name: str, embedding_model_name: str):
        self.vectorstore_type = vectorstore_type.lower()
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model_name.lower()
        self.embedding = self._init_embedding_model()
        self.vectorstore = self._init_vectorstore()

    def _init_embedding_model(self):
        return EmbeddingFactory.get_embedding_model(self.embedding_model_name) 
        
    def _init_vectorstore(self):

        if self.vectorstore_type.lower() in "faisse":
            from langchain.vectorstores import Qdrant
            from qdrant_client import QdrantClient

            client = QdrantClient(url=QDRANT_URL, port=None, api_key=QDRANT_API_KEY)
            return Qdrant(
                client=client,
                collection_name=self.collection_name,
                embeddings=self.embedding,
            )

        elif self.vectorstore_type.lower() in "chroma":
            try:
                from langchain_chroma import Chroma
                from src.config.settings import CHROMA_DIR
                from src.utils.embedder_utils.embedder_warper import EmbeddingWrapper

                chroma_persist_dir = CHROMA_DIR
                if not chroma_persist_dir:
                    raise ValueError("Chroma persist directory must be provided for Chroma vector store.")
                embedding_instance = self.embedding
                wrapped_embedding = EmbeddingWrapper(embedding_instance)
                
                return Chroma(
                    persist_directory=chroma_persist_dir, 
                    collection_name=self.collection_name,
                    embedding_function=wrapped_embedding,
                )
            except Exception as e:
                print(f"Error creating Chroma vector store: {e}")
                raise

        else:
            raise ValueError(f"Unsupported vector store type: {self.vectorstore_type}. Supported types: 'qdrant', 'chroma'.")

    def get_vectorstore(self):

        return self.vectorstore