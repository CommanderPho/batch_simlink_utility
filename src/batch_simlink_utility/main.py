import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QPushButton, 
    QLabel, QHBoxLayout, QTreeView, QFileSystemModel, QTextEdit, QSplitter,
    QMessageBox, QProgressBar, QGroupBox, QGridLayout, QLineEdit, QPushButton,
    QDialog, QDialogButtonBox, QListWidget, QListWidgetItem, QMenu, QAction,
    QStatusBar, QToolBar, QComboBox
)
from PyQt5.QtCore import Qt, QDir, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QFont
from .symlink_actionplan import ActionPlan, ActionItem, ActionStatus
from .auth import AuthManager

class FileBrowserWidget(QWidget):
    """Enhanced file browser with better navigation and selection."""
    
    def __init__(self, title="File Browser", root_path=None):
        super().__init__()
        self.setup_ui(title, root_path)
        
    def setup_ui(self, title, root_path):
        layout = QVBoxLayout()
        
        # Header with title and path display
        header_layout = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 10, QFont.Bold))
        header_layout.addWidget(title_label)
        
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        header_layout.addWidget(self.path_edit)
        
        # Navigation buttons
        self.up_btn = QPushButton("↑")
        self.up_btn.setToolTip("Go to parent directory")
        self.up_btn.clicked.connect(self.go_up)
        header_layout.addWidget(self.up_btn)
        
        self.home_btn = QPushButton("🏠")
        self.home_btn.setToolTip("Go to home directory")
        self.home_btn.clicked.connect(self.go_home)
        header_layout.addWidget(self.home_btn)
        
        layout.addLayout(header_layout)
        
        # File system model and tree view
        self.model = QFileSystemModel()
        self.model.setRootPath(root_path or QDir.homePath())
        
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(root_path or QDir.homePath()))
        self.tree.setSelectionMode(QTreeView.ExtendedSelection)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSortingEnabled(True)
        
        # Context menu
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.tree)
        
        # Update path display when selection changes
        self.tree.selectionModel().selectionChanged.connect(self.update_path_display)
        self.update_path_display()
        
        self.setLayout(layout)
        
    def go_up(self):
        current_index = self.tree.rootIndex()
        parent_index = current_index.parent()
        if parent_index.isValid():
            self.tree.setRootIndex(parent_index)
            self.update_path_display()
            
    def go_home(self):
        home_path = QDir.homePath()
        self.tree.setRootIndex(self.model.index(home_path))
        self.update_path_display()
        
    def update_path_display(self):
        current_path = self.model.filePath(self.tree.rootIndex())
        self.path_edit.setText(current_path)
        
    def show_context_menu(self, position):
        menu = QMenu()
        
        # Add context menu actions
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.refresh_view)
        menu.addAction(refresh_action)
        
        menu.addSeparator()
        
        # Add "Set as Source" and "Set as Destination" actions
        set_source_action = QAction("Set as Source Directory", self)
        set_source_action.triggered.connect(lambda: self.set_as_directory("source"))
        menu.addAction(set_source_action)
        
        set_dest_action = QAction("Set as Destination Directory", self)
        set_dest_action.triggered.connect(lambda: self.set_as_directory("destination"))
        menu.addAction(set_dest_action)
        
        menu.exec_(self.tree.mapToGlobal(position))
        
    def refresh_view(self):
        self.model.setRootPath(self.model.rootPath())
        
    def set_as_directory(self, directory_type):
        # This will be connected to the parent widget
        pass
        
    def selected_paths(self):
        """Get list of selected file/directory paths."""
        indexes = self.tree.selectionModel().selectedIndexes()
        paths = set()
        for idx in indexes:
            if idx.column() == 0:  # Only process the name column
                path = self.model.filePath(idx)
                if path and os.path.exists(path):
                    paths.add(path)
        return list(paths)
        
    def get_current_directory(self):
        """Get the current directory being displayed."""
        return self.model.filePath(self.tree.rootIndex())

