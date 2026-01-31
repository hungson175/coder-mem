# Memory System Design Analysis

## Summary

This document outlines a memory system design for your coding agent project. It addresses a critical limitation: the agent lacks persistence across execution loops and sessions, causing it to forget context, redo work, and make shallow plans.

### Key Design Patterns

1. **Trigger-based Memory**: Memory operations are triggered by TodoWrite calls exceeding N_STEPS_LIMIT (threshold for "meaningful" work)
2. **Recall-Replan Loop**: After first TodoWrite with >N_STEPS_LIMIT steps, inject a recall phase before resuming the agent loop
3. **Leverages Existing Skills**: Reuses the .claude skills memory system you already have configured (coder-memory-store/recall)

---

## Core Problem

Without memory, the agent:
- Forgets past actions/decisions across loops
- Redoes completed work
- Lacks continuity between sessions
- Cannot leverage learned knowledge

---

## Proposed Solution

### What to Remember

- Learn from the **skills memory technique** from `.claude` (your existing coder-memory-store/recall skills)

### When to Remember/Recall

**The Loop Context**: Refers to the agent execution loop at `coding_agent/core/base_agent.py:chat()` in the `while hasattr(response, "tool_calls") and response.tool_calls:` section

**Remember (Store Memory):**
- After each loop when a meaningful task completes
- Trigger: `TodoWrite` called with steps > `N_STEPS_LIMIT`

**Recall (Retrieve Memory):**
- Only once after the **first** TodoWrite call in a loop that exceeds N_STEPS_LIMIT
- Look at planned TodoWrite steps → recall relevant memory → replan if needed
- Inject prompt: *"with the recalled memory, please replan if needed"* → resume loop

### How to Implement

- Use the existing skills memory technique from `.claude` (your coder-memory-store and coder-memory-recall skills)

---

## Interpretation

You're designing an **intelligent memory layer** that:

1. **Watches for substantial planning events** (TodoWrite with >N_STEPS_LIMIT steps)
2. **Automatically recalls relevant past experiences** before execution
3. **Gives the agent a chance to adjust plans** based on recalled knowledge
4. **Stores learnings after completing meaningful work**

This prevents the agent from repeating mistakes and enables cumulative learning across sessions. The design cleverly leverages your existing `.claude` memory skills infrastructure rather than building from scratch.

---

## Implementation Considerations

### Integration Points

1. **base_agent.py:chat()** - Main execution loop where memory triggers occur
2. **TodoWrite tool** - Monitoring point for N_STEPS_LIMIT threshold
3. **Skill invocation** - coder-memory-store and coder-memory-recall skills

### Flow Diagram

```
User Request
    ↓
Agent Loop Starts
    ↓
TodoWrite called (steps > N_STEPS_LIMIT) ← First time only
    ↓
Recall Phase: Invoke coder-memory-recall
    ↓
Inject: "With recalled memory, please replan if needed"
    ↓
Agent continues/replans
    ↓
Execute tasks
    ↓
Task completes (meaningful work done)
    ↓
Remember Phase: Invoke coder-memory-store
    ↓
Loop ends
```

### Key Parameters

- **N_STEPS_LIMIT**: Threshold for determining "meaningful" work (needs to be defined)
- **Recall timing**: Only once per loop to avoid overhead
- **Memory scope**: Leverages existing coder-level (universal) memory system

### Benefits

1. **No new infrastructure**: Reuses proven `.claude` skills memory system
2. **Automatic learning**: Agent learns from every significant task
3. **Context preservation**: Maintains continuity across sessions
4. **Adaptive planning**: Can adjust plans based on past experiences
5. **Prevents rework**: Avoids repeating failed approaches

### Challenges to Address

1. **N_STEPS_LIMIT tuning**: What threshold indicates "meaningful" work? 
   #ANSWER: 5
2. **Memory relevance**: How to ensure recalled memories are relevant to current task?
   #ANSWER: The LLM will decide, we must only inject a messge " "With recalled memory, please replan if needed" - it's enough, it's very smart
3. **Performance overhead**: Recall/store operations add latency
   #ANSWER: Don't worry about it yet
4. **Memory quality**: Need to store valuable insights, not noise
   #ANSWER: that's what you must learn from Coder's memory skills (in ~/.claude/skills/)
5. **Loop state management**: Tracking whether recall has already occurred in current loop
   #ANSWER: no need to worry, the LLM will know

# My review:
- Both recall & remember (pls using store from now on to unify with the current naming in ~/.claude/skills ) , must be call in Task with general-purpose subagent - and with the guide learning from the 2 memory-store/recall SKILL.md files - and copy & update them here to ./memory-feature/
- Scope down in this version: just use global level (Coder's memory)
- 