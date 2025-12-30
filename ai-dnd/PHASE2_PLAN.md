# Phase 2: Structured Outputs & State Management

**Status**: Ready to implement
**Estimated effort**: 6-8 hours
**Prerequisite**: Phase 1 complete (✓)

## Goals

Transform the DM from a "free-form narrator" into a system that:
1. Returns structured JSON with explicit effects
2. Updates game state deterministically
3. Validates and recovers from malformed responses
4. Makes the world feel responsive to actions

## Why Phase 2?

Currently:
- DM generates narration, but state updates are manual
- No linkage between action → narration → state change
- World feels static

After Phase 2:
- Player action → LLM generates JSON → Engine applies effects
- Moving to a location updates `current_location_id`
- Winning items adds them to inventory
- Completing quests marks them done
- NPC relationship changes persist

## Detailed Tasks

### Task 2.1: Define Response Schema

Create `engine/response_schema.py`:

```python
@dataclass
class NPCResponse:
    npc_id: str
    text: str
    emotion: str = "neutral"  # joy, fear, anger, etc.

@dataclass
class WorldEffect:
    location: Optional[str] = None      # Move player here
    time_delta: int = 5                 # Minutes
    hp_change: int = 0                  # + or -
    gold_change: int = 0
    new_items: List[str] = field(default_factory=list)
    new_quests: List[str] = field(default_factory=list)
    completed_quests: List[str] = field(default_factory=list)
    npc_relationship_changes: Dict[str, float] = field(default_factory=dict)

@dataclass  
class DMResponse:
    narration: str
    npc_speeches: List[NPCResponse] = field(default_factory=list)
    effects: WorldEffect = field(default_factory=WorldEffect)
    suggested_options: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
```

### Task 2.2: Update LLM Prompts

Modify `llm/prompts.py` to include:

```python
def json_output_format() -> str:
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
    "location": "tavern",
    "time_delta": 5,
    "hp_change": 0,
    "gold_change": 0,
    "new_items": [],
    "new_quests": [],
    "completed_quests": [],
    "npc_relationship_changes": {
      "bartender": 0.1
    }
  },
  "suggested_options": [
    "Ask about the town",
    "Order a drink",
    "Look around"
  ]
}

CRITICAL RULES:
- Always valid JSON
- npc_speeches must use npc_ids from the world
- Locations must exist in game world
- Relationships are -1.0 to 1.0
- Time can be negative (magic time skip)
- Never give impossible items or quests
"""
```

### Task 2.3: JSON Parser & Validator

Create `engine/response_parser.py`:

```python
class ResponseValidator:
    def validate_dm_response(self, response_json: dict, game_state: GameState) -> bool:
        """Check JSON is valid and values are reasonable."""
        # Check all NPC IDs exist
        # Check locations exist
        # Check relationships in range
        # etc.

    def sanitize_effects(self, effects: dict, game_state: GameState) -> dict:
        """Fix common issues in LLM output."""
        # Clamp relationships to [-1, 1]
        # Remove non-existent NPCs
        # Cap hp_change to reasonable amounts
        # etc.

    def parse_response(self, text: str) -> Optional[DMResponse]:
        """Parse JSON from LLM text, with fallback."""
        # Try JSON extract
        # Try JSON parsing
        # If fails, fallback to regex extraction
        # If still fails, return structured error
```

### Task 2.4: State Update Engine

Modify `engine/game_loop.py`:

```python
class GameEngine:
    def apply_effects(self, effects: WorldEffect, state: GameState) -> str:
        """Apply DM response effects to game state."""
        log = []

        if effects.location and effects.location in state.locations:
            state.current_location_id = effects.location
            log.append(f"Moved to {state.locations[effects.location].name}")

        if effects.time_delta:
            self.advance_time(effects.time_delta)
            log.append(f"Time advanced {effects.time_delta} minutes")

        if effects.hp_change:
            old_hp = state.player.hp
            state.player.hp = max(0, min(state.player.max_hp, state.player.hp + effects.hp_change))
            log.append(f"HP changed: {old_hp} → {state.player.hp}")

        if effects.gold_change:
            old_gold = state.player.gold
            state.player.gold = max(0, state.player.gold + effects.gold_change)
            log.append(f"Gold changed: {old_gold} → {state.player.gold}")

        # Apply new items, quests, relationship changes...

        return " | ".join(log)
```

### Task 2.5: Retry & Fallback Logic

Add to `llm/client.py`:

