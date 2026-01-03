"""Memory storage and retrieval system using ChromaDB.

This module provides the MemoryStore class that manages episodic and semantic
memories using vector embeddings for similarity-based retrieval.
"""

import json
import os
from datetime import datetime
from typing import List, Optional, Union, Literal
from pathlib import Path

try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("Warning: chromadb not installed. Install with: pip install chromadb sentence-transformers")

from memory.types import Memory, EpisodicMemory, SemanticMemory, create_memory_id


class MemoryStore:
    """Manages storage and retrieval of game memories using vector database.
    
    Features:
    - Semantic similarity search using embeddings
    - Episodic memory decay over time
    - Metadata filtering (by NPC, type, importance)
    - Persistence to JSON for save/load
    """
    
    def __init__(self, db_path: str = "./data/memory_db", embedding_model: str = "all-MiniLM-L6-v2"):
        """Initialize the memory store.
        
        Args:
            db_path: Path to ChromaDB persistent storage
            embedding_model: Sentence transformer model name
        """
        self.db_path = db_path
        self.embedding_model = embedding_model
        self.memories: dict[str, Union[EpisodicMemory, SemanticMemory]] = {}
        
        # Initialize ChromaDB if available
        self.chroma_available = CHROMADB_AVAILABLE
        self.client = None
        self.collection = None
        
        if self.chroma_available:
            self._init_chromadb()
        else:
            print("MemoryStore: Running without ChromaDB (semantic search disabled)")
    
    def _init_chromadb(self):
        """Initialize ChromaDB client and collection."""
        try:
            # Create directory if it doesn't exist
            Path(self.db_path).mkdir(parents=True, exist_ok=True)
            
            # Initialize ChromaDB with sentence transformers
            sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self.embedding_model
            )
            
            self.client = chromadb.PersistentClient(path=self.db_path)
            self.collection = self.client.get_or_create_collection(
                name="game_memories",
                embedding_function=sentence_transformer_ef,
                metadata={"hnsw:space": "cosine"}
            )
            
            print(f"MemoryStore: ChromaDB initialized at {self.db_path}")
        except Exception as e:
            print(f"Warning: ChromaDB initialization failed: {e}")
            self.chroma_available = False
    
    def add_memory(self, memory: Union[EpisodicMemory, SemanticMemory]) -> str:
        """Add a memory to the store.
        
        Args:
            memory: Memory object to store
            
        Returns:
            Memory ID
        """
        # Ensure memory has an ID
        if not memory.id:
            memory.id = create_memory_id()
        
        # Store in local dict
        self.memories[memory.id] = memory
        
        # Add to ChromaDB if available
        if self.chroma_available and self.collection:
            try:
                metadata = {
                    "npc_id": memory.npc_id,
                    "memory_type": memory.memory_type,
                    "created_at": memory.created_at.isoformat(),
                }
                
                # Add type-specific metadata
                if isinstance(memory, EpisodicMemory):
                    metadata.update({
                        "importance": memory.importance,
                        "emotion": memory.emotion,
                        "location": memory.location,
                        "current_strength": memory.current_strength
                    })
                elif isinstance(memory, SemanticMemory):
                    metadata.update({
                        "fact_type": memory.fact_type,
                        "confidence": memory.confidence
                    })
                
                self.collection.add(
                    ids=[memory.id],
                    documents=[memory.text],
                    metadatas=[metadata]
                )
            except Exception as e:
                print(f"Warning: Failed to add memory to ChromaDB: {e}")
        
        return memory.id
    
    def retrieve_memories(
        self,
        query: str,
        npc_id: Optional[str] = None,
        memory_type: Optional[Literal["episodic", "semantic"]] = None,
        min_importance: float = 0.0,
        n: int = 5
    ) -> List[Union[EpisodicMemory, SemanticMemory]]:
        """Retrieve relevant memories using semantic similarity.
        
        Args:
            query: Search query text
            npc_id: Filter by NPC ID (None for all NPCs)
            memory_type: Filter by memory type (None for both)
            min_importance: Minimum importance threshold for episodic memories
            n: Number of memories to return
            
        Returns:
            List of relevant memories, sorted by relevance
        """
        if not self.chroma_available or not self.collection:
            # Fallback: return most recent memories
            return self._fallback_retrieve(npc_id, memory_type, n)
        
        try:
            # Build filter
            where_filter = {}
            if npc_id:
                where_filter["npc_id"] = npc_id
            if memory_type:
                where_filter["memory_type"] = memory_type
            
            # Query ChromaDB
            results = self.collection.query(
                query_texts=[query],
                n_results=n * 2,  # Get more to filter
                where=where_filter if where_filter else None
            )
            
            # Extract memory IDs
            memory_ids = results['ids'][0] if results['ids'] else []
            
            # Get full memory objects and filter
            memories = []
            for mem_id in memory_ids:
                if mem_id in self.memories:
                    memory = self.memories[mem_id]
                    
                    # Filter by importance for episodic memories
                    if isinstance(memory, EpisodicMemory):
                        if memory.importance >= min_importance and memory.current_strength > 0.1:
                            memories.append(memory)
                    else:
                        memories.append(memory)
                    
                    if len(memories) >= n:
                        break
            
            return memories
        
        except Exception as e:
            print(f"Warning: ChromaDB query failed: {e}")
            return self._fallback_retrieve(npc_id, memory_type, n)
    
    def _fallback_retrieve(
        self,
        npc_id: Optional[str],
        memory_type: Optional[Literal["episodic", "semantic"]],
        n: int
    ) -> List[Union[EpisodicMemory, SemanticMemory]]:
        """Fallback retrieval without semantic search."""
        filtered = []
        for memory in self.memories.values():
            if npc_id and memory.npc_id not in [npc_id, "all"]:
                continue
            if memory_type and memory.memory_type != memory_type:
                continue
            filtered.append(memory)
        
        # Sort by creation time (most recent first)
        filtered.sort(key=lambda m: m.created_at, reverse=True)
        return filtered[:n]
    
    def get_npc_memories(self, npc_id: str) -> List[Union[EpisodicMemory, SemanticMemory]]:
        """Get all memories for a specific NPC.
        
        Args:
            npc_id: NPC identifier
            
        Returns:
            List of all memories belonging to this NPC
        """
        return [
            memory for memory in self.memories.values()
            if memory.npc_id == npc_id or memory.npc_id == "all"
        ]
    
    def get_important_memories(
        self,
        npc_id: Optional[str] = None,
        min_importance: float = 0.7,
        n: int = 10
    ) -> List[EpisodicMemory]:
        """Get high-importance episodic memories.
        
        Args:
            npc_id: Filter by NPC (None for all)
            min_importance: Minimum importance threshold
            n: Maximum number to return
            
        Returns:
            List of important episodic memories
        """
        memories = []
        for memory in self.memories.values():
            if not isinstance(memory, EpisodicMemory):
                continue
            if npc_id and memory.npc_id not in [npc_id, "all"]:
                continue
            if memory.importance >= min_importance and memory.current_strength > 0.1:
                memories.append(memory)
        
        # Sort by importance * strength
        memories.sort(key=lambda m: m.importance * m.current_strength, reverse=True)
        return memories[:n]
    
    def decay_memories(self, current_time: datetime):
        """Update strength of all episodic memories based on time decay.
        
        Args:
            current_time: Current game time
        """
        for memory in self.memories.values():
            if isinstance(memory, EpisodicMemory):
                memory.update_strength(current_time)
        
        # Update ChromaDB metadata if available
        if self.chroma_available and self.collection:
            self._sync_to_chromadb()
    
    def prune_weak_memories(self, threshold: float = 0.1):
        """Remove episodic memories that have decayed below threshold.
        
        Args:
            threshold: Minimum strength to keep
        """
        to_delete = []
        for mem_id, memory in self.memories.items():
            if isinstance(memory, EpisodicMemory) and memory.current_strength < threshold:
                to_delete.append(mem_id)
        
        # Delete from local storage
        for mem_id in to_delete:
            del self.memories[mem_id]
        
        # Delete from ChromaDB
        if self.chroma_available and self.collection and to_delete:
            try:
                self.collection.delete(ids=to_delete)
            except Exception as e:
                print(f"Warning: Failed to prune memories from ChromaDB: {e}")
        
        if to_delete:
            print(f"Pruned {len(to_delete)} weak memories")
    
    def _sync_to_chromadb(self):
        """Sync all memories to ChromaDB (useful after decay updates)."""
        if not self.chroma_available or not self.collection:
            return
        
        try:
            # Update all episodic memories with current strength
            for mem_id, memory in self.memories.items():
                if isinstance(memory, EpisodicMemory):
                    self.collection.update(
                        ids=[mem_id],
                        metadatas=[{"current_strength": memory.current_strength}]
                    )
        except Exception as e:
            print(f"Warning: Failed to sync to ChromaDB: {e}")
    
    def save_to_json(self, filepath: str):
        """Save all memories to JSON file.
        
        Args:
            filepath: Path to save JSON file
        """
        data = {
            "memories": [memory.to_dict() for memory in self.memories.values()]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_from_json(self, filepath: str):
        """Load memories from JSON file.
        
        Args:
            filepath: Path to JSON file
        """
        if not os.path.exists(filepath):
            return
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Clear existing memories
        self.memories.clear()
        if self.chroma_available and self.collection:
            try:
                # Clear ChromaDB collection
                self.collection.delete(where={})
            except:
                pass
        
        # Load memories
        for mem_dict in data.get("memories", []):
            if mem_dict["memory_type"] == "episodic":
                memory = EpisodicMemory.from_dict(mem_dict)
            else:
                memory = SemanticMemory.from_dict(mem_dict)
            
            self.memories[memory.id] = memory
            
            # Re-add to ChromaDB
            if self.chroma_available and self.collection:
                try:
                    metadata = {
                        "npc_id": memory.npc_id,
                        "memory_type": memory.memory_type,
                        "created_at": memory.created_at.isoformat(),
                    }
                    
                    if isinstance(memory, EpisodicMemory):
                        metadata.update({
                            "importance": memory.importance,
                            "emotion": memory.emotion,
                            "location": memory.location,
                            "current_strength": memory.current_strength
                        })
                    elif isinstance(memory, SemanticMemory):
                        metadata.update({
                            "fact_type": memory.fact_type,
                            "confidence": memory.confidence
                        })
                    
                    self.collection.add(
                        ids=[memory.id],
                        documents=[memory.text],
                        metadatas=[metadata]
                    )
                except Exception as e:
                    print(f"Warning: Failed to load memory into ChromaDB: {e}")
        
        print(f"Loaded {len(self.memories)} memories from {filepath}")
    
    def delete_memory(self, memory_id: str):
        """Delete a specific memory.
        
        Args:
            memory_id: ID of memory to delete
        """
        if memory_id in self.memories:
            del self.memories[memory_id]
        
        if self.chroma_available and self.collection:
            try:
                self.collection.delete(ids=[memory_id])
            except Exception as e:
                print(f"Warning: Failed to delete from ChromaDB: {e}")
    
    def get_memory_stats(self) -> dict:
        """Get statistics about stored memories.
        
        Returns:
            Dictionary with memory statistics
        """
        episodic_count = sum(1 for m in self.memories.values() if isinstance(m, EpisodicMemory))
        semantic_count = sum(1 for m in self.memories.values() if isinstance(m, SemanticMemory))
        
        return {
            "total_memories": len(self.memories),
            "episodic_memories": episodic_count,
            "semantic_memories": semantic_count,
            "chromadb_enabled": self.chroma_available
        }
