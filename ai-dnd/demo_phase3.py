#!/usr/bin/env python3
"""Quick demo of Phase 3: NPC Personalities & Conversation Memory"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.state import GameState, Player, Location, Inventory
from llm.prompts import DMPromptBuilder
import json

def demo_npc_personalities():
    """Show how NPC personalities appear in prompts."""
    print("=" * 70)
    print("PHASE 3 DEMO: NPC Personalities & Conversation Memory")
    print("=" * 70)
    
    # Load NPCs
    with open("data/npcs.json", "r") as f:
        npcs = json.load(f)
    
    print("\n1. NPCs Now Have Rich Personalities:")
    print("-" * 70)
    for npc_id, npc in list(npcs.items())[:3]:
        print(f"\n{npc['name']} - {npc['role']}")
        traits = npc.get('personality_traits', {})
        print(f"  Archetype: {traits.get('archetype', 'N/A')}")
        print(f"  Speech Style: {traits.get('speech_style', 'N/A')}")
        print(f"  Values: {', '.join(traits.get('values', []))}")
        print(f"  Current Goal: {npc.get('current_goal', 'N/A')}")
    
    # Create test game state with conversation history
    player = Player(
        name="Hero",
        class_name="Warrior",
        hp=20,
        max_hp=20,
        gold=50,
        inventory=Inventory()
    )
    
    location = Location(
        id="tavern",
        name="The Rusty Flagon",
        description="A warm, bustling tavern",
        npcs=["bartender"]
    )
    
    state = GameState(
        player=player,
        current_location_id="tavern",
        game_time="2025-01-01T18:00:00",
        locations={"tavern": location},
        npcs=npcs
    )
    
    # Add conversation history
    state.conversation_history.append({
        'turn_number': 1,
        'player_action': 'I walk up to the bar',
        'narration': 'The bartender glances up from polishing a glass.',
        'npc_speeches': [
            {'npc_id': 'bartender', 'text': 'What can I get you?', 'emotion': 'gruff'}
        ],
        'effects_summary': [],
        'timestamp': '2025-01-01T18:00:00'
    })
    
    state.conversation_history.append({
        'turn_number': 2,
        'player_action': 'I ask if she knows anything about the thieves',
        'narration': 'Mira leans in, her expression serious.',
        'npc_speeches': [
            {'npc_id': 'bartender', 'text': "Keep your voice down. The guard captain's been asking questions.", 'emotion': 'cautious'}
        ],
        'effects_summary': ['🤝 Mira: +0.1 (friendly)'],
        'timestamp': '2025-01-01T18:05:00'
    })
    
    print("\n\n2. Conversation History is Tracked:")
    print("-" * 70)
    print(f"Stored {len(state.conversation_history)} turns")
    for turn in state.conversation_history:
        print(f"\nTurn {turn['turn_number']}:")
        print(f"  Player: {turn['player_action']}")
        print(f"  DM: {turn['narration']}")
        if turn['npc_speeches']:
            for speech in turn['npc_speeches']:
                npc_name = npcs.get(speech['npc_id'], {}).get('name', speech['npc_id'])
                print(f"  {npc_name}: \"{speech['text']}\"")
    
    print("\n\n3. Context Sent to LLM Includes Everything:")
    print("-" * 70)
    context = DMPromptBuilder.game_context(state, max_history_turns=5)
    
    # Show key sections
    if "=== NPCs PRESENT ===" in context:
        idx = context.index("=== NPCs PRESENT ===")
        print(context[idx:idx+500])
        print("\n... (NPC details continue) ...\n")
    
    if "=== RECENT CONVERSATION HISTORY ===" in context:
        idx = context.index("=== RECENT CONVERSATION HISTORY ===")
        print(context[idx:idx+600])
        print("\n... (conversation continues) ...")
    
    print("\n\n4. System Prompt Has NPC Personality Rules:")
    print("-" * 70)
    system = DMPromptBuilder.system_prompt()
    if "NPC PERSONALITY RULES" in system:
        idx = system.index("NPC PERSONALITY RULES")
        print(system[idx:idx+400])
    
    print("\n\n" + "=" * 70)
    print("HOW THIS FIXES THE MEMORY ISSUE:")
    print("=" * 70)
    print("""
Before Phase 3:
  - Only last 3 brief event logs
  - No NPC personalities
  - LLM forgets conversations quickly
  - NPCs sound the same

After Phase 3:
  ✅ Last 10 full conversation turns stored
  ✅ Last 5 turns sent to LLM in every prompt
  ✅ NPCs have distinct personalities
  ✅ Relationships tracked and displayed
  ✅ LLM sees full dialogue context

Result: NPCs remember conversations and stay in character!
""")
    
    print("=" * 70)
    print("TRY IT: Run 'python3 main.py' and talk to NPCs")
    print("=" * 70)


if __name__ == "__main__":
    demo_npc_personalities()