```python
def generate_dm_response_with_retry(
    self,
    system_prompt: str,
    game_context: str,
    player_input: str,
    temperature: float = 0.8,
    max_retries: int = 2,
) -> str:
    """Generate response with retry on invalid JSON."""
    for attempt in range(max_retries):
        response = self.generate(...)
        try:
            json_str = self._extract_json(response)
            json.loads(json_str)  # Validate
            return response
        except json.JSONDecodeError:
            if attempt < max_retries - 1:
                # Retry with lower temperature
                temperature *= 0.7
                continue
            else:
                # Fallback: return error response
                return self._fallback_response(player_input)

def _fallback_response(self, action: str) -> str:
    """Fallback response when LLM fails."""
    return json.dumps({
        "narration": f"Your action was: {action}. The world shimmers mysteriously.",
        "npc_speeches": [],
        "effects": {
            "location": None,
            "time_delta": 5,
            "hp_change": 0,
            "gold_change": 0,
            "new_items": [],
            "new_quests": [],
            "completed_quests": [],
            "npc_relationship_changes": {}
        },
        "suggested_options": ["What do you do next?"]
    })
```

### Task 2.6: Integration into CLI

Update `ui/cli.py`:

```python
def run_turn(self, player_action: str) -> bool:
    # Get JSON response from LLM
    system_prompt, user_prompt = DMPromptBuilder.construct_full_prompt(...)
    raw_response = self.llm.generate_dm_response(...)
    
    # Parse and validate
    parsed = ResponseParser.parse_response(raw_response)
    if not parsed:
        print("[ERROR] Invalid response format, using fallback")
        parsed = ResponseParser.create_fallback_response(player_action)
    
    # Validate world consistency
    if not ResponseValidator.validate_dm_response(parsed, self.engine.state):
        parsed = ResponseValidator.sanitize_effects(parsed, self.engine.state)
    
    # Apply effects
    effect_log = self.engine.apply_effects(parsed.effects, self.engine.state)
    
    # Display to player
    print(parsed.narration)
    for npc_speech in parsed.npc_speeches:
        npc_name = state.npcs[npc_speech.npc_id]["name"]
        print(f"{npc_name}: {npc_speech.text}")
    print(f"[Effects: {effect_log}]")
    
    return True
```

## Testing Checklist

- [ ] JSON schema validates against sample responses
- [ ] Parser extracts JSON from LLM text correctly
- [ ] Validator catches invalid locations/NPCs
- [ ] Sanitizer fixes edge cases
- [ ] State updates reflect effects
- [ ] Fallback response is valid JSON
- [ ] CLI displays parsed responses correctly
- [ ] Save/load preserves updated state

## Acceptance Criteria

✅ **Phase 2 is complete when:**

1. LLM generates JSON (not just text)
2. Every turn: action → JSON → state update
3. World state is visible and predictable
4. Player can see inventory change, relationships update, time advance
5. Game doesn't crash on malformed JSON (fallback works)
6. Save/load preserves all state changes

## Example Session (After Phase 2)

```
> I ask Mira for a job
[DM generates JSON with effects:]
{
  "narration": "Mira's eyes light up. 'Yes, actually. Bandits have been raiding the 
                merchant caravans. Bring me proof and there's coin in it.'",
  "npc_speeches": [
    {"npc_id": "bartender", "text": "Bring me proof and there's coin in it.", 
     "emotion": "hopeful"}
  ],
  "effects": {
    "new_quests": ["defeat_bandits"],
    "npc_relationship_changes": {"bartender": 0.2}
  }
}
[Engine applies effects:]
[New quest added: "Defeat the Bandits"]
[Mira's relationship improved: 0.0 → 0.2]
[Effects: Moved to tavern | Time advanced 5 minutes | New quest added]
```

## What Comes After

Once Phase 2 is solid, you're ready for:

- **Phase 3**: Multiple NPCs with distinct personalities
- **Phase 4**: Memory system so NPCs remember you
- **Phase 5**: True multi-agent NPCs with autonomous goals

## Commands to Know (Dev)

```bash
# Test JSON parsing
python -m pytest engine/test_response_parser.py

# Validate schema
python -c "from engine.response_schema import DMResponse; print(DMResponse.__doc__)"

# Test LLM retry
python -c "from llm.client import OllamaClient; c = OllamaClient(); c.generate_dm_response_with_retry(...)"
```

---

**Ready to start Phase 2?** Let me know and I'll implement all tasks!
