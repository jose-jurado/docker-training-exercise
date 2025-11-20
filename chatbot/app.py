#!/usr/bin/env python3
"""
RAG Chatbot Service
FastAPI-based chatbot with OpenAI-compatible API using LangChain and Qdrant
"""
import os
import time
import logging
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from qdrant_client import QdrantClient
from langchain_community.vectorstores import Qdrant
from langchain.embeddings.base import Embeddings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
ENCODER_URL = os.getenv('ENCODER_URL', 'http://encoder:8001')
LLM_URL = os.getenv('LLM_URL', 'http://llm:8002')
VECTOR_DB_URL = os.getenv('VECTOR_DB_URL', 'http://vector-db:6333')
COLLECTION_NAME = os.getenv('COLLECTION_NAME', 'documents')
TOP_K_RESULTS = int(os.getenv('TOP_K_RESULTS', '2'))
MODEL_NAME = os.getenv('MODEL_NAME', 'TinyLlama-1.1B-Chat-v1.0')

logger.info("Starting chatbot service with configuration:")
logger.info(f"  ENCODER_URL: {ENCODER_URL}")
logger.info(f"  LLM_URL: {LLM_URL}")
logger.info(f"  VECTOR_DB_URL: {VECTOR_DB_URL}")
logger.info(f"  COLLECTION_NAME: {COLLECTION_NAME}")
logger.info(f"  TOP_K_RESULTS: {TOP_K_RESULTS}")


# Pydantic Models (OpenAI-compatible)
class Message(BaseModel):
    role: str  # "user", "assistant", "system"
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = MODEL_NAME
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048
    stream: Optional[bool] = False


class ChatCompletionResponse(BaseModel):
    id: str = "chatcmpl-123"
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[dict]
    usage: dict


# EncoderEmbeddings Class (same as data-indexer)
class EncoderEmbeddings(Embeddings):
    """Custom embeddings class that connects to the encoder service API"""
    
    def __init__(self, encoder_url: str):
        """
        Initialize the encoder embeddings
        
        Args:
            encoder_url: URL of the encoder service
        """
        self.encoder_url = encoder_url.rstrip('/')
        logger.info(f"Initialized EncoderEmbeddings with URL: {self.encoder_url}")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of documents using the encoder service
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings
        """
        try:
            logger.debug(f"Embedding {len(texts)} documents")
            response = requests.post(
                f"{self.encoder_url}/v1/embeddings",
                json={"input": texts},
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            embeddings = [item['embedding'] for item in result['data']]
            logger.debug(f"Successfully embedded {len(embeddings)} documents")
            return embeddings
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling encoder service: {e}")
            raise HTTPException(status_code=503, detail=f"Encoder service error: {str(e)}")

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query text
        
        Args:
            text: Query text to embed
            
        Returns:
            Query embedding
        """
        logger.debug(f"Embedding query: {text[:100]}...")
        return self.embed_documents([text])[0]


