"""Prompt templates and builders for DM responses."""

from engine.state import GameState
from typing import Optional


class DMPromptBuilder:
    """Builder for constructing DM system and context prompts."""

    @staticmethod
    def json_output_format() -> str:
        """
        JSON format specification for structured DM responses.
        """
        return """
You MUST respond in this exact JSON format:

{
  "narration": "2-3 sentence description of what happens",
  "npc_speeches": [
    {
      "npc_id": "bartender",
      "text": "What brings you here, friend?",
      "emotion": "friendly"
    }
  ],
  "effects": {
    "location": null,
    "time_delta": 5,
    "hp_change": 0,
    "gold_change": 0,
    "new_items": [],
    "new_quests": [],
    "completed_quests": [],
    "npc_relationship_changes": {}
  },
  "suggested_options": [
    "Ask about the town",
    "Order a drink",
    "Look around"
  ]
}

CRITICAL RULES:
- Always return valid JSON (no trailing commas, proper quotes)
- npc_speeches must use npc_ids that exist in the game world
- location must be a valid location_id from the world, or null
- Relationships changes are between -1.0 and 1.0 (use small increments like 0.1)
- time_delta is in minutes (5-30 for most actions)
- hp_change and gold_change can be positive or negative
- new_items, new_quests, completed_quests are arrays of IDs
- If no NPCs speak, use empty array: "npc_speeches": []
- If no effects, use defaults as shown above
- suggested_options should be 2-4 natural next actions
"""

    @staticmethod
    def system_prompt() -> str:
        """
        Core system prompt that defines DM behavior.
        """
        return """You are an expert Dungeon Master (DM) for a fantasy tabletop RPG adventure.

Your responsibilities:
- Narrate the world vividly but concisely
- Describe locations, NPCs, and events in rich detail
- React to player actions with narrative consequences
- Present options and follow-up questions naturally
- Keep the story engaging and maintain immersion
- Be fair but challenging
- RESPOND IN STRUCTURED JSON FORMAT

Style guidelines:
- Write in second person to the player ("You see...", "You hear...")
- Keep narrations to 2-3 sentences in the JSON 'narration' field
- Use NPC dialogue for character interactions
- Vary sentence structure and vocabulary
- Use sensory details (sounds, smells, textures)
- Be consistent with previously established facts

Turn structure:
- Read the player's action
- Resolve mechanics and consequences
- Describe what happens in 'narration'
- Include NPC speeches in 'npc_speeches'
- Apply effects in 'effects'
- Suggest 2-4 options in 'suggested_options'"""

    @staticmethod
    def game_context(state: GameState) -> str:
        """
        Build a context prompt from game state.
        """
        player = state.player
        location = state.locations.get(state.current_location_id)
        loc_name = location.name if location else "Unknown Location"
        loc_desc = location.description if location else ""

        npcs_here = []
        if location:
            for npc_id in location.npcs:
                if npc_id in state.npcs:
                    npcs_here.append(state.npcs[npc_id].get("name", npc_id))

        quests_str = ""
        if state.active_quests:
            quests_str = "Active Quests:\n"
            for qid, quest in state.active_quests.items():
                quests_str += f"  - {quest.title}: {quest.description}\n"

        context = f"""=== CURRENT SITUATION ===
Turn: {state.turn}
Time: {state.game_time}

=== PLAYER ===
Name: {player.name}
Class: {player.class_name}
HP: {player.hp}/{player.max_hp}
Gold: {player.gold}
Inventory: {', '.join(state.player.inventory.items.keys()) if state.player.inventory.items else 'Empty'}

=== LOCATION ===
{loc_name}
{loc_desc}
"""
        if npcs_here:
            context += f"\nNPCs Here: {', '.join(npcs_here)}\n"

        if quests_str:
            context += f"\n{quests_str}"

        if state.world_events_log:
            context += f"\nRecent Events:\n"
            for event in state.world_events_log[-3:]:  # Last 3 events
                context += f"  - {event}\n"

        return context.strip()

    @staticmethod
    def construct_full_prompt(
        state: GameState,
        player_input: str,
        include_system: bool = True
    ) -> tuple:
        """
        Construct full system + user prompt for LLM.

        Returns:
            (system_prompt, user_prompt) tuple
        """
        system = DMPromptBuilder.system_prompt() if include_system else ""
        
        # Add JSON format to system prompt
        system += "\n\n" + DMPromptBuilder.json_output_format()
        
        context = DMPromptBuilder.game_context(state)
        user = f"{context}\n\n=== PLAYER ACTION ===\n{player_input}\n\n=== DM RESPONSE (JSON) ===\n"

        return system, user
