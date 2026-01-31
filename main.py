"""Main entry point and interactive interface for the coding agent."""

import os
from typing import Optional
from colorama import Fore, Style, init
from langchain_core.messages import HumanMessage

from coding_agent.core.agent import CodingAgent

# Initialize colorama
init(autoreset=True)


def switch_agent_provider(
    current_agent: CodingAgent, provider_name: str, model_name: Optional[str] = None
) -> Optional[CodingAgent]:
    """Switch agent provider while preserving conversation history."""
    try:

        # Extract conversation history (excluding system messages and memory context)
        conversation_history = []

        # Skip system message(s) and memory context - find first actual user interaction
        start_idx = None
        for i, msg in enumerate(current_agent.messages):
            if isinstance(msg, HumanMessage) and not (
                "<system-reminder>" in str(msg.content) or len(str(msg.content)) > 1000
            ):
                start_idx = i
                break

        # Extract meaningful conversation
        if start_idx is not None:
            conversation_history = current_agent.messages[start_idx:]

        # Determine model name - use provider defaults if not specified
        if not model_name:
            provider_defaults = {
                "claude": "claude-sonnet-4-20250514",
                "sonnet": "claude-sonnet-4-20250514",
                "deepseek": "deepseek-chat",
                "ds": "deepseek-chat",
                "grok": "grok-4-fast-reasoning",
                "xai": "grok-4-fast-reasoning",
            }
            model_name = provider_defaults.get(provider_name.lower(), "claude-sonnet-4-20250514")

        # Create new agent with new provider
        new_agent = CodingAgent(model_name=model_name, provider_name=provider_name)

        # Restore conversation history with new provider's caching
        if conversation_history:
            print(Fore.YELLOW + f"🔄 Restoring {len(conversation_history)} messages...")

            for msg in conversation_history:
                if isinstance(msg, HumanMessage):
                    # Re-cache user messages with new provider
                    content = msg.content
                    if isinstance(content, list):
                        # Extract text from complex content
                        content = str(content)
                    cached_content = new_agent.provider.create_cached_message(content)
                    new_agent.messages.append(HumanMessage(content=cached_content))
                else:
                    # Keep other messages as-is (ToolMessage, AIMessage, etc.)
                    new_agent.messages.append(msg)

        # Preserve working directory and update system prompt
        new_agent.working_dir = current_agent.working_dir
        new_agent._update_system_prompt_with_working_dir()

        return new_agent

    except Exception as e:
        print(Fore.RED + f"❌ Failed to switch provider: {str(e)}")
        return None


# Initialize the customized agents system at startup
def initialize_agents_system():
    """Initialize the agents system with dynamic Task tool description."""
    try:
        from coding_agent.tools.task_tool import initialize_task_tool_description
        from coding_agent.core.agent_registry import AgentRegistry

        # Initialize agent registry (discovers available agents)
        registry = AgentRegistry()
        agent_count = registry.get_agent_count()

        print(
            Fore.CYAN
            + Style.DIM
            + f"🔧 Initializing agents system... Found {agent_count['total']} agents ({agent_count['built_in']} built-in, {agent_count['user_defined']} user-defined)"
        )

        # Initialize Task tool description based on available agents
        description = initialize_task_tool_description()

        print(
            Fore.GREEN
            + Style.DIM
            + f"✅ Task tool initialized with dynamic description ({len(description)} characters)"
        )

    except Exception as e:
        print(Fore.YELLOW + f"⚠️  Warning: Failed to initialize agents system: {e}")
        print(Fore.YELLOW + "🔄 Falling back to basic Task tool functionality")


# Initialize the agents system
initialize_agents_system()


def demo():
    """Demo the coding agent."""
    print(Fore.CYAN + "\n" + "=" * 70)
    print(Fore.GREEN + "🚀 DEMO: Coding Agent")
    print(Fore.CYAN + "=" * 70)

    agent = CodingAgent()

    # Demo tasks
    tasks = [
        "List all Python files in the current directory",
        "Create a simple hello_world.py file that prints 'Hello from Coding Agent!'",
        "Run the hello_world.py file we just created",
        "Create a fibonacci.py with a function to calculate fibonacci numbers, then test it",
    ]

    for i, task in enumerate(tasks, 1):
        print(Fore.YELLOW + f"\n📝 Task {i}: {task}")
        response = agent.chat(task)
        print(Fore.GREEN + f"\n✅ Response: {response[:500]}...")

        if i < len(tasks):
            input(Fore.WHITE + "\nPress Enter for next task...")

    print(Fore.CYAN + "\n" + "=" * 70)
    print(Fore.GREEN + "🎉 Demo completed! Files created in current directory.")
    print(Fore.CYAN + "=" * 70)


