#!/usr/bin/env python3
"""
Qubit Puzzle Solver - Quantum Computing Educational Game

Run this file to start the game.
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
