# Batch Symbolic Linker Utility

A cross-platform GUI utility for creating batch symbolic links to save disk space by moving files to larger, slower storage while maintaining access through symbolic links.

## Features

- **Cross-platform support**: Works on Windows, macOS, and Linux
- **Commander-style interface**: Two-pane file browser for easy source/destination selection
- **Multiple tabs**: Manage several concurrent directory hierarchies simultaneously
- **Action Plan preview**: See exactly what operations will be performed before execution
- **Progress tracking**: Real-time updates on operation progress and status
- **Complete reversibility**: All operations can be undone, restoring the original filesystem state
- **Error handling**: Comprehensive error logging and recovery
- **Permission management**: Cross-platform authentication and privilege elevation

## Use Cases

This utility is particularly useful for:
- Moving large files/directories from SSD to HDD to save space
- Organizing media libraries across multiple storage devices
- Managing development environments with large dependencies
- Creating backup strategies that maintain file accessibility

## Installation

### Prerequisites

- Python 3.11 or higher
- PyQt5

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd batch_simlink_utility
```

2. Install dependencies:
```bash
pip install -e .
```

3. Run the application:
```bash
python -m batch_simlink_utility.main
```

## Usage

### Basic Workflow

1. **Launch the application**: The main window opens with a tab-based interface
2. **Select source files/directories**: Use the left pane to navigate and select files/directories to move
3. **Choose destination**: Use the right pane to select the destination directory
4. **Build Action Plan**: Click "Build Plan" to preview the operations
5. **Review and execute**: Review the plan and click "Execute Plan" to perform the operations
6. **Monitor progress**: Watch the progress bar and status updates
7. **Reverse if needed**: Use "Reverse All" to undo completed operations

### Advanced Features

#### Multiple Tabs
- Add new tabs using the toolbar button
- Each tab maintains its own action plan
- Work on multiple projects simultaneously

#### Context Menus
- Right-click in file browsers for additional options
- Set directories as source/destination
- Refresh file listings

#### Error Logging
- Global error log accessible from toolbar
- Detailed error messages for troubleshooting
- Clear error log when needed

## Cross-Platform Support

### Windows
- Uses Windows junctions for directories and symlinks for files
- Requires administrator privileges for symlink creation
- Automatic privilege elevation prompts

### macOS/Linux
- Uses native symbolic links
- Standard file system permissions apply
- No special privileges required for most operations

## Security and Permissions

### Windows
- Administrator privileges required for symlink creation
- UAC prompts for elevation
- Junction creation for directories

### Unix-like Systems
- Standard file system permissions
- Symlink creation requires write permissions
- No special privileges needed

## File Operations

### What the Utility Does

1. **Moves** the original file/directory to the destination
2. **Creates** a symbolic link at the original location pointing to the new location
3. **Maintains** the same file path for applications that expect files in the original location

### Reversibility

All operations are designed to be completely reversible:
- Symbolic links are removed
- Files are moved back to their original locations
- Original file system hierarchy is restored

## Error Handling

The utility provides comprehensive error handling:
- Permission errors with helpful messages
- File system errors with recovery options
- Network path issues
- Disk space problems
- Concurrent access conflicts

## Development

### Project Structure

```
batch_simlink_utility/
├── src/batch_simlink_utility/
│   ├── __init__.py
│   ├── main.py              # Main GUI application
│   ├── auth.py              # Authentication and permissions
│   └── symlink_actionplan.py # Action planning and execution
├── pyproject.toml
└── README.md
```

### Key Components

- **MainWindow**: Main application window with tab management
- **BatchSymlinkTab**: Individual tab for file operations
- **FileBrowserWidget**: Enhanced file browser with navigation
- **ActionPlanWidget**: Action plan display and management
- **ActionPlan/ActionItem**: Core operation logic
- **AuthManager**: Cross-platform authentication

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license information here]

## Support

For issues and feature requests, please use the project's issue tracker.
