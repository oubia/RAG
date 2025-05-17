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

    def __init__(self, llm, vectorstore, chat_history: list | None = None, chunk_size: int = 750):
        self.llm = llm
        self.vectorstore = vectorstore
        self.chunk_size = chunk_size
        self.chat_history = chat_history or []

    def load_raw_documents(self,csv_dir="D:\homy\S9\data-text-mining\RAG_Embeddings\data\output_csvs\output_csvs"):
        import os, pandas as pd
        from langchain.schema import Document

        docs = []
        for filename in os.listdir(csv_dir):
            if filename.endswith(".csv"):
                df = pd.read_csv(os.path.join(csv_dir, filename))
                for idx, row in df.iterrows():
                    txt = row.get("content", "").strip()
                    if txt:
                        docs.append(
                            Document(
                                page_content=txt,
                                metadata={
                                    "source_file": filename,
                                    "title": os.path.splitext(filename)[0],
                                },
                            )
                        )
        return docs

    def format_chat_history(self, chat_history):
        messages = []
        for item in chat_history:
            role, content = item["role"], item["content"].strip()
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
        return messages

    #  1) Standard vector-similarity (or MMR) retriever
  
    def build_similarity_retriever(self,  mmr: bool = False):
        if mmr:
            return self.vectorstore.as_retriever(
                search_type="mmr",
                search_kwargs={"k": 10, "lambda_mult": 0.5},
            )
        return self.vectorstore.as_retriever(
            search_type="similarity", search_kwargs={"k": 10}
        )

    def build_compression_retriever(self):

        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain.retrievers.document_compressors import (
            DocumentCompressorPipeline,
            EmbeddingsFilter, 
        )
        from langchain_community.document_transformers import EmbeddingsRedundantFilter

        from langchain.retrievers import ContextualCompressionRetriever
        from langchain.retrievers.document_compressors import LLMChainExtractor

        try:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size    = int(self.chunk_size) ,
                chunk_overlap = int(self.chunk_size * 0.1)   
            )

            compressor = DocumentCompressorPipeline(transformers=[splitter])


            return ContextualCompressionRetriever(
                base_compressor = compressor,
                base_retriever  = self.vectorstore.as_retriever(
                    search_type   = "similarity",
                    search_kwargs = {"k":10},
                ),
            )   
        except Exception as err:
            import logging, traceback
            logging.error("Failed to build ContextualCompressionRetriever")
            logging.error("".join(traceback.format_exception(err)))
            raise RuntimeError(f"Failed to build compression retriever: {err}") from err

    def build_multiquery_retriever(
        self,
        n_queries: int = 4,         
        top_k    : int = 10,           
    ) -> "MultiQueryRetriever":
        """
        • Uses the LLM to generate `n_queries` reformulations of the user question.
        • Performs similarity search in your *chunk* collection for each reformulation.
        • Merges and deduplicates, then returns at most `top_k` chunks.
        """
        from langchain.retrievers.multi_query import MultiQueryRetriever

        base = self.vectorstore.as_retriever(
            search_type   = "similarity",
            search_kwargs = {"k": top_k},
        )
        from langchain.prompts import PromptTemplate

        prompt = PromptTemplate.from_template(
        "You are a search expert. Generate {n} diverse, \
        semantically different search queries that could be used to look up \
        answers to the user question.\n\nUser question: {question}"
    ).partial(n=n_queries)
        mqr = MultiQueryRetriever.from_llm(
            retriever   = base,
            llm         = self.llm,
            prompt         = prompt,     
            include_original = True,     
            
        )
        return mqr


            
    from langchain.retrievers import BM25Retriever, EnsembleRetriever

    def build_hybrid_fusion_retriever(self,sparse_k: int = 20,alpha: float = 0.5):
        """
        alpha = 1   → only dense scores
        alpha = 0   → only BM25 scores
        """
        from langchain.schema import Document
        from langchain.retrievers import BM25Retriever, EnsembleRetriever

        dense = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 10},
        )

        try:
            results = self.vectorstore.get(
                include=["documents", "metadatas"],
                limit=10,         
            ) or {}

            docs_list  = results.get("documents") or []
            metas_list = results.get("metadatas") or []

            if not docs_list or not metas_list:
                raise RuntimeError(
                    f"No documents found in vectorstore (docs={len(docs_list)}, metas={len(metas_list)})"
                )

            all_docs = [
                Document(page_content=text, metadata=meta)
                for text, meta in zip(docs_list, metas_list)
            ]
            bm25 = BM25Retriever.from_documents(all_docs)
            bm25.k = sparse_k

            hybrid = EnsembleRetriever(
                retrievers=[dense, bm25],
                weights=[alpha, 1 - alpha],
            )
            return hybrid

        except Exception as err:
            import logging, traceback
            logging.error("Failed to build Hybrid-Fusion retriever")
            logging.error("".join(traceback.format_exception(err)))
            raise RuntimeError(f"Failed to build hybrid retriever: {err}") from err

    #  Generic ConversationalRetrieval chain
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
	    
        source_docs = response.get("source_documents", [])
        if source_docs:
            print("Retrieved documents (showing first 10):")
            for idx, doc in enumerate(source_docs[:10], start=1):   # 🔹 keep only first 10
                print(f"\n--- Document {idx} --- Chunk Size: {len(doc.page_content)}")
                print("Content:",   doc.page_content)
                print("Metadata:", doc.metadata)
        else:
            print("No source documents were retrieved.")

        for ch in answer:
            yield ch
            await asyncio.sleep(0.01)

    #  Convenience wrappers
    async def answer_with_similarity(
        self, query: str, prompt_template: str, mmr=False
    ):
        print(f"this ist this the similarity retriever")
        retriever = self.build_similarity_retriever(mmr=mmr)
        async for chunk in self.converse(query, prompt_template, retriever):
            yield chunk

    async def answer_with_compression(
        self, query: str, prompt_template: str
    ):
        print(f"this ist this the compression retriever")
        retriever = self.build_compression_retriever()

        async for chunk in self.converse(query, prompt_template, retriever):
            yield chunk

    async def answer_with_multiquery(
            self,
            query: str,
            prompt_template: str,
            n_queries: int = 4,
            top_k: int = 10,
    ):
        retriever = self.build_multiquery_retriever(
            n_queries=n_queries,
            top_k=top_k,
        )
        async for chunk in self.converse(query, prompt_template, retriever):
            yield chunk


    async def answer_with_hybrid(
        self,
        query: str,
        prompt_template: str,
    ):
        print(f"this ist this the answer_with_hybrid retriever")
        dense_k = 10
        sparse_k = 20
        alpha = 0.5
        retriever = self.build_hybrid_fusion_retriever(
            sparse_k=sparse_k, alpha=alpha
        )
        async for chunk in self.converse(query, prompt_template, retriever):
            yield chunk
