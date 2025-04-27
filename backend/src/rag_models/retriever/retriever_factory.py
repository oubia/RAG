import asyncio
from typing import AsyncGenerator
from langchain.prompts import PromptTemplate

class Retrieval_Factory:
    def __init__(self, llm, vectorstore, chat_history=None):
        self.llm = llm
        self.vectorstore = vectorstore
        self.chat_history = chat_history if chat_history else []

    def format_chat_history(self,chat_history):
        from langchain.schema import HumanMessage, AIMessage

        messages = []
        for item in chat_history:
            role = item['role']
            content = item['content'].strip()
            if role == 'user':
                messages.append(HumanMessage(content=content))
            elif role == 'assistant':
                messages.append(AIMessage(content=content))
        return messages

    def document_to_dict(self, doc):
        return doc


    async def get_retrieve_answer_conversation(self, query: str, prompt_template: str) -> AsyncGenerator[str, None]:
        import asyncio
        from typing import AsyncGenerator
        from langchain.memory import ConversationBufferMemory
        from langchain.chains import ConversationalRetrievalChain
        from langchain.prompts import ChatPromptTemplate

        memory = ConversationBufferMemory(memory_key="chat_history", output_key="answer")

        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": 10,
                # "score_threshold": 0.6,
            },
            # search_type="mmr",
            # search_kwargs={
            #     "k": 5,
            #     "lambda_mult": 0.5,
            # },

            # content_payload_key="page_content",
            # metadata_payload_key=[
            #     "nid", 
            #     "type", 
            #     "created", 
            #     "changed", 
            #     "langcode", 
            #     "source"
            # ],
        )
        prompt = ChatPromptTemplate.from_template(prompt_template)

        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            memory=memory,
            combine_docs_chain_kwargs={"prompt": prompt},
            verbose=True,
            response_if_no_docs_found="No relevant documents",
            return_source_documents=True,
            output_key="answer",
            # stop=["<think>", "</think>"]
        )

        response = await qa_chain.ainvoke(query)
        print("QA chain response:", response)

        source_docs = response.get("source_documents", [])
        if source_docs:
            print("Retrieved documents:")
            for idx, doc in enumerate(source_docs, start=1):
                print(f"\n--- Document {idx} ---")
                print("Content:", doc.page_content)
                print("Metadata:", doc.metadata)
        else:
            print("No source documents were retrieved.")
        answer = response.get("answer", "")
        # answer = self.remove_internal_thoughts(answer)
        # sources = []
        # for doc in source_docs:
        #     source_link = doc.metadata.get("source")
        #     if source_link:
        #         sources.append(source_link)

        # if sources:
        #     answer += "\n\nSources:\n" + "\n".join(sources)

        for letter in answer:
            yield letter
            await asyncio.sleep(0.01)

    async def get_retrieve_answer_conversation_combiened(self, query: str, prompt_template: str) -> AsyncGenerator[str, None]:
        import asyncio
        from typing import AsyncGenerator
        from langchain.memory import ConversationBufferMemory
        from langchain.chains import ConversationalRetrievalChain, LLMChain
        from langchain.prompts import ChatPromptTemplate, PromptTemplate
        memory = ConversationBufferMemory(memory_key="chat_history", output_key="answer")
        print(f"////////////////////{self.vectorstore._collection.count()}")  # Number of documents

        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": 10,
                
            },
        )

        print(f"retirever --------------------->  {retriever}")
        prompt = ChatPromptTemplate.from_template(prompt_template)
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            memory=memory,
            combine_docs_chain_kwargs={"prompt": prompt},
            verbose=True,
            response_if_no_docs_found="No relevant documents",
            return_source_documents=True,
            output_key="answer",
        )
        response = await qa_chain.ainvoke(query)
        print("Initial QA chain response:", response)

        source_docs = response.get("source_documents", [])
        if source_docs:
            print("Retrieved documents:")
            for idx, doc in enumerate(source_docs, start=1):
                print(f"\n--- Document {idx} ---")
                print("Content:", doc.page_content)
                print("Metadata:", doc.metadata)
        else:
            print("No source documents were retrieved.")

        initial_answer = response.get("answer", "")
        initial_answer = self.remove_internal_thoughts(initial_answer)

    
        sources = []
        for doc in source_docs:
            source_link = doc.metadata.get("source")
            if source_link:
                sources.append(source_link)
        source_links_str = "\n".join(sources)

        refinement_prompt_template = (
            "Hai generato la seguente risposta iniziale: n n"
            "{initial_answer} n n"
            "Sono disponibili i seguenti collegamenti:"
            "{source_links} n n"
            "Riscrivere la risposta integrando naturalmente i collegamenti di origine nel punto più appropriato."
            "Non aggiungere informazioni che non sono nella risposta iniziale.  n n"
            "Risposta finale:"
        )
        refinement_prompt = PromptTemplate(
            template=refinement_prompt_template,
            input_variables=["initial_answer", "source_links"]
        )
        
        refinement_input = {
            "initial_answer": initial_answer,
            "source_links": source_links_str
        }
        refinement_chain = LLMChain(llm=self.llm, prompt=refinement_prompt)
        refined_answer = refinement_chain.run(refinement_input)
        refined_answer = self.remove_internal_thoughts(refined_answer)

        for letter in refined_answer:
            yield letter
            await asyncio.sleep(0.01)
