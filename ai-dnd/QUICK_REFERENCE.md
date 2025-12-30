# Quick Reference Card

## Installation (3 steps)

```bash
# 1. Install Ollama, run "ollama serve"
# 2. Download a model: "ollama pull llama2"
# 3. Install dependencies & play:
cd "Python dev/D&D/ai-dnd"
pip install -r requirements.txt
python main.py
```

---

## In-Game Commands

| Command | Action |
|---------|--------|
| `1` | Look around |
| `2` | Talk to NPC |
| `3` | Check inventory |
| `4` | Check quests |
| `5` | Rest |
| `6` | Custom action |
| `7` | Save game |
| `8` | Load game |
| `q` | Quit |
| `help` | Show menu |

Or just **type anything**: "I search the room", "I attack the guard", etc.

---

## File Locations

| What | Where | Edit? |
|------|-------|-------|
| World locations | `data/locations.json` | ✏️ Yes |
| NPCs & personalities | `data/npcs.json` | ✏️ Yes |
| Factions | `data/factions.json` | ✏️ Yes |
| Items | `data/items.json` | ✏️ Yes |
| Game rules | `data/rules.json` | ✏️ Yes |
| Settings | `config/settings.yaml` | ✏️ Yes |
| Game logic | `engine/` | 🔧 Advanced |
| LLM code | `llm/` | 🔧 Advanced |

---

## Key Settings

**LLM Model** (in `main.py`):
```python
model="llama2"  # Options: mistral, neural-chat, wizard-vicuna, orca-mini
```

**Temperature** (in `llm/prompts.py`):
```python
temperature=0.8  # 0.5=consistent, 0.8=balanced, 1.2=creative
```

**Locations to Add**:
1. Edit `data/locations.json`
2. Add location object
3. Add exits from other locations

**NPCs to Add**:
1. Edit `data/npcs.json`
2. Add NPC object with personality
3. Add NPC ID to location's `npcs` list

---

## Architecture Map

```
User Input
    ↓
[ui/cli.py] - Display & get actions
    ↓
[engine/state.py] - Game state (Player, Locations, NPCs, Quests)
    ↓
[engine/game_loop.py] - Turn processing
    ↓
[llm/prompts.py] - Build context prompt
    ↓
[llm/client.py] - Send to Ollama (HTTP)
    ↓
Ollama (Local LLM)
    ↓
Narration response
    ↓
Update state → Save to JSON → Display
```

---

## Data Structure

### Location
```json
{
  "id": "tavern",
  "name": "The Wandering Griffin",
  "description": "...",
  "exits": {"out": "town_square", "north": "inn"},
  "npcs": ["bartender"],
  "items": []
}
```

### NPC
```json
{
  "id": "bartender",
  "name": "Mira",
  "personality": "gruff but kind",
  "faction": "locals",
  "goals": ["keep bar safe", "earn money"],
  "traits": {"courage": 0.5, "honor": 0.6, "intelligence": 0.7, "charisma": 0.8},
  "relationship_to_player": 0.0
}
```

### Game State (Saved)
```json
{
  "player": {"name": "Hero", "class_name": "Warrior", "hp": 20, "gold": 50},
  "current_location_id": "tavern",
  "turn": 5,
  "locations": {...},
  "active_quests": {...},
  "npcs": {...}
}
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Cannot connect to Ollama" | Run `ollama serve` in another terminal |
| No response from LLM | Check Ollama is running on `localhost:11434` |
| ImportError: requests | `pip install requests` |
| Game too slow | Try faster model: `mistral` instead of `llama2` |
| Game too creative/inconsistent | Lower temperature: 0.5 instead of 0.8 |
| Want to add content | Edit JSON files in `data/` folder |
| Want to extend code | Read `ROADMAP.md` for Phase 2+ designs |

---

## Phase Progress

```
Phase 0: ✅ Foundations (structure, config)
Phase 1: ✅ Text-Only DM (playable game!)
Phase 2: 📋 JSON Output (structured state)
Phase 3: ⏳ NPC Personalities (distinct characters)
Phase 4: ⏳ Memory System (NPCs remember)
Phase 5: ⏳ Multi-Agent NPCs (autonomous)
Phase 6: ⏳ World Simulation (living world)
Phase 7: ⏳ Decision Policies (smart NPCs)
Phase 8: ⏳ Rich UI (professional interface)
Phase 9: ⏳ Voice I/O (talk to play)
Phase 10: ⏳ Full Game (campaign + content)
```

---

## Key Files to Understand

```
main.py
  └─ Entry point, game initialization, character creation

engine/state.py
  └─ Data models: GameState, Player, Location, Quest, Inventory

engine/game_loop.py
  └─ Turn processing, time advancement, state updates

llm/client.py
  └─ Ollama communication (HTTP requests)

llm/prompts.py
  └─ DM prompt templates and context building

ui/cli.py
  └─ Terminal display and player input handling
```

---

## Common Customizations

### Change starting location
`main.py`, line ~170:
```python
current_location_id="tavern"  # Change this
```

### Change starting items
`main.py`, line ~155:
```python
player.inventory.add_item("rope", 1)
player.inventory.add_item("sword", 1)  # Add/remove as needed
```

### Change LLM parameters
`llm/client.py`, line ~50:
```python
payload = {
    "temperature": 0.8,  # Change this
    "top_p": 0.9,        # Or this
    "num_predict": 1024, # Or this
}
```

### Add a quest
`data/locations.json` - NPC dialogue or `main.py` at game creation

---

## Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Architecture overview |
| `GETTING_STARTED.md` | Installation & first steps |
| `QUICKSTART.md` | Quick start guide |
| `ROADMAP.md` | Full 10-phase implementation |
| `PHASE2_PLAN.md` | Detailed Phase 2 design |
| (This file) | Quick reference |

---

## Next Steps

1. **Play**: Run `python main.py` and explore
2. **Customize**: Edit `data/*.json` files
3. **Extend**: Implement Phase 2 (see `PHASE2_PLAN.md`)

---

## Remember

- ✅ You have a working game RIGHT NOW
- ✅ You can customize locations, NPCs, items
- ✅ You can change the LLM model anytime
- ✅ You can expand to more phases when ready
- ✅ All code is modular and extensible

**Start playing! The learning happens by doing.** 🎲
