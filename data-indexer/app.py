#!/usr/bin/env python3
"""
Data Indexer Script
Processes PDF, TXT, and Markdown files and indexes them into Qdrant
"""

import os
import sys
from pathlib import Path
from typing import List, Union
import argparse

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader
)
from langchain_community.vectorstores import Qdrant
from langchain_text_splitters import CharacterTextSplitter
from langchain.embeddings.base import Embeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import requests
from langchain_qdrant import QdrantVectorStore

class EncoderEmbeddings(Embeddings):
    """Custom embeddings class that connects to the encoder service API"""
    
    def __init__(self, encoder_url: str):
        """
        Initialize the encoder embeddings
        
        Args:
            encoder_url: URL of the encoder service
        """
        self.encoder_url = encoder_url.rstrip('/')
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of documents using the encoder service
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings
        """
        try:
            response = requests.post(
                f"{self.encoder_url}/v1/embeddings",
                json={"input": texts},
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            # Parse OpenAI-compatible response format
            if isinstance(result, dict) and 'data' in result:
                # Extract embeddings from OpenAI-compatible format
                embeddings = [item['embedding'] for item in result['data']]
                return embeddings
            else:
                raise ValueError(f"Unexpected response format: {result}")
                
        except requests.exceptions.RequestException as e:
            print(f"Error calling encoder service: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            raise

    def embed_query(self, text: str) -> List[float]:
        pass  # Not implemented for simplicity

class DataIndexer:
    """Handles document processing and indexing to Qdrant"""
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.txt', '.md', '.markdown'}
    
    def __init__(
        self,
        vector_db_url: str,
        encoder_url: str,
        collection_name: str = "documents",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        remove_existing: bool = False
    ):
        """
        Initialize the DataIndexer
        
        Args:
            vector_db_url: URL of the vector database instance
            encoder_url: URL of the encoder service
            collection_name: Name of the collection to store documents
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            remove_existing: If True, remove and recreate collection
        """
        self.vector_db_url = vector_db_url
        self.encoder_url = encoder_url
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.remove_existing = remove_existing
        
        # Initialize embeddings using encoder service
        self.embeddings = EncoderEmbeddings(encoder_url=self.encoder_url)
        
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(url=self.vector_db_url)
        
        # Initialize text splitter
        self.text_splitter = CharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separator="\n"
        )
        
        self._ensure_collection_exists(remove_existing=remove_existing)
    
    def _ensure_collection_exists(self, remove_existing: bool = False):
        """
        Create collection if it doesn't exist, optionally remove existing
        
        Args:
            remove_existing: If True, delete and recreate the collection
        """
        collections = self.qdrant_client.get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        if self.collection_name in collection_names:
            if remove_existing:
                print(f"Removing existing collection: {self.collection_name}")
                self.qdrant_client.delete_collection(collection_name=self.collection_name)
                print(f"Creating new collection: {self.collection_name}")
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
            else:
                print(f"Using existing collection: {self.collection_name}")
        else:
            print(f"Creating collection: {self.collection_name}")
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
    
    def _check_existing_documents(self, file_path: Path) -> bool:
        """
        Check if a document has already been indexed
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if document already exists in collection
        """
        try:
            # Search for documents with matching source_path
            result = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter={
                    "must": [
                        {
                            "key": "metadata.source_path",
                            "match": {"value": str(file_path)}
                        }
                    ]
                },
                limit=1
            )
            
            # If we found any results, the document exists
            return len(result[0]) > 0
        except Exception as e:
            print(f"Error checking for existing document: {e}")
            return False
    
    def load_document(self, file_path: Path) -> List:
        """
        Load a document based on its file type
        
        Args:
            file_path: Path to the document
            
        Returns:
            List of loaded documents
        """
        extension = file_path.suffix.lower()
        
        try:
            if extension == '.pdf':
                loader = PyPDFLoader(str(file_path))
            elif extension == '.txt':
                loader = TextLoader(str(file_path))
            elif extension in ['.md', '.markdown']:
                loader = UnstructuredMarkdownLoader(str(file_path))
            else:
                print(f"Unsupported file type: {extension}")
                return []
            
            documents = loader.load()
            
            # Add filename metadata to all documents
            for doc in documents:
                doc.metadata['source_filename'] = file_path.name
                doc.metadata['source_path'] = str(file_path)
            
            return documents
        
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return []
    
    def process_and_index_file(self, file_path: Path) -> int:
        """
        Process a single file and index it to Qdrant
        
        Args:
            file_path: Path to the file
            
        Returns:
            Number of chunks indexed (0 if already exists or error)
        """
        print(f"Processing file: {file_path}")
        
        # Check if already indexed (unless we removed the collection)
        if not self.remove_existing and self._check_existing_documents(file_path):
            print(f"⊘ Skipping {file_path.name} - already indexed")
            return 0
        
        # Load document
        documents = self.load_document(file_path)
        
        if not documents:
            return 0
        
        # Split into chunks
        chunks = self.text_splitter.split_documents(documents)
        
        if not chunks:
            print(f"No chunks created from {file_path}")
            return 0
        
        # Index to Qdrant
        try:
            Qdrant.from_documents(
                chunks,
                self.embeddings,
                url=self.vector_db_url,
                collection_name=self.collection_name,
                force_recreate=False
            )
            print(f"✓ Indexed {len(chunks)} chunks from {file_path.name}")
            return len(chunks)
        
        except Exception as e:
            print(f"Error indexing {file_path}: {e}")
            return 0
    
    def process_path(self, path: Union[str, Path]) -> dict:
        """
        Process a file or directory
        
        Args:
            path: Path to file or directory
            
        Returns:
            Dictionary with processing statistics
        """
        path = Path(path)
        
        if not path.exists():
            print(f"Error: Path does not exist: {path}")
            return {'files_processed': 0, 'files_skipped': 0, 'chunks_indexed': 0, 'errors': 1}
        
        stats = {
            'files_processed': 0,
            'files_skipped': 0,
            'chunks_indexed': 0,
            'errors': 0
        }
        
        if path.is_file():
            # Process single file
            if path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                chunks = self.process_and_index_file(path)
                if chunks > 0:
                    stats['files_processed'] = 1
                    stats['chunks_indexed'] = chunks
                elif chunks == 0 and not self.remove_existing and self._check_existing_documents(path):
                    stats['files_skipped'] = 1
                else:
                    stats['errors'] = 1
            else:
                print(f"Unsupported file type: {path.suffix}")
                stats['errors'] = 1
        
        elif path.is_dir():
            # Process all supported files in directory
            files = [
                f for f in path.rglob('*')
                if f.is_file() and f.suffix.lower() in self.SUPPORTED_EXTENSIONS
            ]
            
            if not files:
                print(f"No supported files found in {path}")
                return stats
            
            print(f"Found {len(files)} supported files")
            
            for file_path in files:
                chunks = self.process_and_index_file(file_path)
                if chunks > 0:
                    stats['files_processed'] += 1
                    stats['chunks_indexed'] += chunks
                elif chunks == 0 and not self.remove_existing and self._check_existing_documents(file_path):
                    stats['files_skipped'] += 1
                else:
                    stats['errors'] += 1
        
        return stats


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Index documents into Qdrant vector database'
    )
    parser.add_argument(
        'path',
        type=str,
        help='Path to file or folder to index'
    )
    parser.add_argument(
        '--collection',
        type=str,
        default=os.getenv('COLLECTION_NAME', 'documents'),
        help='Qdrant collection name (default: documents)'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=500,
        help='Size of text chunks (default: 500)'
    )
    parser.add_argument(
        '--chunk-overlap',
        type=int,
        default=50,
        help='Overlap between chunks (default: 50)'
    )
    parser.add_argument(
        '--remove-existing-collection',
        action='store_true',
        help='Remove and recreate collection if it exists'
    )
    
    args = parser.parse_args()

    vector_db_url = os.getenv('VECTOR_DB_URL', 'http://vector-db:6333')
    encoder_url = os.getenv('ENCODER_URL', 'http://encoder:8001')
    
    # Initialize indexer
    indexer = DataIndexer(
        vector_db_url=vector_db_url,
        encoder_url=encoder_url,
        collection_name=args.collection,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        remove_existing=args.remove_existing_collection
    )
    
    # Process path
    print(f"\n{'='*60}")
    print("Starting indexing process")
    print(f"Path: {args.path}")
    print(f"Vector DB URL: {vector_db_url}")
    print(f"Encoder URL: {encoder_url}")
    print(f"Collection: {args.collection}")
    print(f"Chunk size: {args.chunk_size}, Overlap: {args.chunk_overlap}")
    print(f"Remove existing: {args.remove_existing_collection}")
    print(f"{'='*60}\n")
    
    stats = indexer.process_path(args.path)
    
    # Print summary
    print(f"\n{'='*60}")
    print("Indexing Complete")
    print(f"Files processed: {stats['files_processed']}")
    print(f"Files skipped (already indexed): {stats['files_skipped']}")
    print(f"Chunks indexed: {stats['chunks_indexed']}")
    print(f"Errors: {stats['errors']}")
    print(f"{'='*60}\n")
    
    return 0 if stats['errors'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
