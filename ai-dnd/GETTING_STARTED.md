# 🐉 AI-Driven D&D Engine: Getting Started

**Status**: ✅ Phase 0 & Phase 1 Complete and Ready to Play

Welcome! You now have a fully functional AI-powered D&D engine. Here's what you have and how to use it.

## What You Have

A complete **text-based RPG framework** with:
- 🎮 Turn-based game loop
- 🤖 AI Dungeon Master via Ollama (local LLM)
- 🗺️ 8 explorable locations
- 👥 3 NPCs with personalities
- 📦 Inventory system
- ⚔️ Quest framework
- 💾 Save/load system
- 📊 Character progression

**Total**: ~1500 lines of Python code, ready to extend.

---

## 5-Minute Quick Start

### Step 1: Install Ollama
- Download: https://ollama.ai
- Install and run: `ollama serve`
- In new terminal: `ollama pull llama2`

### Step 2: Install Dependencies
```bash
cd "Python dev/D&D/ai-dnd"
pip install requests pyyaml pydantic
```

### Step 3: Play!
```bash
python main.py
```

Then:
1. Choose "Create new game"
2. Enter your name and pick a class
3. Start typing actions!

### Example Actions
```
> I ask the bartender about bandits
> I explore the forest
> I try to intimidate the merchant
> I rest for a bit
> I check my inventory
```

The AI will respond with rich narration. Have fun! 🎲

---

## File Structure

```
ai-dnd/
├── main.py                  ← START HERE
├── config/settings.yaml     ← LLM & game settings
├── engine/
│   ├── state.py            ← GameState, Player, Location, Quest models
│   └── game_loop.py        ← Turn processing & state updates
├── llm/
│   ├── client.py           ← Ollama HTTP client
│   └── prompts.py          ← DM system prompt templates
├── ui/
│   └── cli.py              ← Terminal interface
├── data/                    ← YOUR WORLD DATA (edit these!)
│   ├── locations.json      ← Map, locations, connections
│   ├── npcs.json           ← NPCs, personalities, relationships
│   ├── factions.json       ← Factions, goals, resources
│   ├── items.json          ← Item definitions
│   └── rules.json          ← Game rules & balance
├── agents/                  ← Phase 5+: autonomous NPC agents
├── world/                   ← Phase 6+: world simulation
├── memory/                  ← Phase 4+: NPC memory systems
└── logs/                    ← Session logs

Documentation:
├── README.md               ← Architecture & features
├── QUICKSTART.md           ← Installation & playing guide
├── ROADMAP.md              ← Full 10-phase implementation plan
└── PHASE2_PLAN.md          ← Detailed Phase 2 design
```

---

## Key Features

### 🎮 Game Loop
```
Display Location
  ↓
Show Last Narration
  ↓
Display Player Status
  ↓
Get Your Action
  ↓
Send to AI DM (Ollama)
  ↓
AI Generates Narrative
  ↓
Time Advances
  ↓
Repeat
```

### 💾 Save System
- Auto-save every 5 turns (configurable)
- Manual save with command `7`
- Load with command `8`
- Full state preserved (player, world, quests)

### 🤖 AI DM Features
- Contextual narration (knows your location, inventory, quests)
- Free-form action interpretation
- Responsive to your decisions
- Uses local Ollama (no API keys needed!)

### 🗺️ World
- 8 locations to explore
- 3 NPCs to interact with
- 2 factions with goals
- Dynamic exits and connections

---

## How to Customize Right Now

### Change the LLM Model

In `main.py`, line ~180:
```python
llm = OllamaClient(
    base_url="http://localhost:11434",
    model="mistral"  # Change this!
)
```

Available models:
- `llama2` (default, balanced)
- `mistral` (faster, 7B)
- `neural-chat` (conversational)
- `wizard-vicuna` (13B, better reasoning)
- `orca-mini` (3B, lightweight)

### Adjust Creativity

In `llm/prompts.py`, change temperature:
```python
temperature=0.5  # More consistent
temperature=0.8  # Balanced (default)
temperature=1.2  # More creative/chaotic
```

### Add a New Location

1. Edit `data/locations.json`
2. Add your location object:
```json
"dark_cave": {
  "id": "dark_cave",
  "name": "Dark Cave",
  "description": "A cave entrance with an eerie glow...",
  "exits": {
    "out": "forest_entrance"
  },
  "npcs": [],
  "items": []
}
```

3. Connect it from another location:
```json
"forest_entrance": {
  ...
  "exits": {
    "south": "town_square",
    "cave": "dark_cave"  ← Add this
  }
}
```

### Add a New NPC

1. Edit `data/npcs.json`
2. Add NPC:
```json
"mysterious_wizard": {
  "id": "mysterious_wizard",
  "name": "Elara the Sage",
  "role": "wizard",
  "personality": "mysterious, wise, speaks in riddles",
  "faction": "mages",
  "goals": ["seek knowledge", "find lost artifacts"],
  "traits": {
    "courage": 0.3,
    "honor": 0.7,
    "intelligence": 1.0,
    "charisma": 0.6
  },
  "relationship_to_player": 0.0,
  "description": "An old woman with piercing eyes and flowing robes",
  "dialogue_sample": "Ah, you seek wisdom..."
}
```

3. Place them in a location (add to `npcs` list in location)

---

## Game Commands

While playing:

