# AI-Driven D&D Engine: Full Roadmap

A complete step-by-step implementation guide from "nothing" to "full AI-powered tabletop RPG with autonomous NPCs".

**Current Status**: ✅ Phase 0 & 1 Complete

## Phase Overview

| Phase | Name | Status | Playstability | Complexity |
|-------|------|--------|---|---|
| 0 | Foundations & Tech | ✅ Done | Setup | Low |
| 1 | Text-Only Single-DM | ✅ Done | **Playable** | Low |
| 2 | Structured JSON Output | 📋 Ready | **More Playable** | Medium |
| 3 | NPC Objects & Personalities | ⏳ Planned | **Rich** | Medium |
| 4 | Memory System | ⏳ Planned | **Immersive** | Medium |
| 5 | Multi-Agent NPCs | ⏳ Planned | **Dynamic** | High |
| 6 | World Simulation | ⏳ Planned | **Living World** | High |
| 7 | Decision Policies | ⏳ Planned | **Intelligent** | High |
| 8 | Rich UI | ⏳ Planned | **Professional** | Medium |
| 9 | Voice I/O | ⏳ Planned | **Immersive** | Medium |
| 10 | Polish & Scenarios | ⏳ Planned | **Complete** | Low |

---

## Phase 0: Foundations & Tech ✅

**Goal**: Have a clean, organized codebase to build on.

**What's Included**:
- ✅ Python 3.8+ environment
- ✅ Directory structure (engine, ui, llm, data, agents, world, memory)
- ✅ Configuration system (YAML)
- ✅ Data layer (JSON files)
- ✅ Git-ready (.gitignore)

**Exit Criteria**: You can import modules and understand the structure.

**Time**: ~30 minutes (already done!)

---

## Phase 1: Minimal Text-Only Single-DM Game ✅

**Goal**: Complete playable game loop with AI DM.

**Core Features**:
- ✅ GameState model (Player, Location, Quest, Inventory)
- ✅ Game loop (turn processing, time advancement)
- ✅ LLM client (Ollama HTTP integration)
- ✅ CLI interface (display, input, menu)
- ✅ Prompt templates (DM system prompt + game context)
- ✅ Save/load system (JSON persistence)
- ✅ World content (8 locations, 3 NPCs, 2 factions)

**How It Works**:
```
Player Input → CLI → Engine → Prompt Builder → Ollama → Narration → Display
```

**Play Experience**:
- Free-form text input ("I talk to the bartender")
- Rich narrative responses
- Inventory, quest tracking
- Character progression framework

**Exit Criteria**: ✅ Game is playable end-to-end with Ollama running.

**Time**: ~2-3 hours (already done!)

**Next**: Go to Phase 2

---

## Phase 2: Structured JSON Output & State Management 📋

**Goal**: Make game state updates deterministic and visible.

**Problem It Solves**:
- Currently: narration is free-form, state doesn't change consistently
- After: every action → JSON → guaranteed state update

**Core Tasks**:
1. Define JSON schema for DM responses
2. Update prompts to request JSON
3. Build JSON parser & validator
4. Create state update engine
5. Add retry/fallback logic
6. Integrate into CLI

**New Features**:
- Inventory changes are visible
- NPC relationships track and change
- Quest completion works
- Location changes are explicit
- HP/Gold modifications are predictable

**How It Works**:
```
Player Action → LLM generates JSON → Parser validates → Engine applies effects → State updated
{
  "narration": "...",
  "npc_speeches": [...],
  "effects": {
    "location": "tavern",
    "new_items": ["sword"],
    "npc_relationship_changes": {"bartender": 0.2}
  }
}
```

**Exit Criteria**:
- LLM returns valid JSON every turn
- Effects are applied correctly
- State persists and is predictable
- Invalid JSON doesn't crash (fallback works)

**Time**: 6-8 hours

**Files to Create/Modify**:
- `engine/response_schema.py` (new)
- `engine/response_parser.py` (new)
- `engine/game_loop.py` (update)
- `llm/prompts.py` (update)
- `llm/client.py` (update)
- `ui/cli.py` (update)

