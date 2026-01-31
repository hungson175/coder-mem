# Memory System Implementation Plan v1

## Executive Summary

This document defines the implementation plan for adding intelligent memory capabilities to the coding agent. The system will automatically store learnings from completed tasks and recall relevant past experiences to inform future planning, preventing repeated mistakes and enabling cumulative learning across sessions.

---

## Design Decisions (Finalized)

### 1. N_STEPS_LIMIT Threshold
**Value: 5 steps**
- When TodoWrite is called with >5 steps, it indicates a meaningful/complex task
- This triggers the recall-replan cycle

### 2. Memory Relevance
**Solution: LLM-driven relevance**
- The LLM will autonomously determine what memories are relevant
- Simple prompt injection: *"With recalled memory, please replan if needed"*
- Trust the LLM's intelligence to filter and apply appropriate memories

### 3. Performance Overhead
**Decision: Defer optimization**
- Accept latency from recall/store operations in v1
- Focus on correctness and functionality first
- Profile and optimize in future iterations if needed

### 4. Memory Quality
**Solution: Learn from existing skills**
- Study and replicate patterns from `~/.claude/skills/coder-memory-store/SKILL.md`
- Study and replicate patterns from `~/.claude/skills/coder-memory-recall/SKILL.md`
- Copy these skill files to `~/.sonph-code-memory/` directory for reference and adaptation (all memory items will be saved there, just like they would be saved in '~/.claude/skills/coder-memory-store/' )
- **CRITICAL**: Remove ONLY the optional Qdrant MCP tool calls when creating new memory-recall/store-guide.md files
  - **Keep the entire file-based architecture** (this is the primary system, already proven)
  - Remove only: `search_memory()` calls in recall and `store_memory()` dual-write in store
  - Keep: File organization, Grep/Read/Glob search, consolidation logic, README.md tree structure
  - Files are source of truth; Qdrant was only an optional optimization layer

### 5. Loop State Management
**Decision: No explicit state tracking**
- Trust the LLM to understand context within the conversation
- The LLM will naturally avoid redundant recalls within the same loop

---

## Implementation Architecture

### Scope: Coder-Level Memory Only
**v1 will focus exclusively on global (coder-level) memory**
- Store universal patterns and lessons learned
- Skip project-specific memory for now
- Simplifies implementation and testing

### Memory Operations via Task Tool
**Critical: Both recall and store MUST be invoked via Task tool**
- Use `subagent_type="general-purpose"` for memory operations
  #REVIEW: just inject this guide to copy-of-SKILL.md file , it's enough !
- This ensures proper isolation and prevents context pollution

**Terminology Update:**
- Use **"store"** instead of "remember" (consistent with `~/.claude/skills/` naming)
- Use **"recall"** for retrieval

---

## Integration Points

### 1. Main Loop: `coding_agent/core/base_agent.py:chat()`
**Location:** `while hasattr(response, "tool_calls") and response.tool_calls:` loop

**Trigger Detection:**
- Monitor for `TodoWrite` tool calls
- Check if `len(todos) > N_STEPS_LIMIT` (5 steps)
- Track if recall has already occurred in current conversation turn

### 2. Recall Phase (Before Execution)
**Trigger:** First TodoWrite call with >5 steps in the current loop

**Action:**
```python
# Pseudo-code
if first_todowrite_with_many_steps and not recall_done_this_loop:
    # Invoke Task tool with general-purpose agent
    # Prompt: "Recall relevant memories for: [summarize TodoWrite steps]"
    # Then inject: "With recalled memory, please replan if needed"
    recall_done_this_loop = True
```

### 3. Store Phase (After Completion)
**Trigger:** Loop completes AND meaningful work was done (TodoWrite had >5 steps)

**Action:**
```python
# Pseudo-code
if loop_completed and meaningful_work_done:
    # Invoke Task tool with general-purpose agent
    # Prompt: "Store learnings from this task: [summarize completed work]"
```

---

## Flow Diagram (Updated)

```
User Request
    ↓
Agent Loop Starts
    ↓
TodoWrite called (steps > 5) ← First time only
    ↓
RECALL PHASE:
  ├─ Invoke Task(general-purpose)
  ├─ Prompt: "Recall relevant memories for: [task summary]"
  └─ Inject: "With recalled memory, please replan if needed"
    ↓
Agent evaluates recalled memories
    ↓
Agent replans (if needed) or continues
    ↓
Execute tasks (normal tool execution loop)
    ↓
Task completes (meaningful work done)
    ↓
STORE PHASE:
  ├─ Invoke Task(general-purpose)
  └─ Prompt: "Store learnings from: [completed task summary]"
    ↓
Loop ends
```
#REVIEW: This part `  ├─ Invoke Task(general-purpose)
  ├─ Prompt: "Recall relevant memories for: [task summary]"` the prompt would be "Read the ~/.sonph-code-memory/memory-recall-guide.md " and look at TodoWrite todos and recall relevant memories
#REVIEW: this part `STORE PHASE:
  ├─ Invoke Task(general-purpose)
  └─ Prompt: "Store learnings from: [completed task summary]` -> the prompt would be "Read the ~/.sonph-code-memory/memory-store-guide.md " and look at TodoWrite todos and store relevant memories (ife needed, well, in the guide, LLM must be very selective)
