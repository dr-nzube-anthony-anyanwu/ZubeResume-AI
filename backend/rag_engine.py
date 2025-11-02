"""
RAG (Retrieval-Augmented Generation) Engine for SmartResume AI
Implements vectorization and semantic search for resume content
"""

import logging
import numpy as np
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import uuid
import re
from pathlib import Path
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGEngine:
    """
    Retrieval-Augmented Generation engine for resume content
    Uses sentence transformers and ChromaDB for vector storage and retrieval
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the RAG engine
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name
        self.embedding_model = None
        self.collection = None
        self.client = None
        self.resume_chunks = []
        
        # Initialize the embedding model
        self._initialize_model()
        
        # Initialize ChromaDB
        self._initialize_vector_store()
    
    def _initialize_model(self):
        """Initialize the sentence transformer model"""
        try:
            logger.info(f"Loading sentence transformer model: {self.model_name}")
            self.embedding_model = SentenceTransformer(self.model_name)
            logger.info("✅ Sentence transformer model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load sentence transformer model: {e}")
            # Fallback to a simpler model
            try:
                self.embedding_model = SentenceTransformer("paraphrase-MiniLM-L3-v2")
                logger.info("✅ Fallback model loaded successfully")
            except Exception as e2:
                logger.error(f"❌ Failed to load fallback model: {e2}")
                self.embedding_model = None
    
    def _initialize_vector_store(self):
        """Initialize ChromaDB vector store"""
        try:
            # Create ChromaDB client with persistent storage
            persist_dir = Path("./vector_store")
            persist_dir.mkdir(exist_ok=True)
            
            self.client = chromadb.PersistentClient(
                path=str(persist_dir),
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Create or get collection
            collection_name = "resume_chunks"
            try:
                self.collection = self.client.get_collection(collection_name)
                logger.info(f"✅ Retrieved existing collection: {collection_name}")
            except:
                self.collection = self.client.create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"✅ Created new collection: {collection_name}")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize vector store: {e}")
            self.collection = None
    
    def chunk_resume_content(self, resume_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Break down resume content into meaningful chunks for vectorization
        
        Args:
            resume_data: Parsed resume data
            
        Returns:
            List of resume chunks with metadata
        """
        chunks = []
        
        try:
            # Personal information chunk
            if resume_data.get('personal_info'):
                personal_info = resume_data['personal_info']
                chunk_text = f"Personal Information: {personal_info.get('name', '')} {personal_info.get('email', '')} {personal_info.get('phone', '')} {personal_info.get('location', '')}"
                chunks.append({
                    'id': str(uuid.uuid4()),
                    'text': chunk_text.strip(),
                    'type': 'personal_info',
                    'metadata': personal_info
                })
            
            # Professional summary chunk
            if resume_data.get('summary'):
                chunks.append({
                    'id': str(uuid.uuid4()),
                    'text': f"Professional Summary: {resume_data['summary']}",
                    'type': 'summary',
                    'metadata': {'summary': resume_data['summary']}
                })
            
            # Experience chunks (each job as separate chunk)
            if resume_data.get('experience'):
                for i, exp in enumerate(resume_data['experience']):
                    exp_text = f"Experience: {exp.get('title', '')} at {exp.get('company', '')} ({exp.get('duration', '')}). {exp.get('description', '')}"
                    chunks.append({
                        'id': str(uuid.uuid4()),
                        'text': exp_text,
                        'type': 'experience',
                        'metadata': {
                            'position': i,
                            'title': exp.get('title', ''),
                            'company': exp.get('company', ''),
                            'duration': exp.get('duration', ''),
                            'description': exp.get('description', '')
                        }
                    })
            
            # Skills chunks (grouped by category if available)
            if resume_data.get('skills'):
                skills_text = f"Skills: {', '.join(resume_data['skills'])}"
                chunks.append({
                    'id': str(uuid.uuid4()),
                    'text': skills_text,
                    'type': 'skills',
                    'metadata': {'skills': resume_data['skills']}
                })
            
            # Education chunks
            if resume_data.get('education'):
                for i, edu in enumerate(resume_data['education']):
                    edu_text = f"Education: {edu.get('degree', '')} from {edu.get('institution', '')} ({edu.get('year', '')}). {edu.get('details', '')}"
                    chunks.append({
                        'id': str(uuid.uuid4()),
                        'text': edu_text,
                        'type': 'education',
                        'metadata': {
                            'position': i,
                            'degree': edu.get('degree', ''),
                            'institution': edu.get('institution', ''),
                            'year': edu.get('year', ''),
                            'details': edu.get('details', '')
                        }
                    })
            
            # Projects chunks
            if resume_data.get('projects'):
                for i, project in enumerate(resume_data['projects']):
                    project_text = f"Project: {project.get('name', '')}. {project.get('description', '')} Technologies: {project.get('technologies', '')}"
                    chunks.append({
                        'id': str(uuid.uuid4()),
                        'text': project_text,
                        'type': 'projects',
                        'metadata': {
                            'position': i,
                            'name': project.get('name', ''),
                            'description': project.get('description', ''),
                            'technologies': project.get('technologies', '')
                        }
                    })
            
            # Certifications chunks
            if resume_data.get('certifications'):
                cert_text = f"Certifications: {', '.join(resume_data['certifications'])}"
                chunks.append({
                    'id': str(uuid.uuid4()),
                    'text': cert_text,
                    'type': 'certifications',
                    'metadata': {'certifications': resume_data['certifications']}
                })
            
            logger.info(f"✅ Created {len(chunks)} resume chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Error chunking resume content: {e}")
            return []
    
    def vectorize_resume(self, resume_data: Dict[str, Any]) -> bool:
        """
        Vectorize resume content and store in vector database
        
        Args:
            resume_data: Parsed resume data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.embedding_model or not self.collection:
                logger.error("❌ RAG engine not properly initialized")
                return False
            
            # Clear existing data
            try:
                self.collection.delete()
                logger.info("🧹 Cleared existing resume vectors")
            except:
                pass
            
            # Chunk the resume content
            chunks = self.chunk_resume_content(resume_data)
            if not chunks:
                logger.error("❌ No chunks created from resume data")
                return False
            
            # Generate embeddings for all chunks
            chunk_texts = [chunk['text'] for chunk in chunks]
            embeddings = self.embedding_model.encode(chunk_texts, convert_to_tensor=False)
            
            # Store in vector database
            ids = [chunk['id'] for chunk in chunks]
            metadatas = []
            documents = []
            
            for chunk in chunks:
                metadatas.append({
                    'type': chunk['type'],
                    'metadata': json.dumps(chunk['metadata'])
                })
                documents.append(chunk['text'])
            
            # Add to collection
            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            # Store chunks for later reference
            self.resume_chunks = chunks
            
            logger.info(f"✅ Successfully vectorized {len(chunks)} resume chunks")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error vectorizing resume: {e}")
            return False
    
    def retrieve_relevant_content(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve the most relevant resume content for a given query
        
        Args:
            query: Search query (e.g., job description or requirements)
            top_k: Number of most relevant chunks to return
            
        Returns:
            List of relevant chunks with similarity scores
        """
        try:
            if not self.embedding_model or not self.collection:
                logger.error("❌ RAG engine not properly initialized")
                return []
            
            # Generate embedding for the query
            query_embedding = self.embedding_model.encode([query], convert_to_tensor=False)
            
            # Search in vector database
            results = self.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=min(top_k, len(self.resume_chunks))
            )
            
            # Format results
            relevant_chunks = []
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    relevant_chunks.append({
                        'text': doc,
                        'type': metadata['type'],
                        'metadata': json.loads(metadata['metadata']),
                        'similarity_score': 1 - distance,  # Convert distance to similarity
                        'rank': i + 1
                    })
            
            logger.info(f"✅ Retrieved {len(relevant_chunks)} relevant chunks for query")
            return relevant_chunks
            
        except Exception as e:
            logger.error(f"❌ Error retrieving relevant content: {e}")
            return []
    
    def get_contextual_resume_data(self, job_description: str, top_k: int = 8) -> Dict[str, Any]:
        """
        Get the most relevant parts of the resume for a specific job description
        
        Args:
            job_description: The job description to match against
            top_k: Number of most relevant chunks to return
            
        Returns:
            Dictionary with contextualized resume data
        """
        try:
            # Retrieve relevant content
            relevant_chunks = self.retrieve_relevant_content(job_description, top_k)
            
            if not relevant_chunks:
                logger.warning("⚠️ No relevant content found, returning empty context")
                return {'relevant_content': [], 'context_summary': ''}
            
            # Group chunks by type for better organization
            grouped_content = {}
            for chunk in relevant_chunks:
                chunk_type = chunk['type']
                if chunk_type not in grouped_content:
                    grouped_content[chunk_type] = []
                grouped_content[chunk_type].append(chunk)
            
            # Create context summary
            context_parts = []
            for chunk_type, chunks in grouped_content.items():
                if chunk_type == 'experience':
                    context_parts.append(f"Most relevant experience ({len(chunks)} positions)")
                elif chunk_type == 'skills':
                    context_parts.append(f"Relevant skills")
                elif chunk_type == 'projects':
                    context_parts.append(f"Relevant projects ({len(chunks)} projects)")
                elif chunk_type == 'education':
                    context_parts.append(f"Relevant education")
                else:
                    context_parts.append(f"Relevant {chunk_type}")
            
            context_summary = f"Retrieved: {', '.join(context_parts)}"
            
            result = {
                'relevant_content': relevant_chunks,
                'grouped_content': grouped_content,
                'context_summary': context_summary,
                'total_chunks': len(relevant_chunks)
            }
            
            logger.info(f"✅ Generated contextual resume data: {context_summary}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting contextual resume data: {e}")
            return {'relevant_content': [], 'context_summary': 'Error retrieving context'}
    
    def get_resume_statistics(self) -> Dict[str, Any]:
        """Get statistics about the vectorized resume"""
        try:
            if not self.collection:
                return {'error': 'Vector store not initialized'}
            
            # Get collection info
            collection_count = self.collection.count()
            
            # Analyze chunk types
            chunk_types = {}
            for chunk in self.resume_chunks:
                chunk_type = chunk['type']
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
            
            return {
                'total_chunks': collection_count,
                'chunk_distribution': chunk_types,
                'model_name': self.model_name,
                'vector_store_status': 'active'
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting resume statistics: {e}")
            return {'error': str(e)}