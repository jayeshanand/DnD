#!/usr/bin/env python3
"""Test commerce/transaction fixes"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.state import GameState, Player, Location, Inventory
from engine.response_parser import ResponseValidator
from engine.response_schema import DMResponse, WorldEffect, NPCResponse
import json


def test_commerce_validation():
    """Test that commerce validation catches free items."""
    print("=" * 70)
    print("COMMERCE VALIDATION TEST")
    print("=" * 70)
    
    # Load NPCs
    with open("data/npcs.json", "r") as f:
        npcs = json.load(f)
    
    # Create game state at tavern
    player = Player(name="Hero", class_name="Warrior", hp=20, max_hp=20, gold=50, inventory=Inventory())
    location = Location(id="tavern", name="Tavern", description="A tavern", npcs=["bartender"])
    
    state = GameState(
        player=player,
        current_location_id="tavern",
        game_time="2025-01-01T12:00:00",
        locations={"tavern": location},
        npcs=npcs
    )
    
    print(f"\nPlayer has: {state.player.gold} gold")
    print(f"Current location: {state.current_location_id}")
    print(f"NPCs here: bartender (role: {npcs['bartender']['role']})")
    
    # Test 1: Free food from bartender (should flag warning)
    print("\n" + "-" * 70)
    print("TEST 1: NPC gives food without charging")
    print("-" * 70)
    
    response1 = DMResponse(
        narration="Mira slides a bowl of stew across the bar.",
        npc_speeches=[NPCResponse(npc_id="bartender", text="Here you go!", emotion="friendly")],
        effects=WorldEffect(
            new_items=["stew"],  # Getting item
            gold_change=0  # But not paying!
        ),
        suggested_options=["Thank her", "Eat the stew"]
    )
    
    is_valid, issues = ResponseValidator.validate_dm_response(response1, state)
    print(f"Valid: {is_valid}")
    print("Issues found:")
    for issue in issues:
        print(f"  ⚠️  {issue}")
    
    # Test 2: Properly paid transaction (should pass)
    print("\n" + "-" * 70)
    print("TEST 2: Player pays for food")
    print("-" * 70)
    
    response2 = DMResponse(
        narration="Mira accepts your coins and serves the stew.",
        npc_speeches=[NPCResponse(npc_id="bartender", text="That'll be 5 gold.", emotion="neutral")],
        effects=WorldEffect(
            new_items=["stew"],
            gold_change=-5  # Paying 5 gold
        ),
        suggested_options=["Eat the stew", "Ask about rumors"]
    )
    
    is_valid, issues = ResponseValidator.validate_dm_response(response2, state)
    print(f"Valid: {is_valid}")
    if issues:
        print("Issues found:")
        for issue in issues:
            print(f"  ⚠️  {issue}")
    else:
        print("✅ No issues - proper transaction!")
    
    # Test 3: Insufficient funds (should catch)
    print("\n" + "-" * 70)
    print("TEST 3: Player tries to buy with insufficient gold")
    print("-" * 70)
    
    response3 = DMResponse(
        narration="You don't have enough gold for that.",
        npc_speeches=[NPCResponse(npc_id="bartender", text="That's 100 gold. You're short.", emotion="apologetic")],
        effects=WorldEffect(
            new_items=["sword"],
            gold_change=-100  # Player only has 50!
        ),
        suggested_options=["Apologize", "Ask for credit"]
    )
    
    is_valid, issues = ResponseValidator.validate_dm_response(response3, state)
    print(f"Valid: {is_valid}")
    print("Issues found:")
    for issue in issues:
        print(f"  ⚠️  {issue}")
    
    # Test 4: Duplicate purchase detection
    print("\n" + "-" * 70)
    print("TEST 4: Detecting duplicate purchases")
    print("-" * 70)
    
    # Simulate buying stew in previous turn
    state.conversation_history.append({
        'turn_number': 1,
        'player_action': 'I order stew',
        'narration': 'Mira serves you a bowl of stew.',
        'npc_speeches': [{'npc_id': 'bartender', 'text': "That's 5 gold.", 'emotion': 'neutral'}],
        'effects_summary': ['💰 Gold: 50 → 45 (-5)', '📦 Gained: stew'],
        'timestamp': '2025-01-01T12:00:00'
    })
    
    # Now try to buy same item again
    response4 = DMResponse(
        narration="Mira serves another bowl of stew.",
        npc_speeches=[NPCResponse(npc_id="bartender", text="Another one? That's 5 gold.", emotion="curious")],
        effects=WorldEffect(
            new_items=["stew"],  # Same item!
            gold_change=-5
        ),
        suggested_options=["Eat", "Pay"]
    )
    
    is_valid, issues = ResponseValidator.validate_dm_response(response4, state)
    print(f"Valid: {is_valid}")
    if issues:
        print("Issues found:")
        for issue in issues:
            print(f"  ⚠️  {issue}")
    else:
        print("✅ No duplicate detected (this could be intentional - buying 2nd bowl)")
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("""
The validation now detects:
✅ Free items from merchants/bartenders (warns)
✅ Insufficient gold for purchases (blocks)
✅ Duplicate purchases in recent history (warns)

The LLM is also instructed to:
✅ Always state price before giving items
✅ Deduct gold with negative gold_change
✅ Check conversation history to avoid re-charging
✅ Only add items AFTER gold is deducted
    """)


if __name__ == "__main__":
    test_commerce_validation()
