"""Agent registry for discovering and loading dynamic agents."""

from pathlib import Path
from typing import Dict, List
from .agent_config_parser import AgentConfigParser
from .config import Config


class AgentRegistry:
    """Registry for discovering and loading agents from ~/.claude/agents/."""

    _instance = None
    _agents_cache = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _load_builtin_memory_agents(self):
        """Load memory agents from this repo's .claude/agents/ as built-in."""
        # Get the directory where THIS file is located
        current_file = Path(__file__)
        repo_root = current_file.parent.parent.parent  # coding_agent/core/agent_registry.py -> repo root
        builtin_agents_dir = repo_root / ".claude" / "agents"

        if builtin_agents_dir.exists():
            for md_file in builtin_agents_dir.glob("*.md"):
                try:
                    config = AgentConfigParser.parse_agent_md(md_file)
                    agent_type = config.get("agentType")
                    if agent_type:
                        config["source"] = "built-in"
                        # Ensure model is set to default if None
                        if not config.get("model") or config.get("model") == "None":
                            config["model"] = Config.MODEL_NAME
                        self._agents_cache[agent_type] = config
                except Exception as e:
                    print(f"Warning: Failed to load built-in memory agent {md_file}: {e}")

    def get_available_agents(self) -> Dict[str, Dict]:
        """Get all available agents (built-in + user-defined + project-level).

        Priority order (highest to lowest):
        1. Project-level agents (.claude/agents/)
        2. User-level agents (~/.claude/agents/)
        3. Built-in agents

        Returns:
            Dict mapping agent_type -> agent_config
        """
        if self._agents_cache is None:
            self._agents_cache = {}

            # Add built-in agents (lowest priority)
            self._agents_cache["general-purpose"] = {
                "agentType": "general-purpose",
                "whenToUse": "General-purpose agent for researching complex questions, searching for code, and executing multi-step tasks. When you are searching for a keyword or file and are not confident that you will find the right match in the first few tries use this agent to perform the search for you.",
                "tools": ["Read", "Write", "Edit", "Bash", "LS", "Glob", "Grep", "BashOutput", "TodoWrite"],
                "model": Config.MODEL_NAME,
                "source": "built-in",
            }

            # Load built-in memory agents from .claude/agents/ in this repo
            self._load_builtin_memory_agents()

            # Scan user-level agents (medium priority) - these can override built-in
            user_agent_dir = Path.home() / ".claude" / "agents"
            if user_agent_dir.exists():
                for md_file in user_agent_dir.glob("*.md"):
                    try:
                        config = AgentConfigParser.parse_agent_md(md_file)
                        agent_type = config.get("agentType")
                        if agent_type:
                            config["source"] = "user-defined"
                            self._agents_cache[agent_type] = config
                    except Exception as e:
                        print(f"Warning: Failed to load user agent {md_file}: {e}")

            # Scan project-level agents (highest priority) - these override everything
            project_agent_dir = Path(".claude") / "agents"
            if project_agent_dir.exists():
                for md_file in project_agent_dir.glob("*.md"):
                    try:
                        config = AgentConfigParser.parse_agent_md(md_file)
                        agent_type = config.get("agentType")
                        if agent_type:
                            config["source"] = "project-level"
                            self._agents_cache[agent_type] = config  # Override if duplicate
                    except Exception as e:
                        print(f"Warning: Failed to load project agent {md_file}: {e}")

        return self._agents_cache

    def get_agent_list_for_task_tool(self) -> List[str]:
        """Get formatted list of agents for Task tool description.

        Returns:
            List of strings formatted as: "- agent-name: description (Tools: tools)"
        """
        agents = self.get_available_agents()
        agent_lines = []

        for agent_type, config in agents.items():
            when_to_use = config.get("whenToUse", "")
            tools = config.get("tools", ["*"])
            tools_str = ", ".join(tools) if tools != ["*"] else "*"

            agent_lines.append(f"- {agent_type}: {when_to_use} (Tools: {tools_str})")

        return agent_lines

    def load_agent(self, agent_type: str, provider_name: str = None, model_name: str = None):
        """Load specific agent instance.

        Args:
            agent_type: The type of agent to load
            provider_name: The LLM provider to use (optional)
            model_name: The model name to use (optional)

        Returns:
            BaseAgent instance

        Raises:
            ValueError: If agent type is unknown
        """
        agents = self.get_available_agents()

        if agent_type not in agents:
            available = list(agents.keys())
            raise ValueError(
                f"Unknown agent type: {agent_type}. Available: {available}"
            )

        config = agents[agent_type]

        if config["source"] == "built-in" and agent_type == "general-purpose":
            # Load general-purpose built-in agent
            from .general_purpose_agent import GeneralPurposeAgent

            return GeneralPurposeAgent(provider_name=provider_name, model_name=model_name)
        else:
            # Load user-defined or built-in memory agents (both use DynamicAgent)
            from .dynamic_agent import DynamicAgent

            return DynamicAgent.from_config(config, provider_name=provider_name, model_name=model_name)

    def clear_cache(self):
        """Clear agents cache to reload from disk."""
        self._agents_cache = None

    def get_agent_count(self) -> Dict[str, int]:
        """Get count of different agent types."""
        agents = self.get_available_agents()
        built_in = sum(
            1 for config in agents.values() if config["source"] == "built-in"
        )
        user_defined = sum(
            1 for config in agents.values() if config["source"] == "user-defined"
        )
        project_level = sum(
            1 for config in agents.values() if config["source"] == "project-level"
        )

        return {
            "built_in": built_in,
            "user_defined": user_defined,
            "project_level": project_level,
            "total": built_in + user_defined + project_level,
        }