**Detailed Plan**: See `PHASE2_PLAN.md`

**Next**: Go to Phase 3

---

## Phase 3: NPC Objects & Distinct Personalities ⏳

**Goal**: NPCs feel like different characters, not just props.

**Problem It Solves**:
- Currently: NPCs are just data, all sound the same
- After: NPCs have distinct personalities, react differently

**Core Tasks**:
1. Expand NPC schema (personality traits, goals, fears)
2. Update world data with rich NPC definitions
3. Modify prompts to pass NPC info to LLM
4. Track NPC state (location, mood, last_interaction)
5. CLI shows NPC names & emotions in dialogue

**New Features**:
- Personality matters: brave vs cowardly, honest vs deceptive
- NPCs have goals and motivations
- Relationship tracking (trust, fear, debt)
- NPC location tracking
- NPC dialogue varies by personality

**How It Works**:
```
Bartender (gruff): "What do you want?"
Merchant (cunning): "Ah, I can see you're looking for something special..."
Shopkeeper (cheerful): "Welcome, friend! What can I help you with?"
```

**Exit Criteria**:
- At least 5 NPCs with distinct personalities in data
- Prompts include personality info
- CLI displays NPC names/emotions with dialogue
- Relationships change based on interactions

**Time**: 4-5 hours

**Builds On**: Phase 2 (structured JSON)

**Next**: Go to Phase 4

---

## Phase 4: Memory System (Episodic & Semantic) ⏳

**Goal**: NPCs remember your past interactions.

**Problem It Solves**:
- Currently: every conversation is fresh, no continuity
- After: NPCs reference what you did last time

**Core Tasks**:
1. Set up vector database (chromadb or faiss)
2. Create memory_store.py (add_memory, retrieve_memories)
3. Define memory types (episodic, semantic)
4. Integrate memories into NPC prompts
5. Update relationships based on memories
6. Track memory decay over time

**Memory Types**:
- **Episodic**: "The player saved me from bandits at the forest" (time, emotion, importance)
- **Semantic**: "The player works for the King" (facts, no decay)

**How It Works**:
```
Player saves NPC → Store memory (importance=high, emotion=gratitude)
Later conversation → Retrieve similar memories → Include in prompt
NPC recognizes you → Relationship increases → Dialogue reflects history
```

**Exit Criteria**:
- NPC clearly remembers past interactions
- Memories influence relationship scores
- Semantic memories persist, episodic ones fade
- Memory system integrates with prompts

**Time**: 5-6 hours

**Dependencies**: Phase 3 (personality)

**Next**: Go to Phase 5

---

## Phase 5: True Multi-Agent NPCs ⏳

**Goal**: Each NPC is an independent agent with its own goals.

**Problem It Solves**:
- Currently: LLM plays all NPCs at once
- After: each NPC has separate decision-making

