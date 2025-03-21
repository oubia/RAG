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
    def remove_internal_thoughts(self,text: str) -> str:
        import re

        cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        cleaned = re.sub(r"<think>|</think>", "", cleaned)
        return cleaned.strip()


    def document_to_dict(self, doc):
        # convert document to dict
        return doc

    async def get_retrieve_qna_answer(self, query: str, prompt_template: str) -> AsyncGenerator[str, None]:
        from langchain.chains import RetrievalQA
        # histoy = self.format_chat_history(self.chat_history)

        # message_history = ChatMessageHistory()

        # memory = ConversationBufferMemory(
        #     chat_memory=message_history,
        #     return_messages=True,
        #     memory_key="chat_history"
        # )

        prompt = PromptTemplate.from_template(prompt_template)

        retriever = self.vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": 5,
                "score_threshold": 0.70,
            },
            content_payload_key="page_content",
            metadata_payload_key=[
                "nid", 
                "type", 
                "created", 
                "changed", 
                "langcode", 
                "source"
            ],  
        )

        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            # return_source_documents=True,
            # chain_kwargs={
            #     "prompt": prompt,
            # },
            verbose=True,
            
        )

        response = await qa_chain.arun(query+prompt_template)

        # print(response["source_documents"])

        result_text = response

        for letter in result_text:
            yield letter
            await asyncio.sleep(0.01)


    
    async def get_retrieve_answer_conversation(self, query: str, prompt_template: str) -> AsyncGenerator[str, None]:
        import asyncio
        from typing import AsyncGenerator
        from langchain.memory import ConversationBufferMemory
        from langchain.chains import ConversationalRetrievalChain
        from langchain.prompts import ChatPromptTemplate

        memory = ConversationBufferMemory(memory_key="chat_history", output_key="answer")

        retriever = self.vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": 10,
                "score_threshold": 0.6,
            },
            # search_type="mmr",
            # search_kwargs={
            #     "k": 5,
            #     "lambda_mult": 0.5,
            # },

            content_payload_key="page_content",
            metadata_payload_key=[
                "nid", 
                "type", 
                "created", 
                "changed", 
                "langcode", 
                "source"
            ],
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


    async def history_aware_retriever_function(self, query: str, prompt_template) -> AsyncGenerator[str, None]:
        from langchain.chains import history_aware_retriever

        retriever = self.vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": 5,
                "score_threshold": 0.50,
            },

            # search_type="mmr",
            # search_kwargs={
            #     "k": 5,
            #     "lambda_mult": 0.5,
            # },

            content_payload_key="page_content",
            metadata_payload_key=[
                "nid", 
                "type", 
                "created", 
                "changed", 
                "langcode", 
                "source"
            ],        
        )

   

        qa_chain = history_aware_retriever.create_history_aware_retriever(
            llm=self.llm,
            retriever=retriever,
            prompt=prompt_template,

        )
        response = await qa_chain.ainvoke(query)

        for letter in response["answer"]:
            yield letter
            await asyncio.sleep(0.01)

    async def get_self_query_retriever(self, query: str, prompt_template: str) -> AsyncGenerator[str, None]:
        from langchain.chains.query_constructor.schema import AttributeInfo
        from langchain.retrievers.self_query.base import SelfQueryRetriever
        from langchain_community.query_constructors.qdrant import QdrantTranslator
        from langchain.chains import ConversationalRetrievalChain
        from langchain.memory import ConversationBufferMemory
        from langchain_core.prompts import ChatPromptTemplate

        memory = ConversationBufferMemory(memory_key="chat_history")

        condense_question_template = """
            Given the following conversation and a follow up question.
            **make sure you include the metadata in every response you give and you answer with the language with which the query is asked by.**
            Context:
            {context}
            Follow Up Input: {question}"""
        
        condense_question_prompt = ChatPromptTemplate.from_template(condense_question_template)

        prompt = ChatPromptTemplate.from_template(prompt_template)

        metadata_field_info = [
            AttributeInfo(
                name="source",
                description="The link of the web page that the user can check",
                type="string",
            ),
            AttributeInfo(
                name="type",
                description="The type of the document",
                type="string",
            ),
        ]

        document_content_description = "This is the content of the web page of the public tansportation company"

        qdrant_translator = QdrantTranslator("source") 
        
        retriever = SelfQueryRetriever.from_llm(
            llm=self.llm,
            vectorstore=self.vectorstore,
            document_contents="page_content",  
            # metadata_key="metadata", 
            document_content_description=document_content_description,
            metadata_field_info=metadata_field_info,
            structured_query_translator=qdrant_translator,
            verbose=True,
        )


        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            memory=memory,
            condense_question_prompt= condense_question_prompt,
            combine_docs_chain_kwargs={
                "prompt": prompt,
            },
            verbose=True,
        )

        response = await qa_chain.ainvoke(query)
        print(f"this is ------------------------------ \n \n \n \n{type(self.llm)}")
        result_text = self.clean_deepseek_response(response["answer"])

        for letter in result_text:
            yield letter
            await asyncio.sleep(0.01)
            

    async def get_llmchain_retriever(self, query: str, prompt_template: str) -> AsyncGenerator[str, None]:

        from langchain.chains import LLMChain
        docs = self.vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": 5,
                "score_threshold": 0.50,
            },

            # search_type="mmr",
            # search_kwargs={
            #     "k": 5,
            #     "lambda_mult": 0.5,
            # },

            content_payload_key="page_content",
            metadata_payload_key=[
                "nid", 
                "type", 
                "created", 
                "changed", 
                "langcode", 
                "source"
            ],        
        )
        docs = docs.invoke(query)
        context = "\n".join([doc.page_content for doc in docs])+"\n links"+"\n".join([doc.metadata.get("source", "") for doc in docs if doc.metadata.get("source")])
        
        print(f"This is the content \n \n \n \t{context}")

        prompt = PromptTemplate.from_template(prompt_template)
        
        chain = LLMChain(
            llm=self.llm, 
            prompt=prompt,
            return_final_only=True,
            verbose=True,
            )
        
        input_data = {
            "context": context,
            "question": query,
            "prompt":prompt,
        }
        
        result = chain.run(input_data)
        

        for letter in result:
            yield letter
            await asyncio.sleep(0.01)



        
    async def get_retrieve_answer_conversation_combiened(self, query: str, prompt_template: str) -> AsyncGenerator[str, None]:
        import asyncio
        from typing import AsyncGenerator
        from langchain.memory import ConversationBufferMemory
        from langchain.chains import ConversationalRetrievalChain, LLMChain
        from langchain.prompts import ChatPromptTemplate, PromptTemplate
        memory = ConversationBufferMemory(memory_key="chat_history", output_key="answer")
        retriever = self.vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": 5,
                "score_threshold": 0.6,
            },
            content_payload_key="page_content",
            metadata_payload_key=["nid", "type", "created", "changed", "langcode", "source"],
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
