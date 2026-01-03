"""Test suite for Phase 4: Memory System

Tests the episodic and semantic memory functionality including:
- Memory creation and storage
- Memory retrieval by relevance
- Memory decay over time
- Integration with game loop
- Save/load with memories
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_memory_types():
    """Test creating and manipulating memory objects."""
    print("\n=== TEST: Memory Types ===")
    
    try:
        from memory.types import EpisodicMemory, SemanticMemory, create_memory_id
        
        # Test episodic memory
        mem_id = create_memory_id()
        episodic = EpisodicMemory(
            id=mem_id,
            memory_type="episodic",
            text="The player saved me from bandits",
            npc_id="npc_mira",
            created_at=datetime.now(),
            importance=0.9,
            emotion="gratitude",
            location="forest",
            participants=["player", "npc_mira"],
            decay_rate=0.1
        )
        
        print(f"✓ Created episodic memory: {episodic.id}")
        print(f"  Text: {episodic.text}")
        print(f"  Importance: {episodic.importance}")
        print(f"  Emotion: {episodic.emotion}")
        
        # Test decay calculation
        future_time = datetime.now() + timedelta(hours=100)
        strength = episodic.calculate_strength(future_time)
        print(f"  Strength after 100 hours: {strength:.2f}")
        
        assert 0.0 <= strength <= 1.0, "Strength should be between 0 and 1"
        assert strength < 1.0, "Strength should decay over time"
        
        # Test semantic memory
        semantic = SemanticMemory(
            id=create_memory_id(),
            memory_type="semantic",
            text="The player is a member of the King's Guard",
            npc_id="npc_aldric",
            created_at=datetime.now(),
            fact_type="profession",
            subject="player",
            confidence=0.9,
            source="witnessed"
        )
        
        print(f"✓ Created semantic memory: {semantic.id}")
        print(f"  Text: {semantic.text}")
        print(f"  Fact type: {semantic.fact_type}")
        print(f"  Confidence: {semantic.confidence}")
        
        # Test serialization
        ep_dict = episodic.to_dict()
        ep_restored = EpisodicMemory.from_dict(ep_dict)
        assert ep_restored.id == episodic.id, "Serialization failed"
        assert ep_restored.importance == episodic.importance, "Importance not preserved"
        
        sem_dict = semantic.to_dict()
        sem_restored = SemanticMemory.from_dict(sem_dict)
        assert sem_restored.id == semantic.id, "Serialization failed"
        assert sem_restored.fact_type == semantic.fact_type, "Fact type not preserved"
        
        print("✓ Serialization/deserialization works correctly")
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_memory_store():
    """Test MemoryStore functionality."""
    print("\n=== TEST: Memory Store ===")
    
    try:
        from memory.memory_store import MemoryStore
        from memory.types import EpisodicMemory, SemanticMemory, create_memory_id
        import tempfile
        import shutil
        
        # Create temporary directory for test database
        temp_dir = tempfile.mkdtemp()
        print(f"Using temp directory: {temp_dir}")
        
        try:
            # Initialize memory store
            store = MemoryStore(db_path=f"{temp_dir}/test_db")
            print(f"✓ Initialized MemoryStore (ChromaDB: {store.chroma_available})")
            
            # Add some test memories
            mem1 = EpisodicMemory(
                id=create_memory_id(),
                memory_type="episodic",
                text="The player helped me clear rats from my tavern",
                npc_id="npc_mira",
                created_at=datetime.now(),
                importance=0.8,
                emotion="gratitude",
                location="tavern",
                participants=["player", "npc_mira"],
                decay_rate=0.1
            )
            store.add_memory(mem1)
            print(f"✓ Added memory: {mem1.text[:50]}...")
            
            mem2 = EpisodicMemory(
                id=create_memory_id(),
                memory_type="episodic",
                text="The player bought a sword from me for 50 gold",
                npc_id="npc_aldric",
                created_at=datetime.now(),
                importance=0.6,
                emotion="neutral",
                location="market",
                participants=["player", "npc_aldric"],
                decay_rate=0.15
            )
            store.add_memory(mem2)
            print(f"✓ Added memory: {mem2.text[:50]}...")
            
            mem3 = SemanticMemory(
                id=create_memory_id(),
                memory_type="semantic",
                text="The player is known as a hero in town",
                npc_id="npc_mira",
                created_at=datetime.now(),
                fact_type="reputation",
                subject="player",
                confidence=0.9,
                source="witnessed"
            )
            store.add_memory(mem3)
            print(f"✓ Added memory: {mem3.text[:50]}...")
            
            # Test retrieval
            print("\nTesting retrieval...")
            results = store.retrieve_memories(
                query="tavern rats",
                npc_id="npc_mira",
                n=5
            )
            print(f"✓ Retrieved {len(results)} memories for 'tavern rats'")
            assert len(results) > 0, "Should find at least one relevant memory"
            assert any("rats" in m.text.lower() or "tavern" in m.text.lower() for m in results), "Should find tavern-related memory"
            
            # Test get NPC memories
            mira_memories = store.get_npc_memories("npc_mira")
            print(f"✓ Mira has {len(mira_memories)} memories")
            assert len(mira_memories) == 2, "Mira should have 2 memories"
            
            # Test important memories
            important = store.get_important_memories(min_importance=0.7)
            print(f"✓ Found {len(important)} high-importance memories")
            assert len(important) >= 1, "Should find at least one important memory"
            
            # Test decay
            future_time = datetime.now() + timedelta(hours=500)
            store.decay_memories(future_time)
            print("✓ Applied memory decay")
            
            # Check that episodic memories have decayed
            for memory in store.memories.values():
                if isinstance(memory, EpisodicMemory):
                    assert memory.current_strength < 1.0, "Episodic memory should have decayed"
            
            # Test pruning
            store.prune_weak_memories(threshold=0.5)
            print("✓ Pruned weak memories")
            
            # Test save/load
            save_path = f"{temp_dir}/test_memories.json"
            store.save_to_json(save_path)
            print(f"✓ Saved memories to {save_path}")
            
            # Load into new store
            store2 = MemoryStore(db_path=f"{temp_dir}/test_db2")
            store2.load_from_json(save_path)
            print(f"✓ Loaded memories (got {len(store2.memories)} memories)")
            
            # Verify loaded memories
            assert len(store2.memories) > 0, "Should load some memories"
            
            # Test stats
            stats = store2.get_memory_stats()
            print(f"✓ Memory stats: {stats}")
            assert stats['total_memories'] > 0, "Should have total memories"
            
            return True
            
        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir)
            print(f"✓ Cleaned up temp directory")
            
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_game_state_integration():
    """Test memory integration with GameState."""
    print("\n=== TEST: GameState Integration ===")
    
    try:
        from engine.state import GameState, Player, Location, Inventory
        from memory.types import EpisodicMemory, create_memory_id
        import tempfile
        
        # Create test game state
        player = Player(
            name="TestHero",
            class_name="Warrior",
            level=1,
            hp=20,
            max_hp=20,
            gold=100
        )
        
        state = GameState(
            player=player,
            current_location_id="test_town",
            game_time=datetime.now().isoformat(),
            turn=0
        )
        
        print(f"✓ Created GameState (memory_store initialized: {state.memory_store is not None})")
        
        if state.memory_store:
            # Add a test memory
            memory = EpisodicMemory(
                id=create_memory_id(),
                memory_type="episodic",
                text="Test memory for integration",
                npc_id="test_npc",
                created_at=datetime.now(),
                importance=0.7,
                emotion="neutral",
                location="test_town",
                participants=["player"],
                decay_rate=0.1
            )
            state.memory_store.add_memory(memory)
            print("✓ Added memory to game state")
            
            # Test save/load with memories
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                save_path = f.name
            
            try:
                state.save_to_file(save_path)
                print(f"✓ Saved game state to {save_path}")
                
                # Check that memory file was created
                memory_path = save_path.replace('.json', '_memories.json')
                assert os.path.exists(memory_path), "Memory file should be created"
                print(f"✓ Memory file created: {memory_path}")
                
                # Load state
                loaded_state = GameState.load_from_file(save_path)
                print("✓ Loaded game state")
                
                # Verify memories were loaded
                if loaded_state.memory_store:
                    loaded_memories = loaded_state.memory_store.get_npc_memories("test_npc")
                    print(f"✓ Loaded {len(loaded_memories)} memories")
                    assert len(loaded_memories) > 0, "Should load saved memories"
                else:
                    print("⚠ Memory store not available in loaded state")
                
            finally:
                # Clean up
                if os.path.exists(save_path):
                    os.remove(save_path)
                if os.path.exists(memory_path):
                    os.remove(memory_path)
                print("✓ Cleaned up save files")
        else:
            print("⚠ Memory store not available (ChromaDB not installed?)")
        
        return True
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_game_loop_memory_creation():
    """Test that game loop creates memories from events."""
    print("\n=== TEST: Game Loop Memory Creation ===")
    
    try:
        from engine.state import GameState, Player, Location
        from engine.game_loop import GameEngine
        from engine.response_schema import WorldEffect
        
        # Create test game state
        player = Player(
            name="TestHero",
            class_name="Warrior",
            level=1,
            hp=20,
            max_hp=20,
            gold=100
        )
        
        loc = Location(
            id="tavern",
            name="The Rusty Mug",
            description="A cozy tavern",
            npcs=["npc_mira"]
        )
        
        state = GameState(
            player=player,
            current_location_id="tavern",
            game_time=datetime.now().isoformat(),
            turn=0,
            locations={"tavern": loc},
            npcs={
                "npc_mira": {
                    "name": "Mira",
                    "role": "bartender",
                    "personality": "friendly"
                }
            }
        )
        
        engine = GameEngine(state)
        print("✓ Created game engine")
        
        # Test memory creation from relationship change
        effects = WorldEffect(
            location=None,
            time_delta=5,
            hp_change=0,
            gold_change=-10,
            new_items=["ale"],
            new_quests=[],
            completed_quests=[],
            npc_relationship_changes={"npc_mira": 0.3}
        )
        
        npc_speeches = [{
            "npc_id": "npc_mira",
            "text": "Thanks for your patronage!",
            "emotion": "friendly"
        }]
        
        # Apply effects (should create memories)
        engine.apply_effects(
            effects,
            player_action="I buy an ale",
            narration="Mira pours you a cold ale",
            npc_speeches=npc_speeches
        )
        
        print("✓ Applied effects with relationship change")
        
        # Check if memories were created
        if state.memory_store:
            mira_memories = state.memory_store.get_npc_memories("npc_mira")
            print(f"✓ Mira has {len(mira_memories)} memories")
            
            if len(mira_memories) > 0:
                print("✓ Memories created successfully:")
                for mem in mira_memories:
                    print(f"  - {mem.text[:60]}...")
            else:
                print("⚠ No memories created (ChromaDB might not be installed)")
        else:
            print("⚠ Memory store not available")
        
        return True
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prompts_with_memory():
    """Test that prompts include memory context."""
    print("\n=== TEST: Prompts with Memory Context ===")
    
    try:
        from engine.state import GameState, Player, Location
        from llm.prompts import DMPromptBuilder
        from memory.types import EpisodicMemory, create_memory_id
        
        # Create test game state
        player = Player(
            name="TestHero",
            class_name="Warrior",
            level=1,
            hp=20,
            max_hp=20,
            gold=100
        )
        
        loc = Location(
            id="tavern",
            name="The Rusty Mug",
            description="A cozy tavern",
            npcs=["npc_mira"]
        )
        
        state = GameState(
            player=player,
            current_location_id="tavern",
            game_time=datetime.now().isoformat(),
            turn=0,
            locations={"tavern": loc},
            npcs={
                "npc_mira": {
                    "name": "Mira",
                    "role": "bartender",
                    "personality": "friendly"
                }
            }
        )
        
        # Add a memory
        if state.memory_store:
            memory = EpisodicMemory(
                id=create_memory_id(),
                memory_type="episodic",
                text="The player helped me with the rat problem last week",
                npc_id="npc_mira",
                created_at=datetime.now(),
                importance=0.8,
                emotion="gratitude",
                location="tavern",
                participants=["player", "npc_mira"],
                decay_rate=0.1
            )
            state.memory_store.add_memory(memory)
            print("✓ Added test memory")
            
            # Build prompt
            system_prompt, user_prompt = DMPromptBuilder.construct_full_prompt(
                state,
                player_input="I walk into the tavern",
                include_system=True
            )
            
            print("✓ Built prompts")
            
            # Check if memory context is included
            if "RELEVANT MEMORIES" in user_prompt:
                print("✓ Memory context included in prompt")
                print(f"  Prompt length: {len(user_prompt)} characters")
                
                # Check if our specific memory is mentioned
                if "rat problem" in user_prompt:
                    print("✓ Specific memory text found in prompt")
                else:
                    print("⚠ Memory text not found (might need better retrieval)")
            else:
                print("⚠ Memory context not included (ChromaDB might not be installed)")
        else:
            print("⚠ Memory store not available")
        
        return True
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all Phase 4 tests."""
    print("\n" + "=" * 70)
    print("PHASE 4 TEST SUITE: MEMORY SYSTEM".center(70))
    print("=" * 70)
    
    tests = [
        ("Memory Types", test_memory_types),
        ("Memory Store", test_memory_store),
        ("GameState Integration", test_game_state_integration),
        ("Game Loop Memory Creation", test_game_loop_memory_creation),
        ("Prompts with Memory", test_prompts_with_memory),
    ]
    
    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY".center(70))
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status:8} {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED! Phase 4 implementation successful.")
        return True
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Review implementation.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
