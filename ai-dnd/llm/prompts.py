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

NPC PERSONALITY RULES:
- Each NPC has a distinct personality, speech style, and temperament
- NPCs react based on their personality traits, values, and fears
- Speech style must match the NPC's archetype (e.g., gruff, smooth, enthusiastic)
- NPCs remember past interactions and reference conversation history
- Relationship changes should be based on player actions aligning with or opposing NPC values
- NPCs have their own goals and may pursue them in conversations
- Mood affects how NPCs respond (happy NPCs are more helpful, upset ones less so)

COMMERCE & TRANSACTION RULES:
- ALWAYS charge for goods and services unless there's a specific reason not to (charity, quest reward, etc.)
- When player requests an item or service, NPC should state the price BEFORE giving it
- Use 'gold_change' with NEGATIVE values for purchases (e.g., -5 for a 5 gold item)
- Only add items to 'new_items' AFTER gold is deducted
- If player doesn't have enough gold, NPC should refuse or negotiate
- Common prices: Food/drink 2-5 gold, Basic supplies 5-20 gold, Weapons 30-100 gold, Potions 20-50 gold
- Merchants should be firm about prices; bartenders might give small discounts to regulars
- NPCs should remember if player already paid for something in recent conversation history
- Don't charge twice for the same item in the same conversation

Turn structure:
- Read the player's action
- Consider NPC personalities and conversation history
- Check if this is a commercial transaction (buying/selling)
- If commercial: State price, deduct gold, then give item
- Resolve mechanics and consequences
- Describe what happens in 'narration'
- Include NPC speeches in 'npc_speeches' with appropriate emotions
- Apply effects in 'effects'
- Suggest 2-4 options in 'suggested_options'"""

    @staticmethod
    def game_context(state: GameState, max_history_turns: int = 5) -> str:
        """
        Build a context prompt from game state.
        
        Args:
            state: Current game state
            max_history_turns: Maximum number of recent conversation turns to include
        """
        player = state.player
        location = state.locations.get(state.current_location_id)
        loc_name = location.name if location else "Unknown Location"
        loc_desc = location.description if location else ""

        npcs_here = []
        npcs_here_details = []
        if location:
            for npc_id in location.npcs:
                if npc_id in state.npcs:
                    npc = state.npcs[npc_id]
                    npcs_here.append(npc.get("name", npc_id))
                    
                    # Build detailed NPC description
                    npc_detail = f"\n{npc.get('name', npc_id)} ({npc_id}):\n"
                    npc_detail += f"  Role: {npc.get('role', 'unknown')}\n"
                    npc_detail += f"  Personality: {npc.get('personality', 'unknown')}\n"
                    
                    # Add personality traits if available
                    if 'personality_traits' in npc:
                        traits = npc['personality_traits']
                        npc_detail += f"  Archetype: {traits.get('archetype', 'unknown')}\n"
                        npc_detail += f"  Temperament: {traits.get('temperament', 'unknown')}\n"
                        npc_detail += f"  Speech Style: {traits.get('speech_style', 'normal')}\n"
                        npc_detail += f"  Values: {', '.join(traits.get('values', []))}\n"
                        npc_detail += f"  Fears: {', '.join(traits.get('fears', []))}\n"
                        if traits.get('quirks'):
                            npc_detail += f"  Quirks: {', '.join(traits.get('quirks', []))}\n"
                    
                    # Add current goal
                    if 'current_goal' in npc:
                        npc_detail += f"  Current Goal: {npc['current_goal']}\n"
                    
                    # Add relationship status
                    relationship = state.npc_relationships.get(npc_id, 0.0)
                    if relationship >= 0.7:
                        rel_status = "trusted ally"
                    elif relationship >= 0.3:
                        rel_status = "friendly"
                    elif relationship >= -0.3:
                        rel_status = "neutral"
                    elif relationship >= -0.7:
                        rel_status = "unfriendly"
                    else:
                        rel_status = "hostile"
                    npc_detail += f"  Relationship with player: {rel_status} ({relationship:+.1f})\n"
                    
                    # Add mood if available
                    if 'mood' in npc:
                        mood = npc['mood']
                        if mood > 0.3:
                            mood_status = "happy"
                        elif mood > -0.3:
                            mood_status = "neutral"
                        else:
                            mood_status = "upset"
                        npc_detail += f"  Current Mood: {mood_status} ({mood:+.1f})\n"
                    
                    npcs_here_details.append(npc_detail)

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
Gold: {player.gold} 💰 (IMPORTANT: Player can only afford items/services they have gold for)
Inventory: {', '.join(state.player.inventory.items.keys()) if state.player.inventory.items else 'Empty'}

=== LOCATION ===
{loc_name}
{loc_desc}
"""
        if npcs_here:
            context += f"\n=== NPCs PRESENT ==="
            for npc_detail in npcs_here_details:
                context += npc_detail

        if quests_str:
            context += f"\n{quests_str}"

        # Add conversation history (recent turns)
        if state.conversation_history:
            context += f"\n=== RECENT CONVERSATION HISTORY ===\n"
            # Get last N turns
            recent_turns = state.conversation_history[-max_history_turns:]
            for turn_data in recent_turns:
                context += f"\nTurn {turn_data.get('turn_number', '?')}:\n"
                context += f"  Player: {turn_data.get('player_action', '')}\n"
                context += f"  Narration: {turn_data.get('narration', '')}\n"
                
                # Add NPC speeches if any
                if turn_data.get('npc_speeches'):
                    for speech in turn_data['npc_speeches']:
                        npc_name = state.npcs.get(speech.get('npc_id', ''), {}).get('name', speech.get('npc_id', 'Unknown'))
                        emotion = speech.get('emotion', 'neutral')
                        text = speech.get('text', '')
                        context += f"  {npc_name} ({emotion}): \"{text}\"\n"
                
                # Add effects summary if any
                if turn_data.get('effects_summary'):
                    context += f"  Effects: {', '.join(turn_data['effects_summary'])}\n"

        # Fallback to old events log if no conversation history yet
        elif state.world_events_log:
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
