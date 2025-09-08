#!/usr/bin/env python3
"""
Splash Screen for Infinity Qubit
Displays loading animation before showing game mode selection.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk
import sys

from q_utils import get_colors_from_file, extract_color_palette

sys.path.append('..')
from run import PROJECT_ROOT, get_resource_path

# Get color palette
color_file_path = get_resource_path('config/color_palette.json')
palette = extract_color_palette(get_colors_from_file(color_file_path), 'splash_screen')

class SplashScreen:
    def __init__(self, fullscreen=True):
        self.splash = tk.Tk()
        self.splash.title("Infinity Qubit")

        # Add animation control flags
        self.animation_active = True
        self.text_animation_active = True

        # Pre-initialize game mode selection
        self.game_mode_selection = None

        # Track scheduled callbacks
        self.scheduled_callbacks = []

        # Remove window decorations
        self.splash.overrideredirect(True)

        # Store fullscreen mode
        self.fullscreen = fullscreen

        # Get screen dimensions
        screen_width = self.splash.winfo_screenwidth()
        screen_height = self.splash.winfo_screenheight()

        if fullscreen:
            # Set fullscreen mode
            self.splash.attributes('-fullscreen', True)
            self.splash.geometry(f"{screen_width}x{screen_height}+0+0")

            # Add escape key binding for testing
            self.splash.bind('<Escape>', lambda e: self.splash.quit())
        else:
            # Get screen dimensions
            screen_width = self.splash.winfo_screenwidth()
            screen_height = self.splash.winfo_screenheight()

            # Splash screen dimensions
            splash_width = 600
            splash_height = 400

            # Center the splash screen
            x = (screen_width - splash_width) // 2
            y = (screen_height - splash_height) // 2

            self.splash.geometry(f"{splash_width}x{splash_height}+{x}+{y}")

        self.splash.configure(bg=palette['background'])

        # Make splash screen stay on top
        self.splash.attributes('-topmost', True)

        self.create_splash_content()
        self.animate_loading()

        # Start pre-loading game mode selection after splash content is ready
        self.splash.after(500, self.pre_load_game_mode_selection)

        # Start timer to close splash screen (increased to allow pre-loading)
        self.splash.after(2000, self.close_splash)

    def pre_load_game_mode_selection(self):
        """Pre-load the game mode selection window while splash is visible"""
        try:
            from game_mode_selection import GameModeSelection
            # Create the game mode selection window but keep it hidden
            self.game_mode_selection = GameModeSelection()
            # Hide the window immediately after creation
            self.game_mode_selection.root.withdraw()
            print("✅ Game mode selection pre-loaded successfully")
        except Exception as e:
            print(f"Error pre-loading game mode selection: {e}")
            self.game_mode_selection = None

    def create_splash_content(self):
        """Create the content for the splash screen"""
        if self.fullscreen:
            # For fullscreen, create a centered container
            # Main container that fills the screen
            outer_frame = tk.Frame(self.splash, bg=palette['background'])
            outer_frame.pack(fill=tk.BOTH, expand=True)

            # Centered content container with fixed width
            main_frame = tk.Frame(outer_frame, bg=palette['background'])
            main_frame.place(relx=0.5, rely=0.5, anchor='center')

            # Scale fonts for fullscreen
            title_font_size = 48
            subtitle_font_size = 20
            loading_font_size = 16
            version_font_size = 12
            canvas_width, canvas_height = 500, 120
        else:
            # Original windowed layout
            main_frame = tk.Frame(self.splash, bg=palette['background'])
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

            # Original font sizes
            title_font_size = 28
            subtitle_font_size = 14
            loading_font_size = 11
            version_font_size = 9
            canvas_width, canvas_height = 380, 90

        # Title - adjusted font size based on mode
        title_label = tk.Label(main_frame, text="🔬 Infinity Qubit",
                            font=('Arial', title_font_size, 'bold'),
                            fg=palette['title_color'], bg=palette['background'])
        title_label.pack(pady=(40, 15))

        # Subtitle - adjusted font size
        subtitle_label = tk.Label(main_frame, text="Quantum Computing Educational Game",
                                font=('Arial', subtitle_font_size),
                                fg=palette['sub-title_color'], bg=palette['background'])
        subtitle_label.pack(pady=(5, 30))

        # Quantum circuit animation area
        self.animation_frame = tk.Frame(main_frame, bg=palette['background'])
        self.animation_frame.pack(pady=15)

        # Create animated quantum gates with scaled canvas
        self.create_quantum_animation(canvas_width, canvas_height)

        # Loading text - adjusted font size
        self.loading_label = tk.Label(main_frame, text="Initializing quantum circuits...",
                                    font=('Arial', loading_font_size),
                                    fg=palette['loading_text_color'], bg=palette['background'])
        self.loading_label.pack(pady=(30, 15))

        # Progress bar - scaled length
        progress_length = 400 if self.fullscreen else 300
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate',
                                    length=progress_length, style='Splash.Horizontal.TProgressbar')
        self.progress.pack(pady=(5, 20))

        # Version info - adjusted font size
        version_label = tk.Label(main_frame, text="Version 1.0 | Built with Qiskit",
                                font=('Arial', version_font_size),
                                fg=palette['version_text_color'], bg=palette['background'])
        if self.fullscreen:
            version_label.pack(pady=(20, 0))
        else:
            version_label.pack(side=tk.BOTTOM, pady=(10, 15))

        # Configure progress bar style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Splash.Horizontal.TProgressbar',
                    background=palette['background'],
                    troughcolor=palette['throughcolor'],
                    borderwidth=0,
                    lightcolor=palette['background'],
                    darkcolor=palette['background'])

    def create_quantum_animation(self, canvas_width=380, canvas_height=90):
        """Create animated quantum circuit elements with scalable dimensions"""
        circuit_canvas = tk.Canvas(self.animation_frame, width=canvas_width, height=canvas_height,
                                bg='#1a1a1a', highlightthickness=0)
        circuit_canvas.pack(pady=10)

        # Scale wire spacing and positions based on canvas size
        wire_spacing = canvas_height // 4
        start_x = canvas_width // 8
        end_x = canvas_width - start_x

        # Draw quantum wires
        for i in range(3):
            y = wire_spacing + i * wire_spacing
            circuit_canvas.create_line(start_x, y, end_x, y, fill='#ffffff', width=2)
            circuit_canvas.create_text(start_x - 20, y, text=f'q{i}', fill='#ffffff',
                                     font=('Arial', 10 if not self.fullscreen else 12))

        # Store canvas reference and dimensions for animation
        self.circuit_canvas = circuit_canvas
        self.canvas_width = canvas_width
        self.wire_spacing = wire_spacing

        # Scale gate positions based on canvas width
        gate_spacing = (end_x - start_x - 80) // 3
        self.gate_positions = [start_x + 40 + i * gate_spacing for i in range(3)]
        self.gate_colors = ["#002b7f", '#fcd116', '#ce1126']
        self.gate_labels = ['H', 'X', 'Z']

        self.draw_animated_gates()

    def draw_animated_gates(self):
        """Draw the animated quantum gates"""
        if not self.animation_active or not hasattr(self, 'circuit_canvas'):
            return

        try:
            # Clear previous gates
            self.circuit_canvas.delete("gate")

            # Scale gate size based on fullscreen mode
            gate_size = 20 if self.fullscreen else 18

            # Draw gates at current positions
            for i, (x, color, label) in enumerate(zip(self.gate_positions, self.gate_colors, self.gate_labels)):
                y = self.wire_spacing + i * self.wire_spacing

                # Gate rectangle
                self.circuit_canvas.create_rectangle(x-gate_size, y-gate_size//2, x+gate_size, y+gate_size//2,
                                                fill=color, outline='#ffffff', width=2, tags="gate")

                # Gate label
                font_size = 12 if self.fullscreen else 10
                self.circuit_canvas.create_text(x, y, text=label, fill='#000000',
                                            font=('Arial', font_size, 'bold'), tags="gate")
        except tk.TclError:
            self.animation_active = False


    def schedule_callback(self, delay, callback):
        """Helper method to track scheduled callbacks"""
        callback_id = self.splash.after(delay, callback)
        self.scheduled_callbacks.append(callback_id)
        return callback_id


    def cancel_all_callbacks(self):
        """Cancel all scheduled callbacks"""
        for callback_id in self.scheduled_callbacks:
            try:
                self.splash.after_cancel(callback_id)
            except:
                pass
        self.scheduled_callbacks.clear()


    def animate_gates(self):
        """Animate the quantum gates movement"""
        def move_gates():
            if not self.animation_active:
                return

            try:
                if hasattr(self, 'circuit_canvas') and self.circuit_canvas.winfo_exists():
                    # Move gates based on canvas width
                    move_speed = 3 if self.fullscreen else 2
                    reset_position = self.canvas_width // 8 + 20
                    max_position = self.canvas_width - reset_position

                    for i in range(len(self.gate_positions)):
                        self.gate_positions[i] += move_speed
                        if self.gate_positions[i] > max_position:
                            self.gate_positions[i] = reset_position

                    self.draw_animated_gates()

                    if self.animation_active:
                        self.schedule_callback(100, move_gates)
            except tk.TclError:
                self.animation_active = False

        move_gates()

    def animate_loading(self):
        """Animate the loading elements"""
        # Start progress bar animation
        self.progress.start(10)

        # Animate loading text
        self.animate_text()

        # Animate quantum gates
        self.animate_gates()

    def animate_text(self):
        """Animate the loading text"""
        texts = [
            "Initializing quantum circuits...",
            "Loading quantum gates...",
            "Preparing qubit states...",
            "Calibrating quantum simulator...",
            "Ready to explore quantum computing!"
        ]

        def update_text(index=0):
            # Check if animation should continue and widget exists
            if not self.text_animation_active:
                return

            try:
                if hasattr(self, 'loading_label') and self.loading_label.winfo_exists():
                    self.loading_label.config(text=texts[index % len(texts)])
                    if index < 20 and self.text_animation_active:  # Animate for ~4 seconds
                        self.schedule_callback(800, lambda: update_text(index + 1))
            except tk.TclError:
                # Widget has been destroyed, stop animation
                self.text_animation_active = False

        update_text()


    def close_splash(self):
        """Close the splash screen and show game mode selection"""
        # Stop all animations before destroying the window
        self.animation_active = False
        self.text_animation_active = False

        # Cancel all scheduled callbacks
        self.cancel_all_callbacks()

        # Stop progress bar
        try:
            self.progress.stop()
        except:
            pass

        # Small delay to ensure all animations stop
        self.schedule_callback(100, self._destroy_and_continue)


    def _destroy_and_continue(self):
        """Destroy splash screen and continue to game mode selection"""
        try:
            if self.game_mode_selection:
                self.splash.destroy()
                self.game_mode_selection.root.deiconify()
                self.game_mode_selection.root.lift()
                self.game_mode_selection.root.focus_force()
            else:
                # Fallback
                self.splash.destroy()
                self.show_game_mode_selection()
        except Exception as e:
            print(f"Error transitioning: {e}")
            try:
                self.splash.destroy()
            except:
                pass
            self.show_game_mode_selection()


    def show_game_mode_selection(self):
        """Show the game mode selection window (fallback method)"""
        from game_mode_selection import GameModeSelection
        selection_window = GameModeSelection()
        selection_window.run()

    def run(self):
        """Run the splash screen"""
        self.splash.mainloop()

def show_splash_screen(fullscreen=True):
    """Show the splash screen before the game mode selection"""
    splash = SplashScreen(fullscreen)
    splash.run()

if __name__ == "__main__":
    # Test in fullscreen
    show_splash_screen(fullscreen=True)
    # Or test in windowed mode
    # show_splash_screen(fullscreen=False)
