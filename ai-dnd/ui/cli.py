"""Command-line interface for the game."""

import os
import sys
from engine.state import GameState, Location
from engine.game_loop import GameEngine
from engine.response_parser import ResponseParser, ResponseValidator
from llm.client import OllamaClient
from llm.prompts import DMPromptBuilder


class GameCLI:
    """Command-line interface for playing the game."""

    def __init__(self, llm_client: OllamaClient, engine: GameEngine):
        self.llm = llm_client
        self.engine = engine
        self.running = True

    def clear_screen(self):
        """Clear terminal screen."""
        os.system("cls" if os.name == "nt" else "clear")

    def display_header(self):
        """Display game header."""
        print("\n" + "=" * 70)
        print("AI-DRIVEN D&D ENGINE".center(70))
        print("=" * 70 + "\n")

    def display_location(self):
        """Display current location and situation."""
        state = self.engine.state
        location = self.engine.get_current_location()

        if not location:
            print("[ERROR] No location loaded!")
            return

        print(f"\n>>> {location.name.upper()} <<<")
        print("-" * 70)
        print(location.description)

        if location.npcs:
            npc_names = [
                state.npcs.get(npc_id, {}).get("name", npc_id)
                for npc_id in location.npcs
                if npc_id in state.npcs
            ]
            if npc_names:
                print(f"\nNPCs here: {', '.join(npc_names)}")

        print("-" * 70)

    def display_last_narration(self):
        """Display the last narration from the DM."""
        state = self.engine.state
        if state.last_narration:
            print("\n[DM NARRATION]")
            print(state.last_narration)
            print()

    def display_player_status(self):
        """Display player status bar."""
        player = self.engine.state.player
        hp_bar = f"{'█' * player.hp}{'░' * (player.max_hp - player.hp)}"
        print(f"\n{player.name} | HP: [{hp_bar}] {player.hp}/{player.max_hp} | Gold: {player.gold}")

    def display_menu(self):
        """Display action menu."""
        print("\nOptions:")
        print("  (1) Look around")
        print("  (2) Talk to someone")
        print("  (3) Check inventory")
        print("  (4) Check quests")
        print("  (5) Rest")
        print("  (6) Custom action (type your own)")
        print("  (7) Save game")
        print("  (8) Load game")
        print("  (q) Quit")

    def get_player_action(self) -> str:
        """Prompt player for action."""
        while True:
            action = input("\n> Your action (or help): ").strip()

            if not action:
                print("Please enter an action.")
                continue

            if action.lower() == "help":
                self.display_menu()
                continue

            if action.lower() == "q":
                self.running = False
                return "quit"

            return action

    def handle_quick_action(self, action: str) -> bool:
        """
        Handle predefined quick actions. Returns True if handled, False if custom.
        """
        state = self.engine.state

        if action == "1":  # Look
            return True  # LLM will handle
        elif action == "2":  # Talk
            return True  # LLM will handle
        elif action == "3":  # Inventory
            print("\n[INVENTORY]")
            if state.player.inventory.items:
                for item, qty in state.player.inventory.items.items():
                    print(f"  {item}: {qty}")
            else:
                print("  (empty)")
            return False  # Don't call LLM
        elif action == "4":  # Quests
            print("\n[QUESTS]")
            if state.active_quests:
                for qid, quest in state.active_quests.items():
                    status = "✓ DONE" if quest.completed else "[ ]"
                    print(f"  {status} {quest.title}")
                    print(f"      {quest.description}")
            else:
                print("  (no active quests)")
            return False  # Don't call LLM
        elif action == "5":  # Rest
            return True  # LLM will handle
        elif action == "7":  # Save
            self.engine.state.save_to_file("data/save_state.json")
            print("[Game saved]")
            return False
        elif action == "8":  # Load
            try:
                self.engine.state = GameState.load_from_file("data/save_state.json")
                print("[Game loaded]")
            except Exception as e:
                print(f"[Load failed: {e}]")
            return False
        else:
            return True  # Custom action, let LLM handle

    def run_turn(self, player_action: str) -> bool:
        """
        Run a single game turn with structured JSON response.
        
        Returns: True if turn was successful, False otherwise.
        """
        state = self.engine.state

        # Quick action handling
        if player_action[0] in "12345678" or player_action.lower() in ["q"]:
            if not self.handle_quick_action(player_action):
                return True

        # Process turn in engine
        self.engine.process_turn(player_action)

        # Get DM response with retry logic
        system_prompt, user_prompt = DMPromptBuilder.construct_full_prompt(
            state, player_action
        )

        print("\n[Thinking...]")
        raw_response = self.llm.generate_dm_response_with_retry(
            system_prompt=system_prompt,
            game_context=DMPromptBuilder.game_context(state),
            player_input=player_action,
            temperature=0.8,
            max_retries=2,
        )

        # Parse JSON response
        parsed = ResponseParser.parse_response(raw_response)
        
        if not parsed:
            print("\n[WARNING] Could not parse LLM response, using fallback")
            parsed = ResponseParser.create_fallback_response(player_action)

        # Validate and sanitize
        is_valid, issues = ResponseValidator.validate_dm_response(parsed, state)
        if not is_valid:
            print(f"\n[WARNING] Response validation issues: {len(issues)} found")
            for issue in issues[:3]:  # Show first 3 issues
                print(f"  - {issue}")
            parsed = ResponseValidator.sanitize_effects(parsed, state)

        # Apply effects to game state
        effect_log = self.engine.apply_effects(parsed.effects)

        # Display narration
        print("\n" + "=" * 70)
        print("[DM]")
        print(parsed.narration)

        # Display NPC speeches
        if parsed.npc_speeches:
            print("\n" + "-" * 70)
            for npc_speech in parsed.npc_speeches:
                npc_name = state.npcs.get(npc_speech.npc_id, {}).get('name', npc_speech.npc_id)
                emotion_emoji = {
                    'friendly': '😊', 'joy': '😄', 'happy': '😊',
                    'angry': '😠', 'fear': '😨', 'sad': '😢',
                    'surprise': '😲', 'neutral': '😐',
                    'suspicious': '🤨', 'grateful': '🙏'
                }.get(npc_speech.emotion, '')
                
                print(f"{npc_name} {emotion_emoji}: \"{npc_speech.text}\"")

        # Display effects
        if effect_log:
            print("\n" + "-" * 70)
            print("[EFFECTS]")
            for log_entry in effect_log:
                print(f"  {log_entry}")

        # Display suggested options
        if parsed.suggested_options:
            print("\n" + "-" * 70)
            print("[SUGGESTIONS]")
            for i, option in enumerate(parsed.suggested_options, 1):
                print(f"  {i}. {option}")

        print("=" * 70)

        # Store narration for display on next turn
        state.last_narration = parsed.narration

        return True

    def main_loop(self):
        """Main game loop."""
        state = self.engine.state

        # Check LLM availability
        print("Checking LLM availability...")
        if not self.llm.is_available():
            print(
                f"[WARNING] Cannot connect to Ollama at {self.llm.base_url}"
            )
            print("Make sure Ollama is running: ollama serve")
            response = input("Continue anyway? (y/n): ").lower()
            if response != "y":
                return

        # Main loop
        while self.running:
            self.clear_screen()
            self.display_header()
            self.display_location()
            self.display_last_narration()
            self.display_player_status()
            self.display_menu()

            action = self.get_player_action()

            if not self.running:
                break

            if self.run_turn(action):
                input("\nPress Enter to continue...")
            else:
                input("\nPress Enter to continue...")

        print("\n[Game Over]")
