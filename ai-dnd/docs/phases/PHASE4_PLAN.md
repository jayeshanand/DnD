# Phase 4: Memory System Implementation Plan

## Goal
Implement episodic and semantic memory system using vector database so NPCs remember past interactions and experiences, creating more immersive and continuous gameplay.

## Problem Phase 4 Solves
**Currently**: 
- NPCs only remember recent conversation history (last 5 turns from Phase 3)
- No long-term memory of significant events
- Past actions beyond recent turns are forgotten
- No way to reference historical interactions

**After Phase 4**:
- NPCs remember important past events long-term
- Semantic memories (facts) persist indefinitely
- Episodic memories (experiences) have importance scores and decay
- Memory retrieval based on context relevance
- Richer dialogue that references past experiences

## Architecture Overview

### Memory Types

#### 1. Episodic Memories
**What**: Specific events/experiences tied to time and emotion
**Examples**:
- "The player saved me from bandits in the forest three days ago"
- "I witnessed the player stealing from the merchant"
- "The player helped me solve the rats problem in my tavern"

**Properties**:
- `timestamp`: When it happened
- `importance`: 0.0-1.0 (how significant)
- `emotion`: gratitude, fear, anger, joy, neutral
- `location`: Where it happened
- `participants`: Who was involved
- `decay_rate`: How fast it fades (0.0 = never, 1.0 = fast)

#### 2. Semantic Memories
**What**: General facts and knowledge (no decay)
**Examples**:
- "The player is a member of the King's Guard"
- "The player is known as a thief in the market district"
- "The player has a debt to Aldric"

**Properties**:
- `fact_type`: profession, relationship, reputation, quest_status
- `subject`: Who/what the fact is about
- `confidence`: 0.0-1.0 (how certain)
- `source`: Where this knowledge came from

### Technology Stack

**Vector Database**: ChromaDB
- Lightweight, embeddable, no separate server needed
- Good for small-to-medium datasets
- Easy Python integration

**Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- Fast inference, ~384 dimensions
- Good semantic understanding
- Works well with ChromaDB

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                    Game Loop                            │
│  Player Action → Memory Creation → State Update         │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│                 MemoryStore                             │
│  - add_memory(memory)                                   │
│  - retrieve_memories(query, filter, n)                  │
│  - decay_memories(time_elapsed)                         │
│  - get_npc_memories(npc_id)                            │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│              ChromaDB Collection                        │
│  - Vector embeddings of memory text                     │
│  - Metadata filtering (npc_id, type, importance)        │
│  - Semantic similarity search                           │
└─────────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│               LLM Prompt Builder                        │
│  Context includes:                                       │
│  - Current game state                                    │
│  - Recent conversation (Phase 3)                         │
│  - Relevant memories (Phase 4) ← NEW                    │
└─────────────────────────────────────────────────────────┘
```

## Implementation Steps

### Step 1: Create Memory Data Classes
**File**: `memory/types.py` (new)

```python
from dataclasses import dataclass
from typing import Literal, Optional
from datetime import datetime

@dataclass
class Memory:
    """Base memory class"""
    id: str  # Unique identifier
    memory_type: Literal["episodic", "semantic"]
    text: str  # Human-readable description
    npc_id: str  # Which NPC has this memory
    created_at: datetime
    embedding: Optional[list[float]] = None  # Vector embedding

@dataclass
class EpisodicMemory(Memory):
    """Event-based memory with decay"""
    importance: float  # 0.0-1.0
    emotion: Literal["gratitude", "fear", "anger", "joy", "neutral"]
    location: str
    participants: list[str]
    decay_rate: float = 0.1
    
    def get_current_strength(self, current_time: datetime) -> float:
        """Calculate current memory strength based on decay"""
        # Implementation in memory_store.py

@dataclass
class SemanticMemory(Memory):
    """Fact-based memory (no decay)"""
    fact_type: Literal["profession", "relationship", "reputation", "quest_status"]
    subject: str
    confidence: float  # 0.0-1.0
    source: str  # Where this fact came from
