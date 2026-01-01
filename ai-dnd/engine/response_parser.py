"""Parser and validator for structured DM responses."""

import json
import re
from typing import Optional
from datetime import datetime

from engine.state import GameState
from engine.response_schema import DMResponse, NPCResponse, WorldEffect


class ResponseParser:
    """Parser for extracting and validating DMResponse from LLM output."""

    @staticmethod
    def extract_json(text: str) -> Optional[str]:
        """
        Extract JSON from LLM response text.
        
        Handles cases where LLM adds extra text before/after JSON.
        """
        # Try to find JSON block with curly braces
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return match.group(0)
        
        # If no match, return text as-is and let JSON parser try
        return text.strip()

    @staticmethod
    def parse_response(text: str) -> Optional[DMResponse]:
        """
        Parse LLM text into DMResponse object.
        
        Returns None if parsing fails.
        """
        try:
            # Extract JSON
            json_str = ResponseParser.extract_json(text)
            if not json_str:
                return None
            
            # Parse JSON
            data = json.loads(json_str)
            
            # Convert to DMResponse
            return DMResponse.from_dict(data)
            
        except json.JSONDecodeError as e:
            print(f"[JSON Parse Error: {e}]")
            return None
        except Exception as e:
            print(f"[Response Parse Error: {e}]")
            return None

    @staticmethod
    def create_fallback_response(player_action: str) -> DMResponse:
        """
        Create a fallback response when parsing fails.
        """
        return DMResponse(
            narration=f"You attempt to {player_action}. The world shimmers mysteriously as reality adjusts.",
            npc_speeches=[],
            effects=WorldEffect(time_delta=5),
            suggested_options=["Try something else", "Look around", "Wait and see"],
            timestamp=datetime.now().isoformat()
        )


