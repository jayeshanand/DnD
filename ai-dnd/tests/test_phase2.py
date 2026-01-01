#!/usr/bin/env python3
"""Test Phase 2 implementation."""

from engine.response_schema import DMResponse, NPCResponse, WorldEffect
from engine.response_parser import ResponseParser, ResponseValidator
from engine.state import GameState, Player, Location
from engine.game_loop import GameEngine
from datetime import datetime
import json

def test_parsing():
    """Test JSON parsing."""
    print("=" * 70)
    print("TEST 1: Valid JSON Parsing")
    print("=" * 70)
    
    test_json = """{
  "narration": "You enter the tavern and see a friendly bartender.",
  "npc_speeches": [
    {"npc_id": "bartender", "text": "Welcome, traveler!", "emotion": "friendly"}
  ],
  "effects": {
    "location": "tavern",
    "time_delta": 5,
    "hp_change": 0,
    "gold_change": -5,
    "new_items": ["ale"],
    "new_quests": [],
    "completed_quests": [],
    "npc_relationship_changes": {"bartender": 0.1}
  },
  "suggested_options": ["Talk to bartender", "Look around", "Order food"]
}"""
    
    parsed = ResponseParser.parse_response(test_json)
    assert parsed is not None, "Failed to parse valid JSON"
    assert parsed.narration.startswith("You enter"), "Narration not parsed correctly"
    assert len(parsed.npc_speeches) == 1, "NPC speeches not parsed"
    assert parsed.effects.gold_change == -5, "Gold change not parsed"
    print("✅ Valid JSON parsed successfully")
    print(f"   Narration: {parsed.narration[:60]}...")
    print(f"   NPC speeches: {len(parsed.npc_speeches)}")
    print(f"   Effects: {len(parsed.effects.new_items)} new items")
    
    print("\n" + "=" * 70)
    print("TEST 2: JSON with Extra Text")
    print("=" * 70)
    
    test_json2 = 'Sure, here is the response:\n\n{"narration": "Test narration", "effects": {}}'
    parsed2 = ResponseParser.parse_response(test_json2)
    assert parsed2 is not None, "Failed to extract JSON from text"
    print("✅ JSON extracted from surrounding text")
    
    print("\n" + "=" * 70)
    print("TEST 3: Fallback Response")
    print("=" * 70)
    
    fallback = ResponseParser.create_fallback_response("test action")
    assert fallback is not None, "Fallback response creation failed"
    assert "test action" in fallback.narration, "Fallback doesn't reference action"
    print("✅ Fallback response created")
    print(f"   Narration: {fallback.narration[:60]}...")


def test_validation():
    """Test response validation."""
    print("\n" + "=" * 70)
    print("TEST 4: Response Validation")
    print("=" * 70)
    
    # Create minimal game state
    player = Player(name="TestHero", class_name="Warrior")
    state = GameState(
        player=player,
        current_location_id="tavern",
        game_time=datetime.now().isoformat(),
        locations={
            "tavern": Location(id="tavern", name="Tavern", description="A cozy tavern")
        },
        npcs={
            "bartender": {"name": "Mira", "role": "bartender"}
        }
    )
    
    # Valid response
    response = DMResponse(
        narration="Test",
        effects=WorldEffect(
            location="tavern",
            npc_relationship_changes={"bartender": 0.1}
        )
    )
    
    is_valid, issues = ResponseValidator.validate_dm_response(response, state)
    assert is_valid, f"Valid response marked as invalid: {issues}"
    print("✅ Valid response passes validation")
    
    # Invalid location
    response2 = DMResponse(
        narration="Test",
        effects=WorldEffect(location="invalid_place")
    )
    
    is_valid2, issues2 = ResponseValidator.validate_dm_response(response2, state)
    assert not is_valid2, "Invalid location not caught"
    print(f"✅ Invalid location detected: {issues2[0]}")
    
    # Sanitize it
    sanitized = ResponseValidator.sanitize_effects(response2, state)
    assert sanitized.effects.location is None, "Location not sanitized"
    print("✅ Invalid location sanitized to None")


def test_effects():
    """Test effect application."""
    print("\n" + "=" * 70)
    print("TEST 5: Effect Application")
    print("=" * 70)
    
    # Create game state
    player = Player(name="TestHero", class_name="Warrior", hp=15, gold=100)
    state = GameState(
        player=player,
        current_location_id="forest",
        game_time=datetime.now().isoformat(),
        locations={
            "forest": Location(id="forest", name="Forest", description="Dark forest"),
            "tavern": Location(id="tavern", name="Tavern", description="Cozy tavern")
        },
        npcs={"bartender": {"name": "Mira"}}
    )
    
    engine = GameEngine(state)
    
    # Apply effects
    effects = WorldEffect(
        location="tavern",
        time_delta=10,
        hp_change=5,
        gold_change=-20,
        new_items=["sword", "potion"],
        npc_relationship_changes={"bartender": 0.3}
    )
    
    log = engine.apply_effects(effects)
    
    assert state.current_location_id == "tavern", "Location not updated"
    assert state.player.hp == 20, "HP not updated correctly"
    assert state.player.gold == 80, "Gold not updated correctly"
    assert "sword" in state.player.inventory.items, "Items not added"
    assert state.npc_relationships.get("bartender") == 0.3, "Relationship not updated"
    
    print("✅ All effects applied correctly")
    for log_entry in log:
        print(f"   {log_entry}")


def main():
    """Run all tests."""
    print("\n🧪 PHASE 2 IMPLEMENTATION TESTS\n")
    
    try:
        test_parsing()
        test_validation()
        test_effects()
        
        print("\n" + "=" * 70)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 70)
        print("\n✅ Phase 2 implementation is working correctly!")
        print("   - JSON parsing: OK")
        print("   - Response validation: OK")
        print("   - Effect application: OK")
        print("   - Fallback handling: OK")
        print("\nYou can now run the game with: python main.py")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
