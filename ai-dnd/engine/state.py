"""Game state models for the D&D engine."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional
import json


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
    last_narration: str = ""
    npc_relationships: Dict[str, float] = field(default_factory=dict)  # npc_id -> relationship (-1.0 to 1.0)

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
            'last_narration': self.last_narration,
            'npc_relationships': self.npc_relationships,
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str):
        """Load game state from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        player = Player.from_dict(data['player'])
        locations = {k: Location.from_dict(v) for k, v in data['locations'].items()}
        active_quests = {k: Quest.from_dict(v) for k, v in data['active_quests'].items()}

        return cls(
            player=player,
            current_location_id=data['current_location_id'],
            game_time=data['game_time'],
            turn=data['turn'],
            locations=locations,
            active_quests=active_quests,
            npcs=data['npcs'],
            world_events_log=data['world_events_log'],
            last_narration=data['last_narration'],
            npc_relationships=data.get('npc_relationships', {}),
        )

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
            'last_narration': self.last_narration,
            'npc_relationships': self.npc_relationships,
        }