class ResponseValidator:
    """Validator for ensuring DMResponse is consistent with game state."""

    @staticmethod
    def _find_location_id(candidate: Optional[str], game_state: GameState) -> Optional[str]:
        """Resolve a location id from either an id or a location name (case-insensitive)."""
        def _slug(s: str) -> str:
            return re.sub(r"[^a-z0-9_]+", "_", s.strip().lower()).strip("_")

        if not candidate:
            return None
        if candidate in game_state.locations:
            return candidate

        normalized = candidate.strip().lower()
        slug_candidate = _slug(candidate)
        for loc_id, loc in game_state.locations.items():
            if loc.name.strip().lower() == normalized:
                return loc_id
            if _slug(loc.name) == slug_candidate:
                return loc_id
            if _slug(loc_id) == slug_candidate:
                return loc_id
        return None

    @staticmethod
    def _find_npc_id(candidate: Optional[str], game_state: GameState) -> Optional[str]:
        """Resolve an NPC id from either an id or an NPC name (case-insensitive)."""
        def _slug(s: str) -> str:
            return re.sub(r"[^a-z0-9_]+", "_", s.strip().lower()).strip("_")

        if not candidate:
            return None
        if candidate in game_state.npcs:
            return candidate

        normalized = candidate.strip().lower()
        slug_candidate = _slug(candidate)
        for npc_id, npc in game_state.npcs.items():
            npc_name = str(npc.get("name", "")).strip().lower()
            if npc_name == normalized:
                return npc_id
            if _slug(npc_name) == slug_candidate:
                return npc_id
            if _slug(npc_id) == slug_candidate:
                return npc_id
        return None

    @staticmethod
    def validate_dm_response(response: DMResponse, game_state: GameState) -> tuple[bool, list[str]]:
        """
        Validate DMResponse against game state.
        
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []
        
        # Validate location
        if response.effects.location:
            resolved_location = ResponseValidator._find_location_id(response.effects.location, game_state)
            if not resolved_location:
                issues.append(f"Invalid location: {response.effects.location}")
            else:
                response.effects.location = resolved_location
        
        # Validate NPCs
        for npc_speech in response.npc_speeches:
            resolved_npc = ResponseValidator._find_npc_id(npc_speech.npc_id, game_state)
            if not resolved_npc:
                issues.append(f"Invalid NPC ID: {npc_speech.npc_id}")
            else:
                npc_speech.npc_id = resolved_npc
        
        # Validate NPC relationships
        cleaned_relationships = {}
        for npc_id, delta in response.effects.npc_relationship_changes.items():
            resolved_npc = ResponseValidator._find_npc_id(npc_id, game_state)
            if not resolved_npc:
                issues.append(f"Invalid NPC in relationship changes: {npc_id}")
                continue
            cleaned_relationships[resolved_npc] = delta
            if not (-1.0 <= delta <= 1.0):
                issues.append(f"Relationship change out of range for {resolved_npc}: {delta}")
        response.effects.npc_relationship_changes = cleaned_relationships
        
        # Validate quests
        for quest_id in response.effects.completed_quests:
            if quest_id not in game_state.active_quests:
                issues.append(f"Cannot complete non-existent quest: {quest_id}")
        
        # Validate HP change doesn't go below 0 or above max
        potential_hp = game_state.player.hp + response.effects.hp_change
        if potential_hp < 0 or potential_hp > game_state.player.max_hp:
            issues.append(f"HP change would result in invalid HP: {potential_hp}")
        
        # Validate gold doesn't go negative
        potential_gold = game_state.player.gold + response.effects.gold_change
        if potential_gold < 0:
            issues.append(f"Gold change would result in negative gold: {potential_gold} (Player only has {game_state.player.gold} gold)")
        
        # Detect suspicious free items (new items without gold cost)
        if response.effects.new_items and response.effects.gold_change >= 0:
            # Check if this is likely a purchase by looking for merchant/shopkeeper NPCs
            current_location = game_state.locations.get(game_state.current_location_id)
            if current_location:
                for npc_id in current_location.npcs:
                    npc = game_state.npcs.get(npc_id, {})
                    role = npc.get('role', '').lower()
                    if role in ['merchant', 'shopkeeper', 'bartender', 'vendor', 'trader']:
                        issues.append(f"WARNING: Receiving items from {role} without gold cost. Items should be paid for!")
                        break
        
        # Check for duplicate transactions in recent history
        if response.effects.new_items and response.effects.gold_change < 0:
            # Look at last 2 turns to see if same item was already purchased
            recent_turns = game_state.conversation_history[-2:] if game_state.conversation_history else []
            for turn in recent_turns:
                turn_items = set()
                # Parse effects_summary to find items
                for effect in turn.get('effects_summary', []):
                    if '📦 Gained:' in effect:
                        item = effect.split('📦 Gained:')[1].strip()
                        turn_items.add(item)
                
                # Check for overlap
                current_items = set(response.effects.new_items)
                overlap = turn_items & current_items
                if overlap:
                    issues.append(f"WARNING: Possible duplicate purchase - {', '.join(overlap)} was already received in recent turns")
        
        return len(issues) == 0, issues

    @staticmethod
    def sanitize_effects(response: DMResponse, game_state: GameState) -> DMResponse:
        """
        Sanitize and fix common issues in DMResponse.
        
        Returns a corrected DMResponse.
        """
        effects = response.effects
        
        # Fix location if invalid
        if effects.location:
            resolved_location = ResponseValidator._find_location_id(effects.location, game_state)
            if resolved_location:
                effects.location = resolved_location
            else:
                print(f"[Sanitizing: Invalid location '{effects.location}' -> keeping current]")
                effects.location = None
        
        # Remove invalid NPCs from speeches
        valid_speeches = []
        for npc in response.npc_speeches:
            resolved_npc = ResponseValidator._find_npc_id(npc.npc_id, game_state)
            if resolved_npc:
                npc.npc_id = resolved_npc
                valid_speeches.append(npc)
        if len(valid_speeches) != len(response.npc_speeches):
            print(f"[Sanitizing: Removed {len(response.npc_speeches) - len(valid_speeches)} invalid NPC speeches]")
            response.npc_speeches = valid_speeches
        
        # Clamp relationship changes
        sanitized_relationships = {}
        for npc_id, delta in effects.npc_relationship_changes.items():
            resolved_npc = ResponseValidator._find_npc_id(npc_id, game_state)
            if resolved_npc:
                clamped = max(-1.0, min(1.0, delta))
                sanitized_relationships[resolved_npc] = clamped
                if clamped != delta:
                    print(f"[Sanitizing: Clamped relationship change for {resolved_npc}: {delta} -> {clamped}]")
        effects.npc_relationship_changes = sanitized_relationships
        
        # Remove completed quests that don't exist
        valid_completed = [
            qid for qid in effects.completed_quests
            if qid in game_state.active_quests
        ]
        if len(valid_completed) != len(effects.completed_quests):
            print(f"[Sanitizing: Removed invalid completed quests]")
            effects.completed_quests = valid_completed
        
        # Clamp HP change
        potential_hp = game_state.player.hp + effects.hp_change
        if potential_hp < 0:
            effects.hp_change = -game_state.player.hp
            print(f"[Sanitizing: Clamped HP change to prevent negative HP]")
        elif potential_hp > game_state.player.max_hp:
            effects.hp_change = game_state.player.max_hp - game_state.player.hp
            print(f"[Sanitizing: Clamped HP change to prevent exceeding max HP]")
        
        # Clamp gold change
        potential_gold = game_state.player.gold + effects.gold_change
        if potential_gold < 0:
            effects.gold_change = -game_state.player.gold
            print(f"[Sanitizing: Clamped gold change to prevent negative gold]")
        
        return response
