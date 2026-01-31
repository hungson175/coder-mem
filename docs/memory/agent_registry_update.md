# Agent Registry Update - Dual-Location Support

## Changes Made

Updated `coding_agent/core/agent_registry.py` to support both project-level and user-level agents with proper priority handling.

## Agent Discovery Priority

1. **Project-level** (`.claude/agents/`) - **Highest priority**
2. **User-level** (`~/.claude/agents/`) - Medium priority
3. **Built-in** (hardcoded) - Lowest priority

If an agent with the same name exists in multiple locations, the higher-priority one wins (duplicates are removed).

## Implementation Details

### `get_available_agents()` method:
- Scans built-in agents first (lowest priority)
- Scans user-level agents second (overrides built-in if duplicate)
- Scans project-level agents last (overrides everything if duplicate)
- Each agent gets a `source` field: `"built-in"`, `"user-defined"`, or `"project-level"`

### `get_agent_count()` method:
- Now tracks three source types: `built_in`, `user_defined`, `project_level`
- Returns total count

### `load_agent()` method:
- No changes needed - already handles all non-built-in agents via `DynamicAgent.from_config()`

## Memory Agents Location

The memory agents are now in:
```
.claude/agents/
├── memory-recall.md  (project-level)
└── memory-store.md   (project-level)
```

These will be automatically discovered and have **highest priority** over any global versions.

## Testing

To verify the agents are loaded:
1. Start the coding agent
2. Check that `memory-recall` and `memory-store` appear in available agents
3. The Task tool should list them in its description
4. The base_agent.py memory triggers should be able to invoke them

## Benefits

- **Flexibility**: Can have project-specific agent configurations
- **Override capability**: Project agents override global ones
- **Clean separation**: Each project can customize agents without affecting others
- **Backward compatible**: Existing user-level agents still work