class ActionPlanWidget(QWidget):
    """Widget for displaying and managing the action plan."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Action Plan")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(title_label)
        
        self.clear_btn = QPushButton("Clear Plan")
        self.clear_btn.clicked.connect(self.clear_plan)
        header_layout.addWidget(self.clear_btn)
        
        layout.addLayout(header_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Action plan display
        self.plan_display = QTextEdit()
        self.plan_display.setReadOnly(True)
        self.plan_display.setFont(QFont("Consolas", 9))
        layout.addWidget(self.plan_display)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.build_btn = QPushButton("Build Plan")
        self.build_btn.clicked.connect(self.build_plan_requested)
        button_layout.addWidget(self.build_btn)
        
        self.execute_btn = QPushButton("Execute Plan")
        self.execute_btn.clicked.connect(self.execute_plan_requested)
        self.execute_btn.setEnabled(False)
        button_layout.addWidget(self.execute_btn)
        
        self.reverse_btn = QPushButton("Reverse All")
        self.reverse_btn.clicked.connect(self.reverse_plan_requested)
        self.reverse_btn.setEnabled(False)
        button_layout.addWidget(self.reverse_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def clear_plan(self):
        self.plan_display.clear()
        self.execute_btn.setEnabled(False)
        self.reverse_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        
    def build_plan_requested(self):
        # Signal to parent
        pass
        
    def execute_plan_requested(self):
        # Signal to parent
        pass
        
    def reverse_plan_requested(self):
        # Signal to parent
        pass
        
    def update_display(self, action_plan: ActionPlan):
        """Update the action plan display."""
        self.plan_display.setPlainText(str(action_plan))
        
        # Enable/disable buttons based on plan state
        has_planned = any(item.status == ActionStatus.PLANNED for item in action_plan.items)
        has_completed = any(item.status == ActionStatus.COMPLETED for item in action_plan.items)
        
        self.execute_btn.setEnabled(has_planned)
        self.reverse_btn.setEnabled(has_completed)

class BatchSymlinkTab(QWidget):
    """Main tab widget for batch symbolic linking operations."""
    
    def __init__(self, auth_manager, global_error_log, remembered_dirs):
        super().__init__()
        self.auth_manager = auth_manager
        self.global_error_log = global_error_log
        self.remembered_dirs = remembered_dirs
        self.action_plan = ActionPlan()
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Create splitter for file browsers
        splitter = QSplitter(Qt.Horizontal)
        
        # Source file browser
        self.src_browser = FileBrowserWidget("Source Files", self.remembered_dirs.get('src'))
        self.src_browser.set_as_directory = self.set_source_directory
        splitter.addWidget(self.src_browser)
        
        # Destination file browser
        self.dst_browser = FileBrowserWidget("Destination Directory", self.remembered_dirs.get('dst'))
        self.dst_browser.set_as_directory = self.set_destination_directory
        splitter.addWidget(self.dst_browser)
        
        # Set splitter proportions
        splitter.setSizes([400, 200])
        layout.addWidget(splitter)
        
        # Action plan widget
        self.action_plan_widget = ActionPlanWidget()
        self.action_plan_widget.build_plan_requested = self.build_plan
        self.action_plan_widget.execute_plan_requested = self.execute_plan
        self.action_plan_widget.reverse_plan_requested = self.reverse_plan
        layout.addWidget(self.action_plan_widget)
        
        self.setLayout(layout)
        
    def set_source_directory(self, directory_type):
        # This would be called from context menu
        pass
        
    def set_destination_directory(self, directory_type):
        # This would be called from context menu
        pass
        
    def build_plan(self):
        """Build the action plan based on current selections."""
        src_paths = self.src_browser.selected_paths()
        dst_dir = self.dst_browser.get_current_directory()
        
        if not src_paths:
            QMessageBox.warning(self, "No Selection", "Please select source files/directories.")
            return
            
        if not dst_dir:
            QMessageBox.warning(self, "No Destination", "Please select a destination directory.")
            return
            
        # Clear existing plan
        self.action_plan.clear()
        
        # Add actions for each selected source
        for src_path in src_paths:
            item = ActionItem(src_path, dst_dir)
            self.action_plan.add_item(item)
            
        # Update display
        self.action_plan_widget.update_display(self.action_plan)
        
    def execute_plan(self):
        """Execute the action plan."""
        if not self.auth_manager.is_authenticated():
            self.auth_manager.authenticate()
            
        # Show confirmation dialog
        reply = QMessageBox.question(
            self, 
            "Confirm Execution", 
            f"Execute {len(self.action_plan.items)} operations?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.action_plan_widget.progress_bar.setVisible(True)
            self.action_plan_widget.progress_bar.setMaximum(len(self.action_plan.items))
            
            errors = self.action_plan.execute_all()
            
            self.action_plan_widget.progress_bar.setVisible(False)
            self.action_plan_widget.update_display(self.action_plan)
            
            if errors:
                error_msg = "\n".join(errors)
                QMessageBox.warning(self, "Execution Errors", f"Some operations failed:\n{error_msg}")
                self.global_error_log.extend(errors)
            else:
                QMessageBox.information(self, "Success", "All operations completed successfully!")
                
    def reverse_plan(self):
        """Reverse all completed actions."""
        reply = QMessageBox.question(
            self,
            "Confirm Reversal",
            "Reverse all completed operations?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            errors = self.action_plan.reverse_all()
            self.action_plan_widget.update_display(self.action_plan)
            
            if errors:
                error_msg = "\n".join(errors)
                QMessageBox.warning(self, "Reversal Errors", f"Some reversals failed:\n{error_msg}")
                self.global_error_log.extend(errors)
            else:
                QMessageBox.information(self, "Success", "All operations reversed successfully!")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Batch Symbolic Linker Utility")
        self.setMinimumSize(1200, 800)
        
        # Initialize managers and state
        self.global_error_log = []
        self.remembered_dirs = {"src": QDir.homePath(), "dst": QDir.homePath()}
        self.auth_manager = AuthManager()
        
        # Create central widget with tabs
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        
        # Add initial tab
        self.add_tab()
        
        self.setCentralWidget(self.tabs)
        
        # Create toolbar
        self.create_toolbar()
        
        # Create status bar
        self.create_status_bar()
        
    def create_toolbar(self):
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # Add tab button
        add_tab_action = QAction("➕ Add Tab", self)
        add_tab_action.triggered.connect(self.add_tab)
        toolbar.addAction(add_tab_action)
        
        toolbar.addSeparator()
        
        # Error log button
        error_log_action = QAction("📋 Error Log", self)
        error_log_action.triggered.connect(self.show_errors)
        toolbar.addAction(error_log_action)
        
    def create_status_bar(self):
        self.statusBar().showMessage("Ready")
        
    def add_tab(self):
        tab = BatchSymlinkTab(self.auth_manager, self.global_error_log, self.remembered_dirs)
        tab_index = self.tabs.addTab(tab, f"Job {self.tabs.count() + 1}")
        self.tabs.setCurrentIndex(tab_index)
        
    def close_tab(self, index):
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)
        else:
            QMessageBox.information(self, "Cannot Close", "At least one tab must remain open.")
            
    def show_errors(self):
        if not self.global_error_log:
            QMessageBox.information(self, "Error Log", "No errors logged.")
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle("Global Error Log")
        dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout()
        
        # Error list
        error_list = QListWidget()
        for error in self.global_error_log:
            item = QListWidgetItem(error)
            error_list.addItem(item)
        layout.addWidget(error_list)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Clear)
        button_box.accepted.connect(dialog.accept)
        button_box.button(QDialogButtonBox.Clear).clicked.connect(self.clear_error_log)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        dialog.exec_()
        
    def clear_error_log(self):
        self.global_error_log.clear()
        QMessageBox.information(self, "Cleared", "Error log has been cleared.")

def main():
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Batch Symbolic Linker Utility")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Batch Symlink Utility")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()