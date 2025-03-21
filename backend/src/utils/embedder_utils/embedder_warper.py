class EmbeddingWrapper:
    """ This class allows to warp and normalize the data before embeding during data storing or data retrieving
        Best practice to have well represented vectore space.
        Without the warpper the documents can not be retrieved.
        THis is usefull only when we use chromadb as a vectorstore.
       """
    def __init__(self, embedding_instance):
        self.embedding_instance = embedding_instance

    def embed_query(self, text: str):
        raw_embedding = self.embedding_instance.embed_query(text)
        if hasattr(self.embedding_instance, "normalizer") and callable(getattr(self.embedding_instance, "normalizer")):
            normalized_embedding = self.embedding_instance.normalizer(raw_embedding)
        elif hasattr(self.embedding_instance, "normalize") and callable(getattr(self.embedding_instance, "normalize")):
            normalized_embedding = self.embedding_instance.normalize(raw_embedding)
        else:
            import math
            norm = math.sqrt(sum(x * x for x in raw_embedding))
            normalized_embedding = [x / norm for x in raw_embedding] if norm != 0 else raw_embedding
        return normalized_embedding

    def embed_documents(self, texts: list) -> list:
        return [self.embed_query(text) for text in texts]
