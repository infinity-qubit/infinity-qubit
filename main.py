#!/usr/bin/env python3
"""
Infinity Qubit - Quantum Computing Educational Game
Main entry point for the application.
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main entry point for the game"""
    try:
        from splash_screen import show_splash_screen
        show_splash_screen()
    except KeyboardInterrupt:
        print("\n👋 Thanks for trying Infinity Qubit!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error running game: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
