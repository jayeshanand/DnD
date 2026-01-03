# AI-Driven D&D Engine

A progressive, step-by-step implementation of an AI-powered Dungeons & Dragons world with autonomous NPCs, built from the ground up in Python.

## Phases

- **Phase 0** ✅ Foundations and Tech Choices - Complete!
- **Phase 1** ✅ Minimal Text-Only Single-DM Game - Complete!
- **Phase 2** ✅ Structured Outputs & State Management - Complete!
- **Phase 3** ✅ NPC Objects with Personalities & Conversation Memory - Complete!
- **Phase 4** ✅ Memory System for NPCs (Vector DB) - Complete! 🎉
- **Phase 5** ⏳ True Multi-Agent NPCs
- **Phase 6** ⏳ World Simulation & Factions
- **Phase 7** ⏳ Decision Policies & Heuristics
- **Phase 8** ⏳ Rich UI & Better UX
- **Phase 9** ⏳ Voice Input & TTS
- **Phase 10** ⏳ Polish, Scenarios & Testing

## What's New in Phase 4 🆕

**Long-Term Memory System**: NPCs now remember past interactions!

- 🧠 **Episodic Memories**: Events with emotion, importance, and decay
- 📚 **Semantic Memories**: Persistent facts about the player
- 🔍 **Vector Search**: ChromaDB integration for relevant memory retrieval
- ⏰ **Memory Decay**: Important memories last longer, minor ones fade
- 💾 **Persistence**: Memories save/load with game state
- 🎭 **Natural Dialogue**: NPCs reference past events naturally
- 📊 **Memory Viewer**: In-game command to view NPC memories

See [PHASE4_COMPLETE.md](docs/phases/PHASE4_COMPLETE.md) for details.

## Quick Start

### Prerequisites

- Python 3.8+
- Ollama running locally (`ollama serve`)

### Installation

```bash
cd ai-dnd
pip install -r requirements.txt

# Optional: Install memory system (Phase 4)
pip install chromadb sentence-transformers
```

### Running the Game

```bash
python main.py
```

The game will prompt you to:
1. Create a new character (or load existing)
2. Choose your class (Warrior, Rogue, Mage, Cleric)
3. Start playing in the text-based interface

### Ollama Setup

If you don't have Ollama installed:

1. Download from https://ollama.ai
2. Run: `ollama serve`
3. In another terminal: `ollama pull llama2` (or another model)

The game will warn if Ollama isn't available but let you continue with simulated responses.

## Architecture (current)

```
ai-dnd/
├── main.py                 # Entry point
├── config/
│   └── settings.yaml       # Configuration
├── engine/
│   ├── state.py           # Game state models
│   └── game_loop.py       # Main game loop
├── llm/
│   ├── client.py          # Ollama HTTP client
│   └── prompts.py         # DM prompt templates
├── ui/
│   └── cli.py             # Command-line interface
├── data/
│   ├── locations.json     # World map
│   ├── npcs.json          # NPC definitions
│   ├── factions.json      # Faction data
│   ├── items.json         # Item definitions
│   └── rules.json         # Game rules
│   └── save_state.json    # Previously played game's saved status
├── agents/                 # (Phase 5+) NPC agents
├── world/                  # (Phase 6+) World simulation
├── memory/                 # (Phase 4+) Memory systems
├── docs/
│   └── phases/             # Phase plans and writeups
├── tests/                  # Test suites (phase and commerce tests)
└── logs/                   # Game session logs
```

## Features

- Structured JSON DM responses for deterministic state updates
- NPC personalities (archetypes, speech styles, values, fears, goals) and mood-aware dialogue
- Conversation history (recent turns stored; included in prompts for coherence)
- Relationship tracking and basic commerce rules (state price → deduct gold → deliver item; duplicate-purchase warnings)
- Inventory, quests, locations, and time advancement
- Save/Load full game state (including conversation history)
- CLI with emotion-aware NPC dialogue display

## Game Controls

While playing, use these commands:

- `1` - Look around
- `2` - Talk to someone
- `3` - Check inventory
- `4` - Check quests
- `5` - Rest
- `6` - Custom action (type anything)
- `7` - Save game
- `8` - Load game
- `q` - Quit
- `help` - Show menu

You can also type free-form actions like "I swing my sword at the goblin" or "I ask Mira about the bandits".

## Customization

### Change the LLM Model

Edit `main.py` or pass different parameters:

```python
llm = OllamaClient(
    base_url="http://localhost:11434",
    model="mistral"  # or "neural-chat", "wizard-vicuna", etc.
)
```

- You can also adjust sampling in `llm/client.py` (temperature, top_p, max_tokens) for more creative vs. safer outputs.
- Point to a remote Ollama host by changing `base_url` in `config/settings.yaml`.

### Add NPCs

Edit `data/npcs.json` and add a new entry with personality, goals, etc.

- Include `personality_traits` (archetype, temperament, speech_style, values, fears, quirks), `current_goal`, and optional `mood`.
- Set `current_location` to place the NPC in a location’s `npcs` list inside `data/locations.json`.

### Add Locations

Edit `data/locations.json` with new location descriptions and connections.

- Add exits (direction → location_id), and list `npcs` and `items` present.
- Keep IDs lowercase_with_underscores to match prompts and validation.

### Add Items and Prices

Edit `data/items.json` to add trade goods, consumables, or gear:

```json
"healing_potion": {
    "id": "healing_potion",
    "name": "Healing Potion",
    "description": "Restores some health",
    "weight": 0.5,
    "value": 25
}
```

- `value` is the gold price used by NPCs; ensure prices are sensible (food 2–5g, supplies 5–20g, weapons 30–100g, potions 20–50g).
- Commerce logic expects gold to be deducted before granting items.

### Tune Prompts and Context

- `llm/prompts.py` controls the system prompt, JSON schema, and context building.
- To reduce prompt length, lower `max_history_turns` in `game_context` or trim NPC details.
- To emphasize safety or determinism, lower temperature in `OllamaClient.generate_dm_response_with_retry`.

### Adjust Saving/Loading

- Saves default to `data/save_state.json`; change the path when calling `save_to_file` / `load_from_file`.
- Conversation history is included in saves; inventory and quests are persisted as well.

## Development Notes

### Design Philosophy

- **Incremental**: Complete each phase before moving to the next
- **Playable**: After each phase, you have a working game
- **Modular**: Each component (LLM, UI, engine) is independent
- **Extensible**: Easy to add features without major refactoring

### Error Handling

If Ollama isn't available:
- The game will warn but continue
- LLM responses will be simulated or error messages shown
- You can still play with basic mechanics

### Saving State

- Auto-saves every 5 turns (configurable)
- Manual save with command `7`
- State includes player, locations, NPCs, quests
- Conversation history already saves; long-term memories arrive in Phase 4+

## Future Enhancements

- Vector database for NPC memories
- Faction warfare simulation
- RL-based NPC decision making
- Web UI with FastAPI
- Voice input/output (Whisper + TTS)
- Multi-player support
- Procedural content generation

## License

MIT
