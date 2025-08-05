import os
import platform
import subprocess
import sys
from typing import Optional, Tuple
from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton, QDialogButtonBox

class AuthManager:
    def __init__(self):
        self._authenticated = False
        self._credentials = None
        self._elevation_method = None

    def is_authenticated(self):
        return self._authenticated

    def authenticate(self) -> bool:
        """Authenticate the user for file system operations."""
        if self._authenticated:
            return True
            
        # Check if we're on Windows and need elevation
        if platform.system() == "Windows":
            return self._authenticate_windows()
        else:
            return self._authenticate_unix()
    
    def _authenticate_windows(self) -> bool:
        """Handle Windows authentication/elevation."""
        try:
            # Check if we're already running with admin privileges
            if self._is_admin_windows():
                self._authenticated = True
                return True
                
            # Show dialog asking for elevation
            dialog = QDialog()
            dialog.setWindowTitle("Administrator Privileges Required")
            dialog.setModal(True)
            
            layout = QVBoxLayout()
            
            label = QLabel(
                "This operation requires administrator privileges.\n"
                "Please run the application as Administrator or click 'Continue' to attempt elevation."
            )
            layout.addWidget(label)
            
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            dialog.setLayout(layout)
            
            if dialog.exec_() == QDialog.Accepted:
                # Try to elevate privileges
                if self._elevate_windows():
                    self._authenticated = True
                    return True
                else:
                    QMessageBox.warning(None, "Elevation Failed", 
                                       "Could not obtain administrator privileges.\n"
                                       "Please run the application as Administrator.")
                    return False
            else:
                return False
                
        except Exception as e:
            QMessageBox.critical(None, "Authentication Error", 
                               f"Authentication failed: {str(e)}")
            return False
    
    def _authenticate_unix(self) -> bool:
        """Handle Unix-like system authentication."""
        try:
            # On Unix systems, we mainly need to check if we can create symlinks
            # and have write permissions to the target directories
            test_dir = "/tmp"
            test_symlink = os.path.join(test_dir, "test_symlink")
            test_target = os.path.join(test_dir, "test_target")
            
            # Create a test file
            with open(test_target, 'w') as f:
                f.write("test")
            
            # Try to create a symlink
            os.symlink(test_target, test_symlink)
            
            # Clean up
            os.unlink(test_symlink)
            os.unlink(test_target)
            
            self._authenticated = True
            return True
            
        except (OSError, PermissionError):
            # Show dialog for Unix systems
            dialog = QDialog()
            dialog.setWindowTitle("Permissions Required")
            dialog.setModal(True)
            
            layout = QVBoxLayout()
            
            label = QLabel(
                "This operation requires appropriate file system permissions.\n"
                "Please ensure you have write permissions to the source and destination directories."
            )
            layout.addWidget(label)
            
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            dialog.setLayout(layout)
            
            if dialog.exec_() == QDialog.Accepted:
                # For now, just assume permissions are OK
                self._authenticated = True
                return True
            else:
                return False
                
        except Exception as e:
            QMessageBox.critical(None, "Authentication Error", 
                               f"Authentication failed: {str(e)}")
            return False
    
    def _is_admin_windows(self) -> bool:
        """Check if running with administrator privileges on Windows."""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def _elevate_windows(self) -> bool:
        """Attempt to elevate privileges on Windows."""
        try:
            # This is a simplified approach - in a real application,
            # you might want to restart the application with elevated privileges
            import ctypes
            if ctypes.windll.shell32.IsUserAnAdmin():
                return True
            else:
                # Try to restart with admin privileges
                script = sys.argv[0]
                params = ' '.join(sys.argv[1:])
                
                try:
                    subprocess.run([
                        'powershell', 'Start-Process', script, 
                        '-ArgumentList', params, '-Verb', 'RunAs'
                    ], check=True)
                    return True
                except subprocess.CalledProcessError:
                    return False
        except:
            return False
    
    def check_permissions(self, source_path: str, destination_path: str) -> Tuple[bool, str]:
        """Check if we have the necessary permissions for the operation."""
        try:
            source = os.path.abspath(source_path)
            destination = os.path.abspath(destination_path)
            
            # Check if source exists and is readable
            if not os.path.exists(source):
                return False, f"Source path does not exist: {source}"
            
            if not os.access(source, os.R_OK):
                return False, f"No read permission for source: {source}"
            
            # Check if destination directory exists and is writable
            dest_dir = os.path.dirname(destination)
            if not os.path.exists(dest_dir):
                try:
                    os.makedirs(dest_dir, exist_ok=True)
                except PermissionError:
                    return False, f"No permission to create destination directory: {dest_dir}"
            
            if not os.access(dest_dir, os.W_OK):
                return False, f"No write permission for destination: {dest_dir}"
            
            # Check if destination file/directory already exists
            if os.path.exists(destination):
                return False, f"Destination already exists: {destination}"
            
            return True, "Permissions OK"
            
        except Exception as e:
            return False, f"Permission check failed: {str(e)}"
    
    def deauthenticate(self):
        """Clear authentication state."""
        self._authenticated = False
        self._credentials = None
        self._elevation_method = None