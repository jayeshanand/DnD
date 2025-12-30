"""Main game loop and engine."""

from datetime import datetime, timedelta
from .state import GameState, Player, Location, Quest, Inventory
from .response_schema import WorldEffect
from typing import List


class GameEngine:
    """Main game engine that orchestrates turns and state updates."""

    def __init__(self, game_state: GameState):
        self.state = game_state
        # Track NPC relationships (npc_id -> relationship_score)
        # -1.0 = hostile, 0.0 = neutral, 1.0 = trusted ally
        if not hasattr(self.state, 'npc_relationships'):
            self.state.npc_relationships = {}

    def advance_time(self, minutes: int = 5):
        """Advance game time by specified minutes."""
        current = datetime.fromisoformat(self.state.game_time)
        new_time = current + timedelta(minutes=minutes)
        self.state.game_time = new_time.isoformat()

    def apply_effects(self, effects: WorldEffect) -> List[str]:
        """
        Apply DM response effects to game state.
        
        Returns:
            List of log messages describing what changed.
        """
        log = []

        # Location change
        if effects.location and effects.location in self.state.locations:
            old_loc = self.state.locations[self.state.current_location_id].name
            self.state.current_location_id = effects.location
            new_loc = self.state.locations[effects.location].name
            log.append(f"📍 Moved: {old_loc} → {new_loc}")

        # Time advancement
        if effects.time_delta:
            self.advance_time(effects.time_delta)
            log.append(f"⏰ Time: +{effects.time_delta} minutes")

        # HP change
        if effects.hp_change:
            old_hp = self.state.player.hp
            self.state.player.hp = max(0, min(self.state.player.max_hp, 
                                              self.state.player.hp + effects.hp_change))
            change_symbol = "+" if effects.hp_change > 0 else ""
            log.append(f"❤️  HP: {old_hp} → {self.state.player.hp} ({change_symbol}{effects.hp_change})")

        # Gold change
        if effects.gold_change:
            old_gold = self.state.player.gold
            self.state.player.gold = max(0, self.state.player.gold + effects.gold_change)
            change_symbol = "+" if effects.gold_change > 0 else ""
            log.append(f"💰 Gold: {old_gold} → {self.state.player.gold} ({change_symbol}{effects.gold_change})")

        # New items
        for item_id in effects.new_items:
            self.state.player.inventory.add_item(item_id, 1)
            log.append(f"📦 Gained: {item_id}")

        # New quests
        for quest_id in effects.new_quests:
            # Create basic quest if not already defined
            if quest_id not in self.state.active_quests:
                new_quest = Quest(
                    id=quest_id,
                    title=quest_id.replace('_', ' ').title(),
                    description=f"New quest: {quest_id}",
                    giver_npc_id="unknown",
                    started_at=datetime.now().isoformat()
                )
                self.state.active_quests[quest_id] = new_quest
                log.append(f"📜 New Quest: {new_quest.title}")

        # Completed quests
        for quest_id in effects.completed_quests:
            if quest_id in self.state.active_quests:
                self.state.active_quests[quest_id].completed = True
                quest_title = self.state.active_quests[quest_id].title
                log.append(f"✅ Quest Complete: {quest_title}")
                
                # Award quest gold if any
                reward = self.state.active_quests[quest_id].reward_gold
                if reward > 0:
                    self.state.player.gold += reward
                    log.append(f"💰 Quest Reward: +{reward} gold")

        # NPC relationship changes
        for npc_id, delta in effects.npc_relationship_changes.items():
            if npc_id in self.state.npcs:
                old_val = self.state.npc_relationships.get(npc_id, 0.0)
                new_val = max(-1.0, min(1.0, old_val + delta))
                self.state.npc_relationships[npc_id] = new_val
                
                npc_name = self.state.npcs[npc_id].get('name', npc_id)
                change_symbol = "+" if delta > 0 else ""
                
                # Add relationship description
                if new_val >= 0.7:
                    status = "trusted ally"
                elif new_val >= 0.3:
                    status = "friendly"
                elif new_val >= -0.3:
                    status = "neutral"
                elif new_val >= -0.7:
                    status = "unfriendly"
                else:
                    status = "hostile"
                
                log.append(f"🤝 {npc_name}: {change_symbol}{delta:.1f} ({status})")

        return log

    def process_turn(self, player_action: str) -> str:
        """
        Process a single game turn.
        
        Returns: A brief log of what happened this turn.
        """
        self.state.turn += 1
        
        # Log the action
        self.state.world_events_log.append(f"Turn {self.state.turn}: Player action: {player_action}")
        
        # Advance time
        self.advance_time(5)
        
        return f"Turn {self.state.turn} processed."

    def get_current_location(self) -> Location:
        """Get the Location object for the player's current location."""
        return self.state.locations.get(self.state.current_location_id)

    def move_player(self, direction: str) -> bool:
        """
        Move player in a direction. Returns True if successful.
        """
        current_loc = self.get_current_location()
        if not current_loc or direction not in current_loc.exits:
            return False

        new_location_id = current_loc.exits[direction]
        self.state.current_location_id = new_location_id
        return True

    def add_quest(self, quest: Quest):
        """Add a quest to active quests."""
        self.state.active_quests[quest.id] = quest

    def complete_quest(self, quest_id: str) -> bool:
        """Mark a quest as completed."""
        if quest_id not in self.state.active_quests:
            return False
        self.state.active_quests[quest_id].completed = True
        return True

    def get_state_summary(self) -> str:
        """Get a human-readable summary of current game state."""
        location = self.get_current_location()
        loc_name = location.name if location else "Unknown"

        summary = f"""
=== GAME STATE ===
Turn: {self.state.turn}
Time: {self.state.game_time}
Player: {self.state.player.name} ({self.state.player.class_name})
HP: {self.state.player.hp}/{self.state.player.max_hp}
Gold: {self.state.player.gold}
Location: {loc_name}
Active Quests: {len(self.state.active_quests)}
"""
        return summary.strip()
