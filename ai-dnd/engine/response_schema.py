"""Schema definitions for structured DM responses."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class NPCResponse:
    """Represents a single NPC's speech or reaction."""
    npc_id: str
    text: str
    emotion: str = "neutral"  # joy, fear, anger, sadness, surprise, neutral, etc.


@dataclass
class WorldEffect:
    """Effects that change game state."""
    location: Optional[str] = None              # Move player to this location_id
    time_delta: int = 5                         # Minutes that passed (can be negative for time magic)
    hp_change: int = 0                          # HP gained (+) or lost (-)
    gold_change: int = 0                        # Gold gained (+) or lost (-)
    new_items: List[str] = field(default_factory=list)      # Item IDs to add to inventory
    new_quests: List[str] = field(default_factory=list)     # Quest IDs to start
    completed_quests: List[str] = field(default_factory=list)  # Quest IDs to complete
    npc_relationship_changes: Dict[str, float] = field(default_factory=dict)  # npc_id -> delta (-1.0 to 1.0)


@dataclass
class DMResponse:
    """Complete structured response from the DM."""
    narration: str                                      # Main narrative text
    npc_speeches: List[NPCResponse] = field(default_factory=list)  # NPC dialogues
    effects: WorldEffect = field(default_factory=WorldEffect)      # State changes
    suggested_options: List[str] = field(default_factory=list)     # Suggested player actions
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())  # When generated

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'narration': self.narration,
            'npc_speeches': [
                {'npc_id': npc.npc_id, 'text': npc.text, 'emotion': npc.emotion}
                for npc in self.npc_speeches
            ],
            'effects': {
                'location': self.effects.location,
                'time_delta': self.effects.time_delta,
                'hp_change': self.effects.hp_change,
                'gold_change': self.effects.gold_change,
                'new_items': self.effects.new_items,
                'new_quests': self.effects.new_quests,
                'completed_quests': self.effects.completed_quests,
                'npc_relationship_changes': self.effects.npc_relationship_changes,
            },
            'suggested_options': self.suggested_options,
            'timestamp': self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'DMResponse':
        """Create DMResponse from dictionary."""
        npc_speeches = [
            NPCResponse(**npc) for npc in data.get('npc_speeches', [])
        ]
        effects_data = data.get('effects', {})
        effects = WorldEffect(
            location=effects_data.get('location'),
            time_delta=effects_data.get('time_delta', 5),
            hp_change=effects_data.get('hp_change', 0),
            gold_change=effects_data.get('gold_change', 0),
            new_items=effects_data.get('new_items', []),
            new_quests=effects_data.get('new_quests', []),
            completed_quests=effects_data.get('completed_quests', []),
            npc_relationship_changes=effects_data.get('npc_relationship_changes', {}),
        )
        return cls(
            narration=data.get('narration', ''),
            npc_speeches=npc_speeches,
            effects=effects,
            suggested_options=data.get('suggested_options', []),
            timestamp=data.get('timestamp', datetime.now().isoformat()),
        )
