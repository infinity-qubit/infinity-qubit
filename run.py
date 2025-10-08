import os
import sys
import argparse
import tkinter as tk
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

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Infinity Qubit - Quantum Computing Educational Game")
    parser.add_argument("--mode", choices=["splash", "learn_hub", "sandbox", "puzzle", "tutorial"],
                        default="splash", help="Select the game mode to launch directly")
    return parser.parse_args()

def main():
    """Main entry point for the application."""
    # Setup the environment
    setup_environment()
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Now import and run your main application based on the mode
    try:
        print("🔬 Starting Qubit Puzzle Solver...")
        print("📚 Educational quantum computing game")
        print("🎮 Have fun learning quantum gates!")
        print("-" * 40)
        
        if args.mode == "learn_hub":
            # Direct launch of Learn Hub
            print("� Starting Learn Hub...")
            from learn_hub import LearnHub
            root = tk.Tk()
            learn_hub = LearnHub(root)
            root.mainloop()
        elif args.mode == "sandbox":
            # Direct launch of Sandbox Mode
            print("� Starting Sandbox Mode...")
            from sandbox_mode import SandboxMode
            root = tk.Tk()
            sandbox = SandboxMode(root)
            root.mainloop()
        elif args.mode == "puzzle":
            # Direct launch of Puzzle Mode
            print("🚀 Starting Puzzle Mode...")
            from puzzle_mode import PuzzleMode
            root = tk.Tk()
            puzzle = PuzzleMode(root)
            root.mainloop()
        elif args.mode == "tutorial":
            # Direct launch of Tutorial Mode
            print("🚀 Starting Tutorial Mode...")
            from tutorial import Tutorial
            root = tk.Tk()
            tutorial = Tutorial(root)
            root.mainloop()
        else:
            # Default splash screen entry point
            from main import main
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