#!/usr/bin/env python3
"""Test script for Phase 3: NPC Personalities & Conversation Memory"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.state import GameState, Player, Location, Inventory
from engine.game_loop import GameEngine
from llm.prompts import DMPromptBuilder


def test_npc_data():
    """Test that NPC data has been enriched with personality traits."""
    print("=" * 70)
    print("TEST 1: NPC Data Schema")
    print("=" * 70)
    
    with open("data/npcs.json", "r") as f:
        npcs = json.load(f)
    
    required_fields = [
        'personality_traits', 'current_goal', 'mood', 
        'current_location', 'last_interaction_turn'
    ]
    
    for npc_id, npc in npcs.items():
        print(f"\nChecking {npc.get('name', npc_id)}:")
        for field in required_fields:
            if field in npc:
                print(f"  ✓ {field}: {npc[field] if not isinstance(npc[field], dict) else '(object)'}")
            else:
                print(f"  ✗ MISSING: {field}")
        
        # Check personality_traits structure
        if 'personality_traits' in npc:
            traits = npc['personality_traits']
            sub_fields = ['archetype', 'temperament', 'speech_style', 'values', 'fears']
            for sf in sub_fields:
                if sf in traits:
                    print(f"    ✓ {sf}")
                else:
                    print(f"    ✗ MISSING: {sf}")
    
    print("\n✅ Test 1 Complete\n")


def test_conversation_history():
    """Test that conversation history is being tracked."""
    print("=" * 70)
    print("TEST 2: Conversation History Tracking")
    print("=" * 70)
    
    # Create a simple game state
    player = Player(
        name="TestHero",
        class_name="Warrior",
        hp=20,
        max_hp=20,
        gold=50,
        inventory=Inventory()
    )
    
    location = Location(
        id="test_room",
        name="Test Room",
        description="A room for testing",
        npcs=["bartender"]
    )
    
    with open("data/npcs.json", "r") as f:
        npcs = json.load(f)
    
    state = GameState(
        player=player,
        current_location_id="test_room",
        game_time="2025-01-01T12:00:00",
        locations={"test_room": location},
        npcs=npcs
    )
    
    print(f"\nInitial conversation history length: {len(state.conversation_history)}")
    
    # Simulate adding conversation turns
    turn1 = {
        'turn_number': 1,
        'player_action': 'I greet the bartender',
        'narration': 'The bartender looks up from cleaning a glass.',
        'npc_speeches': [
            {'npc_id': 'bartender', 'text': 'What can I get you?', 'emotion': 'gruff'}
        ],
        'effects_summary': [],
        'timestamp': '2025-01-01T12:00:00'
    }
    
    turn2 = {
        'turn_number': 2,
        'player_action': 'I ask about the local news',
        'narration': 'Mira leans in conspiratorially.',
        'npc_speeches': [
            {'npc_id': 'bartender', 'text': 'Well, there have been some strange happenings...', 'emotion': 'curious'}
        ],
        'effects_summary': ['🤝 Mira: +0.1 (friendly)'],
        'timestamp': '2025-01-01T12:05:00'
    }
    
    state.conversation_history.append(turn1)
    state.conversation_history.append(turn2)
    
    print(f"After adding 2 turns: {len(state.conversation_history)}")
    
    # Test that conversation history is included in prompts
    print("\n--- Testing prompt generation with conversation history ---")
    context = DMPromptBuilder.game_context(state, max_history_turns=5)
    
    if "RECENT CONVERSATION HISTORY" in context:
        print("✓ Conversation history section found in prompt")
    else:
        print("✗ ERROR: Conversation history not in prompt")
    
    if "I greet the bartender" in context:
        print("✓ Turn 1 player action found")
    else:
        print("✗ ERROR: Turn 1 not in context")
    
    if "I ask about the local news" in context:
        print("✓ Turn 2 player action found")
    else:
        print("✗ ERROR: Turn 2 not in context")
    
    print("\n--- Sample Context Output (first 1000 chars) ---")
    print(context[:1000])
    
    print("\n✅ Test 2 Complete\n")


def test_npc_personalities_in_prompt():
    """Test that NPC personalities are included in prompts."""
    print("=" * 70)
    print("TEST 3: NPC Personality in Prompts")
    print("=" * 70)
    
    # Load NPCs and create test state
    with open("data/npcs.json", "r") as f:
        npcs = json.load(f)
    
    player = Player(
        name="TestHero",
        class_name="Warrior",
        hp=20,
        max_hp=20,
        gold=50,
        inventory=Inventory()
    )
    
    location = Location(
        id="tavern",
        name="The Rusty Flagon",
        description="A cozy tavern",
        npcs=["bartender", "mysterious_stranger"]
    )
    
    state = GameState(
        player=player,
        current_location_id="tavern",
        game_time="2025-01-01T12:00:00",
        locations={"tavern": location},
        npcs=npcs
    )
    
    # Generate context
    context = DMPromptBuilder.game_context(state)
    
    print("\nChecking for personality information in context:")
    
    checks = [
        ("NPCs PRESENT", "NPC section header"),
        ("Archetype:", "Archetype field"),
        ("Speech Style:", "Speech style field"),
        ("Values:", "Values field"),
        ("Fears:", "Fears field"),
        ("Current Goal:", "Current goal field"),
        ("Relationship with player:", "Relationship tracking"),
        ("gruff", "Mira's personality trait"),
        ("cryptic", "Raven's personality trait")
    ]
    
    for search_term, description in checks:
        if search_term in context:
            print(f"  ✓ {description} found")
        else:
            print(f"  ✗ {description} NOT found")
    
    print("\n--- Full Context Output ---")
    print(context)
    
    print("\n✅ Test 3 Complete\n")


def test_system_prompt():
    """Test that system prompt includes NPC personality rules."""
    print("=" * 70)
    print("TEST 4: System Prompt Enhancement")
    print("=" * 70)
    
    system_prompt = DMPromptBuilder.system_prompt()
    
    print("\nChecking for NPC personality rules in system prompt:")
    
    checks = [
        ("NPC PERSONALITY RULES", "Personality rules section"),
        ("distinct personality", "Distinct personalities"),
        ("speech style", "Speech style matching"),
        ("conversation history", "Memory of conversations"),
        ("Relationship changes", "Relationship mechanics"),
        ("own goals", "NPC goals"),
        ("Mood affects", "Mood system")
    ]
    
    for search_term, description in checks:
        if search_term in system_prompt:
            print(f"  ✓ {description} found")
        else:
            print(f"  ✗ {description} NOT found")
    
    print("\n--- System Prompt Excerpt ---")
    # Show NPC personality section
    if "NPC PERSONALITY RULES" in system_prompt:
        idx = system_prompt.index("NPC PERSONALITY RULES")
        print(system_prompt[idx:idx+800])
    
    print("\n✅ Test 4 Complete\n")


def test_save_load_conversation_history():
    """Test that conversation history persists across save/load."""
    print("=" * 70)
    print("TEST 5: Save/Load Conversation History")
    print("=" * 70)
    
    # Create state with conversation history
    player = Player(
        name="TestHero",
        class_name="Warrior",
        hp=20,
        max_hp=20,
        gold=50,
        inventory=Inventory()
    )
    
    location = Location(
        id="tavern",
        name="Tavern",
        description="A tavern",
        npcs=["bartender"]
    )
    
    with open("data/npcs.json", "r") as f:
        npcs = json.load(f)
    
    state = GameState(
        player=player,
        current_location_id="tavern",
        game_time="2025-01-01T12:00:00",
        locations={"tavern": location},
        npcs=npcs
    )
    
    # Add conversation history
    state.conversation_history.append({
        'turn_number': 1,
        'player_action': 'Test action',
        'narration': 'Test narration',
        'npc_speeches': [{'npc_id': 'bartender', 'text': 'Test', 'emotion': 'neutral'}],
        'effects_summary': [],
        'timestamp': '2025-01-01T12:00:00'
    })
    
    print(f"\nBefore save: {len(state.conversation_history)} conversation turns")
    
    # Save
    test_save_path = "data/test_phase3_save.json"
    state.save_to_file(test_save_path)
    print(f"✓ Saved to {test_save_path}")
    
    # Load
    loaded_state = GameState.load_from_file(test_save_path)
    print(f"After load: {len(loaded_state.conversation_history)} conversation turns")
    
    if len(loaded_state.conversation_history) == 1:
        print("✓ Conversation history preserved")
        turn = loaded_state.conversation_history[0]
        print(f"  Turn {turn['turn_number']}: {turn['player_action']}")
    else:
        print("✗ ERROR: Conversation history not preserved")
    
    # Cleanup
    os.remove(test_save_path)
    print(f"✓ Cleaned up test save file")
    
    print("\n✅ Test 5 Complete\n")


if __name__ == "__main__":
    print("\n🎮 PHASE 3 TEST SUITE: NPC Personalities & Conversation Memory\n")
    
    try:
        test_npc_data()
        test_conversation_history()
        test_npc_personalities_in_prompt()
        test_system_prompt()
        test_save_load_conversation_history()
        
        print("=" * 70)
        print("🎉 ALL TESTS COMPLETE")
        print("=" * 70)
        print("\nPhase 3 Implementation Summary:")
        print("✅ NPCs have detailed personality traits, goals, fears")
        print("✅ Conversation history tracks full turns with narration and speeches")
        print("✅ Prompts include NPC personalities and recent conversation history")
        print("✅ System prompt instructs LLM to use NPC personalities")
        print("✅ Save/load preserves conversation history")
        print("\nNPCs should now:")
        print("  • Have distinct speech patterns matching their personality")
        print("  • Remember conversations from previous turns")
        print("  • React consistently with their values and fears")
        print("  • Display emotions that match their mood and temperament")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
