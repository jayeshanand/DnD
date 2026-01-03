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
        print("  (9) View memories (Phase 4)")
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
        elif action == "9":  # View memories (Phase 4)
            self.display_memories()
            return False
        else:
            return True  # Custom action, let LLM handle
    
    def display_memories(self):
        """Display memories for NPCs in current location (Phase 4)."""
        state = self.engine.state
        
        # Check if memory system is available
        try:
            from memory.memory_store import MemoryStore
            from memory.types import EpisodicMemory, SemanticMemory
        except ImportError:
            print("\n[MEMORIES] Memory system not available. Install with: pip install chromadb sentence-transformers")
            return
        
        if not state.memory_store:
            print("\n[MEMORIES] Memory system not initialized.")
            return
        
        location = self.engine.get_current_location()
        if not location or not location.npcs:
            print("\n[MEMORIES] No NPCs present to have memories.")
            return
        
        print("\n" + "=" * 70)
        print("NPC MEMORIES".center(70))
        print("=" * 70)
        
        # Get memory stats
        stats = state.memory_store.get_memory_stats()
        print(f"\nTotal memories: {stats['total_memories']} (Episodic: {stats['episodic_memories']}, Semantic: {stats['semantic_memories']})")
        print(f"ChromaDB: {'Enabled' if stats['chromadb_enabled'] else 'Disabled'}")
        
        # Show memories for each NPC present
        for npc_id in location.npcs:
            if npc_id not in state.npcs:
                continue
            
            npc_name = state.npcs[npc_id].get('name', npc_id)
            memories = state.memory_store.get_npc_memories(npc_id)
            
            if memories:
                print(f"\n--- {npc_name}'s Memories ({len(memories)}) ---")
                
                # Sort by importance/confidence
                episodic_mems = [m for m in memories if isinstance(m, EpisodicMemory)]
                semantic_mems = [m for m in memories if isinstance(m, SemanticMemory)]
                
                episodic_mems.sort(key=lambda m: m.importance * m.current_strength, reverse=True)
                semantic_mems.sort(key=lambda m: m.confidence, reverse=True)
                
                if episodic_mems:
                    print("\nEpisodic Memories (experiences):")
                    for mem in episodic_mems[:5]:  # Show top 5
                        emotion_icon = {"gratitude": "🙏", "fear": "😨", "anger": "😠", 
                                       "joy": "😊", "sadness": "😢", "neutral": "😐"}.get(mem.emotion, "")
                        strength_pct = int(mem.current_strength * 100)
                        importance = "⭐" * int(mem.importance * 3)
                        print(f"  {emotion_icon} [{importance} {strength_pct}%] {mem.text}")
                
                if semantic_mems:
                    print("\nSemantic Memories (facts):")
                    for mem in semantic_mems[:5]:  # Show top 5
                        confidence_pct = int(mem.confidence * 100)
                        print(f"  📝 [{mem.fact_type}, {confidence_pct}%] {mem.text}")
            else:
                print(f"\n--- {npc_name} has no memories yet ---")
        
        print("\n" + "=" * 70)

    def confirm_effects(self, effects, state: GameState) -> bool:
        """Ask the player to confirm costly effects before applying them."""
        costs = []

        if effects.gold_change < 0:
            costs.append(f"Spend {-effects.gold_change} gold")

        if effects.hp_change < 0:
            costs.append(f"Lose {-effects.hp_change} HP")

        negative_relationships = {
            npc_id: delta for npc_id, delta in effects.npc_relationship_changes.items()
            if delta < 0
        }
        if negative_relationships:
            names = [state.npcs.get(nid, {}).get("name", nid) for nid in negative_relationships]
            costs.append(f"Relationship drops with {', '.join(names)}")

        if not costs:
            return True

        print("\n[CONFIRM] This action will:")
        for cost in costs:
            print(f"  - {cost}")

        while True:
            choice = input("Proceed? (y/n): ").strip().lower()
            if choice in ("y", "yes"):
                return True
            if choice in ("n", "no", ""):
                return False
            print("Please type 'y' or 'n'.")

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

        # Confirm effects; if declined, abort turn without changes or narration
        if not self.confirm_effects(parsed.effects, state):
            print("\n[INFO] Action canceled; nothing happens.")
            return True

        # Process turn and apply effects to game state
        self.engine.process_turn(player_action)
        effect_log = self.engine.apply_effects(
            parsed.effects,
            player_action=player_action,
            narration=parsed.narration,
            npc_speeches=[speech.__dict__ for speech in parsed.npc_speeches]
        )

        # Display narration
        print("\n" + "=" * 70)
        print("[DM]")
        print(parsed.narration)

        # Display NPC speeches
        if parsed.npc_speeches:
            print("\n" + "-" * 70)
            for npc_speech in parsed.npc_speeches:
                npc_name = state.npcs.get(npc_speech.npc_id, {}).get('name', npc_speech.npc_id)
                
                # Enhanced emotion emojis
                emotion_emoji = {
                    'friendly': '😊', 'joy': '😄', 'happy': '😊', 'cheerful': '😀',
                    'angry': '😠', 'furious': '😡', 'annoyed': '😒',
                    'fear': '😨', 'worried': '😟', 'nervous': '😰',
                    'sad': '😢', 'melancholy': '😔', 'depressed': '😞',
                    'surprise': '😲', 'shocked': '😱', 'amazed': '🤩',
                    'neutral': '😐', 'calm': '😌',
                    'suspicious': '🤨', 'distrustful': '🧐',
                    'grateful': '🙏', 'thankful': '🥰',
                    'gruff': '😤', 'stern': '😑',
                    'curious': '🤔', 'interested': '👀',
                    'confused': '😕', 'puzzled': '🤷',
                    'excited': '🤗', 'enthusiastic': '😆',
                    'secretive': '🤫', 'mysterious': '🎭',
                    'compassionate': '🥺', 'caring': '💝'
                }.get(npc_speech.emotion.lower(), '💬')
                
                # Get NPC's personality archetype for styling
                archetype = ""
                if npc_speech.npc_id in state.npcs:
                    traits = state.npcs[npc_speech.npc_id].get('personality_traits', {})
                    archetype = traits.get('archetype', '')
                
                # Display with emotion and archetype context
                print(f"\n{npc_name} {emotion_emoji} [{npc_speech.emotion}]")
                print(f'  "{npc_speech.text}"')
                
                # Add visual separator for multiple NPCs
                if len(parsed.npc_speeches) > 1:
                    print()

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
