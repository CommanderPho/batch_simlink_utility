import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QTreeView, QFileSystemModel, QTextEdit
)
from PyQt5.QtCore import Qt, QDir
from .symlink_actionplan import ActionPlan, ActionItem
from .auth import AuthManager

class CommanderPane(QWidget):
    def __init__(self, root_path=None):
        super().__init__()
        layout = QVBoxLayout()
        self.model = QFileSystemModel()
        self.model.setRootPath(root_path or QDir.homePath())
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(root_path or QDir.homePath()))
        self.tree.setSelectionMode(QTreeView.ExtendedSelection)
        layout.addWidget(self.tree)
        self.setLayout(layout)

    def selected_paths(self):
        indexes = self.tree.selectionModel().selectedIndexes()
        paths = set()
        for idx in indexes:
            if idx.column() == 0:
                paths.add(self.model.filePath(idx))
        return list(paths)

class BatchSymlinkTab(QWidget):
    def __init__(self, auth_manager, global_error_log, remembered_dirs):
        super().__init__()
        self.auth_manager = auth_manager
        self.global_error_log = global_error_log
        self.remembered_dirs = remembered_dirs

        layout = QVBoxLayout()
        panes = QHBoxLayout()
        self.src_pane = CommanderPane(root_path=self.remembered_dirs.get('src'))
        self.dst_pane = CommanderPane(root_path=self.remembered_dirs.get('dst'))
        panes.addWidget(self.src_pane)
        panes.addWidget(self.dst_pane)
        layout.addLayout(panes)

        self.actionplan = ActionPlan()
        self.plan_preview = QTextEdit()
        self.plan_preview.setReadOnly(True)
        layout.addWidget(self.plan_preview)

        btn_layout = QHBoxLayout()
        self.plan_btn = QPushButton("Build ActionPlan")
        self.plan_btn.clicked.connect(self.build_plan)
        self.exec_btn = QPushButton("Execute Plan")
        self.exec_btn.clicked.connect(self.execute_plan)
        btn_layout.addWidget(self.plan_btn)
        btn_layout.addWidget(self.exec_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def build_plan(self):
        srcs = self.src_pane.selected_paths()
        dst_dir = self.dst_pane.model.rootPath()
        self.actionplan.clear()
        for src in srcs:
            self.actionplan.add_item(ActionItem(src, dst_dir))
        self.plan_preview.setPlainText(str(self.actionplan))

    def execute_plan(self):
        # Placeholder: check authentication
        if not self.auth_manager.is_authenticated():
            self.auth_manager.authenticate()
        # Execute all actions
        for item in self.actionplan.items:
            try:
                item.execute()
            except Exception as e:
                self.global_error_log.append(f"{item}: {e}")
        self.plan_preview.setPlainText(str(self.actionplan))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Batch Symbolic Linker Utility")
        self.tabs = QTabWidget()
        self.global_error_log = []
        self.remembered_dirs = {"src": QDir.homePath(), "dst": QDir.homePath()}
        self.auth_manager = AuthManager()

        # Add initial tab
        self.add_tab()

        self.setCentralWidget(self.tabs)
        self.statusBar().showMessage("Ready")

        # Error log viewer
        error_btn = QPushButton("Show Global Error Log")
        error_btn.clicked.connect(self.show_errors)
        self.statusBar().addPermanentWidget(error_btn)

    def add_tab(self):
        tab = BatchSymlinkTab(self.auth_manager, self.global_error_log, self.remembered_dirs)
        self.tabs.addTab(tab, f"Job {self.tabs.count() + 1}")

    def show_errors(self):
        dlg = QTextEdit()
        dlg.setWindowTitle("Global Error Log")
        dlg.setReadOnly(True)
        dlg.setPlainText("\n".join(self.global_error_log))
        dlg.setMinimumSize(400, 200)
        dlg.show()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()