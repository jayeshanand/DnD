"""Memory data structures for the AI D&D engine.

This module defines different types of memories that NPCs can have:
- EpisodicMemory: Specific events with emotion and decay
- SemanticMemory: General facts that persist indefinitely
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional
from uuid import uuid4


@dataclass
class Memory:
    """Base memory class for all memory types."""
    
    id: str
    memory_type: Literal["episodic", "semantic"]
    text: str  # Human-readable description of the memory
    npc_id: str  # Which NPC has this memory ("all" for shared memories)
    created_at: datetime
    embedding: Optional[list[float]] = None  # Vector embedding for similarity search
    
    def to_dict(self) -> dict:
        """Convert memory to dictionary for serialization."""
        return {
            "id": self.id,
            "memory_type": self.memory_type,
            "text": self.text,
            "npc_id": self.npc_id,
            "created_at": self.created_at.isoformat(),
            "embedding": self.embedding
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create memory from dictionary."""
        # This will be overridden by subclasses
        raise NotImplementedError("Use EpisodicMemory or SemanticMemory from_dict")


@dataclass
class EpisodicMemory(Memory):
    """Event-based memory that decays over time.
    
    Represents specific experiences that happened at a particular time
    and place, with emotional context. These memories fade over time
    based on their importance and decay rate.
    
    Examples:
    - "The player saved me from bandits in the forest"
    - "I witnessed the player stealing from the merchant"
    - "The player helped me solve the rats problem in my tavern"
    """
    
    importance: float = 0.5  # 0.0-1.0, how significant is this memory
    emotion: Literal["gratitude", "fear", "anger", "joy", "neutral", "sadness"] = "neutral"
    location: str = ""  # Where this event occurred
    participants: list[str] = field(default_factory=list)  # Who was involved
    decay_rate: float = 0.1  # How fast it fades (0.0 = never, 1.0 = very fast)
    current_strength: float = 1.0  # Current memory strength (1.0 = fresh, 0.0 = forgotten)
    
    def __post_init__(self):
        """Ensure memory type is set correctly."""
        self.memory_type = "episodic"
    
    def calculate_strength(self, current_time: datetime) -> float:
        """Calculate current memory strength based on time elapsed and decay.
        
        Args:
            current_time: Current game time
            
        Returns:
            Float between 0.0 and 1.0 representing memory strength
        """
        time_delta = (current_time - self.created_at).total_seconds() / 3600  # Hours
        
        # High importance memories decay slower
        effective_decay = self.decay_rate * (1.0 - self.importance * 0.5)
        
        # Exponential decay: strength = initial * e^(-decay * time)
        import math
        strength = math.exp(-effective_decay * time_delta / 100)  # /100 to make decay reasonable
        
        return max(0.0, min(1.0, strength))
    
    def update_strength(self, current_time: datetime):
        """Update the current_strength field based on time elapsed."""
        self.current_strength = self.calculate_strength(current_time)
    
    def to_dict(self) -> dict:
        """Convert episodic memory to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            "importance": self.importance,
            "emotion": self.emotion,
            "location": self.location,
            "participants": self.participants,
            "decay_rate": self.decay_rate,
            "current_strength": self.current_strength
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: dict) -> "EpisodicMemory":
        """Create episodic memory from dictionary."""
        created_at = datetime.fromisoformat(data["created_at"]) if isinstance(data["created_at"], str) else data["created_at"]
        
        return cls(
            id=data["id"],
            memory_type="episodic",
            text=data["text"],
            npc_id=data["npc_id"],
            created_at=created_at,
            embedding=data.get("embedding"),
            importance=data.get("importance", 0.5),
            emotion=data.get("emotion", "neutral"),
            location=data.get("location", ""),
            participants=data.get("participants", []),
            decay_rate=data.get("decay_rate", 0.1),
            current_strength=data.get("current_strength", 1.0)
        )


@dataclass
class SemanticMemory(Memory):
    """Fact-based memory that doesn't decay.
    
    Represents general knowledge and facts that persist indefinitely.
    These are not tied to specific events but represent learned truths.
    
    Examples:
    - "The player is a member of the King's Guard"
    - "The player is known as a thief in the market district"
    - "The player owes Aldric a debt"
    """
    
    fact_type: Literal["profession", "relationship", "reputation", "quest_status", "general"] = "general"
    subject: str = ""  # Who/what this fact is about
    confidence: float = 1.0  # 0.0-1.0, how certain is this fact
    source: str = ""  # Where this knowledge came from
    
    def __post_init__(self):
        """Ensure memory type is set correctly."""
        self.memory_type = "semantic"
    
    def to_dict(self) -> dict:
        """Convert semantic memory to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            "fact_type": self.fact_type,
            "subject": self.subject,
            "confidence": self.confidence,
            "source": self.source
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: dict) -> "SemanticMemory":
        """Create semantic memory from dictionary."""
        created_at = datetime.fromisoformat(data["created_at"]) if isinstance(data["created_at"], str) else data["created_at"]
        
        return cls(
            id=data["id"],
            memory_type="semantic",
            text=data["text"],
            npc_id=data["npc_id"],
            created_at=created_at,
            embedding=data.get("embedding"),
            fact_type=data.get("fact_type", "general"),
            subject=data.get("subject", ""),
            confidence=data.get("confidence", 1.0),
            source=data.get("source", "")
        )


def create_memory_id() -> str:
    """Generate a unique memory ID."""
    return f"mem_{uuid4().hex[:8]}"
