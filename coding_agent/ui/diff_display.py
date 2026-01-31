"""
Diff display utilities for showing code changes in Claude Code style.
Provides beautiful diff visualization for Edit and Write tools.
"""

import difflib
from typing import List, Optional, Tuple
from rich.console import Console
from rich.syntax import Syntax
from rich.text import Text
from rich.panel import Panel
from rich import box


class DiffDisplay:
    """Display code diffs in a beautiful, Claude Code-like format."""

    def __init__(self):
        self.console = Console()

    def show_edit_diff(self, file_path: str, old_content: str, new_content: str,
                      edit_description: Optional[str] = None) -> None:
        """
        Display a diff for an Edit operation.

        Args:
            file_path: Path to the file being edited
            old_content: Original content
            new_content: New content after edit
            edit_description: Optional description of the edit
        """
        # Generate unified diff
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=file_path,
            tofile=file_path,
            lineterm='',
            n=3  # Context lines
        )

        # Create formatted diff text
        diff_text = Text()

        # Add header
        diff_text.append(f"● Update({file_path})\n", style="bold cyan")

        # Count changes
        additions = sum(1 for line in new_lines if line not in old_lines)
        deletions = sum(1 for line in old_lines if line not in new_lines)

        diff_text.append(f"  └─ Updated {file_path} with ", style="dim")
        diff_text.append(f"{additions} additions", style="green")
        diff_text.append(" and ", style="dim")
        diff_text.append(f"{deletions} removals\n", style="red")

        if edit_description:
            diff_text.append(f"     {edit_description}\n", style="italic dim")

        # Process diff lines
        line_num_old = 0
        line_num_new = 0
        in_hunk = False

        for line in diff:
            if line.startswith('---') or line.startswith('+++'):
                continue  # Skip file headers
            elif line.startswith('@@'):
                # Parse hunk header to get line numbers
                import re
                match = re.match(r'@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@', line)
                if match:
                    line_num_old = int(match.group(1))
                    line_num_new = int(match.group(2))
                    in_hunk = True
                continue
            elif in_hunk:
                if line.startswith('-'):
                    # Deletion - red background
                    diff_text.append(f"  {line_num_old:4d} ", style="dim red")
                    diff_text.append("- ", style="bold red")
                    diff_text.append(line[1:].rstrip() + "\n", style="on red")
                    line_num_old += 1
                elif line.startswith('+'):
                    # Addition - green background
                    diff_text.append(f"  {line_num_new:4d} ", style="dim green")
                    diff_text.append("+ ", style="bold green")
                    diff_text.append(line[1:].rstrip() + "\n", style="on green")
                    line_num_new += 1
                else:
                    # Context line
                    diff_text.append(f"  {line_num_old:4d} ", style="dim")
                    diff_text.append("  ", style="dim")
                    diff_text.append(line.rstrip() + "\n", style="dim")
                    line_num_old += 1
                    line_num_new += 1

        # Display the diff
        self.console.print(diff_text)

    def show_write_diff(self, file_path: str, content: str, is_new_file: bool = True) -> None:
        """
        Display content for a Write operation (all green for new files).

        Args:
            file_path: Path to the file being written
            content: Content being written
            is_new_file: Whether this is a new file creation
        """
        # Create formatted text
        write_text = Text()

        # Add header
        if is_new_file:
            write_text.append(f"● Create({file_path})\n", style="bold green")
            write_text.append(f"  └─ Created new file: {file_path}\n", style="dim green")
        else:
            write_text.append(f"● Write({file_path})\n", style="bold yellow")
            write_text.append(f"  └─ Overwrote file: {file_path}\n", style="dim yellow")

        # Add content with line numbers (all green for new files)
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            if is_new_file:
                write_text.append(f"  {i:4d} ", style="dim green")
                write_text.append("+ ", style="bold green")
                write_text.append(line + "\n", style="on green")
            else:
                write_text.append(f"  {i:4d} ", style="dim")
                write_text.append("  ", style="dim")
                write_text.append(line + "\n")

        # Display the content
        self.console.print(write_text)

    def show_multi_edit_diff(self, file_path: str, edits: List[Tuple[str, str]],
                            original_content: str) -> None:
        """
        Display diffs for MultiEdit operation.

        Args:
            file_path: Path to the file being edited
            edits: List of (old_string, new_string) tuples
            original_content: Original file content before any edits
        """
        # Create header
        diff_text = Text()
        diff_text.append(f"● MultiEdit({file_path})\n", style="bold cyan")
        diff_text.append(f"  └─ Applying {len(edits)} edits to {file_path}\n", style="dim")

        self.console.print(diff_text)

        # Apply edits sequentially and show diffs
        current_content = original_content
        for i, (old_str, new_str) in enumerate(edits, 1):
            # Apply this edit
            if old_str in current_content:
                new_content = current_content.replace(old_str, new_str, 1)

                # Show mini diff for this edit
                edit_text = Text()
                edit_text.append(f"\n  Edit {i}/{len(edits)}:\n", style="bold dim")

                # Show what's being replaced
                old_lines = old_str.splitlines()
                new_lines = new_str.splitlines()

                # Show deletions
                if old_lines:
                    for line in old_lines[:3]:  # Show first 3 lines
                        edit_text.append("    - ", style="bold red")
                        edit_text.append(line[:80] + "\n", style="on red")
                    if len(old_lines) > 3:
                        edit_text.append(f"    ... ({len(old_lines) - 3} more lines)\n", style="dim red")

                # Show additions
                if new_lines:
                    for line in new_lines[:3]:  # Show first 3 lines
                        edit_text.append("    + ", style="bold green")
                        edit_text.append(line[:80] + "\n", style="on green")
                    if len(new_lines) > 3:
                        edit_text.append(f"    ... ({len(new_lines) - 3} more lines)\n", style="dim green")

                self.console.print(edit_text)
                current_content = new_content
            else:
                error_text = Text()
                error_text.append(f"\n  Edit {i}/{len(edits)}: ", style="bold red")
                error_text.append("FAILED - string not found\n", style="red")
                self.console.print(error_text)

    def show_file_operation_summary(self, operation: str, file_path: str,
                                   success: bool = True, details: Optional[str] = None) -> None:
        """
        Show a summary panel for file operations.

        Args:
            operation: Type of operation (Edit, Write, Create, etc.)
            file_path: Path to the file
            success: Whether the operation succeeded
            details: Optional additional details
        """
        # Create summary text
        summary = Text()

        if success:
            summary.append("✓ ", style="bold green")
            summary.append(f"{operation} completed successfully\n", style="green")
        else:
            summary.append("✗ ", style="bold red")
            summary.append(f"{operation} failed\n", style="red")

        summary.append(f"File: {file_path}\n", style="cyan")

        if details:
            summary.append(f"{details}\n", style="dim")

        # Create and display panel
        panel = Panel(
            summary,
            title=f"[bold]File Operation: {operation}[/bold]",
            border_style="green" if success else "red",
            box=box.ROUNDED,
            padding=(0, 1),
            expand=False
        )

        self.console.print(panel)


# Singleton instance for easy import
diff_display = DiffDisplay()