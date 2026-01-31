"""Base agent class for configurable agents."""

import os
from typing import List, Optional
from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool

from .config import Config
from .llm_providers import LLMProviderFactory
from ..utils.keyboard import setup_keyboard_interrupt

# Memory system trigger threshold
N_STEPS_LIMIT = 3


class BaseAgent:
    """Configurable agent base class."""

    def __init__(
        self,
        system_prompt: str,
        tools: List[BaseTool] = None,
        model_name: str = Config.MODEL_NAME,
        provider_name: Optional[str] = None,
    ):
        """Initialize agent with configurable system prompt and tools."""
        # Setup keyboard interrupt handling
        setup_keyboard_interrupt()

        # Store configuration
        self.system_prompt_str = system_prompt
        self.working_dir = os.path.abspath(".")

        # Setup LLM provider
        if provider_name is None:
            provider_name = Config.DEFAULT_PROVIDER

        self.provider = LLMProviderFactory.create_provider(
            provider_name, model_name=model_name
        )

        # Setup tools AFTER provider is set
        self.tools = tools or self._get_default_tools()
        self.tools_map, self.llm_with_tools = self._setup_tools()

        # Initialize with correct prompt from the start
        self.messages = [
            SystemMessage(content=self.provider.create_cached_message(system_prompt))
        ]

    def _get_default_tools(self) -> List[BaseTool]:
        """Get default tool set - override in subclasses."""
        from ..tools.file_tools import read_file, write_file, edit_file, list_files
        from ..tools.search_tools import glob_files, grep_files
        from ..tools.execution_tools import run_command, get_bash_output, todo_write
        from ..tools.task_tool import task_tool

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
            task_tool,
        ]

    def _setup_tools(self):
        """Setup tools and create tools map."""
        tools_map = {tool.name: tool for tool in self.tools}

        # Bind tools to LLM through provider
        llm_with_tools = self.provider.bind_tools(self.tools)

        return tools_map, llm_with_tools

    def _create_cached_message(self, content: str):
        """Create a message using provider's caching strategy."""
        return self.provider.create_cached_message(content)

    def _remove_cache_control(self, message):
        """Remove cache control using provider's strategy."""
        self.provider.remove_cache_control(message)

    def set_working_dir(self, directory: str):
        """Set the working directory for commands."""
        from colorama import Fore

        self.working_dir = directory
        # Update system prompt with new working directory
        if hasattr(self, "_update_system_prompt_with_working_dir"):
            self._update_system_prompt_with_working_dir()
        print(Fore.GREEN + f"📁 Working directory set to: {directory}")

    def get_current_provider_info(self) -> str:
        """Get current provider information."""
        return f"{self.provider.provider_name} ({self.provider.model_name})"

    def chat(self, user_input: str) -> str:
        """Process user request."""
        from langchain_core.messages import HumanMessage, ToolMessage
        from colorama import Fore, Style

        # Add user message
        self.messages.append(HumanMessage(content=user_input))

        # Get initial response
        response = self.llm_with_tools.invoke(self.messages)

        # Memory trigger tracking
        todo_step_count = 0
        is_first_time_planning = True
        should_call_replan = False

        # Only show initial response in debug mode or if there's actual content
        # Handle both string and list content (some LLMs return content as list)
        content = response.content
        if content:
            # Convert to string if it's a list
            if isinstance(content, list):
                content = " ".join(str(item) for item in content)

            if isinstance(content, str) and content.strip():
                try:
                    from ..ui.enhanced_cli import enhanced_cli
                    enhanced_cli.print_separator()
                    enhanced_cli.show_status_message(f"Agent response: {content[:100]}...", "info")
                except ImportError:
                    print(Fore.CYAN + "=" * 50)
                    print(Fore.GREEN + "🤖 Response: " + content[:200])

        # Only show token usage in debug mode or with a flag
        # This keeps the output clean for normal usage
        if os.getenv("SHOW_TOKEN_USAGE", "").lower() == "true":
            if hasattr(response, "response_metadata"):
                usage_info = self.provider.format_usage_info(response.response_metadata)
                if usage_info:
                    try:
                        from ..ui.enhanced_cli import enhanced_cli
                        enhanced_cli.show_status_message(usage_info, "info")
                    except ImportError:
                        print(Fore.BLUE + usage_info)

        # Remove cache_control from user message
        self._remove_cache_control(self.messages[-1])

        # Add response
        self.messages.append(response)

        # Handle tool calls
        while hasattr(response, "tool_calls") and response.tool_calls:
            # Memory trigger: Check FIRST if we need to call memory-recall
            if should_call_replan:
                should_call_replan = False
                print(Fore.YELLOW + "\n[MEMORY] Suggesting memory-recall agent...")
                self.messages.append(
                    HumanMessage(content="Call memory-recall agent to recall relevant memories, then replan using TodoWrite ONLY if the recalled patterns suggest a better approach.")
                )
                print(Fore.CYAN + "[DEBUG] Waiting for LLM response on memory-recall suggestion...")
                response = self.llm_with_tools.invoke(self.messages)
                print(Fore.GREEN + f"[DEBUG] Got response, has tool_calls: {hasattr(response, 'tool_calls') and bool(response.tool_calls)}")
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    print(Fore.CYAN + f"[DEBUG] Tool calls detected: {[tc['name'] for tc in response.tool_calls]}")
                self.messages.append(response)
                continue  # Skip to next iteration to process any tool calls

            # Show tool execution count with enhanced CLI if available
            try:
                from ..ui.enhanced_cli import enhanced_cli
                if len(response.tool_calls) == 1:
                    enhanced_cli.show_status_message("Executing tool...", "processing")
                else:
                    enhanced_cli.show_status_message(f"Executing {len(response.tool_calls)} tools...", "processing")
            except ImportError:
                print(
                    Fore.MAGENTA + f"\n🔧 Executing {len(response.tool_calls)} tool(s)..."
                )

            try:
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]

                    # Special handling for run_command to use working_dir
                    if tool_name == "run_command" and "working_dir" not in tool_args:
                        tool_args["working_dir"] = self.working_dir

                    # Try to use enhanced CLI if available
                    try:
                        from ..ui.enhanced_cli import enhanced_cli

                        # Special handling for TodoWrite - show the full todo list
                        if tool_name.lower() == "todowrite" and "todos" in tool_args:
                            enhanced_cli.show_tool_execution("TODOWRITE", "Managing todo list", {})
                            # Display the todo list with proper formatting
                            enhanced_cli.show_todo_list(tool_args["todos"])
                        else:
                            # Get tool description if available
                            tool_desc = ""
                            if tool_name in self.tools_map and hasattr(self.tools_map[tool_name], 'description'):
                                tool_desc = self.tools_map[tool_name].description[:80] if hasattr(self.tools_map[tool_name], 'description') else ""

                            # Show enhanced tool execution panel
                            enhanced_cli.show_tool_execution(tool_name.upper(), tool_desc, tool_args)

                        # Show cancellation hint for long-running tools
                        if tool_name in ["run_command", "grep_files"]:
                            enhanced_cli.show_status_message("Press Ctrl+C to cancel if needed", "info")
                    except ImportError:
                        # Fallback to original display if enhanced CLI not available
                        print(Fore.CYAN + "\n🔧 TOOL CALL DEBUG:")
                        print(Fore.WHITE + f"   📝 Name: {tool_name}")
                        print(Fore.WHITE + f"   ⚙️  Parameters: {tool_args}")

                        # Show cancellation instruction for potentially long-running tools
                        if tool_name in ["run_command", "grep_files"]:
                            print(Fore.YELLOW + "   ⌨️  Press Ctrl+C to cancel if needed")

                    # Execute tool
                    if tool_name in self.tools_map:
                        tool_result = self.tools_map[tool_name].invoke(tool_args)
                    else:
                        tool_result = f"Unknown tool: {tool_name}"

                    # Try to use enhanced CLI for result display
                    try:
                        from ..ui.enhanced_cli import enhanced_cli

                        # Show result with enhanced formatting
                        result_str = str(tool_result)

                        # Determine status based on result - only show error for actual errors
                        if (result_str.startswith("Error:") or
                            result_str.startswith("File not found:") or
                            result_str.startswith("Directory not found:") or
                            "Traceback" in result_str or
                            "Exception:" in result_str):
                            # This is an actual error - show up to 300 chars
                            error_preview = result_str[:300]
                            if len(result_str) > 300:
                                error_preview += "..."
                            enhanced_cli.show_status_message(f"❌ {error_preview}", "error")
                        else:
                            # For successful results, show more content (up to 2000 chars)
                            # This gives better visibility into what the tool is doing
                            if len(result_str) > 2000:
                                # For very long output, show first 1500 chars and indicate truncation
                                result_preview = result_str[:1500]
                                result_preview += f"\n... [truncated, showing first 1500 of {len(result_str)} chars]"
                            else:
                                # Show full result if under 2000 chars
                                result_preview = result_str

                            # Use a panel for better formatting of multi-line results
                            from rich.panel import Panel
                            from rich.text import Text
                            result_text = Text(f"✓ Result:\n{result_preview}", style="green")
                            panel = Panel(
                                result_text,
                                border_style="green",
                                expand=False,
                                padding=(0, 1)
                            )
                            enhanced_cli.console.print(panel)

                        enhanced_cli.print_separator()
                    except ImportError:
                        # Fallback to original display
                        print(
                            Fore.GREEN
                            + f"   ✅ Result (first 500 chars): {str(tool_result)[:500]}..."
                        )
                        print(
                            Fore.BLUE
                            + f"   📏 Result length: {len(str(tool_result))} characters"
                        )
                        print(Fore.CYAN + "=" * 50)

                    # Add tool result
                    self.messages.append(
                        ToolMessage(
                            content=str(tool_result)[
                                : Config.MAX_OUTPUT_LENGTH
                            ],  # Limit size
                            tool_call_id=tool_call["id"],
                        )
                    )

                    # Memory trigger: Detect first TodoWrite with >N_STEPS_LIMIT
                    if (tool_name.lower() == "todowrite" and
                        "todos" in tool_args and
                        is_first_time_planning):

                        todo_step_count = len(tool_args["todos"])
                        is_first_time_planning = False

                        if todo_step_count > N_STEPS_LIMIT:
                            should_call_replan = True

                # Get next response from LLM
                response = self.llm_with_tools.invoke(self.messages)

            except KeyboardInterrupt:
                print(Fore.YELLOW + "\n⚠️  Tool execution interrupted by user (Ctrl+C)")
                print(Fore.GREEN + "🔄 Returning to main prompt...")
                return "Tool execution was cancelled by user."

            self.messages.append(response)

            # Only show token usage if debugging is enabled
            if os.getenv("SHOW_TOKEN_USAGE", "").lower() == "true":
                if hasattr(response, "response_metadata"):
                    usage_info = self.provider.format_usage_info(response.response_metadata)
                    if usage_info:
                        print(Fore.BLUE + f"📊 After tools - {usage_info}")

        # Save the final task completion response before memory trigger
        final_response = response

        # Memory trigger: After loop completes, remind LLM to consider storing learnings
        print(Fore.YELLOW + "\n[MEMORY] Reminding to consider memory-store...")
        self.messages.append(
            HumanMessage(content="Consider storing learnings from this task using memory-store agent if valuable patterns were discovered.")
        )
        memory_response = self.llm_with_tools.invoke(self.messages)
        self.messages.append(memory_response)

        # Convert final task response to string before returning
        if isinstance(final_response.content, list):
            return " ".join(str(item) for item in final_response.content)
        return final_response.content

    def reset(self):
        """Reset conversation but keep cached system prompt and memory context."""
        from colorama import Fore

        if len(self.messages) >= 2 and "<system-reminder>" in str(
            self.messages[1].content
        ):
            # Keep system prompt and memory context
            self.messages = [self.messages[0], self.messages[1]]
            print(
                Fore.YELLOW
                + "🔄 Conversation reset (keeping cached system prompt and memory context)"
            )
        else:
            # Only keep system prompt
            self.messages = [self.messages[0]]
            print(Fore.YELLOW + "🔄 Conversation reset (keeping cached system prompt)")