---

## Implementation Tasks

### Phase 1: Study Existing Skills ✅ COMPLETED
**Location:** `~/.claude/skills/`
- [x] Read and analyze `coder-memory-recall/SKILL.md`
- [x] Read and analyze `coder-memory-store/SKILL.md`
- [x] Document key patterns, prompts, and techniques used
  - **Output**: `docs/memory/phase1_analysis.md`
  - **Key findings**: File-based is primary, only 3 Qdrant sections to remove, 15+ proven patterns to keep
- [ ] Copy both files to `~/.sonph-code-memory/` directory (moved to Phase 2)

### Phase 2: Create Memory Feature Directory ✅ COMPLETED
**Location:** `~/.sonph-code-memory/`
- [x] Copy reference skill files from `~/.claude/skills/` to `~/.sonph-code-memory/`
  - **Output**: `REFERENCE_coder-memory-recall.md` (200 lines), `REFERENCE_coder-memory-store.md` (266 lines)
- [x] Create memory-recall-guide.md (164 lines):
  - Copied from REFERENCE, adapted paths to `~/.sonph-code-memory/`
  - Removed: Qdrant Step 0 vector search section
  - Removed: Skill-related terminology
  - Kept: ALL original file-based logic intact
- [x] Create memory-store-guide.md (211 lines):
  - Copied from REFERENCE, adapted paths to `~/.sonph-code-memory/`
  - Removed: Qdrant Step 2 vector search + dual-write sections
  - Removed: Skill-related terminology
  - Kept: ALL original file-based logic, consolidation, PHASE 0 lazy initialization intact
- [x] Added memory trigger info to CLAUDE.md (3 lines)

**Progress Notes:**
- Phase 1 analysis completed: See `docs/memory/phase1_analysis.md`
- Phase 2: **4 files in `~/.sonph-code-memory/`** (lazy initialization approach)
  - 2 guide files: Complete originals minus Qdrant, adapted paths only
  - 2 reference files: For comparison
  - Memory directories created lazily on first store operation

### Phase 3: Modify Base Agent ✅ COMPLETED
**Location:** `coding_agent/core/base_agent.py`
- [x] Add N_STEPS_LIMIT constant (value: 5) at top of file
- [x] ~~Add loop state tracking for recall phase~~ (Not needed - LLM handles it)
- [x] Detect TodoWrite calls with >5 steps in tool execution loop
- [x] Implement recall trigger logic (inject HumanMessage after TodoWrite detected)
- [x] Implement store trigger logic (inject HumanMessage after loop completes)
- [x] LLM reads guide files and decides whether to use Task tool

**Progress Notes:**
- Added N_STEPS_LIMIT = 5 constant
- Recall trigger: After TodoWrite >5 steps, inject message to read recall guide
- Store trigger: After loop completes with TodoWrite >5, inject message to read store guide
- LLM autonomously decides memory operations based on guide instructions

### Phase 4: Integration Testing - skip this part first, LLM testing VERY expensive !
- [ ] Test recall phase activation
- [ ] Test store phase activation
- [ ] Verify Task tool invocation with general-purpose agent
- [ ] Validate memory persistence across sessions
- [ ] Test replan behavior after recall

---

## Success Criteria

### Functional Requirements
1. ✓ Agent automatically recalls memories when TodoWrite has >5 steps (first time only)
2. ✓ Agent gets opportunity to replan based on recalled memories
3. ✓ Agent automatically stores learnings after completing meaningful work
4. ✓ Memory operations use Task tool with general-purpose agent
5. ✓ Only coder-level (global) memory is used

### Quality Requirements
1. ✓ Memory quality matches patterns from `~/.claude/skills/`
2. ✓ No manual intervention required from user
3. ✓ LLM autonomously determines memory relevance
4. ✓ No duplicate recall operations within same loop

---

## Future Enhancements (Out of Scope for v1)

- Project-level memory support
- Performance optimization for recall/store operations
- Advanced memory filtering and search
- Memory statistics and analytics
- Memory pruning/cleanup strategies
- Multi-level memory hierarchy (project + coder)

---

## References

- Analysis doc: `./analysis_v1.md`
- Existing skills: `~/.claude/skills/coder-memory-{store,recall}/`
- Base agent: `coding_agent/core/base_agent.py`
