# Quick Start Guide

## What You Have

You now have a fully-structured **Phase 0 + Phase 1** implementation of an AI-driven D&D engine with:

- ✅ **Complete directory structure** organized by function
- ✅ **GameState models** (Player, Location, Quest, Inventory)
- ✅ **LLM client** ready to connect to Ollama
- ✅ **CLI interface** with turn-based game loop
- ✅ **World data** (7 locations, 3 NPCs, 2 factions)
- ✅ **Save/load system** for persistent state

## Installation (5 minutes)

### Step 1: Install Ollama

Download and install Ollama from https://ollama.ai

### Step 2: Start Ollama

```bash
ollama serve
```

Keep this running in a terminal.

### Step 3: Pull a Model

In a new terminal:

```bash
ollama pull llama2
```

Or choose another model: `mistral`, `neural-chat`, `wizard-vicuna`, etc.

### Step 4: Install Python Dependencies

```bash
cd "Python dev/D&D/ai-dnd"
pip install -r requirements.txt
```

### Step 5: Run the Game

```bash
python main.py
```

## Playing the Game

When you run `main.py`:

1. You'll be asked if you want to load an existing game or create new
2. **Create New**: Enter character name and choose class
   - Warrior, Rogue, Mage, or Cleric
3. **Start Playing**: You begin in a tavern in a town

### Game Commands

```
1 - Look around
2 - Talk to someone  
3 - Check inventory
4 - Check quests
5 - Rest
6 - Custom action (type anything!)
7 - Save game
8 - Load game
q - Quit
help - Show this menu
```

### Example Actions

You can type natural language commands:

```
> I ask Mira about the town
> I look for clues
> I examine the bar counter
> I try to intimidate the merchant
> I go to the forest to explore
```

The AI DM (via Ollama) will respond with narrative and consequences.

## How It Works

```
You type action
    ↓
CLI captures input
    ↓
Engine processes turn (time advances, logs action)
    ↓
Prompt builder creates system + context prompts
    ↓
Ollama LLM generates DM narration
    ↓
Narration stored in game state
    ↓
Screen displays location, narration, status
    ↓
You see results and take next action
```

## What's Where

```
main.py              ← Start here
engine/state.py      ← Game data models
engine/game_loop.py  ← Turn processing
llm/client.py        ← Ollama communication
llm/prompts.py       ← DM prompt templates
ui/cli.py            ← Screen display and input
data/*.json          ← World content (edit these!)
```

## Customizing Your World

### Add a New Location

Edit `data/locations.json`:

```json
"my_dungeon": {
  "id": "my_dungeon",
  "name": "Dark Dungeon",
  "description": "Stone walls dripping with moisture...",
  "exits": {
    "out": "town_square"
  },
  "npcs": ["skeleton_guard"],
  "items": []
}
```

Then add connections from existing locations:

```json
"town_square": {
  ...
  "exits": {
    "dungeon": "my_dungeon"
  }
}
```

### Add a New NPC

Edit `data/npcs.json`:

```json
"skeleton_guard": {
  "id": "skeleton_guard",
  "name": "Bone Rattler",
  "role": "guardian",
  "personality": "haunted, speaks in riddles",
  "faction": "undead",
  "goals": ["guard the dungeon", "find peace"],
  "traits": {
    "courage": 1.0,
    "honor": 0.3,
    "intelligence": 0.5,
    "charisma": 0.2
  },
  "relationship_to_player": 0.0,
  "description": "A skeleton in rusted armor",
  "dialogue_sample": "Who dares enter this tomb?"
}
```

### Change the LLM Model

Edit `main.py`, line ~180, change the model parameter:

```python
llm = OllamaClient(
    base_url="http://localhost:11434",
    model="mistral"  # Change this!
)
```

Available models (run `ollama pull <name>`):

- `llama2` (7B, good balance)
- `mistral` (7B, faster)
- `neural-chat` (7B, conversational)
- `orca-mini` (3B, lightweight)
- `wizard-vicuna` (13B, better reasoning)

## Troubleshooting

### "Cannot connect to Ollama"

- Check Ollama is running: `ollama serve`
- Default runs on `http://localhost:11434`
- Game will warn but still work with simulated responses

### "ModuleNotFoundError"

```bash
pip install -r requirements.txt
```

### "requests" error

```bash
pip install requests pyyaml pydantic
```

## Next Steps: Phase 2

When you're ready to level up:

**Phase 2 Goals:**
- Structured JSON outputs from LLM
- State update engine that parses effects
- Validation layer
- More deterministic world changes

Once you want Phase 2, let me know and I can add:

1. JSON schema for DM responses
2. State validation and update engine
3. Better error recovery
4. More complex quest chains

## Tips for Best Experience

1. **Model selection**: Start with `mistral` for speed, upgrade to `wizard-vicuna` for better narrative
2. **Temperature tuning**: Change `temperature=0.8` in `main.py` to 0.5 (more consistent) or 1.0 (more creative)
3. **Keep context brief**: Very long narrations can slow down generation - keep turns under 2 minutes in-game
4. **Save often**: Use command `7` to save manually
5. **Edit world freely**: The JSON files are meant to be customized!

## Need Help?

- Check `README.md` for architecture overview
- Review `config/settings.yaml` for all options
- Look at existing data JSON files for format examples

Have fun! 🐉