def interactive():
    """Interactive coding session."""
    from coding_agent.utils.banner import show_startup_screen
    from coding_agent.core.agent_registry import AgentRegistry
    from coding_agent.ui import RichCLI
    from coding_agent.ui.enhanced_cli import enhanced_cli

    # Get agent information for startup screen
    try:
        registry = AgentRegistry()
        agent_count = registry.get_agent_count()
    except:
        agent_count = None

    # Get working directory
    current_dir = os.getcwd()

    # Initialize Rich CLI
    rich_cli = RichCLI()

    # Show beautiful startup screen
    show_startup_screen(agent_count=agent_count, working_dir=current_dir)

    # Show enhanced startup panel
    enhanced_cli.show_startup_panel(current_dir, agent_count)

    # Show rich welcome panel
    rich_cli.show_welcome(current_dir)

    # Check for LLM provider from command line, default to grok
    llm_provider = os.getenv("SONPH_LLM_PROVIDER", "grok")
    agent = CodingAgent(provider_name=llm_provider)

    # Show quick command reference
    print(Fore.YELLOW + Style.BRIGHT + "Quick Commands:")
    print(Fore.CYAN + "  quit/exit" + Fore.WHITE + " - Exit the program")
    print(Fore.CYAN + "  reset" + Fore.WHITE + " - Clear conversation history")
    print(Fore.CYAN + "  cd <dir>" + Fore.WHITE + " - Change working directory")
    print(
        Fore.CYAN + "  /init" + Fore.WHITE + " - Analyze codebase and create CLAUDE.md"
    )
    print(Fore.CYAN + "  /commands" + Fore.WHITE + " - List all available commands")
    print(Fore.CYAN + "  /memory" + Fore.WHITE + " - View current memory context")
    print(
        Fore.CYAN
        + "  /model"
        + Fore.WHITE
        + " - Switch LLM provider (claude/deepseek/grok)"
    )
    print()
    print(Fore.YELLOW + "💡 Press Ctrl+C to cancel any long-running operation")
    print(Fore.BLACK + Style.BRIGHT + "─" * 80)
    print()

    # Set working directory if provided via environment
    initial_dir = os.getenv("INITIAL_DIR")
    if initial_dir and os.path.isdir(initial_dir):
        agent.set_working_dir(initial_dir)

    while True:
        # Use rich CLI for input with autocomplete
        user_input = rich_cli.get_input()
        if user_input is None:  # Ctrl+C or EOF
            rich_cli.print_response("\n👋 Goodbye!", "green")
            break

        if user_input.lower() in ["quit", "exit", "/quit", "/exit"]:
            rich_cli.print_response("\n👋 Goodbye!\n", "green")
            break

        if user_input.lower() in ["reset", "/reset"]:
            agent.reset()
            enhanced_cli.show_status_message("Conversation history cleared", "success")
            continue

        if user_input.lower() in ["pwd", "/pwd"]:
            rich_cli.print_response(f"📁 Current working directory: {agent.working_dir}", "blue")
            continue

        if user_input.lower().startswith("cd ") or user_input.lower().startswith("/cd "):
            if user_input.lower().startswith("/cd"):
                new_dir = user_input[4:].strip()
            else:
                new_dir = user_input[3:].strip()
            if os.path.isdir(new_dir):
                agent.set_working_dir(new_dir)
                enhanced_cli.show_status_message(f"Changed to: {agent.working_dir}", "success")
            else:
                enhanced_cli.show_status_message(f"Directory not found: {new_dir}", "error")
            continue

        # Handle native and custom commands
        if user_input.strip().startswith("/"):
            parts = user_input.strip()[1:].split(" ", 1)
            command_name = parts[0]
            arguments = parts[1] if len(parts) > 1 else ""

            # Check if this is a native command first
            if agent.native_command_manager.is_native_command(command_name):
                print(Fore.CYAN + f"\n🔧 Executing native command: /{command_name}")

                try:
                    processed_message = (
                        agent.native_command_manager.process_native_command(
                            command_name, arguments
                        )
                    )
                    response = agent.chat(processed_message)
                    print(Fore.GREEN + f"\n🤖 Agent: {response}")
                except Exception as e:
                    print(Fore.RED + f"❌ Error executing /{command_name}: {str(e)}")
                continue

            # Check for special commands that aren't in the native command system yet
            elif command_name == "commands":
                print(Fore.CYAN + "\n📋 Available Commands:")
                print(Fore.CYAN + "=" * 40)

                # Show native commands
                native_commands = agent.native_command_manager.list_native_commands()
                if native_commands:
                    print(Fore.YELLOW + "Native Commands:")
                    for cmd in sorted(native_commands):
                        print(Fore.WHITE + f"  /{cmd}")

                # Show custom commands
                custom_commands = agent.command_manager.list_commands()
                if custom_commands:
                    print(Fore.YELLOW + "Custom Commands:")
                    for cmd in sorted(custom_commands):
                        print(Fore.WHITE + f"  /{cmd}")
                    print(
                        Fore.YELLOW + f"\nFound {len(custom_commands)} custom commands"
                    )
                    print(Fore.YELLOW + "Usage: /<command_name> [arguments]")
                else:
                    print(
                        Fore.YELLOW + "No custom commands found in ~/.claude/commands/"
                    )
                print(Fore.CYAN + "=" * 40)
                continue

            elif command_name == "memory":
                print(Fore.CYAN + "\n🧠 Current Memory Context:")
                print(Fore.CYAN + "=" * 50)
                if hasattr(agent, "memory_context") and agent.memory_context:
                    # Show first 1000 chars to avoid overwhelming output
                    context_preview = agent.memory_context[:1000]
                    if len(agent.memory_context) > 1000:
                        context_preview += f"\n\n... (truncated, total length: {len(agent.memory_context)} chars)"
                    print(Fore.WHITE + context_preview)
                else:
                    print(Fore.YELLOW + "No memory context loaded.")
                print(Fore.CYAN + "=" * 50)
                continue

            elif command_name == "model":
                from coding_agent.core.llm_providers import LLMProviderFactory

                if not arguments:
                    # Show current model and available providers
                    print(Fore.CYAN + "\n🤖 Current Model:")
                    print(Fore.GREEN + f"   {agent.get_current_provider_info()}")
                    print(Fore.CYAN + "\n📋 Available Providers:")
                    providers = LLMProviderFactory.get_available_providers()
                    for provider in providers:
                        print(Fore.WHITE + f"   {provider}")
                    print(Fore.CYAN + "\nUsage: /model <provider> [model_name]")
                    print(Fore.YELLOW + "Examples:")
                    print(Fore.WHITE + "   /model claude")
                    print(Fore.WHITE + "   /model deepseek")
                    print(Fore.WHITE + "   /model grok")
                    print(Fore.WHITE + "   /model sonnet claude-sonnet-4-20250514")
                    continue

                # Parse arguments
                parts = arguments.split()
                provider_name = parts[0]
                model_name = parts[1] if len(parts) > 1 else None

                # Switch provider with history preservation
                enhanced_cli.show_phase_transition(f"MODEL SWITCH", f"Switching to {provider_name}...", "yellow")
                old_model = agent.get_current_provider_info()
                new_agent = switch_agent_provider(agent, provider_name, model_name)
                if new_agent:
                    agent = new_agent
                    enhanced_cli.show_model_switch(old_model, agent.get_current_provider_info())
                    enhanced_cli.show_status_message("Conversation history preserved", "success")
                continue

            # Check if this is a custom command
            command = agent.command_manager.get_command(command_name)
            if command:
                print(Fore.CYAN + f"\n🔧 Executing custom command: /{command_name}")

                # Process the command
                processed_message = command.process(arguments)

                try:
                    response = agent.chat(processed_message)
                    rich_cli.print_response(f"\n🤖 Agent: {response}", "green")
                except Exception as e:
                    rich_cli.print_error(f"Error executing /{command_name}: {str(e)}")
                continue
            else:
                print(Fore.RED + f"❌ Unknown command: /{command_name}")
                print(Fore.YELLOW + "Use '/commands' to see available commands")
                continue

        try:
            response = agent.chat(user_input)
            # Use enhanced CLI for better response display
            try:
                from coding_agent.ui.enhanced_cli import enhanced_cli
                if response and len(response.strip()) > 0:
                    # NEVER truncate the final response - always show in full
                    enhanced_cli.show_result_panel("🤖 Agent Response", response, "green")
                else:
                    enhanced_cli.show_status_message("Agent completed task (no response)", "success")
            except ImportError:
                rich_cli.print_response(f"\n🤖 Agent: {response}", "green")
        except Exception as e:
            rich_cli.print_error(f"Error: {str(e)}")


if __name__ == "__main__":
    interactive()
