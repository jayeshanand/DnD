# Commerce & Transaction Fixes

## Problem Fixed

**Original Issues:**
1. NPCs (like Mira) gave items for free without asking for payment
2. When reminded about payment, player was charged
3. When asking again for the same item, player was charged again (double-billing)

## What Changed

### 1. Enhanced System Prompt with Commerce Rules
**File**: `llm/prompts.py`

Added explicit commerce rules to the system prompt:
```
COMMERCE & TRANSACTION RULES:
- ALWAYS charge for goods and services unless there's a specific reason not to
- State the price BEFORE giving items
- Use 'gold_change' with NEGATIVE values for purchases
- Only add items AFTER gold is deducted
- Check conversation history to avoid double-billing
- NPCs remember if player already paid in recent turns
```

**Common Prices:**
- Food/drink: 2-5 gold
- Basic supplies: 5-20 gold
- Weapons: 30-100 gold
- Potions: 20-50 gold

### 2. Player Gold Highlighted in Context
Player's gold is now prominently displayed:
```
Gold: 50 💰 (IMPORTANT: Player can only afford items/services they have gold for)
```

### 3. Validation Detects Free Items
**File**: `engine/response_parser.py`

The validator now checks:
- ✅ **Free items from merchants**: Warns if NPC (bartender, merchant, shopkeeper) gives items without gold_change
- ✅ **Insufficient funds**: Blocks purchases that would make gold negative
- ✅ **Duplicate purchases**: Warns if same item was received in last 2 turns

### 4. Added Food & Trade Items
**File**: `data/items.json`

New items with prices:
- `bread` - 2 gold
- `ale` - 3 gold
- `stew` - 5 gold
- `rations` - 10 gold
- `lockpick` - 15 gold
- `dagger` - 20 gold

## How It Works Now

### Correct Transaction Flow

**Turn 1: Player asks for food**
```
Player: "I'd like some stew"
Mira: "That'll be 5 gold. Interested?"
Effects: (no items yet, no gold change yet)
```

**Turn 2: Player confirms**
```
Player: "Yes, I'll take it"
Mira: "Here you go!"
Effects: 
  - gold_change: -5
  - new_items: ["stew"]
Result: Player pays 5 gold, receives stew
```

**Turn 3: Player asks again**
```
Player: "Can I have another stew?"
Mira: "Another one? That's 5 gold."
Effects: (LLM sees in history player already bought stew)
```

### What the LLM Sees

**Context includes:**
1. **Player's current gold**: 45 💰
2. **Conversation history**: Shows previous purchase
```
Turn 2:
  Player: "Yes, I'll take it"
  Mira: "Here you go!"
  Effects: 💰 Gold: 50 → 45 (-5), 📦 Gained: stew
```
3. **Commerce rules**: Reminds LLM to charge, check history, avoid double-billing

### Validation Catches Mistakes

If the LLM makes an error, validation will catch it:

```
❌ Free items detected
   "WARNING: Receiving items from bartender without gold cost. 
    Items should be paid for!"

❌ Insufficient funds
   "Gold change would result in negative gold: -50 
    (Player only has 45 gold)"

⚠️  Duplicate purchase
   "WARNING: Possible duplicate purchase - stew was already 
    received in recent turns"
```

## Testing

Run the commerce test:
```bash
python3 test_commerce.py
```

This tests:
1. Free item detection ✅
2. Proper payment validation ✅
3. Insufficient funds blocking ✅
4. Duplicate purchase warnings ✅

## Expected Behavior

### Scenario 1: Buying Food
```
You: "I'd like some food"
Mira: "I've got bread for 2 gold or stew for 5 gold. What'll it be?"

You: "I'll have the stew"
Mira: "Here you go." *slides bowl across bar*
Effects: -5 gold, +1 stew
```

### Scenario 2: Asking Again
```
You: "Can I have another stew?"
Mira: "Another one? That's 5 more gold."

You: "Yes"
Mira: "Coming right up."
Effects: -5 gold, +1 stew
(This is fine - buying a second bowl)
```

### Scenario 3: Reminding About Payment
```
You: "Can I have some food?"
Mira: "Stew's 5 gold. Want it?"

You: "Didn't I already pay?"
LLM checks history → sees no previous payment
Mira: "Not yet, friend. 5 gold for the stew."
```

### Scenario 4: Not Enough Gold
```
You: "I want to buy a sword"
Merchant: "Fine blade, 50 gold."

You: "I'll take it" (but only have 30 gold)
System validation: ❌ Blocks transaction
Merchant: "You don't have enough gold, friend."
```

## Why This Fixes Your Issue

**Before:**
1. LLM gave items freely (no commerce logic)
2. No tracking of what was already purchased
3. No validation of gold costs

**After:**
1. ✅ LLM explicitly instructed to charge for items
2. ✅ Conversation history tracks all purchases
3. ✅ Validation catches free items and duplicate charges
4. ✅ Player gold prominently displayed
5. ✅ NPCs instructed to check history before charging

The game now properly handles commerce transactions with:
- Consistent pricing
- No free items from merchants
- No double-billing for same item
- Proper validation of gold costs

## Files Modified

```
llm/prompts.py          - Added commerce rules to system prompt
data/items.json         - Added food & trade items with prices
engine/response_parser.py - Added transaction validation
test_commerce.py (new)  - Test suite for commerce logic
```
