"""Main game loop and engine."""

from datetime import datetime, timedelta
from .state import GameState, Player, Location, Quest, Inventory
from .response_schema import WorldEffect
from typing import List

# Import memory system (Phase 4)
try:
    from memory.types import EpisodicMemory, SemanticMemory, create_memory_id
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False


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

    def apply_effects(self, effects: WorldEffect, player_action: str = "", narration: str = "", npc_speeches: List[dict] = None) -> List[str]:
        """
        Apply DM response effects to game state.
        
        Args:
            effects: WorldEffect object with state changes
            player_action: What the player did this turn
            narration: DM's narration for this turn
            npc_speeches: List of NPC speeches this turn
        
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
                
                # Update NPC's last_interaction_turn
                if 'last_interaction_turn' in self.state.npcs[npc_id]:
                    self.state.npcs[npc_id]['last_interaction_turn'] = self.state.turn

        # Record conversation turn in history
        if player_action and narration:
            from datetime import datetime
            conversation_turn = {
                'turn_number': self.state.turn,
                'player_action': player_action,
                'narration': narration,
                'npc_speeches': npc_speeches or [],
                'effects_summary': log.copy(),
                'timestamp': datetime.now().isoformat()
            }
            self.state.conversation_history.append(conversation_turn)
            
            # Keep only last 10 turns to avoid context overflow
            if len(self.state.conversation_history) > 10:
                self.state.conversation_history = self.state.conversation_history[-10:]
        
        # Create memories from significant events (Phase 4)
        if MEMORY_AVAILABLE and self.state.memory_store:
            self.create_memories_from_events(effects, player_action, narration, npc_speeches or [])

        return log
    
    def create_memories_from_events(self, effects: WorldEffect, player_action: str, 
                                     narration: str, npc_speeches: List[dict]):
        """Create memories for NPCs based on significant events (Phase 4).
        
        Args:
            effects: The effects that were applied this turn
            player_action: What the player did
            narration: DM's narration
            npc_speeches: List of NPC speeches
        """
        if not MEMORY_AVAILABLE or not self.state.memory_store:
            return
        
        current_location = self.state.locations.get(self.state.current_location_id)
        if not current_location:
            return
        
        npcs_present = current_location.npcs
        current_time = datetime.fromisoformat(self.state.game_time)
        
        # 1. Quest completion memories (high importance)
        for quest_id in effects.completed_quests:
            if quest_id in self.state.active_quests:
                quest = self.state.active_quests[quest_id]
                quest_giver = quest.giver_npc_id
                
                # Create memory for quest giver
                if quest_giver in self.state.npcs:
                    memory = EpisodicMemory(
                        id=create_memory_id(),
                        memory_type="episodic",
                        text=f"The player completed my quest: {quest.title}. {quest.description}",
                        npc_id=quest_giver,
                        created_at=current_time,
                        importance=0.9,
                        emotion="joy",
                        location=self.state.current_location_id,
                        participants=["player", quest_giver],
                        decay_rate=0.05  # Very slow decay
                    )
                    self.state.memory_store.add_memory(memory)
                
                # All NPCs present learn about it (lower importance)
                for npc_id in npcs_present:
                    if npc_id != quest_giver and npc_id in self.state.npcs:
                        memory = SemanticMemory(
                            id=create_memory_id(),
                            memory_type="semantic",
                            text=f"The player completed a quest for {self.state.npcs[quest_giver].get('name', quest_giver)}",
                            npc_id=npc_id,
                            created_at=current_time,
                            fact_type="quest_status",
                            subject="player",
                            confidence=0.9,
                            source="witnessed"
                        )
                        self.state.memory_store.add_memory(memory)
        
        # 2. Significant relationship changes (medium-high importance)
        for npc_id, delta in effects.npc_relationship_changes.items():
            if abs(delta) >= 0.2 and npc_id in self.state.npcs:  # Significant change
                # Determine emotion based on change
                if delta > 0:
                    emotion = "gratitude" if delta > 0.3 else "joy"
                    emotion_text = "helpful to me"
                else:
                    emotion = "anger" if delta < -0.3 else "neutral"
                    emotion_text = "upset me" if delta < -0.3 else "disappointed me"
                
                importance = min(0.9, abs(delta) * 2)  # Scale importance by relationship change
                
                memory = EpisodicMemory(
                    id=create_memory_id(),
                    memory_type="episodic",
                    text=f"The player {emotion_text}. {player_action}",
                    npc_id=npc_id,
                    created_at=current_time,
                    importance=importance,
                    emotion=emotion,
                    location=self.state.current_location_id,
                    participants=["player", npc_id],
                    decay_rate=0.1
                )
                self.state.memory_store.add_memory(memory)
        
        # 3. Commerce transactions (medium importance)
        if effects.gold_change < 0:  # Player spent money
            amount = abs(effects.gold_change)
            if amount >= 10:  # Significant purchase
                for npc_id in npcs_present:
                    if npc_id in self.state.npcs:
                        npc = self.state.npcs[npc_id]
                        if npc.get('role') in ['merchant', 'bartender', 'shopkeeper']:
                            items_str = ", ".join(effects.new_items) if effects.new_items else "services"
                            memory = EpisodicMemory(
                                id=create_memory_id(),
                                memory_type="episodic",
                                text=f"The player bought {items_str} from me for {amount} gold",
                                npc_id=npc_id,
                                created_at=current_time,
                                importance=min(0.7, amount / 50),  # Scale by amount
                                emotion="neutral",
                                location=self.state.current_location_id,
                                participants=["player", npc_id],
                                decay_rate=0.15  # Moderate decay
                            )
                            self.state.memory_store.add_memory(memory)
        
        # 4. Combat or HP changes (high importance)
        if effects.hp_change < -5:  # Significant damage
            for npc_id in npcs_present:
                if npc_id in self.state.npcs:
                    memory = EpisodicMemory(
                        id=create_memory_id(),
                        memory_type="episodic",
                        text=f"I witnessed the player take {abs(effects.hp_change)} damage. {narration[:100]}",
                        npc_id=npc_id,
                        created_at=current_time,
                        importance=min(0.8, abs(effects.hp_change) / 20),
                        emotion="fear",
                        location=self.state.current_location_id,
                        participants=["player"] + list(npcs_present),
                        decay_rate=0.1
                    )
                    self.state.memory_store.add_memory(memory)
        
        # 5. Significant conversation interactions (low-medium importance)
        # Create memories for NPCs who spoke this turn
        for speech in npc_speeches:
            npc_id = speech.get('npc_id')
            if npc_id and npc_id in self.state.npcs:
                speech_text = speech.get('text', '')
                
                # Only create memory if it's a substantial interaction
                if len(speech_text) > 30:
                    memory = EpisodicMemory(
                        id=create_memory_id(),
                        memory_type="episodic",
                        text=f"I talked with the player. They said: '{player_action[:50]}'. I responded about: {speech_text[:50]}",
                        npc_id=npc_id,
                        created_at=current_time,
                        importance=0.3,
                        emotion=speech.get('emotion', 'neutral'),
                        location=self.state.current_location_id,
                        participants=["player", npc_id],
                        decay_rate=0.2  # Faster decay for casual conversations
                    )
                    self.state.memory_store.add_memory(memory)
        
        # 6. Run memory decay every 10 turns
        if self.state.turn % 10 == 0:
            self.state.memory_store.decay_memories(current_time)
            # Prune very weak memories
            if self.state.turn % 50 == 0:
                self.state.memory_store.prune_weak_memories(threshold=0.1)

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
