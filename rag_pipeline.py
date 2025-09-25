#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.document_loaders import TextLoader
    from langchain_community.vectorstores import FAISS
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.chains import ConversationalRetrievalChain
    from langchain.memory import ConversationBufferWindowMemory
    from langchain.schema import Document
    from langchain.prompts import PromptTemplate
    import warnings

    warnings.filterwarnings("ignore", category=UserWarning)

except ImportError as e:
    print("Missing required packages. Please install them using:")
    print("pip install langchain langchain-google-genai langchain-huggingface langchain-community faiss-cpu")
    print(f"Error: {e}")
    sys.exit(1)


class RAGPipeline:
    def __init__(self, gemini_api_key: str = "AIzaSyD3R_-41HkKljnZgeI0_QXz5bdymMMsBbs"):
        self.gemini_api_key = gemini_api_key
        self.embeddings = None
        self.vectorstore = None
        self.llm = None
        self.memory = None
        self.qa_chain = None

    def setup_embeddings(self) -> None:
        logger.info("Setting up HuggingFace embeddings...")
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            logger.info("Embeddings initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {e}")
            raise

    def load_and_process_text(self, text_content: str) -> List[Document]:
        logger.info("Processing text content...")
        try:
            documents = [Document(page_content=text_content, metadata={"source": "extracted_text"})]
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            split_docs = text_splitter.split_documents(documents)
            logger.info(f"Text processed and split into {len(split_docs)} chunks")
            return split_docs
        except Exception as e:
            logger.error(f"Failed to process text: {e}")
            raise

    def load_and_process_document(self, txt_file_path: str) -> List[Document]:
        logger.info(f"Loading document from: {txt_file_path}")
        if not Path(txt_file_path).exists():
            raise FileNotFoundError(f"File not found: {txt_file_path}")
        try:
            loader = TextLoader(txt_file_path, encoding='utf-8')
            documents = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            split_docs = text_splitter.split_documents(documents)
            logger.info(f"Document loaded and split into {len(split_docs)} chunks")
            return split_docs
        except Exception as e:
            logger.error(f"Failed to load document: {e}")
            raise

    def create_vectorstore(self, documents: List[Document]) -> None:
        logger.info("Creating FAISS vector store...")
        try:
            self.vectorstore = FAISS.from_documents(
                documents=documents,
                embedding=self.embeddings
            )
            logger.info("Vector store created successfully")
        except Exception as e:
            logger.error(f"Failed to create vector store: {e}")
            raise

    def setup_llm(self) -> None:
        logger.info("Setting up Gemini 2.5 Flash LLM...")
        try:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=self.gemini_api_key,
                temperature=0.7,
                max_tokens=1024,
                timeout=60
            )
            logger.info("LLM initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise

    def setup_memory(self) -> None:
        logger.info("Setting up conversational memory...")
        self.memory = ConversationBufferWindowMemory(
            k=5,
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        logger.info("Memory initialized successfully")

    def create_qa_chain(self) -> None:
        logger.info("Creating QA chain with retrieval...")
        prompt_template = """You are an intelligent document assistant. Your primary role is to help users understand and extract information from uploaded documents, while also being able to engage in natural conversation.

    Instructions for responding:

    1. CONVERSATIONAL INTERACTIONS (greetings, small talk, general chat):
       - If the user is greeting you, making small talk, or having casual conversation that doesn't require document analysis, respond naturally and conversationally
       - Be helpful and friendly without mentioning the uploaded documents

    2. DOCUMENT-RELATED QUESTIONS (queries about content, analysis, specific information):
       - First, carefully examine the provided context from the uploaded document
       - If the answer is found in the context, provide a comprehensive response based on that information
       - Reference the document naturally (e.g., "According to the document...", "The text indicates...", "Based on the uploaded content...")

    3. OUT-OF-SCOPE QUESTIONS (information not in the document):
       - If the question is document-related but the answer is not available in the provided context, respond with:
       "This information is not available in the provided document. However, based on my general knowledge: [provide helpful general information]"
       - Be clear about what comes from the document vs. your general knowledge

    Context from uploaded document:
    {context}

    Previous conversation:
    {chat_history}

    Current question: {question}

    Response:"""
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question", "chat_history"]
        )
        try:
            self.qa_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=self.vectorstore.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 5}
                ),
                memory=self.memory,
                return_source_documents=True,
                verbose=False,
                combine_docs_chain_kwargs={"prompt": prompt}
            )
            logger.info("QA chain created successfully")
        except Exception as e:
            logger.error(f"Failed to create QA chain: {e}")
            raise

    def initialize_pipeline_from_text(self, text_content: str) -> None:
        print("Initializing RAG Pipeline from extracted text...")
        print("=" * 50)
        self.setup_embeddings()
        documents = self.load_and_process_text(text_content)
        self.create_vectorstore(documents)
        self.setup_llm()
        self.setup_memory()
        self.create_qa_chain()
        print("RAG Pipeline initialized successfully!")
        print("=" * 50)

    def initialize_pipeline_from_file(self, txt_file_path: str) -> None:
        print("Initializing RAG Pipeline from file...")
        print("=" * 50)
        self.setup_embeddings()
        documents = self.load_and_process_document(txt_file_path)
        self.create_vectorstore(documents)
        self.setup_llm()
        self.setup_memory()
        self.create_qa_chain()
        print("RAG Pipeline initialized successfully!")
        print("=" * 50)

    def query(self, question: str) -> dict:
        if not self.qa_chain:
            raise RuntimeError("Pipeline not initialized. Call initialize_pipeline() first.")
        try:
            result = self.qa_chain.invoke({"question": question})
            return result
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {"answer": f"Sorry, I encountered an error: {e}", "source_documents": []}

    def clear_memory(self) -> None:
        if self.memory:
            self.memory.clear()
            print("Conversation memory cleared.")

    def get_conversation_history(self) -> list:
        if hasattr(self.memory, 'chat_memory') and self.memory.chat_memory.messages:
            return self.memory.chat_memory.messages
        return []

    def save_vectorstore(self, path: str) -> None:
        if self.vectorstore:
            self.vectorstore.save_local(path)
            logger.info(f"Vector store saved to: {path}")

    def load_vectorstore(self, path: str) -> None:
        if self.embeddings and Path(path).exists():
            self.vectorstore = FAISS.load_local(path, self.embeddings, allow_dangerous_deserialization=True)
            logger.info(f"Vector store loaded from: {path}")
