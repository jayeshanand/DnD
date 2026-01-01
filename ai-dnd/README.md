# AI-Driven D&D Engine

A progressive, step-by-step implementation of an AI-powered Dungeons & Dragons world with autonomous NPCs, built from the ground up in Python.

## Phases

- **Phase 0** ✅ Foundations and Tech Choices - Complete!
- **Phase 1** ✅ Minimal Text-Only Single-DM Game - Complete!
- **Phase 2** ✅ Structured Outputs & State Management - Complete!
- **Phase 3** ✅ NPC Objects with Personalities & Conversation Memory - Complete!
- **Phase 4** ⏳ Memory System for NPCs (Vector DB)
- **Phase 5** ⏳ True Multi-Agent NPCs
- **Phase 6** ⏳ World Simulation & Factions
- **Phase 7** ⏳ Decision Policies & Heuristics
- **Phase 8** ⏳ Rich UI & Better UX
- **Phase 9** ⏳ Voice Input & TTS
- **Phase 10** ⏳ Polish, Scenarios & Testing

## Latest: Phase 3 Complete! 🎉

**NPCs Now Have Personalities and Remember Conversations!**

- 5 distinct NPCs with full personality profiles (archetypes, values, fears)
- Conversation history system (last 10 turns stored, last 5 in context)
- NPCs speak in character based on their personality
- Enhanced dialogue display with emotions and emojis
- Relationship tracking affects future interactions

See [PHASE3_COMPLETE.md](PHASE3_COMPLETE.md) for details.

## Quick Start

### Prerequisites

- Python 3.8+
- Ollama running locally (`ollama serve`)

### Installation

```bash
cd ai-dnd
pip install -r requirements.txt
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

## Architecture

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
├── agents/                 # (Phase 5+) NPC agents
├── world/                  # (Phase 6+) World simulation
├── memory/                 # (Phase 4+) Memory systems
└── logs/                   # Game session logs
```

## Current Features (Phase 1)

- ✓ Persistent game state (save/load to JSON)
- ✓ Rich location descriptions
- ✓ NPC definitions with personalities
- ✓ Inventory system
- ✓ Quest framework
- ✓ AI DM via Ollama
- ✓ Turn-based game loop
- ✓ Player status display

## Next Steps (Phase 2)

- Structured JSON outputs from LLM
- State validation engine
- More deterministic world updates
- Better error handling

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

### Add NPCs

Edit `data/npcs.json` and add a new entry with personality, goals, etc.

### Add Locations

Edit `data/locations.json` with new location descriptions and connections.

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
- Memories will be saved in Phase 4+

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
