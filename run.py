import os
import sys
from pathlib import Path

# Get the absolute path of the project root directory
PROJECT_ROOT = Path(__file__).parent.absolute()

# Define common resource paths
RESOURCES_DIR = PROJECT_ROOT / "resources"
CONFIG_DIR = PROJECT_ROOT / "config"
SRC_DIR = PROJECT_ROOT / "src"

def get_resource_path(relative_path):
    """Get absolute path to a resource file."""
    return PROJECT_ROOT / relative_path

def setup_environment():
    """Setup the Python environment for the project."""
    # Add src directory to Python path so modules can be imported
    src_path = str(SRC_DIR)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

def main():
    """Main entry point for the application."""
    # Setup the environment
    setup_environment()
    
    # Now import and run your main application
    try:
        from main import main

        if __name__ == "__main__":
            print("🔬 Starting Qubit Puzzle Solver...")
            print("📚 Educational quantum computing game")
            print("🎮 Have fun learning quantum gates!")
            print("-" * 40)
            main()

    except ImportError as e:
        print(f"❌ Error importing game: {e}")
        print("📦 Please install required packages:")
        print("pip install qiskit numpy")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running game: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()