```

### Step 2: Build MemoryStore Class
**File**: `memory/memory_store.py` (new)

**Key Methods**:
1. `__init__(db_path, embedding_model)` - Initialize ChromaDB
2. `add_memory(memory)` - Store a memory with embedding
3. `retrieve_memories(query, npc_id, n=5)` - Get most relevant memories
4. `retrieve_by_importance(npc_id, min_importance=0.5, n=10)` - Get important memories
5. `decay_memories(time_elapsed)` - Update episodic memory strength
6. `delete_weak_memories(threshold=0.1)` - Prune decayed memories
7. `get_all_npc_memories(npc_id)` - Get all memories for an NPC
8. `save_to_json()` / `load_from_json()` - Persistence

**ChromaDB Setup**:
```python
import chromadb
from chromadb.utils import embedding_functions

# Use sentence-transformers for embeddings
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

client = chromadb.PersistentClient(path="./data/memory_db")
collection = client.get_or_create_collection(
    name="game_memories",
    embedding_function=sentence_transformer_ef
)
```

### Step 3: Integrate with GameState
**File**: `engine/state.py` (update)

Add:
```python
from memory.memory_store import MemoryStore

@dataclass
class GameState:
    # ... existing fields ...
    memory_store: Optional[MemoryStore] = None  # NEW
    
    def __post_init__(self):
        if self.memory_store is None:
            self.memory_store = MemoryStore()
```

### Step 4: Create Memories from Game Events
**File**: `engine/game_loop.py` (update)

Add memory creation after processing effects:
```python
def process_turn(state, player_input):
    # ... existing logic ...
    
    # Extract memories from response
    create_memories_from_response(state, parsed_response)
    
    # Decay memories based on time passed
    if state.turn_count % 10 == 0:  # Every 10 turns
        state.memory_store.decay_memories(time_elapsed=state.time)

def create_memories_from_response(state, response):
    """Extract and store memories from LLM response"""
    # Check for significant events in effects
    if response.effects.quest_completed:
        # Create high-importance episodic memory
        memory = EpisodicMemory(
            id=f"mem_{state.turn_count}_{uuid4()}",
            memory_type="episodic",
            text=f"Player completed quest: {quest_name}",
            npc_id="all",  # All NPCs can know this
            created_at=datetime.now(),
            importance=0.9,
            emotion="joy",
            location=state.location,
            participants=["player", ...],
        )
        state.memory_store.add_memory(memory)
    
    # Check for relationship changes
    for npc_id, change in response.effects.npc_relationship_changes.items():
        if abs(change) > 0.3:  # Significant change
            emotion = "gratitude" if change > 0 else "anger"
            memory = EpisodicMemory(...)
            state.memory_store.add_memory(memory)
```

### Step 5: Enhance Prompts with Memories
**File**: `llm/prompts.py` (update)

```python
def build_npc_context(state, npc_ids):
    context = []
    for npc_id in npc_ids:
        npc = state.get_npc(npc_id)
        
        # Get relevant memories for this NPC
        recent_action = state.conversation_history[-1].player_action if state.conversation_history else ""
        memories = state.memory_store.retrieve_memories(
            query=recent_action,
            npc_id=npc_id,
            n=5
        )
        
        if memories:
            memory_text = "\n".join([
                f"  - [{m.memory_type}] {m.text} (importance: {m.importance if hasattr(m, 'importance') else 'N/A'})"
                for m in memories
            ])
            context.append(f"**{npc.name}'s Relevant Memories**:\n{memory_text}")
    
    return "\n\n".join(context)
