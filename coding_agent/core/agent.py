"""Main CodingAgent class."""

from typing import Optional
from langchain_core.messages import HumanMessage, SystemMessage

from .base_agent import BaseAgent
from .config import Config
from .prompts import coding_agent_prompt
from ..commands.custom_commands import CustomCommandManager
from ..commands.native_commands import NativeCommandManager
from ..utils.context import load_memory_context
from ..tools.file_tools import read_file, write_file, edit_file, list_files
from ..tools.search_tools import glob_files, grep_files
from ..tools.execution_tools import run_command, get_bash_output, todo_write
from ..tools.task_tool import task


class CodingAgent(BaseAgent):
    def __init__(
        self, model_name: Optional[str] = None, provider_name: Optional[str] = None
    ):
        """Initialize the coding agent with tools and caching."""
        # If model_name not specified, use provider-appropriate defaults
        if model_name is None:
            provider_defaults = {
                "claude": "claude-sonnet-4-20250514",
                "sonnet": "claude-sonnet-4-20250514",
                "deepseek": "deepseek-chat",
                "ds": "deepseek-chat",
                "grok": "grok-code-fast-1",
                "xai": "grok-code-fast-1",
            }
            # Use provider default if provider specified, else use Config default
            if provider_name and provider_name.lower() in provider_defaults:
                model_name = provider_defaults[provider_name.lower()]
            else:
                model_name = Config.MODEL_NAME

        # Initialize command managers
        self.command_manager = CustomCommandManager()
        self.native_command_manager = NativeCommandManager()

        # Initialize empty memory context - will be loaded after working directory is set
        self.memory_context = ""

        # Call parent with coding-specific configuration
        super().__init__(
            system_prompt=coding_agent_prompt(),
            tools=self._get_coding_tools(),
            model_name=model_name,
            provider_name=provider_name,
        )

        # Update system prompt with correct working directory after BaseAgent sets it
        self._update_system_prompt_with_working_dir()

        # Add memory context if exists
        if self.memory_context and len(self.memory_context.strip()) > 100:
            self.messages.append(
                HumanMessage(content=self._create_cached_message(self.memory_context))
            )

    def _update_system_prompt_with_working_dir(self):
        """Update system prompt with correct working directory."""
        # Reload memory context with correct working directory
        from ..utils.context import load_memory_context
        self.memory_context = load_memory_context(working_dir=self.working_dir)
        
        # Recreate system message with correct working directory
        updated_prompt = coding_agent_prompt(working_dir=self.working_dir)
        cached_content = self.provider.create_cached_message(updated_prompt)
        self.messages[0] = SystemMessage(content=cached_content)
        
        # Update ALL memory context messages (there might be multiple)
        memory_message_indices = []
        for i, message in enumerate(self.messages):
            if isinstance(message, HumanMessage) and "<system-reminder>" in str(message.content):
                memory_message_indices.append(i)
        
        # Remove all old memory context messages (in reverse order to maintain indices)
        for i in reversed(memory_message_indices):
            self.messages.pop(i)
        
        # Add new memory context if significant
        memory_message_found = len(memory_message_indices) > 0
        
        # Add new memory context if it should exist
        if self.memory_context and len(self.memory_context.strip()) > 100:
            self.messages.insert(1, HumanMessage(content=self._create_cached_message(self.memory_context)))

    def _get_coding_tools(self):
        """Get tools specific to coding agent (includes Task tool)."""
        return [
            read_file,
            write_file,
            edit_file,
            run_command,
            list_files,
            glob_files,
            grep_files,
            get_bash_output,
            todo_write,
            task,
        ]
