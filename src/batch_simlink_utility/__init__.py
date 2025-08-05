"""
Batch Symbolic Linker Utility

A cross-platform GUI utility for creating batch symbolic links to save disk space
by moving files to larger, slower storage while maintaining access through symbolic links.
"""

__version__ = "1.0.0"
__author__ = "Pho Hale"
__email__ = "PhoHale@gmail.com"

def hello() -> str:
    return "Hello from batch-simlink-utility!"

def main():
    """Entry point for the application."""
    from .main import main as main_func
    main_func()

if __name__ == "__main__":
    main()
