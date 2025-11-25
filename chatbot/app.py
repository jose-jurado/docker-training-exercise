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
#from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
#from langchain_community.vectorstores import Qdrant
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
MODEL_NAME = os.getenv('MODEL_NAME', 'gpt-4o-mini')

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
        #self.qdrant_client = QdrantClient(url=VECTOR_DB_URL)
        
        logger.info(f"Connecting to Qdrant collection: {COLLECTION_NAME}")
        self.vectorstore = QdrantVectorStore.from_existing_collection(
            embedding=self.embeddings,
            collection_name=COLLECTION_NAME,
            url=VECTOR_DB_URL,
        )
        
        logger.info("RAG Chatbot initialized successfully")
    
    def retrieve_context(self, query: str, k: int = TOP_K_RESULTS) -> str:
        """
        Retrieve relevant document chunks from Qdrant
        """
        logger.info(f"Retrieving top {k} documents for query: {query[:100]}...")

        try:
            # Buscar en Qdrant los k documentos más parecidos
            docs = self.vectorstore.similarity_search(query, k=k)

            logger.info(f"similarity_search devolvió {len(docs)} documentos")

            if not docs:
                logger.info("No documents found for query, returning empty context")
                return ""

            # Log de un  trozo de los docs para ver qué están devolviendo
            for i, d in enumerate(docs[:3]):
                snippet = d.page_content[:200].replace("\n", " ")
                logger.info(f"[DOC {i}] filename={d.metadata.get('source_filename')} snippet={snippet!r}")

            # unir los textos del doc e n un solo context
            context = "\n\n".join(doc.page_content for doc in docs)

            logger.info(f"Context length: {len(context)} characters")
            return context

        except Exception as e:
            logger.error(f"Error retrieving context: {e}", exc_info=True)
            raise HTTPException(status_code=503, detail=f"Vector DB error: {str(e)}")

    
    def generate_response(self, messages: List[Message], context: str,
                        temperature: float, max_tokens: int) -> str:
        """
        Generate response using LLM with retrieved context
        """

        #extraer la última pregunta del usuario
        user_query = next(
            (msg.content for msg in reversed(messages) if msg.role == "user"),
            ""
        )
        if not user_query:
            raise HTTPException(status_code=400, detail="No user message found")

        logger.info(f"Generating response for query: {user_query[:100]}...")

        #solo puede usar el contexto
        system_prompt = (
            "Eres un asistente RAG jurídico que responde SIEMPRE en español, "
            "de forma clara y concisa.\n\n"
            "Solo puedes utilizar la información que aparece en el CONTEXTO "
            "proporcionado (fragmentos del BOE).\n\n"
            "Normas estrictas:\n"
            "- Usa únicamente el CONTEXTO para responder.\n"
            "- Puedes citar artículos, disposiciones o capítulos SOLO si aparecen "
            "claramente en el CONTEXTO.\n"
            "- Si el CONTEXTO no contiene información relevante para la pregunta, "
            "responde EXACTAMENTE:\n"
            "\"No lo sé; esa información no aparece en los documentos disponibles.\"\n"
            "- No inventes artículos, números de disposición ni contenido que no esté "
            "en el CONTEXTO.\n"
        )

        # mensaje de usuario le pasamos contexto + pregunta
        user_content = (
            "CONTEXTO:\n"
            f"{context}\n"
            f"Pregunta del usuario:\n{user_query}"
        )

        llm_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        logger.debug(f"Calling LLM with temperature={temperature}, max_tokens={max_tokens}")

        try:
            response = requests.post(
                f"{LLM_URL}/v1/chat/completions",
                json={
                    "model": MODEL_NAME,
                    "messages": llm_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=180,
            )
            response.raise_for_status()

            result = response.json()
            generated_text = result["choices"][0]["message"]["content"]
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
        # Extraer ultimo mensaje del user
        user_query = next(
            (msg.content for msg in reversed(request.messages) if msg.role == "user"),
            ""
        )
        if not user_query:
            raise HTTPException(status_code=400, detail="No user message found")

        #Recupero contexto desde Qdrant 
        logger.info("Retrieving context from vector DB")
        context = rag_chatbot.retrieve_context(user_query)

        # me aseguro que context sea siempre string
        if context is None:
            context = ""

        # Si NO hay contexto, decimos que no lo sé
        if not context.strip():
            logger.info("No context returned for query - answering 'no lo sé'")
            response_content = (
                "No he encontrado información relacionada con tu pregunta "
                "en los documentos que tengo indexados. "
                "No lo sé; esa información no aparece en los documentos disponibles."
            )
        else:
            logger.info("Generating response with LLM via RAGChatbot")
            response_content = rag_chatbot.generate_response(
                messages=request.messages,
                context=context,
                temperature=request.temperature or 0.7,
                max_tokens=request.max_tokens or 512
            )


        #Retorno respuesta 
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
                "prompt_tokens": 0,
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
