# Phase 1: Analysis of Existing Skills

## Overview

Analyzed `~/.claude/skills/coder-memory-{store,recall}/SKILL.md` to understand patterns for adaptation.

---

## Key Architecture Patterns

### 1. Execution Context
**Pattern**: Both skills MUST be invoked via Task tool with `subagent_type="general-purpose"`
- Runs in separate context to avoid polluting main conversation
- Ensures isolation and clean execution

### 2. Memory Organization
**Three-tier structure**:
- `episodic/` - Concrete coding events with full context
- `procedural/` - Proven workflows and step-by-step processes
- `semantic/` - Distilled principles and patterns

### 3. Progressive Disclosure
**Tree guideline structure**:
- SKILL.md provides overview
- README.md files in subdirectories provide navigation
- Detailed memories in specific files
- Agent reads overviews first, drills down only when needed

### 4. File-Based Operations (Primary System)
**Tools used**:
- **Grep**: Search for keywords across memory files
- **Read**: Load specific files for detailed analysis
- **Glob**: File pattern matching for navigation
- **Write/Edit**: Store and update memories

**No database required** - filesystem is source of truth

---

## Memory Store Key Patterns

### Phase Structure
1. **PHASE 0**: Initialize directory structure if needed
2. **PHASE 1**: Extract 0-3 insights (most conversations yield 0-1)
3. **PHASE 2**: Search for similar memories using file-based search
4. **PHASE 3**: Consolidation decision (MERGE/UPDATER/GENERALIZE/CREATE)
5. **PHASE 4**: Store memory using compact format
6. **PHASE 5**: Update skill metadata if structure changed

### Selection Criteria (ALL must be true)
1. **Non-obvious**: Not standard practice or well-documented
2. **Universal**: Applies across multiple projects/languages/frameworks
3. **Actionable**: Provides concrete guidance for future situations
4. **Generalizable**: Can be abstracted beyond specific codebase

### Consolidation Logic
| Similarity | Action | Rationale |
|-----------|--------|-----------|
| **Duplicate/Very Similar** | **MERGE** | Combine into single stronger entry |
| **Related (same topic)** | **UPDATER** | Update existing memory with new information |
| **Pattern Emerges** | **GENERALIZE** | Extract pattern → promote episodic to semantic |
| **Different** | **CREATE** | New file or separate section |

### Compact Memory Format
**CRITICAL**: 3-5 sentences MAX to prevent bloat

```
**Title:** <concise title>
**Description:** <one sentence summary>

**Content:** <3-5 sentences covering: what happened, what was tried (including failures), what worked/failed, key lesson>

**Tags:** #tag1 #tag2 #success OR #failure
```

**Formatting rules**:
- NO blank line between Title and Description
- ONE blank line before Content
- ONE blank line before Tags
- Tag with memory type: #episodic, #procedural, #semantic

### Storage Execution
1. Write to file (PRIMARY - must succeed)
2. ~~Optional: Dual-write to Qdrant~~ (REMOVED - not needed)
3. If file becomes too long: Create subdirectory with README.md
4. Update parent README.md to reference new structure

---

## Memory Recall Key Patterns

### Phase Structure
1. **PHASE 0**: Understand memory structure (read SKILL.md)
2. **PHASE 1**: Construct search strategy based on query
3. **PHASE 2**: Search for relevant memories using file-based navigation
4. **PHASE 3**: Extract top 3 most relevant memories
5. **PHASE 4**: Check if refactoring needed (>5 file reads = problem)
6. **PHASE 5**: Present results with application guidance

### Search Strategy
**Determine memory type to search**:
- Need specific past experience? → Search episodic
- Need step-by-step process? → Search procedural
- Need general principle/pattern? → Search semantic
- Unclear? → Search all three

**Query keywords**: Extract 3-8 core concepts (no filler words)

### File-Based Navigation
1. Read README.md in memory type directory
2. Identify relevant subdirectories based on query
3. Use Grep to search for keywords across files
4. Use Read to load promising files
5. Progressive disclosure: Read READMEs first, then specific files

**Do NOT read entire memory tree** - use filesystem tools intelligently

### Relevance Criteria
- Keyword match quality
- Context similarity to current task
- Actionability for current situation

### Results Presentation
**Format**:
- Query summary
- Memory types searched
- Number of results found
- Full memory content for each result
- Relevance explanation for each
- Application guidance (2-3 sentences synthesizing actionable next steps)

---

## What to Remove (Qdrant/Vector Search)

### In Memory Store (PHASE 2, Step 2)
Remove entire section:
```
**Step 2 (Optional): Try Vector Search First**

**If Qdrant MCP server available**, try semantic search...
[Lines 77-97 in original]
```

### In Memory Store (PHASE 4, Step 2)
Remove dual-write section:
```
2. **Optional: Dual-Write to Qdrant**:

   **If Qdrant MCP server available**, also store to vector database...
   [Lines 185-207 in original]
```

### In Memory Recall (PHASE 2, Step 0)
Remove entire section:
```
### Step 0 (Optional): Try Vector Search First

**If Qdrant MCP server available**, try semantic search...
[Lines 58-83 in original]
```

---

## What to Keep (Everything Else!)

### Core Patterns to Preserve
✅ Three-tier memory structure (episodic/procedural/semantic)
✅ Progressive disclosure with README.md files
✅ Compact memory format (3-5 sentences)
✅ Consolidation logic (MERGE/UPDATER/GENERALIZE/CREATE)
✅ File-based search using Grep/Read/Glob
✅ Selection criteria for universal insights
✅ Max 2-level directory depth
✅ Both success AND failure tagging
✅ Refactoring trigger (>5 file reads)
✅ Self-maintenance capability

### Tool Usage
✅ Grep for keyword search
✅ Read for file loading
✅ Glob for pattern matching
✅ Write/Edit for storage
✅ Task tool invocation requirement

---

## Adaptations for Coding Agent

### Directory Location
- **Original**: `~/.claude/skills/coder-memory-store/`
- **New**: `~/.sonph-code-memory/`

### File Names
- **Original**: SKILL.md (skill invocation format)
- **New**: memory-store-guide.md, memory-recall-guide.md (simpler naming)

### Trigger Integration
**New requirement**: Integrate with TodoWrite in base_agent.py loop
- **Recall trigger**: First TodoWrite with >5 steps
- **Store trigger**: Loop completes with meaningful work (>5 steps)

### Prompt Format
**New approach**: Agent reads guide files, not skill invocation
- Recall prompt: "Read ~/.sonph-code-memory/memory-recall-guide.md and recall relevant memories for [TodoWrite todos]"
- Store prompt: "Read ~/.sonph-code-memory/memory-store-guide.md and store learnings from [completed todos]"

---

## Summary

**What works**: File-based architecture with progressive disclosure is elegant and proven
**What to remove**: Only the optional Qdrant MCP tool calls (3 sections total)
**What to adapt**: Directory location, file naming, trigger integration with TodoWrite
**Ready for**: Phase 2 implementation
