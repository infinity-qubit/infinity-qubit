#!/usr/bin/env python3
"""
Puzzle Level Selection Window for Infinity Qubit
Displays a grid of puzzle levels with progress-based unlocking.
"""

import sys
import os
import tkinter as tk
import json
import warnings

# Suppress pygame welcome message
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame
from tkinter import messagebox

from q_utils import get_colors_from_file, extract_color_palette

sys.path.append('..')
from run import PROJECT_ROOT, get_resource_path

# Get color palette
color_file_path = get_resource_path('config/color_palette.json')
palette = extract_color_palette(get_colors_from_file(color_file_path), 'puzzle_level_selection')


class PuzzleLevelSelection:
    def __init__(self, root=None):
        # Use provided root or create new one if none provided
        if root is None:
            self.root = tk.Tk()
            self.owns_root = True
        else:
            self.root = root
            self.owns_root = False
        
        self.root.title("Infinity Qubit - Level Selection")

        # Set fullscreen mode
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Make window fullscreen without title bar
        self.root.overrideredirect(True)
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        self.root.configure(bg=palette['background'])

        # Store dimensions
        self.window_width = screen_width
        self.window_height = screen_height

        # Bind keys
        self.root.bind('<Escape>', self.return_to_game_mode_selection)
        self.root.bind('<F11>', self.toggle_fullscreen)

        # Initialize sound system
        try:
            pygame.mixer.init()
            self.sound_enabled = True
        except:
            self.sound_enabled = False

        # Load puzzle levels and progress
        self.load_puzzle_levels()
        self.load_progress()

        # Setup UI
        self.create_level_selection_ui()

        # Make sure window is focused and on top
        self.root.lift()
        self.root.focus_force()


    def load_puzzle_levels(self):
        """Load puzzle levels from JSON file"""
        try:
            levels_file = get_resource_path('config/puzzle_levels_temp.json')
            with open(levels_file, 'r') as f:
                self.levels = json.load(f)
        except FileNotFoundError:
            print("❌ puzzle_levels_temp.json not found, using fallback levels")
            self.levels = self.create_fallback_levels()


    def create_fallback_levels(self):
        """Create fallback levels if JSON file is not found"""
        return [
            {
                "name": "Basic Bit Flip",
                "description": "Transform |0⟩ into |1⟩ using the X gate",
                "input_state": "|0⟩",
                "target_state": "|1⟩",
                "available_gates": ["X"],
                "qubits": 1,
                "difficulty": "Beginner"
            },
            {
                "name": "Superposition",
                "description": "Create equal superposition from |0⟩",
                "input_state": "|0⟩",
                "target_state": "|+⟩",
                "available_gates": ["H"],
                "qubits": 1,
                "difficulty": "Beginner"
            }
        ]


    def load_progress(self):
        """Load player progress from save file"""
        try:
            save_file = get_resource_path('resources/saves/infinity_qubit_puzzle_save.json')
            with open(save_file, 'r') as f:
                self.progress = json.load(f)
                self.max_unlocked_level = self.progress.get('current_level', 0)
                self.completed_levels = self.progress.get('completed_levels', [])
                self.level_scores = self.progress.get('level_scores', {})
        except (FileNotFoundError, json.JSONDecodeError):
            # No progress file exists or corrupted, start from beginning
            self.max_unlocked_level = 0  # Only level 1 (index 0) unlocked
            self.completed_levels = []
            self.level_scores = {}
            self.progress = {
                'current_level': 0,
                'completed_levels': [],
                'level_scores': {}
            }


    def save_progress(self):
        """Save current progress to file"""
        try:
            save_file = get_resource_path('resources/saves/infinity_qubit_puzzle_save.json')
            os.makedirs(os.path.dirname(save_file), exist_ok=True)
            
            with open(save_file, 'w') as f:
                json.dump(self.progress, f, indent=2)
        except Exception as e:
            print(f"Failed to save progress: {e}")


    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode"""
        current_state = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not current_state)


    def return_to_game_mode_selection(self, event=None):
        """Return to the game mode selection window"""
        self.play_sound('click')

        from game_mode_selection import GameModeSelection
        new_root = tk.Tk()
        new_app = GameModeSelection(new_root)

        # Make sure the new window is on top
        new_root.update()
        new_root.lift()
        new_root.focus_force()

        # Close main window
        self.root.destroy()

        new_root.mainloop()


    def play_sound(self, sound_type="click"):
        """Play a sound effect"""
        if not self.sound_enabled:
            return
        
        try:
            sound_files = {
                'click': get_resource_path('resources/sounds/click.wav'),
                'success': get_resource_path('resources/sounds/correct.wav'),
                'locked': get_resource_path('resources/sounds/error.wav')
            }
            
            if sound_type in sound_files:
                sound = pygame.mixer.Sound(sound_files[sound_type])
                sound.play()
        except Exception as e:
            pass  # Fail silently if sound can't be played


    def create_level_selection_ui(self):
        """Create the main level selection interface"""
        # Main container
        main_frame = tk.Frame(self.root, bg=palette['background'])
        main_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Level grid section
        self.create_level_grid_section(main_frame)


    def create_level_grid_section(self, parent):
        """Create the scrollable level grid section"""
        # Container for the level grid
        grid_container_frame = tk.Frame(parent, bg=palette['background_3'], relief=tk.RAISED, bd=2)
        grid_container_frame.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=0.9)

        # Header frame for title and back button
        header_frame = tk.Frame(grid_container_frame, bg=palette['background_3'])
        header_frame.place(relx=0, rely=0, relwidth=1, relheight=0.12)

        # Title for level grid (positioned to the left side of center)
        grid_title = tk.Label(header_frame,
                             text="Choose Your Level",
                             font=('Arial', max(18, int(self.window_width / 80)), 'bold'),
                             fg=palette.get('title_color', '#ffffff'),
                             bg=palette['background_3'])
        grid_title.place(relx=0.5, rely=0.5, anchor='center')

        # Back to Main Menu button (positioned to the right)
        self.create_back_to_main_button(header_frame)

        # Level grid area (adjusted to account for header)
        self.create_level_grid(grid_container_frame)


    def create_back_to_main_button(self, parent):
        """Create the back to main menu button"""
        # Button canvas only - no container
        btn_canvas = tk.Canvas(parent, highlightthickness=0, bd=0,
                              width=max(50, int(self.window_width * 0.04)),
                              height=max(50, int(self.window_height * 0.04)),
                              bg=palette.get('level_button_color', '#ffb86b'))
        btn_canvas.place(relx=0.95, rely=0.5, anchor='center')

        def draw_button(hover=False):
            btn_canvas.delete("all")
            btn_canvas.update_idletasks()
            width = btn_canvas.winfo_width()
            height = btn_canvas.winfo_height()

            if width <= 1 or height <= 1:
                return

            # Colors
            if hover:
                bg_color = palette.get('level_button_hover_color', '#ffd08f')
                text_color = palette.get('level_button_text_color', '#2c1f12')
            else:
                bg_color = palette.get('level_button_color', '#ffb86b')
                text_color = palette.get('level_button_text_color', '#2c1f12')

            # Draw button background
            btn_canvas.create_rectangle(0, 0, width, height,
                                      fill=bg_color, outline=bg_color, tags="bg")

            # Draw 'X' text
            font_size = max(16, int(min(width, height) * 0.4))
            btn_canvas.create_text(width//2, height//2,
                                 text="X",
                                 font=('Arial', font_size, 'bold'),
                                 fill=text_color, tags="text")

        # Event handlers
        def on_click(event):
            self.play_sound('click')
            self.return_to_game_mode_selection()

        def on_enter(event):
            draw_button(hover=True)
            btn_canvas.configure(cursor='hand2')

        def on_leave(event):
            draw_button(hover=False)
            btn_canvas.configure(cursor='')

        # Bind events
        btn_canvas.bind("<Button-1>", on_click)
        btn_canvas.bind("<Enter>", on_enter)
        btn_canvas.bind("<Leave>", on_leave)

        # Initial draw
        btn_canvas.bind('<Configure>', lambda e: draw_button(False))
        btn_canvas.after(10, lambda: draw_button(False))

        return btn_canvas


    def create_level_grid(self, parent):
        """Create the responsive grid of level buttons"""
        # Grid container (adjusted to start below the header)
        grid_frame = tk.Frame(parent, bg=palette['background_3'])
        grid_frame.place(relx=0.05, rely=0.15, relwidth=0.9, relheight=0.8)

        # Calculate grid dimensions (6x5 for 30 levels)
        cols = 6
        rows = 5
        
        # Calculate responsive button dimensions
        button_rel_width = 0.85 / cols  # 85% of width divided by columns
        button_rel_height = 0.85 / rows  # 85% of height divided by rows
        
        # Create level buttons
        for level_index in range(len(self.levels)):
            if level_index >= 30:  # Safety check
                break
                
            row = level_index // cols
            col = level_index % cols
            
            # Calculate relative position
            rel_x = (col * (1.0 / cols)) + (1.0 / cols) * 0.5
            rel_y = (row * (1.0 / rows)) + (1.0 / rows) * 0.5
            
            self.create_level_button(grid_frame, level_index, rel_x, rel_y, 
                                   button_rel_width, button_rel_height)


    def create_level_button(self, parent, level_index, rel_x, rel_y, rel_width, rel_height):
        """Create an individual level button"""
        level = self.levels[level_index]
        is_unlocked = level_index <= self.max_unlocked_level
        is_completed = level_index in self.completed_levels
        is_current = level_index == self.max_unlocked_level
        
        # Button container
        btn_container = tk.Frame(parent, bg=palette['background_4'], relief=tk.RAISED, bd=2)
        btn_container.place(relx=rel_x, rely=rel_y, relwidth=rel_width * 0.9, 
                           relheight=rel_height * 0.9, anchor='center')

        # Create canvas for custom drawing
        btn_canvas = tk.Canvas(btn_container, highlightthickness=0, bd=0)
        btn_canvas.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=0.9)

        # Draw button content
        def draw_button():
            btn_canvas.delete("all")
            btn_canvas.update_idletasks()
            width = btn_canvas.winfo_width()
            height = btn_canvas.winfo_height()
            
            if width <= 1 or height <= 1:
                return

            # Determine button colors based on state
            if not is_unlocked:
                bg_color = palette.get('locked_level_color', '#666666')
                text_color = '#999999'
                border_color = '#555555'
            elif is_completed:
                bg_color = palette.get('level_button_color', '#ffb86b')
                text_color = palette.get('level_button_text_color', '#2c1f12')
                border_color = bg_color
            elif is_current:
                bg_color = palette.get('level_button_color', '#ffb86b')
                text_color = palette.get('level_button_text_color', '#2c1f12')
                border_color = bg_color
            else:
                # Available but not completed - use uniform color
                bg_color = palette.get('level_button_color', '#ffb86b')
                text_color = palette.get('level_button_text_color', '#2c1f12')
                border_color = bg_color

            # Draw button background
            btn_canvas.create_rectangle(2, 2, width-2, height-2,
                                      fill=bg_color, outline=border_color, width=2, tags="bg")

            # Level number
            level_num = level_index + 1
            level_font_size = max(14, int(min(width, height) * 0.25))
            btn_canvas.create_text(width//2, height//4, 
                                 text=f"Level {level_num}",
                                 font=('Arial', level_font_size, 'bold'),
                                 fill=text_color, tags="text")

            # Level name (wrapped)
            name = level['name']
            name_font_size = max(10, int(min(width, height) * 0.12))
            
            # Calculate text wrapping with smaller character limit
            max_chars_per_line = max(8, min(12, int(width / (name_font_size * 0.7))))  # Smaller chars per line
            words = name.split()
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                if len(test_line) <= max_chars_per_line:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                        current_line = word
                    else:
                        # Single word is too long, truncate it
                        lines.append(word[:max_chars_per_line-3] + "...")
                        current_line = ""
            
            if current_line:
                lines.append(current_line)
            
            # Limit to 3 lines max
            if len(lines) > 3:
                lines = lines[:1] + [lines[1][:max_chars_per_line-3] + "..."]
            
            # Draw wrapped text
            line_height = name_font_size + 2
            total_height = len(lines) * line_height
            start_y = height//2 - total_height//2 + line_height
            
            for i, line in enumerate(lines):
                y_pos = start_y + i * line_height
                btn_canvas.create_text(width//2, y_pos,
                                     text=line,
                                     font=('Arial', name_font_size),
                                     fill=text_color, tags="text")

        # Bind drawing to canvas configuration
        btn_canvas.bind('<Configure>', lambda e: draw_button())
        btn_canvas.after(10, draw_button)

        # Click handler
        if is_unlocked:
            def on_click(event):
                self.select_level(level_index)
            
            def on_enter(event):
                btn_canvas.itemconfig("bg", fill=palette.get('level_button_hover_color', '#ffd08f'))
            
            def on_leave(event):
                draw_button()
            
            btn_canvas.bind("<Button-1>", on_click)
            btn_canvas.bind("<Enter>", on_enter)
            btn_canvas.bind("<Leave>", on_leave)


    def show_locked_message(self, level_index):
        """Show message for locked levels"""
        required_level = level_index
        message = f"Complete Level {required_level} to unlock this level!"
        
        # Simple message dialog
        messagebox.showinfo("Level Locked", message)


    def select_level(self, level_index):
        """Handle level selection"""
        self.play_sound('success')

        from puzzle_mode import PuzzleMode
        # Create new window first
        puzzle_root = tk.Tk()
        puzzle_app = PuzzleMode(puzzle_root, starting_level=level_index)

        # Make sure the new window is on top
        puzzle_root.update()
        puzzle_root.lift()
        puzzle_root.focus_force()

        # Close main window
        self.root.destroy()

        puzzle_root.mainloop()


    def create_nav_button(self, parent, text, command, relx, rely, anchor='center'):
        """Create a navigation button with consistent styling"""
        btn_frame = tk.Frame(parent, bg=palette.get('puzzle_mode_button_color', '#4CAF50'), 
                            relief=tk.RAISED, bd=2)
        btn_frame.place(relx=relx, rely=rely, anchor=anchor)

        btn_label = tk.Label(btn_frame, text=text,
                            font=('Arial', max(12, int(self.window_width / 120)), 'bold'),
                            fg=palette.get('puzzle_mode_button_text_color', 'white'),
                            bg=palette.get('puzzle_mode_button_color', '#4CAF50'),
                            padx=20, pady=10)
        btn_label.pack()

        # Click and hover handlers
        def on_click(event):
            self.play_sound('click')
            command()

        def on_enter(event):
            btn_frame.configure(bg=palette.get('puzzle_mode_button_hover_color', '#45a049'))
            btn_label.configure(bg=palette.get('puzzle_mode_button_hover_color', '#45a049'))
            btn_label.configure(cursor='hand2')

        def on_leave(event):
            btn_frame.configure(bg=palette.get('puzzle_mode_button_color', '#4CAF50'))
            btn_label.configure(bg=palette.get('puzzle_mode_button_color', '#4CAF50'))
            btn_label.configure(cursor='')

        btn_label.bind("<Button-1>", on_click)
        btn_label.bind("<Enter>", on_enter)
        btn_label.bind("<Leave>", on_leave)

        return btn_frame


    def run(self):
        """Start the level selection window"""
        self.root.mainloop()


def main():
    """For testing the puzzle level selection independently"""
    app = PuzzleLevelSelection()
    app.run()


if __name__ == "__main__":
    main()