```

### Step 6: Add Memory Management Commands
**File**: `ui/cli.py` (update)

Add new commands:
- `/memories` - Show player's memories
- `/npc-memories <npc_name>` - Show NPC's memories about player
- `/forget <memory_id>` - Delete a specific memory (for testing)

### Step 7: Testing
**File**: `tests/test_phase4.py` (new)

Test scenarios:
1. Memory creation and storage
2. Memory retrieval by relevance
3. Memory decay over time
4. Semantic vs episodic memory behavior
5. Integration with game loop
6. Save/load with memories
7. Multi-NPC memory scenarios

## Data Structure Examples

### Example 1: Quest Completion Memory
```json
{
  "id": "mem_042_abc123",
  "memory_type": "episodic",
  "text": "The adventurer helped me clear the rats from my tavern cellar. I was worried they'd ruin my reputation.",
  "npc_id": "npc_mira",
  "created_at": "2026-01-03T14:30:00",
  "importance": 0.8,
  "emotion": "gratitude",
  "location": "tavern",
  "participants": ["player", "npc_mira"],
  "decay_rate": 0.05
}
```

### Example 2: Reputation Semantic Memory
```json
{
  "id": "mem_sem_001",
  "memory_type": "semantic",
  "text": "This person is known as a thief in the market district",
  "npc_id": "npc_aldric",
  "created_at": "2026-01-03T12:00:00",
  "fact_type": "reputation",
  "subject": "player",
  "confidence": 0.9,
  "source": "witnessed_theft"
}
```

## Memory Creation Rules

### High Importance (0.7-1.0)
- Quest completion
- Major relationship changes (±0.5 or more)
- Combat victories/defeats
- Major story revelations
- Player saves/betrays NPC

### Medium Importance (0.4-0.6)
- Gift giving/trading
- Helping with minor tasks
- Learning new information
- Moderate relationship changes (±0.2 to ±0.4)

### Low Importance (0.1-0.3)
- Casual conversations
- Small transactions
- Minor interactions
- Background observations

### Semantic Memory Triggers
- Player joins faction → fact_type="relationship"
- Player gets title/profession → fact_type="profession"
- Reputation spreads → fact_type="reputation"
- Quest milestones → fact_type="quest_status"

## Performance Considerations

1. **Memory Limits**: Cap episodic memories per NPC at ~100, prune weak ones
2. **Retrieval Speed**: Limit to top 5-10 memories per query
3. **Embedding Caching**: Cache embeddings in ChromaDB, don't recalculate
4. **Decay Frequency**: Run decay every 10 turns, not every turn
5. **DB Size**: Use persistent ChromaDB, expect ~50MB for typical game

## Expected Behavior After Phase 4

### Scenario 1: Return to NPC After Long Absence
```
Turn 5: Player helps Mira with rats (memory created, importance=0.8)
Turns 6-50: Player does other things
Turn 51: Player returns to tavern

Expected: Mira says "Good to see you again! Thanks for dealing with those rats last week. Drinks are on me."
Memory retrieved because "tavern" + "Mira" triggers similarity search
```

### Scenario 2: Reputation Spread
```
Turn 10: Player steals from merchant (witnessed by Aldric)
  → Semantic memory created for Aldric: "Player is a thief"
Turn 15: Player meets Captain Varen (guard)
  → Semantic memories about player retrieved
  → Varen is suspicious because of reputation

Expected: "I've heard rumors about you from the merchant quarter..."
```

### Scenario 3: Memory Decay
```
Turn 0: Minor conversation with NPC (importance=0.2, decay_rate=0.2)
Turn 50: Memory strength = 0.2 - (0.2 * 5 decay cycles) = weak
Turn 100: Memory auto-pruned (strength < 0.1)

Expected: Low-importance memories fade over time, keeping DB clean
```

## Exit Criteria (Definition of Done)

✅ Phase 4 is complete when:
1. MemoryStore class implemented with ChromaDB integration
2. Memory types (episodic, semantic) defined and working
3. Memories created automatically from game events
4. Memory retrieval integrated into LLM prompts
5. Memory decay system functioning
6. Memories persist across save/load
7. CLI commands for viewing memories work
8. Test suite passes (test_phase4.py)
9. NPCs reference past events in dialogue
10. Documentation complete (PHASE4_COMPLETE.md)

## Files to Create/Modify

### New Files
- `memory/types.py` - Memory dataclasses
- `memory/memory_store.py` - MemoryStore class with ChromaDB
- `tests/test_phase4.py` - Test suite
- `docs/phases/PHASE4_COMPLETE.md` - Completion documentation

### Modified Files
- `requirements.txt` - Add chromadb, sentence-transformers
- `memory/__init__.py` - Export memory classes
- `engine/state.py` - Add memory_store field
- `engine/game_loop.py` - Create memories from events
- `llm/prompts.py` - Include memories in context
- `ui/cli.py` - Add memory viewing commands
- `docs/phases/ROADMAP.md` - Update Phase 4 status

## Estimated Time
**5-6 hours** of focused development

## Dependencies
- Phase 3 (NPC personalities & conversation history) ✅ Complete
- Python 3.8+
- ChromaDB library
- sentence-transformers library

## Next Phase
After Phase 4 → **Phase 5**: True Multi-Agent NPCs (each NPC as independent agent)

---

**Status**: 🚧 In Development (Phase 4)
**Last Updated**: January 3, 2026
