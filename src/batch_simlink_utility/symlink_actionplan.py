import os
import shutil
import platform
from enum import Enum
from typing import List, Optional, Dict, Any
from pathlib import Path

class ActionStatus(Enum):
    PLANNED = "Planned"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    FAILED = "Failed"
    REVERSED = "Reversed"

class ActionItem:
    def __init__(self, src: str, dst_dir: str):
        self.src = Path(src)
        self.dst_dir = Path(dst_dir)
        self.status = ActionStatus.PLANNED
        self.error: Optional[str] = None
        self.original_location: Optional[Path] = None
        self.symlink_created: bool = False
        self.file_moved: bool = False
        
    def __str__(self):
        base_name = self.src.name
        target = self.dst_dir / base_name
        status_str = f"[{self.status.value}]"
        if self.error:
            status_str += f" (Error: {self.error})"
        return f"Move {self.src} -> {target} {status_str}"

    def execute(self):
        """Execute the move and symlink creation operation."""
        if self.status != ActionStatus.PLANNED:
            raise ValueError(f"Cannot execute action in {self.status.value} state")
        
        self.status = ActionStatus.IN_PROGRESS
        
        try:
            base_name = self.src.name
            target = self.dst_dir / base_name
            
            # Ensure destination directory exists
            self.dst_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if target already exists
            if target.exists():
                raise FileExistsError(f"Target {target} already exists")
            
            # Store original location for reversal
            self.original_location = self.src
            
            # Move the file/directory
            shutil.move(str(self.src), str(target))
            self.file_moved = True
            
            # Create symbolic link
            if platform.system() == "Windows":
                # On Windows, we need to use junction for directories or symlink for files
                if target.is_dir():
                    # Use junction for directories on Windows
                    os.system(f'mklink /J "{self.src}" "{target}"')
                else:
                    # Use symlink for files on Windows
                    os.system(f'mklink "{self.src}" "{target}"')
            else:
                # Unix-like systems
                self.src.symlink_to(target)
            
            self.symlink_created = True
            self.status = ActionStatus.COMPLETED
            
        except Exception as e:
            self.status = ActionStatus.FAILED
            self.error = str(e)
            # Attempt to reverse any partial changes
            self._reverse_partial()
            raise

    def reverse(self):
        """Reverse the operation, restoring the original state."""
        if self.status not in [ActionStatus.COMPLETED, ActionStatus.FAILED]:
            raise ValueError(f"Cannot reverse action in {self.status.value} state")
        
        try:
            # Remove the symbolic link
            if self.symlink_created and self.src.exists():
                if self.src.is_symlink():
                    self.src.unlink()
                elif platform.system() == "Windows":
                    # Remove junction/symlink on Windows
                    os.system(f'rmdir "{self.src}"')
                self.symlink_created = False
            
            # Move the file back to original location
            if self.file_moved and self.original_location:
                base_name = self.original_location.name
                target = self.dst_dir / base_name
                if target.exists():
                    shutil.move(str(target), str(self.original_location))
                    self.file_moved = False
            
            self.status = ActionStatus.REVERSED
            self.error = None
            
        except Exception as e:
            self.error = f"Reversal failed: {str(e)}"
            raise

    def _reverse_partial(self):
        """Reverse partial changes if execution failed."""
        try:
            if self.symlink_created and self.src.exists():
                if self.src.is_symlink():
                    self.src.unlink()
                elif platform.system() == "Windows":
                    os.system(f'rmdir "{self.src}"')
                self.symlink_created = False
            
            if self.file_moved and self.original_location:
                base_name = self.original_location.name
                target = self.dst_dir / base_name
                if target.exists():
                    shutil.move(str(target), str(self.original_location))
                    self.file_moved = False
        except Exception:
            # If reversal fails, we can't do much more
            pass

class ActionPlan:
    def __init__(self):
        self.items: List[ActionItem] = []
        self.execution_history: List[Dict[str, Any]] = []

    def add_item(self, item: ActionItem):
        self.items.append(item)

    def clear(self):
        self.items.clear()
        self.execution_history.clear()

    def execute_all(self) -> List[str]:
        """Execute all planned actions and return list of errors."""
        errors = []
        for item in self.items:
            if item.status == ActionStatus.PLANNED:
                try:
                    item.execute()
                    self.execution_history.append({
                        'action': item,
                        'status': 'success',
                        'timestamp': None  # Could add actual timestamp
                    })
                except Exception as e:
                    errors.append(f"{item.src}: {str(e)}")
                    self.execution_history.append({
                        'action': item,
                        'status': 'failed',
                        'error': str(e),
                        'timestamp': None
                    })
        return errors

    def reverse_all(self) -> List[str]:
        """Reverse all completed actions and return list of errors."""
        errors = []
        for item in reversed(self.items):  # Reverse in reverse order
            if item.status == ActionStatus.COMPLETED:
                try:
                    item.reverse()
                except Exception as e:
                    errors.append(f"Failed to reverse {item.src}: {str(e)}")
        return errors

    def get_status_summary(self) -> Dict[str, int]:
        """Get a summary of action statuses."""
        summary = {status.value: 0 for status in ActionStatus}
        for item in self.items:
            summary[item.status.value] += 1
        return summary

    def __str__(self):
        if not self.items:
            return "No actions planned"
        
        lines = []
        summary = self.get_status_summary()
        
        # Add summary header
        summary_line = " | ".join([f"{status}: {count}" for status, count in summary.items() if count > 0])
        lines.append(f"Action Plan Summary: {summary_line}")
        lines.append("-" * 50)
        
        # Add individual items
        for i, item in enumerate(self.items, 1):
            lines.append(f"{i}. {item}")
        
        return "\n".join(lines)