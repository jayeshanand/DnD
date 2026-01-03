"""Game state models for the D&D engine."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional
import json
import os

# Import memory system (Phase 4)
try:
    from memory.memory_store import MemoryStore
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    MemoryStore = None


@dataclass
class Location:
    """Represents a location in the game world."""
    id: str
    name: str
    description: str
    exits: Dict[str, str] = field(default_factory=dict)  # direction -> location_id
    npcs: List[str] = field(default_factory=list)  # NPC IDs present
    items: List[str] = field(default_factory=list)  # Item IDs present

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


@dataclass
class Quest:
    """Represents a quest."""
    id: str
    title: str
    description: str
    giver_npc_id: str
    objectives: List[str] = field(default_factory=list)
    completed: bool = False
    reward_gold: int = 0
    started_at: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


@dataclass
class Inventory:
    """Represents a player inventory."""
    items: Dict[str, int] = field(default_factory=dict)  # item_id -> quantity
    max_weight: int = 100
    current_weight: int = 0

    def add_item(self, item_id: str, quantity: int = 1):
        if item_id not in self.items:
            self.items[item_id] = 0
        self.items[item_id] += quantity

    def remove_item(self, item_id: str, quantity: int = 1) -> bool:
        if item_id not in self.items or self.items[item_id] < quantity:
            return False
        self.items[item_id] -= quantity
        if self.items[item_id] == 0:
            del self.items[item_id]
        return True

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


@dataclass
class Player:
    """Represents the player character."""
    name: str
    class_name: str
    level: int = 1
    hp: int = 20
    max_hp: int = 20
    experience: int = 0
    gold: int = 50
    inventory: Inventory = field(default_factory=Inventory)

    def to_dict(self):
        data = asdict(self)
        data['inventory'] = self.inventory.to_dict()
        return data

    @classmethod
    def from_dict(cls, data):
        inv_data = data.pop('inventory', {})
        player = cls(**data)
        player.inventory = Inventory.from_dict(inv_data)
        return player


@dataclass
class ConversationTurn:
    """Represents a single conversation turn."""
    turn_number: int
    player_action: str
    narration: str
    npc_speeches: List[dict]  # [{"npc_id": "...", "text": "...", "emotion": "..."}]
    effects_summary: List[str]  # Brief summary of state changes
    timestamp: str  # ISO format

    def to_dict(self):
        return {
            'turn_number': self.turn_number,
            'player_action': self.player_action,
            'narration': self.narration,
            'npc_speeches': self.npc_speeches,
            'effects_summary': self.effects_summary,
            'timestamp': self.timestamp
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


@dataclass
class GameState:
    """Core game state containing all world and player data."""
    player: Player
    current_location_id: str
    game_time: str  # ISO format datetime
    turn: int = 0
    locations: Dict[str, Location] = field(default_factory=dict)
    active_quests: Dict[str, Quest] = field(default_factory=dict)
    npcs: Dict[str, dict] = field(default_factory=dict)  # NPC data
    world_events_log: List[str] = field(default_factory=list)  # Recent events
    conversation_history: List[dict] = field(default_factory=list)  # Full conversation turns
    last_narration: str = ""
    npc_relationships: Dict[str, float] = field(default_factory=dict)  # npc_id -> relationship (-1.0 to 1.0)
    memory_store: Optional[MemoryStore] = None  # Phase 4: Long-term memory system
    
    def __post_init__(self):
        """Initialize memory store if not provided."""
        if MEMORY_AVAILABLE and self.memory_store is None:
            self.memory_store = MemoryStore()

    def save_to_file(self, filepath: str):
        """Save game state to JSON file."""
        data = {
            'player': self.player.to_dict(),
            'current_location_id': self.current_location_id,
            'game_time': self.game_time,
            'turn': self.turn,
            'locations': {k: v.to_dict() for k, v in self.locations.items()},
            'active_quests': {k: v.to_dict() for k, v in self.active_quests.items()},
            'npcs': self.npcs,
            'world_events_log': self.world_events_log,
            'conversation_history': self.conversation_history,
            'last_narration': self.last_narration,
            'npc_relationships': self.npc_relationships,
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Save memories separately (Phase 4)
        if MEMORY_AVAILABLE and self.memory_store:
            memory_path = filepath.replace('.json', '_memories.json')
            self.memory_store.save_to_json(memory_path)

    @classmethod
    def load_from_file(cls, filepath: str):
        """Load game state from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        player = Player.from_dict(data['player'])
        locations = {k: Location.from_dict(v) for k, v in data['locations'].items()}
        active_quests = {k: Quest.from_dict(v) for k, v in data['active_quests'].items()}

        state = cls(
            player=player,
            current_location_id=data['current_location_id'],
            game_time=data['game_time'],
            turn=data['turn'],
            locations=locations,
            active_quests=active_quests,
            npcs=data['npcs'],
            world_events_log=data['world_events_log'],
            conversation_history=data.get('conversation_history', []),
            last_narration=data['last_narration'],
            npc_relationships=data.get('npc_relationships', {}),
        )
        
        # Load memories separately (Phase 4)
        if MEMORY_AVAILABLE and state.memory_store:
            memory_path = filepath.replace('.json', '_memories.json')
            if os.path.exists(memory_path):
                state.memory_store.load_from_json(memory_path)
        
        return state

    def to_dict(self):
        """Convert entire state to dictionary."""
        return {
            'player': self.player.to_dict(),
            'current_location_id': self.current_location_id,
            'game_time': self.game_time,
            'turn': self.turn,
            'locations': {k: v.to_dict() for k, v in self.locations.items()},
            'active_quests': {k: v.to_dict() for k, v in self.active_quests.items()},
            'npcs': self.npcs,
            'world_events_log': self.world_events_log,
            'conversation_history': self.conversation_history,
            'last_narration': self.last_narration,
            'npc_relationships': self.npc_relationships,
        }
