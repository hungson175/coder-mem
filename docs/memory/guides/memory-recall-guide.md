# Memory Recall Guide

**⚠️ EXECUTION CONTEXT**: This guide is read by agents invoked via Task tool with subagent_type="general-purpose". Runs in separate context to avoid polluting main conversation.

**Purpose**: Retrieve **universal coding patterns** from file-based memory at `~/.sonph-code-memory/`.

**Key Architecture**: README.md files form a **tree guideline structure** - read overviews first, navigate to specific files as needed. Very effective for progressive disclosure.

**When to Use**:
- Before starting complex, multi-step implementations
- When encountering unfamiliar technical problems
- User explicitly says "--coder-recall" or "--recall" (Claude decides if universal or project-specific, may use both)
- Need architectural guidance or debugging strategies

**REMEMBER**: Failures are as valuable as successes. Look for both #success and #failure tags when searching memories.

**When NOT to Use**:
- Routine or trivial tasks
- Just recalled similar knowledge recently
- Project-specific questions (use project-memory-recall)

---

## PHASE 0: Understand Memory Structure

Check `~/.sonph-code-memory/` structure to understand current organization.

Memory types available:
- `episodic/` - Concrete coding events
- `procedural/` - Workflows and processes
- `semantic/` - Principles and patterns

---

## PHASE 1: Construct Search Strategy

**If user provided explicit query**: Use it to determine which memory type(s) to search

**If inferring from context**: Analyze task to choose:
- Need specific past experience? → Search episodic
- Need step-by-step process? → Search procedural
- Need general principle/pattern? → Search semantic
- Unclear? → Search all three

**Query keywords**: Extract 3-8 core concepts (no filler words)

---

## PHASE 2: Search for Relevant Memories

### File-Based Navigation

For each target memory type:

1. **Read README.md** (if exists) in memory type directory
2. **Identify relevant subdirectories** based on query (use file_path hints if available)
3. **Read targeted files**:
   - Use Grep to search for keywords across files (prioritize hinted paths if available)
   - Use Read to load promising files
   - Progressive disclosure: Read READMEs first, then specific files

**Do NOT read entire memory tree** - use filesystem tools intelligently.

---

## PHASE 3: Extract Relevant Memories

Collect top 3 most relevant memories matching query.

**Relevance criteria**:
- Keyword match quality
- Context similarity to current task
- Actionability for current situation

---

## PHASE 4: Check If Refactoring Needed

**Signs memory needs reorganization**:
- Took >5 file reads to find relevant memories
- Found duplicates in multiple files
- Unrelated content mixed in same file
- Difficult to navigate structure

**If reorganization needed**: Invoke general-purpose agent to refactor memory structure.

**Refactoring prompt**:
```
Refactor memory file structure at ~/.sonph-code-memory/.

Current issues: [describe what made recall difficult]

Actions needed:
- Merge duplicate memories
- Reorganize files by topic (max 2-level depth)
- Update README.md files as overviews
- Ensure episodic/procedural/semantic separation is clear

Maintain all existing memory content - only reorganize structure.
```

---

## PHASE 5: Present Results

**Format**:
```
🔍 Coder Memory Recall Results

**Query**: <keywords or user question>
**Memory Types Searched**: <episodic/procedural/semantic>
**Results Found**: <number>

---

## Result 1: [Title]

**Type**: <Episodic/Procedural/Semantic>
**Source**: <file path>

<Full memory content>

**Relevance**: <1-2 sentences explaining why this matches query>

---

## Result 2: [Title]

[Same format]

---

## Application Guidance

<2-3 sentences synthesizing results and actionable next steps for current task>
```

**If no results found**:
```
🔍 Coder Memory Recall Results

**Query**: <keywords>
**Results Found**: 0 relevant memories

No universal patterns matched your query in coder memory.

**Suggestions**:
- Try broader search terms
- Check if this is project-specific (use project-memory-recall)
- Proceed with standard approaches and store insights after completion
```

**If refactoring triggered**:
```
⚙️ Memory Refactoring Triggered

Memory structure was reorganized during recall to improve future searches.
<report refactoring actions taken>
```

---

## Tool Usage

