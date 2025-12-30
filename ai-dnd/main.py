#!/usr/bin/env python3
"""Main entry point for AI-driven D&D engine."""

import json
import sys
import os
from datetime import datetime

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.state import GameState, Player, Location, Inventory
from engine.game_loop import GameEngine
from llm.client import OllamaClient
from ui.cli import GameCLI


def load_world_data():
    """Load world data from JSON files."""
    world = {}

    # Load locations
    with open("data/locations.json", "r") as f:
        locations_data = json.load(f)
        world["locations"] = {
            loc_id: Location(**data) for loc_id, data in locations_data.items()
        }

    # Load NPCs
    with open("data/npcs.json", "r") as f:
        world["npcs"] = json.load(f)

    # Load factions
    with open("data/factions.json", "r") as f:
        world["factions"] = json.load(f)

    # Load items
    with open("data/items.json", "r") as f:
        world["items"] = json.load(f)

    # Load rules
    with open("data/rules.json", "r") as f:
        world["rules"] = json.load(f)

    return world


def create_new_game(player_name: str = None, player_class: str = None):
    """Create a new game state."""
    if not player_name:
        player_name = input("Enter your character name: ").strip() or "Adventurer"

    if not player_class:
        print("\nChoose your class:")
        print("  1. Warrior")
        print("  2. Rogue")
        print("  3. Mage")
        print("  4. Cleric")
        choice = input("Select (1-4): ").strip()
        class_map = {"1": "Warrior", "2": "Rogue", "3": "Mage", "4": "Cleric"}
        player_class = class_map.get(choice, "Warrior")

    # Load world data
    world = load_world_data()

    # Create player
    player = Player(
        name=player_name,
        class_name=player_class,
        level=1,
        hp=20,
        max_hp=20,
        experience=0,
        gold=50,
        inventory=Inventory(),
    )

    # Add starting items
    player.inventory.add_item("rope", 1)
    player.inventory.add_item("torch", 2)
    player.inventory.add_item("healing_potion", 1)

    # Create game state
    game_state = GameState(
        player=player,
        current_location_id="tavern",
        game_time=datetime.now().isoformat(),
        turn=0,
        locations=world["locations"],
        active_quests={},
        npcs=world["npcs"],
        world_events_log=[],
        last_narration="You awaken in a cozy tavern. The aroma of ale and hearth smoke fills the air. Your adventure begins...",
    )

    return game_state


def main():
    """Main entry point."""
    print("\n" + "=" * 70)
    print("WELCOME TO AI-DRIVEN D&D ENGINE".center(70))
    print("=" * 70)
    print("\nPhase 0: Foundations")
    print("Phase 1: Minimal Text-Only Single-DM Game")
    print()

    # Check if save exists
    save_file = "data/save_state.json"
    if os.path.exists(save_file):
        choice = input("Load existing game? (y/n): ").lower()
        if choice == "y":
            try:
                game_state = GameState.load_from_file(save_file)
                print("[Game loaded]")
            except Exception as e:
                print(f"[Load failed: {e}]")
                print("Starting new game instead...")
                game_state = create_new_game()
        else:
            game_state = create_new_game()
    else:
        game_state = create_new_game()

    # Initialize engine
    engine = GameEngine(game_state)
    print("\n✓ Game engine initialized")

    # Initialize LLM client
    llm = OllamaClient(base_url="http://localhost:11434", model="llama3.2:latest")
    print("✓ LLM client initialized")

    # Initialize CLI
    cli = GameCLI(llm, engine)
    print("✓ CLI initialized\n")

    # Run game
    cli.main_loop()


if __name__ == "__main__":
    main()