```
1 - Look around (triggers narration)
2 - Talk to someone
3 - Check inventory
4 - Check active quests
5 - Rest (advance time)
6 - Custom action (type your own)
7 - Save game
8 - Load game
q - Quit
help - Show menu
```

Or type **anything** (command 6):
- "I pick up the torch"
- "I demand gold from the merchant"
- "I cast a fireball"
- "I seduce the bartender"
- "I investigate the strange noise"

---

## Troubleshooting

### "Cannot connect to Ollama"
- Make sure Ollama is running: `ollama serve`
- Default URL is `http://localhost:11434`
- Game will work without it (with simulated responses)

### "ModuleNotFoundError: No module named 'requests'"
```bash
pip install -r requirements.txt
```

### "Game is slow"
- Models vary in speed: mistral < llama2 < wizard-vicuna
- Try `mistral` or `neural-chat` for faster responses
- Reduce `max_tokens` in `config/settings.yaml`

### "I want more content"
- Add locations to `data/locations.json`
- Add NPCs to `data/npcs.json`
- Write better descriptions
- See PHASE2_PLAN.md for structured content

---

## Next Steps: Where to Go

### Option A: Play & Customize (Now)
1. Run the game several times
2. Edit data files to add your own world
3. Experiment with different LLM models
4. Invite friends to play (one controls party, reads narration)

### Option B: Implement Phase 2 (Next Week)
Phase 2 adds **structured game updates** so:
- Actions change game state predictably
- NPCs relationships track and change
- Quest completion is guaranteed
- Inventory changes are visible

See `PHASE2_PLAN.md` for full details.

### Option C: Go Deeper (2+ Weeks)
Full roadmap in `ROADMAP.md` takes you from:
- Single DM → Multiple independent NPC agents
- Static world → Living world with faction conflicts
- Text only → Rich UI + voice I/O
- Sandbox → Full campaign with story

---

## Architecture Overview

### How It Works

```python
# You type action
"I talk to Mira"

# CLI passes to engine
engine.process_turn("I talk to Mira")

# Prompt builder creates context
system_prompt = "You are a DM..."
user_prompt = "[GameState context]\nPlayer: Talk to Mira"

# Ollama generates response
dm_response = llm.generate_dm_response(system_prompt, user_prompt)

# Response is stored and displayed
state.last_narration = dm_response
print(dm_response)

# Turn advances, state persists
state.turn += 1
state.game_time = now + 5 minutes
```

### Key Classes

**GameState** (`engine/state.py`):
- Holds all world data
- Player character info
- Locations, NPCs, quests
- Save/load methods

**GameEngine** (`engine/game_loop.py`):
- Processes turns
- Advances time
- Manages state transitions

**OllamaClient** (`llm/client.py`):
- Calls Ollama HTTP API
- Handles timeouts/errors
- Retry logic

**GameCLI** (`ui/cli.py`):
- Displays locations, status
- Gets player input
- Shows responses

---

## Development Philosophy

This project follows these principles:

1. **Modular**: Each component (engine, LLM, UI) works independently
2. **Data-driven**: World content in JSON, not hardcoded
3. **Incremental**: Each phase adds features without breaking existing ones
4. **Playable**: Stop after any phase and have a working game
5. **Extensible**: Easy to add memory, agents, world simulation later

---

## Resources

### Ollama Models
- https://ollama.ai/library
- Try: `llama2`, `mistral`, `neural-chat`

### Python Docs
- Dataclasses: https://docs.python.org/3/library/dataclasses.html
- JSON: https://docs.python.org/3/library/json.html

### Prompt Engineering
- System prompts define behavior
- Context includes world state
- Few-shot examples improve consistency

---

## What Comes Next (Optionally)

| Phase | Feature | Effort | Value |
|-------|---------|--------|-------|
| 2 | Structured JSON output | 6h | High - game feels more responsive |
| 3 | Rich NPC personalities | 5h | High - NPCs feel distinct |
| 4 | NPC memory system | 6h | High - NPCs remember you |
| 5 | Multi-agent NPCs | 10h | Very high - world feels alive |
| 6 | World simulation | 7h | Very high - world changes without you |
| 7 | NPC decision policies | 5h | Medium - consistency |
| 8 | Rich UI | 4h | Medium - better UX |
| 9 | Voice I/O | 6h | High - immersion |
| 10 | Full campaign content | 15h | Very high - depth |

**Recommended**: Implement Phase 2 next. It's a sweet spot of effort vs. impact.

---

## You're Ready!

You have:
- ✅ Clean, organized codebase
- ✅ Working game loop
- ✅ LLM integration
- ✅ World content
- ✅ Save/load system
- ✅ Full roadmap for future features

**Now**: Run `python main.py` and start playing! 

Questions? Read the code—it's well-commented. Check `README.md` for architecture, `QUICKSTART.md` for setup, `ROADMAP.md` for the big picture.

Enjoy building! 🎲🐉

---

## Quick Command Reference

```bash
# Setup
pip install -r requirements.txt

# Play
python main.py

# Customize
# Edit: data/locations.json (add places)
#       data/npcs.json (add characters)
#       config/settings.yaml (tune settings)
#       main.py (change model)

# Save/Load
# In game: 7 to save, 8 to load
# Files: data/save_state.json

# Next phase
# Read: PHASE2_PLAN.md for detailed design
```