# RAG Service Class
class RAGChatbot:
    """Handles retrieval-augmented generation for chatbot responses"""
    
    def __init__(self):
        """Initialize the RAG chatbot with vector store and embeddings"""
        logger.info("Initializing RAG Chatbot...")
        
        self.embeddings = EncoderEmbeddings(encoder_url=ENCODER_URL)
        self.qdrant_client = QdrantClient(url=VECTOR_DB_URL)
        
        logger.info(f"Connecting to Qdrant collection: {COLLECTION_NAME}")
        self.vectorstore = Qdrant(
            client=self.qdrant_client,
            collection_name=COLLECTION_NAME,
            embeddings=self.embeddings
        )
        
        logger.info("RAG Chatbot initialized successfully")
    
    def retrieve_context(self, query: str, k: int = TOP_K_RESULTS) -> str:
        """
        Retrieve relevant document chunks from Qdrant
        
        Args:
            query: User query to search for
            k: Number of top results to retrieve
            
        Returns:
            Concatenated context from retrieved documents
        """
        logger.info(f"Retrieving top {k} documents for query: {query[:100]}...")
        
        try:
            # TODO: Complete the retrieval logic
            return "Hi AI!"
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            raise HTTPException(status_code=503, detail=f"Vector DB error: {str(e)}")
    
    def generate_response(self, messages: List[Message], context: str, 
                         temperature: float, max_tokens: int) -> str:
        """
        Generate response using LLM with retrieved context
        
        Args:
            messages: Conversation messages
            context: Retrieved context from vector DB
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response text
        """
        # Extract user query (last user message)
        user_query = next(
            (msg.content for msg in reversed(messages) if msg.role == "user"),
            ""
        )
        
        if not user_query:
            raise HTTPException(status_code=400, detail="No user message found")
        
        logger.info(f"Generating response for query: {user_query[:100]}...")
        
        # TODO: Construct prompt with context
        system_prompt = ""
        
        # Prepare LLM request (OpenAI-compatible format)
        llm_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
        
        logger.debug(f"Calling LLM with temperature={temperature}, max_tokens={max_tokens}")
        
        try:
            # Call LLM service
            response = requests.post(
                f"{LLM_URL}/v1/chat/completions",
                json={
                    "model": MODEL_NAME,
                    "messages": llm_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=180
            )
            response.raise_for_status()
            
            result = response.json()
            generated_text = result['choices'][0]['message']['content']
            logger.info(f"Generated response: {len(generated_text)} characters")
            
            return generated_text
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling LLM service: {e}")
            raise HTTPException(status_code=503, detail=f"LLM service error: {str(e)}")


# Initialize FastAPI app
app = FastAPI(
    title="RAG Chatbot API",
    description="OpenAI-compatible chat API with Retrieval-Augmented Generation",
    version="1.0.0"
)

# Initialize RAG chatbot (singleton)
rag_chatbot = None


@app.on_event("startup")
async def startup_event():
    """Initialize RAG chatbot on startup"""
    global rag_chatbot
    logger.info("Starting up chatbot service...")
    try:
        rag_chatbot = RAGChatbot()
        logger.info("Chatbot service ready!")
    except Exception as e:
        logger.error(f"Failed to initialize chatbot: {e}")
        raise


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "RAG Chatbot API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "encoder_url": ENCODER_URL,
        "llm_url": LLM_URL,
        "vector_db_url": VECTOR_DB_URL,
        "collection": COLLECTION_NAME
    }


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
    """
    OpenAI-compatible chat completions endpoint
    
    Implements RAG workflow:
    1. Extract user query from messages
    2. Retrieve relevant context from vector DB
    3. Generate response using LLM with context
    4. Return OpenAI-compatible response
    """
    logger.info(f"Received chat completion request with {len(request.messages)} messages")
    
    if rag_chatbot is None:
        logger.error("Chatbot not initialized")
        raise HTTPException(status_code=503, detail="Chatbot service not initialized")
    
    try:
        # TODO: Extract user query
        user_query = ""
        
        # TODO: Retrieve relevant context from vector DB
        logger.info("Retrieving context from vector DB")
        
        # TODO:Generate response using LLM with context
        logger.info("Generating response with LLM (dummy)")

        # Coger el último mensaje de usuario de la request
        user_query = next(
            (msg.content for msg in reversed(request.messages) if msg.role == "user"),
            ""
        )

        response_content = f"Soy un bot de pruebas, Me has preguntado: {user_query}"

        
        # Return OpenAI-compatible response
        logger.info("Returning response to client")
        return ChatCompletionResponse(
            created=int(time.time()),
            model=request.model,
            choices=[{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_content
                },
                "finish_reason": "stop"
            }],
            usage={
                "prompt_tokens": 0,  # Could calculate if needed
                "completion_tokens": 0,
                "total_tokens": 0
            }
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chat completion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting uvicorn server on 0.0.0.0:8080")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
