# retrieval_factory.py
import asyncio
from typing import AsyncGenerator

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.retrievers import (
    ContextualCompressionRetriever,
    EnsembleRetriever,
    BM25Retriever,
)
from langchain_community.document_compressors.rankllm_rerank import RankLLMRerank
from langchain.schema import HumanMessage, AIMessage, Document
from langchain.prompts import ChatPromptTemplate

class Retrieval_Factory:
    """Create and use different retrievers on the same vector store."""

    def __init__(self, llm, vectorstore, chat_history: list | None = None, chunk_size: int = 750):
        self.llm = llm
        self.vectorstore = vectorstore
        self.chunk_size = chunk_size
        self.chat_history = chat_history or []

    # -----------------------------------------------------------
    #  Chat-history formatter (unchanged)
    # -----------------------------------------------------------
    def format_chat_history(self, chat_history):
        messages = []
        for item in chat_history:
            role, content = item["role"], item["content"].strip()
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
        return messages

    # -----------------------------------------------------------
    #  1) Standard vector-similarity (or MMR) retriever
    # -----------------------------------------------------------
    def build_similarity_retriever(self, k: int = 10, mmr: bool = False):
        if mmr:
            return self.vectorstore.as_retriever(
                search_type="mmr",
                search_kwargs={"k": k, "lambda_mult": 0.5},
            )
        return self.vectorstore.as_retriever(
            search_type="similarity", search_kwargs={"k": k}
        )

    # -----------------------------------------------------------
    #  2) ContextualCompression (late-chunking) retriever
    # -----------------------------------------------------------
    def build_compression_retriever(
        self,
        k: int = 8,
        chunk_size: int = 750,
        chunk_overlap: int = 80,
    ):
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        return ContextualCompressionRetriever(
            base_retriever=self.vectorstore.as_retriever(
                search_type="similarity", search_kwargs={"k": k}
            ),
            base_compressor=splitter,
        )

    # -----------------------------------------------------------
    #  3) Document-Rerank retriever (vector → LLM cross-encoder)
    # -----------------------------------------------------------
    def build_rerank_retriever(
        self,
        first_pass_k: int = 50,
        final_k: int = 8,
    ):
        first_pass = self.vectorstore.as_retriever(
            search_type="similarity", search_kwargs={"k": first_pass_k}
        )
        reranker = RankLLMRerank(top_n=final_k, llm=self.llm)
        return ContextualCompressionRetriever(
            base_retriever=first_pass, base_compressor=reranker
        )
    # -----------------------------------------------------------
    #  4) Hybrid-Fusion retriever  (dense + BM25)
    # Removed redundant import statement
    from langchain.retrievers import BM25Retriever, EnsembleRetriever

    

    def build_hybrid_fusion_retriever(
        self,
        dense_k: int = 8,
        sparse_k: int = 20,
        alpha: float = 0.5,          # weight for dense vs sparse (0–1)
    ):
        """
        alpha = 1   → only dense scores
        alpha = 0   → only BM25 scores
        """

        # 1️⃣  Dense part (similarity search on Chroma)
        dense_retriever = self.vectorstore.as_retriever(
            search_type="similarity", search_kwargs={"k": dense_k}
        )

        # 2️⃣  Sparse part (BM25 over the same corpus)
        #     We need the full corpus once to build the index
        all_docs = []
        for doc_text, meta in zip(
            *self.vectorstore.get(
                include=["documents", "metadatas"],
                limit=None,
            ).values()
        ):
            all_docs.append(Document(page_content=doc_text, metadata=meta))

        bm25 = BM25Retriever.from_documents(all_docs)
        bm25.k = sparse_k

        # 3️⃣  Fuse scores
        hybrid = EnsembleRetriever(
            retrievers=[dense_retriever, bm25],
            weights=[alpha, 1 - alpha],
        )
        return hybrid

    # -----------------------------------------------------------
    #  Generic ConversationalRetrieval chain
    # -----------------------------------------------------------
    async def converse(
        self,
        query: str,
        prompt_template: str,
        retriever,
    ) -> AsyncGenerator[str, None]:
        from langchain.memory import ConversationBufferMemory
        from langchain.chains import ConversationalRetrievalChain

        memory = ConversationBufferMemory(
            memory_key="chat_history", output_key="answer"
        )
        prompt = ChatPromptTemplate.from_template(prompt_template)

        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            memory=memory,
            combine_docs_chain_kwargs={"prompt": prompt},
            return_source_documents=True,
            verbose=True,
        )

        response = await qa_chain.ainvoke(query)
        answer = response.get("answer", "")

        # --- stream answer as characters ---
        for ch in answer:
            yield ch
            await asyncio.sleep(0.01)

    # -----------------------------------------------------------
    #  Convenience wrappers
    # -----------------------------------------------------------
    async def answer_with_similarity(
        self, query: str, prompt_template: str, k: int = 10, mmr=False
    ):
        retriever = self.build_similarity_retriever(k=k, mmr=mmr)
        async for chunk in self.converse(query, prompt_template, retriever):
            yield chunk

    async def answer_with_compression(
        self, query: str, prompt_template: str, k: int = 8
    ):
        retriever = self.build_compression_retriever(k=k)
        async for chunk in self.converse(query, prompt_template, retriever):
            yield chunk

    async def answer_with_rerank(
        self,
        query: str,
        prompt_template: str,
        first_pass_k: int = 50,
        final_k: int = 8,
    ):
        retriever = self.build_rerank_retriever(
            first_pass_k=first_pass_k, final_k=final_k
        )
        async for chunk in self.converse(query, prompt_template, retriever):
            yield chunk

    # -----------------------------------------------------------
    # convenience async wrapper
    # -----------------------------------------------------------
    async def answer_with_hybrid(
        self,
        query: str,
        prompt_template: str,
        dense_k: int = 8,
        sparse_k: int = 20,
        alpha: float = 0.5,
    ):
        retriever = self.build_hybrid_fusion_retriever(
            dense_k=dense_k, sparse_k=sparse_k, alpha=alpha
        )
        async for chunk in self.converse(query, prompt_template, retriever):
            yield chunk