**Core Tasks**:
1. Create NPC Agent class (agents/npc_agent.py)
2. Implement decide_action() for each NPC
3. Build scene manager (tracks who's in scene)
4. Add internal monologue (NPC thoughts, not shown to player)
5. Implement action types (dialogue, move, plot, combat, plan)
6. Integrate multi-agent responses into CLI

**Agent Structure**:
```python
class NPCAgent:
    identity: str           # personality, goals, fears
    memory: MemoryStore     # personal memories
    current_mood: float     # -1 to 1
    current_plan: str       # what they're trying to do
    
    def decide_action(world_state) -> AgentAction:
        # Decide what to do based on personality + situation
```

**How It Works**:
```
Scene: Player enters tavern where Mira and Aldric are
  → Ask Mira: "What do I do?"
    → Recall: Player bought from Aldric last time
    → Decision: Be cautious but friendly
  → Ask Aldric: "What do I do?"
    → Recall: Player has no items to trade
    → Decision: Ignore player, talk to Mira

Action Selection:
  Mira chooses: Dialogue("greet", emotion=cautious)
  Aldric chooses: Dialogue("pitch_to_mira", emotion=ignore_player)

CLI Display:
  Mira: "Ah, you're back. Haven't seen you in days."
  Aldric: [to Mira] "Any luck finding those rare herbs?"
```

**Exit Criteria**:
- Multiple NPCs act independently in scenes
- Some respond, some ignore, some plot
- Internal monologues stored as memories
- Actions feel coordinated, not random

**Time**: 8-10 hours

**Dependencies**: Phase 4 (memory)

**Next**: Go to Phase 6

---

## Phase 6: World Simulation & Factions ⏳

**Goal**: The world changes even when you're not looking.

**Problem It Solves**:
- Currently: world is static, only changes when player acts
- After: factions fight, trade, grow, decline

**Core Tasks**:
1. Expand faction model (goals, relationships, resources)
2. Create world_tick() function (advance world time)
3. Implement faction AI (simple rule-based)
4. Track faction relationships & power
5. Show world changes when player rests
6. Let NPC actions affect factions

**Faction Actions**:
- Trade (increase gold, improve relations)
- Raid (decrease resources, damage relations)
- Negotiate (change relations)
- Spy (gather intel, risk discovery)

**How It Works**:
```
Player: "I rest for a week"
World Tick (7 days × 4 ticks):
  Day 1: Merchant Guild trades → +50 gold
  Day 2: Local militia raids bandit camp → reduces unrest
  Day 3: Undead cult performs ritual → tension rises
  Day 4: Farmers' crops fail → shortage

Result: World state changes, new quests available, prices change
```

**Exit Criteria**:
- Factions have measurable resources & relationships
- World ticks when player rests
- Faction actions are visible in narration
- NPC actions affect faction standing

**Time**: 6-8 hours

**Dependencies**: Phase 3 (NPC objects)

**Next**: Go to Phase 7

---

## Phase 7: Decision Policies & Heuristics ⏳

**Goal**: NPC decisions are consistent and goal-aligned (groundwork for RL).

**Problem It Solves**:
- Currently: LLM picks actions somewhat randomly
- After: consistent personalities with clear decision logic

**Core Tasks**:
1. Define utility functions for each action type
2. Calculate utilities based on: personality, relationships, goals, risk
3. Implement action selection (max utility or softmax)
4. Log all decisions for future RL training
5. Tune weights to match desired personalities

**Utility Calculation**:
```
For "attack" action:
  utility = courage * 0.5 + (HP / max_HP) * 0.3 + allies_count * 0.2
  
For "negotiate" action:
  utility = charisma * 0.4 + trust_in_player * 0.6
  
For "flee" action:
  utility = (1 - courage) * 0.5 + (damage_taken / max_HP) * 0.5
```

**How It Works**:
```
NPC in combat:
  Option 1 (attack): utility = 0.3 (low courage, tired)
  Option 2 (flee): utility = 0.7 (self-preservation)
  Option 3 (negotiate): utility = 0.2 (no trust)
  → Choose: Flee

Later, same NPC in tavern:
  Option 1 (help): utility = 0.8 (remember player saved them)
  Option 2 (ignore): utility = 0.2
  → Choose: Help
```

**Exit Criteria**:
- NPCs behave predictably based on personality
- Decision log is detailed enough for RL training
- Actions align with stated goals
- Personalities are consistent

**Time**: 4-5 hours

**Dependencies**: Phase 5 (agents)

**Optional Next**: Machine Learning
- Collect decision logs from Phase 7
- Train small policy model offline
- Use RL for NPC decision-making instead of heuristics

**Next**: Go to Phase 8

---

## Phase 8: Rich UI & Better UX ⏳

**Goal**: Game looks professional and is fun to play with friends.

**Current State**: Basic CLI with text-only interface

**Options**:
1. **Rich CLI**: Terminal UI with colors, panels, animations
2. **Web UI**: FastAPI backend + HTML/JS frontend

**Option 1: Rich CLI (Easier)**

Using `rich` and `textual` libraries:

```
┌─ The Wandering Griffin ─────────────────────────────────────┐
│                                                               │
│ A cozy tavern with wooden beams and a roaring fireplace...  │
│                                                               │
├─ NPCs: Mira (bartender), Aldric (merchant) ────────────────┤
│                                                               │
├─ DIALOGUE ──────────────────────────────────────────────────┤
│ Mira: "What brings you here, traveler?"                     │
│ You: "I'm looking for work."                                │
│ Aldric: *raises eyebrow* "Work, eh?"                        │
├─ STATUS ────────────────────────────────────────────────────┤
│ Warrior | ❤️ 20/20 | 💰 50 | Turn 5                          │
├─ COMMANDS: /look /talk /inventory /quests /rest /help ─────┤
│ >                                                            │
└────────────────────────────────────────────────────────────┘
```

**Option 2: Web UI (More Work)**

FastAPI server + React/Vue frontend:
- HTTP API for game state
- Real-time updates via WebSocket
- Multiplayer-ready architecture
- Can play in browser or desktop (Electron)

**UI Features**:
- Scene view (location description, NPCs, items)
- Dialogue log (colored by NPC)
- Status bar (HP, gold, level, time)
- Quick command buttons
- Inventory panel
- Quest tracker
- Save/load UI
- Settings panel

**Exit Criteria**:
- UI is polished and responsive
- Can comfortably run multi-player (one player types for party)
- All game features accessible from UI
- Performance is good (sub-second response)

**Time**:
- Rich CLI: 3-4 hours
- Web UI: 8-10 hours

**Recommended**: Start with Rich CLI, upgrade to Web if needed

**Next**: Go to Phase 9

---

## Phase 9: Voice Input & TTS ⏳

**Goal**: Play by talking instead of typing.

**Problem It Solves**:
- Currently: typing-only, breaks immersion with friends
- After: speak to play, optionally hear responses

**Core Tasks**:
1. Add ASR (Automatic Speech Recognition) via Whisper
2. Add speaker detection (who's talking?)
3. Integrate transcription into game loop
4. Add TTS (Text-to-Speech) for narration
5. Manage latency (only speak finished sentences)

**Architecture**:
```
Microphone → Whisper (transcribe) → Speaker ID → Map to player → Feed to engine → 
LLM response → TTS (Piper/ElevenLabs) → Speaker → Next turn
```

**How It Works**:
```
Player 1: "I ask the bartender about the bandits"
  → Transcribed: "I ask the bartender about the bandits"
  → Engine processes
  → LLM response: "Mira leans in. 'Bandits? They've been raiding caravans...'"
  → TTS plays: Mira's voice tells the story
  → [5 seconds later] "What do you do?"

Player 2: "We head to the forest to track them"
  → Transcribed
  → Process...
```

**Speaker Mapping** (simple approach):
- Manual toggle: "Now Player 1 is speaking"
- Button: Click to record
- Hotkey: Push-to-talk (like Discord)

**Exit Criteria**:
- Speech is transcribed and fed to engine
- Speaker attribution works
- TTS plays response narration
- Latency is acceptable (<3 seconds)

**Time**: 5-6 hours

**Dependencies**: Phase 8 (UI)

**Next**: Go to Phase 10

---

## Phase 10: Polish, Scenarios & Testing ⏳

**Goal**: Transform prototype into a playable game with content.

**Core Tasks**:
1. Create default starting region
   - 1 main city with 5-10 locations
   - 2-3 nearby villages
   - 1-2 dungeons/wilderness areas
2. Create 10-20 important NPCs with full backstories
3. Create 5-10 faction arcs and conflicts
4. Write 20+ starter quests
5. Run test campaigns
   - Log odd behavior
   - Tune NPC personalities
   - Fix edge cases
   - Balance difficulty

**Content Creation**:
```
Region: "Kingdom of Aldermoor"
  City: "Greystone"
    Mayor Thorne (allied with merchants)
    Temple of Light (conflict with Thieves Guild)
    Several taverns and shops
  Villages:
    Farriver (farming, simple folk)
    Shadowbrook (shady dealings, smuggling)
  Dungeons:
    Ruins of Old Citadel (undead, treasure)
    Blackmire Swamp (cultists, secrets)
```

**Scenario Modes**:
1. **Sandbox**: No main quest, free exploration
2. **Campaign**: Main story with chapters
3. **Survival**: Resources scarce, danger high
4. **Political**: Navigate faction intrigue

**Exit Criteria**:
- World feels alive and interconnected
- Quests have multiple solutions
- Factions matter and conflict
- No major bugs or exploits
- Playtime can be 5+ hours without repetition

**Time**: 10-15 hours (ongoing)

---

## Implementation Timeline

**Recommended Pace**:

```
Week 1:
  - Phase 0 ✅ (30 min)
  - Phase 1 ✅ (3 hours)
  - Phase 2 (6 hours)

Week 2:
  - Phase 3 (5 hours)
  - Phase 4 (6 hours)

Week 3:
  - Phase 5 (10 hours)
  - Phase 6 (7 hours)

Week 4:
  - Phase 7 (5 hours)
  - Phase 8 (4 hours with Rich CLI)

Week 5+:
  - Phase 9 (6 hours)
  - Phase 10 (ongoing)
```

**Total**: ~60-70 hours for complete implementation (can stop at any phase)

---

## Decision Tree: Where to Go Next

```
You're now at Phase 1 ✅

Ready for more complexity?
  ├─ YES → Phase 2 (structured JSON)
  │         (makes game feel more responsive)
  │
  └─ NO → Customize Phase 1
           (add more locations/NPCs to data/)
           (adjust LLM model/temperature)
           (play with friends!)

After Phase 2?
  ├─ Want richer NPCs? → Phase 3
  ├─ Want NPCs to remember? → Phase 4
  ├─ Want independent agents? → Phase 5
  └─ Want changing world? → Phase 6

After Phase 6?
  ├─ Want smart NPCs? → Phase 7
  ├─ Want better UI? → Phase 8
  ├─ Want voice? → Phase 9
  └─ Want full game? → Phase 10
```

---

## Key Design Principles

1. **Each phase is playable**: You can stop and have a working game
2. **Clear exit criteria**: Know when a phase is complete
3. **Modular code**: Features don't depend on later phases
4. **Gradual complexity**: Start simple, add features incrementally
5. **Data-driven**: World content in JSON, not hardcoded
6. **LLM-native**: Uses LLMs intelligently without over-relying

---

## Success Metrics

- [ ] Phase 1: Game runs and generates responses
- [ ] Phase 2: State changes are predictable and visible
- [ ] Phase 3: NPCs have distinct personalities
- [ ] Phase 4: NPCs remember your past interactions
- [ ] Phase 5: Multiple NPCs act independently
- [ ] Phase 6: World changes when you rest
- [ ] Phase 7: NPC decisions are consistent
- [ ] Phase 8: UI is polished and comfortable
- [ ] Phase 9: You can play by talking
- [ ] Phase 10: Full campaign with 5+ hours of content

---

## Resources & Tools

**LLMs**:
- Local: Ollama (llama2, mistral, neural-chat)
- Cloud: OpenAI, Anthropic, Cohere APIs

**Databases**:
- Vector: ChromaDB, FAISS, Pinecone
- Relational: SQLite, PostgreSQL

**UI**:
- Terminal: Rich, Textual, Blessed
- Web: FastAPI, React, Vue

**Voice**:
- ASR: Whisper, faster-whisper
- TTS: Piper, ElevenLabs, gTTS

**Testing**:
- Unit: pytest, unittest
- Integration: Scenario playthrough
- Load: concurrent players

---

## Next Steps: Immediate Actions

### Right Now
1. ✅ Phase 0 & 1 are complete
2. Verify installation: `python main.py`
3. Play a few turns to get familiar with the loop

### When Ready for Phase 2
```bash
# Tell me and I'll implement:
# - Response schema
# - JSON parser
# - State update engine
# - Integration tests
```

### For Customization Today
- Edit `data/locations.json` - add new areas
- Edit `data/npcs.json` - change personalities
- Edit `main.py` - change LLM model
- Change `config/settings.yaml` - tune temperature

---

**You now have a solid foundation. The whole roadmap is clear, and you can go as deep or stay as light as you want. Have fun building!** 🐉
