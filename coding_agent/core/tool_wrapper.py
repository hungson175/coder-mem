"""
Tool execution wrapper with enhanced CLI display
Provides visual feedback for tool operations
"""

from typing import Any, Dict, Optional, Callable
from functools import wraps
import time
import traceback


def with_enhanced_display(tool_func: Callable) -> Callable:
    """
    Decorator to add enhanced CLI display to tool executions.

    This wrapper:
    1. Shows tool execution panel before running
    2. Displays progress during execution
    3. Shows results or errors with appropriate styling
    """

    @wraps(tool_func)
    def wrapper(*args, **kwargs) -> Any:
        # Try to import enhanced CLI, fall back gracefully if not available
        try:
            from coding_agent.ui.enhanced_cli import enhanced_cli
            use_enhanced = True
        except ImportError:
            use_enhanced = False

        tool_name = tool_func.__name__.replace('_', ' ').title()

        # Extract description from kwargs or docstring
        description = kwargs.get('description', '')
        if not description and tool_func.__doc__:
            # Get first line of docstring
            description = tool_func.__doc__.strip().split('\n')[0]
            if len(description) > 80:
                description = description[:77] + "..."

        # Show tool execution start
        if use_enhanced:
            # Filter out large content from params display
            display_params = {}
            for key, value in kwargs.items():
                if key not in ['content', 'prompt', 'todos', 'messages']:
                    if isinstance(value, str) and len(value) > 100:
                        display_params[key] = value[:97] + "..."
                    elif isinstance(value, list) and len(str(value)) > 100:
                        display_params[key] = f"[{len(value)} items]"
                    else:
                        display_params[key] = value

            enhanced_cli.show_tool_execution(tool_name, description, display_params)

        # Execute the tool
        start_time = time.time()
        try:
            # For long-running tools, show progress
            if tool_name in ['Bash', 'Web Search', 'Web Fetch', 'Task']:
                if use_enhanced:
                    with enhanced_cli.progress_context(f"Executing {tool_name}...") as update:
                        result = tool_func(*args, **kwargs)
                        update()
                else:
                    result = tool_func(*args, **kwargs)
            else:
                result = tool_func(*args, **kwargs)

            duration = time.time() - start_time

            # Show success for certain tools
            if use_enhanced and tool_name in ['Write', 'Edit', 'Multi Edit']:
                enhanced_cli.show_status_message(f"{tool_name} completed successfully", "success")

            # Show command summary for Bash
            if use_enhanced and tool_name == 'Bash' and 'command' in kwargs:
                # Try to extract exit code from result if available
                exit_code = 0 if "Error" not in str(result) else 1
                enhanced_cli.show_command_execution_summary(
                    kwargs['command'][:100],
                    exit_code,
                    duration
                )

            return result

        except Exception as e:
            duration = time.time() - start_time

            # Show error
            if use_enhanced:
                enhanced_cli.show_status_message(f"{tool_name} failed: {str(e)}", "error")
                if tool_name == 'Bash' and 'command' in kwargs:
                    enhanced_cli.show_command_execution_summary(
                        kwargs['command'][:100],
                        1,
                        duration
                    )

            # Re-raise the exception
            raise

    return wrapper


def wrap_agent_tools(agent: Any) -> None:
    """
    Wrap all tools of an agent with enhanced display.

    Args:
        agent: The CodingAgent instance with tools to wrap
    """
    try:
        # Check if agent has tools
        if not hasattr(agent, 'tools'):
            return

        # Wrap each tool
        for i, tool in enumerate(agent.tools):
            if hasattr(tool, 'func'):
                # Wrap the tool's function
                original_func = tool.func
                tool.func = with_enhanced_display(original_func)

        print("✨ Enhanced CLI display activated for tools")

    except Exception as e:
        # Silently fail if wrapping doesn't work
        pass


def show_agent_phase(phase_name: str, description: str = "", style: str = "blue") -> None:
    """
    Show a phase transition in the agent's execution.

    Args:
        phase_name: Name of the phase
        description: Optional description
        style: Color style for the phase
    """
    try:
        from coding_agent.ui.enhanced_cli import enhanced_cli
        enhanced_cli.show_phase_transition(phase_name, description, style)
    except ImportError:
        # Fall back to simple print if enhanced CLI not available
        print(f"\n{'=' * 60}")
        print(f"PHASE: {phase_name}")
        if description:
            print(f"  {description}")
        print(f"{'=' * 60}\n")