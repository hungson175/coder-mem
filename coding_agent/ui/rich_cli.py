"""
Rich CLI interface with autocomplete for sonph-code
Provides Claude Code-like autocomplete and UI elements
"""

import sys
import os
import io
from typing import Optional, Dict, List
from prompt_toolkit import prompt
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.styles import Style
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.history import InMemoryHistory
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Only force TTY mode in VS Code or other non-TTY environments
_tty_forced = False
if os.environ.get('TERM_PROGRAM') == 'vscode' and not sys.stdin.isatty():
    try:
        # Force TTY only for VS Code
        original_stdin = sys.stdin
        sys.stdin = io.TextIOWrapper(
            io.BufferedReader(io.FileIO(0, 'rb', closefd=False)),
            encoding='utf-8',
            line_buffering=True
        )
        _tty_forced = True
    except Exception:
        _tty_forced = False

class SonphCodeCompleter(Completer):
    """Custom completer for sonph-code with all commands and tools"""

    def __init__(self):
        # Native commands
        self.commands = {
            '/help': 'Show available commands and tools',
            '/exit': 'Exit sonph-code',
            '/quit': 'Exit sonph-code',
            '/reset': 'Reset conversation history',
            '/clear': 'Clear terminal screen',
            '/pwd': 'Show current working directory',
            '/cd': 'Change directory',
            '/init': 'Initialize CLAUDE.md for project',
            '/commands': 'List all available commands',
            '/memory': 'View current memory context',
            '/model': 'Switch LLM provider or show current model',
            '/context': 'Show context usage',
            '/compact': 'Clear history but keep summary',
            '/ecp': 'Execute prompt from file',
        }

        # Tool names with descriptions
        self.tools = {
            'Read': 'Read a file from the filesystem',
            'Write': 'Write content to a file',
            'Edit': 'Edit a file with find and replace',
            'MultiEdit': 'Make multiple edits to a file',
            'Bash': 'Execute a bash command',
            'BashOutput': 'Get output from background shell',
            'KillShell': 'Kill a background shell',
            'Grep': 'Search for patterns in files',
            'Glob': 'Find files by pattern',
            'LS': 'List directory contents',
            'TodoWrite': 'Manage todo list',
            'WebSearch': 'Search the web',
            'WebFetch': 'Fetch content from URL',
        }

        # Common file paths and patterns
        self.common_paths = [
            'README.md',
            'CLAUDE.md',
            'main.py',
            'coding_agent/',
            'experiments/',
            '.env',
            'pyproject.toml',
            'requirements.txt',
        ]

    def get_completions(self, document, complete_event):
        text = document.text

        # ONLY provide completions if text starts with /
        if not text.startswith('/'):
            return  # No completions for regular text

        # Command completions only when starting with /
        for cmd, desc in self.commands.items():
            if cmd.startswith(text):
                yield Completion(
                    cmd,
                    start_position=-len(text),
                    display=cmd,
                    display_meta=self._truncate(desc, 40),
                )

    def _truncate(self, text: str, max_len: int) -> str:
        """Truncate text with ellipsis if too long"""
        return text[:max_len] + '...' if len(text) > max_len else text


class RichCLI:
    """Rich CLI interface for sonph-code"""

    def __init__(self):
        self.console = Console()
        self.completer = SonphCodeCompleter()
        self.history = InMemoryHistory()

        # Custom style for prompt_toolkit (EXACT match from working demo)
        self.style = Style.from_dict({
            'completion-menu': 'bg:#008888 #ffffff',
            'completion-menu.completion.current': 'bg:#00aaaa #000000',
            'scrollbar.background': 'bg:#88aaaa',
            'scrollbar.button': 'bg:#222222',
        })

    def show_welcome(self, cwd: str):
        """Display welcome message"""
        welcome_text = f"""[bold green]Welcome to sonph-code![/bold green]

[yellow]/help[/yellow] for help, [yellow]/commands[/yellow] for all commands

[dim]cwd: {cwd}[/dim]"""

        panel = Panel(
            welcome_text,
            title="[bold blue]→ sonph-code[/bold blue]",
            border_style="green",
            padding=(1, 2),
        )
        self.console.print(panel)

    def get_prompt_message(self) -> HTML:
        """Get the prompt message with styling"""
        return HTML('<ansigreen><b>→ </b></ansigreen>')

    def get_bottom_toolbar(self) -> HTML:
        """Get bottom toolbar with hints"""
        return HTML(
            '<b>Commands:</b> /help /model /reset  '
            '<b>Tools:</b> Read Write Edit Bash  '
            '<b>Exit:</b> /exit or Ctrl+C'
        )

    def get_input(self, multiline: bool = False) -> Optional[str]:
        """Get user input with rich autocomplete"""
        # Always try to use rich prompt first since we force TTY mode
        try:
            # patch_stdout() ensures prompt_toolkit doesn't interfere with other output
            # mouse_support=False allows normal terminal scrolling with mouse wheel
            with patch_stdout():
                user_input = prompt(
                    self.get_prompt_message(),
                    completer=self.completer,
                    complete_style=CompleteStyle.MULTI_COLUMN,
                    style=self.style,
                    complete_while_typing=True,  # This enables gray inline suggestions!
                    mouse_support=False,  # Disabled to allow normal terminal scrolling
                )
                return user_input
        except (KeyboardInterrupt, EOFError):
            return None
        except Exception as e:
            # Fallback to simple input only if rich prompt fails
            # This should rarely happen now with forced TTY mode
            self.console.print(f"[yellow]Autocomplete unavailable, using simple mode[/yellow]")
            try:
                self.console.print("[green]→[/green] ", end="")
                return input()
            except (KeyboardInterrupt, EOFError):
                return None

    def print_response(self, text: str, style: str = ""):
        """Print a response with optional styling"""
        if style:
            self.console.print(f"[{style}]{text}[/{style}]")
        else:
            self.console.print(text)

    def print_tool_use(self, tool_name: str, description: str = ""):
        """Print tool usage notification"""
        styled_text = Text(f"🔧 Using tool: ", style="cyan")
        styled_text.append(tool_name, style="bold yellow")
        if description:
            styled_text.append(f" - {description}", style="dim")
        self.console.print(styled_text)

    def print_error(self, error: str):
        """Print error message"""
        self.console.print(f"[red]❌ Error: {error}[/red]")

    def print_success(self, message: str):
        """Print success message"""
        self.console.print(f"[green]✓ {message}[/green]")

    def clear_screen(self):
        """Clear the console screen"""
        self.console.clear()


# Set terminal environment if not set
if 'TERM' not in os.environ:
    os.environ['TERM'] = 'xterm-256color'