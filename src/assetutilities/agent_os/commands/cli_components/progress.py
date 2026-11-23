# ABOUTME: Progress indicator and spinner for long-running CLI operations.
# ABOUTME: Extracted from cli.py ProgressIndicator class.
"""Progress indicators for the Agent OS CLI system."""

import sys
import time
import threading
from typing import List, Optional

class ProgressIndicator:
    """Progress indicator with spinner and step tracking."""

    def __init__(self, message: str, steps: Optional[List[str]] = None, 
                 show_spinner: bool = False, show_percentage: bool = False, total_items: int = 0):
        """Initialize progress indicator.
        
        Args:
            message: Main progress message
            steps: List of step descriptions
            show_spinner: Whether to show spinner animation
            show_percentage: Whether to show percentage
            total_items: Total number of items for percentage calculation
        """
        self.message = message
        self.steps = steps or []
        self.total_steps = len(self.steps) if self.steps else 1
        self.current_step = 0
        self.show_spinner = show_spinner
        self.show_percentage = show_percentage
        self.total_items = total_items
        self.current_items = 0
        
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.current_spinner = 0
        self.spinner_thread = None
        self.spinner_running = False

    def update(self, status_message: str) -> None:
        """Update progress with status message.
        
        Args:
            status_message: Current status message
        """
        if self.steps:
            step_info = f"[{self.current_step + 1}/{self.total_steps}]"
            print(f"\r{step_info} {status_message}", end="", flush=True)
        else:
            print(f"\r{self.message}: {status_message}", end="", flush=True)

    def advance(self, completion_message: str) -> None:
        """Advance to next step.
        
        Args:
            completion_message: Message for completed step
        """
        if self.current_step < self.total_steps:
            print(f"\r✓ {completion_message}")
            self.current_step += 1

    def complete(self, final_message: str) -> None:
        """Complete progress indication.
        
        Args:
            final_message: Final completion message
        """
        self.stop_spinner()
        print(f"\r✓ {final_message}")

    def spin(self) -> None:
        """Update spinner character."""
        if self.show_spinner:
            self.current_spinner = (self.current_spinner + 1) % len(self.spinner_chars)
            spinner_char = self.spinner_chars[self.current_spinner]
            print(f"\r{spinner_char} {self.message}", end="", flush=True)

    def start_spinner(self) -> None:
        """Start spinner in background thread."""
        if self.show_spinner and not self.spinner_running:
            self.spinner_running = True
            self.spinner_thread = threading.Thread(target=self._spinner_loop)
            self.spinner_thread.daemon = True
            self.spinner_thread.start()

    def stop_spinner(self) -> None:
        """Stop spinner thread."""
        if self.spinner_running:
            self.spinner_running = False
            if self.spinner_thread:
                self.spinner_thread.join(timeout=0.1)

    def _spinner_loop(self) -> None:
        """Spinner animation loop."""
        while self.spinner_running:
            self.spin()
            time.sleep(0.1)

    def update_percentage(self, completed_items: int) -> None:
        """Update percentage progress.
        
        Args:
            completed_items: Number of completed items
        """
        if self.show_percentage and self.total_items > 0:
            self.current_items = completed_items
            percentage = (completed_items / self.total_items) * 100
            print(f"\r{self.message}: {percentage:.1f}% ({completed_items}/{self.total_items})", end="", flush=True)


