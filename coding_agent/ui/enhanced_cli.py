"""
Enhanced Rich CLI with progress indicators, panels, and better visual styling
Inspired by the deep research system's UI patterns
"""

import sys
from typing import Optional, Dict, List, Any
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, BarColumn
from rich.text import Text
from rich.table import Table
from rich.markdown import Markdown
from rich.live import Live
from rich.layout import Layout
from rich.columns import Columns
from rich import box
from contextlib import contextmanager


class EnhancedCLI:
    """Enhanced CLI with beautiful Rich components"""

    def __init__(self):
        self.console = Console()
        self.current_phase = None
        self.phase_counter = 0

    def show_startup_panel(self, working_dir: str, agent_count: Dict = None):
        """Show an enhanced startup panel with system info"""
        startup_text = Text()
        startup_text.append("🚀 ", style="bold")
        startup_text.append("SONPH-CODE AGENT", style="bold magenta")
        startup_text.append("\n\n", style="")

        # Working directory
        startup_text.append("📁 ", style="")
        startup_text.append("Working Directory: ", style="dim")
        startup_text.append(f"{working_dir}\n", style="yellow")

        # Agent info if available
        if agent_count:
            startup_text.append("🤖 ", style="")
            startup_text.append("Available Agents: ", style="dim")
            startup_text.append(f"{agent_count['total']} ", style="green")
            startup_text.append(f"({agent_count['built_in']} built-in, ", style="dim")
            startup_text.append(f"{agent_count['user_defined']} custom)\n", style="dim")

        # Timestamp
        startup_text.append("🕐 ", style="")
        startup_text.append("Started: ", style="dim")
        startup_text.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), style="cyan")

        panel = Panel(
            startup_text,
            title="[bold cyan]═══ CODING AGENT INITIALIZED ═══[/bold cyan]",
            border_style="cyan",
            box=box.DOUBLE,
            padding=(1, 2),
            expand=False
        )
        self.console.print(panel)

    def show_phase_transition(self, phase_name: str, description: str = "", style: str = "blue"):
        """Display a phase transition with visual separators"""
        self.phase_counter += 1
        self.current_phase = phase_name

        # Visual separator
        self.console.print("\n" + "═" * 80, style="bright_black")

        # Phase panel
        phase_text = Text()
        phase_text.append(f"PHASE {self.phase_counter}: ", style="bold")
        phase_text.append(phase_name.upper(), style=f"bold {style}")

        if description:
            phase_text.append("\n", style="")
            phase_text.append(description, style="dim")

        panel = Panel(
            phase_text,
            border_style=style,
            box=box.ROUNDED,
            padding=(0, 1),
            expand=False
        )
        self.console.print(panel)

    @contextmanager
    def progress_context(self, description: str, total: Optional[int] = None):
        """Context manager for showing progress with spinner or bar"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn() if total else TextColumn(""),
            TimeElapsedColumn(),
            console=self.console,
            transient=True,
        ) as progress:
            task = progress.add_task(description, total=total)
            try:
                yield lambda completed=1: progress.update(task, advance=completed)
            finally:
                progress.update(task, completed=total if total else 100)

    def show_tool_execution(self, tool_name: str, description: str = "", params: Dict = None):
        """Show tool execution with styled panel"""
        tool_text = Text()
        tool_text.append("🔧 ", style="")
        tool_text.append(f"Executing: ", style="dim")
        tool_text.append(tool_name, style="bold yellow")

        if description:
            tool_text.append("\n", style="")
            tool_text.append(f"📝 {description}", style="italic dim")

        if params:
            tool_text.append("\n", style="")
            tool_text.append("Parameters:", style="dim")
            for key, value in params.items():
                if key not in ['content', 'prompt']:  # Skip large content
                    tool_text.append(f"\n  • {key}: ", style="dim")
                    tool_text.append(str(value)[:100], style="cyan dim")

        panel = Panel(
            tool_text,
            border_style="yellow",
            box=box.ROUNDED,
            padding=(0, 1),
            expand=False
        )
        self.console.print(panel)

    def show_todo_list(self, todos: List[Dict[str, Any]]):
        """Display todo list with beautiful formatting"""
        if not todos:
            return

        # Create a table for todos
        table = Table(
            title="📋 Task List",
            box=box.ROUNDED,
            border_style="blue",
            show_lines=True,
            expand=False
        )

        table.add_column("#", width=3, justify="center")
        table.add_column("", width=3, justify="center")  # Status icon
        table.add_column("Task", style="white", no_wrap=False)
        table.add_column("Status", style="dim", width=12)

        status_icons = {
            "pending": "⏳",
            "in_progress": "🔄",
            "completed": "✅"
        }

        status_colors = {
            "pending": "yellow",
            "in_progress": "cyan",
            "completed": "green"
        }

        for idx, todo in enumerate(todos, 1):
            status = todo.get('status', 'pending')
            icon = status_icons.get(status, "❓")

            # Always use content, not activeForm
            task_text = todo.get('content', '')

            # Apply strikethrough for completed tasks
            if status == 'completed':
                task_text = Text(task_text, style="strike dim")
            else:
                task_text = Text(task_text)

            table.add_row(
                str(idx),
                icon,
                task_text,
                Text(status.replace('_', ' ').title(), style=status_colors.get(status, "white"))
            )

        self.console.print(table)

    def show_result_panel(self, title: str, content: str, style: str = "green"):
        """Show a result panel with formatted content"""
        # If content is markdown-like, render it
        if any(marker in content for marker in ['#', '**', '```', '- ', '* ']):
            rendered_content = Markdown(content)
        else:
            rendered_content = Text(content)

        panel = Panel(
            rendered_content,
            title=f"[bold {style}]{title}[/bold {style}]",
            border_style=style,
            box=box.DOUBLE_EDGE,
            padding=(1, 2),
            expand=False
        )
        self.console.print(panel)

    def show_status_message(self, message: str, status_type: str = "info"):
        """Show status message with semantic colors"""
        status_styles = {
            "success": ("✅", "green"),
            "error": ("❌", "red"),
            "warning": ("⚠️", "yellow"),
            "info": ("ℹ️", "blue"),
            "processing": ("⚙️", "magenta"),
            "complete": ("✨", "bold green")
        }

        icon, color = status_styles.get(status_type, ("•", "white"))

        styled_text = Text()
        styled_text.append(f"{icon} ", style="")
        styled_text.append(message, style=color)

        self.console.print(styled_text)

    def show_command_execution_summary(self, command: str, exit_code: int, duration: float = None):
        """Show command execution summary with status"""
        summary_text = Text()

        # Command
        summary_text.append("Command: ", style="dim")
        summary_text.append(f"{command}\n", style="cyan")

        # Exit code with color
        summary_text.append("Exit Code: ", style="dim")
        if exit_code == 0:
            summary_text.append(f"{exit_code} ✓", style="green")
        else:
            summary_text.append(f"{exit_code} ✗", style="red")

        # Duration if provided
        if duration:
            summary_text.append("\nDuration: ", style="dim")
            summary_text.append(f"{duration:.2f}s", style="yellow")

        panel = Panel(
            summary_text,
            title="[bold]Command Summary[/bold]",
            border_style="green" if exit_code == 0 else "red",
            box=box.ROUNDED,
            padding=(0, 1),
            expand=False
        )
        self.console.print(panel)

    def show_file_operation(self, operation: str, file_path: str, details: Dict = None):
        """Show file operation with visual feedback"""
        op_icons = {
            "read": "📖",
            "write": "✍️",
            "edit": "📝",
            "create": "➕",
            "delete": "🗑️",
            "search": "🔍"
        }

        op_text = Text()
        op_text.append(f"{op_icons.get(operation, '📄')} ", style="")
        op_text.append(f"{operation.upper()}: ", style="bold")
        op_text.append(file_path, style="cyan")

        if details:
            for key, value in details.items():
                op_text.append(f"\n  {key}: ", style="dim")
                op_text.append(str(value), style="yellow dim")

        self.console.print(op_text)

    def print_separator(self, char: str = "─", width: int = 80, style: str = "bright_black"):
        """Print a visual separator line"""
        self.console.print(char * width, style=style)

    def show_model_switch(self, from_model: str, to_model: str):
        """Show model switching animation"""
        switch_text = Text()
        switch_text.append("🔄 Model Switch\n", style="bold yellow")
        switch_text.append("From: ", style="dim")
        switch_text.append(f"{from_model}\n", style="red")
        switch_text.append("  To: ", style="dim")
        switch_text.append(f"{to_model}", style="green")

        panel = Panel(
            switch_text,
            border_style="yellow",
            box=box.DOUBLE,
            padding=(0, 1),
            expand=False
        )
        self.console.print(panel)


# Export a singleton instance for easy access
enhanced_cli = EnhancedCLI()