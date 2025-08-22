#!/usr/bin/env python3
"""
Splash Screen for Infinity Qubit
Displays loading animation before showing game mode selection.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk

class SplashScreen:
    def __init__(self):
        self.splash = tk.Tk()
        self.splash.title("Infinity Qubit")
        
        # Add animation control flags
        self.animation_active = True
        self.text_animation_active = True
        
        # Remove window decorations
        self.splash.overrideredirect(True)
        
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
        self.splash.configure(bg='#1a1a1a')
        
        # Make splash screen stay on top
        self.splash.attributes('-topmost', True)
        
        self.create_splash_content()
        self.animate_loading()
        
        # Start timer to close splash screen
        self.splash.after(1500, self.close_splash)
        
    def create_splash_content(self):
        """Create the content for the splash screen"""
        # Main container
        main_frame = tk.Frame(self.splash, bg='#1a1a1a')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title - increased top padding and adjusted font
        title_label = tk.Label(main_frame, text="🔬 Infinity Qubit",
                            font=('Arial', 28, 'bold'),  # Slightly smaller font
                            fg='#00ff88', bg='#1a1a1a')
        title_label.pack(pady=(40, 15))  # More balanced padding
        
        # Subtitle - added more padding
        subtitle_label = tk.Label(main_frame, text="Quantum Computing Educational Game",
                                font=('Arial', 14),  # Slightly smaller
                                fg='#ffffff', bg='#1a1a1a')
        subtitle_label.pack(pady=(5, 30))  # Better spacing
        
        # Quantum circuit animation area - reduced padding
        self.animation_frame = tk.Frame(main_frame, bg='#1a1a1a')
        self.animation_frame.pack(pady=15)
        
        # Create animated quantum gates
        self.create_quantum_animation()
        
        # Loading text - increased padding and better positioning
        self.loading_label = tk.Label(main_frame, text="Initializing quantum circuits...",
                                    font=('Arial', 11),  # Slightly smaller
                                    fg='#4ecdc4', bg='#1a1a1a')
        self.loading_label.pack(pady=(30, 15))  # More space above and below
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate', 
                                    length=300, style='Splash.Horizontal.TProgressbar')
        self.progress.pack(pady=(5, 20))  # Better spacing
        
        # Version info - with more space from bottom
        version_label = tk.Label(main_frame, text="Version 1.0 | Built with Qiskit",
                                font=('Arial', 9),  # Smaller font
                                fg='#888888', bg='#1a1a1a')
        version_label.pack(side=tk.BOTTOM, pady=(10, 15))  # More space from bottom
        
        # Configure progress bar style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Splash.Horizontal.TProgressbar',
                    background='#00ff88',
                    troughcolor='#2a2a2a',
                    borderwidth=0,
                    lightcolor='#00ff88',
                    darkcolor='#00ff88')
    
    def create_quantum_animation(self):
        """Create animated quantum circuit elements"""
        # Create a simple quantum circuit visualization - slightly smaller
        circuit_canvas = tk.Canvas(self.animation_frame, width=380, height=90,
                                bg='#1a1a1a', highlightthickness=0)
        circuit_canvas.pack(pady=10)  # Add some padding around canvas
        
        # Draw quantum wires
        for i in range(3):
            y = 15 + i * 25  # Reduced spacing between wires
            circuit_canvas.create_line(50, y, 330, y, fill='#ffffff', width=2)
            circuit_canvas.create_text(30, y, text=f'q{i}', fill='#ffffff', font=('Arial', 9))
        
        # Store canvas reference for animation
        self.circuit_canvas = circuit_canvas
        
        # Initial gate positions
        self.gate_positions = [100, 180, 260]
        self.gate_colors = ['#ff6b6b', '#4ecdc4', '#96ceb4']
        self.gate_labels = ['H', 'X', 'Z']
        
        self.draw_animated_gates()
    
    def draw_animated_gates(self):
        """Draw the animated quantum gates"""
        # Check if animation should continue and canvas exists
        if not self.animation_active or not hasattr(self, 'circuit_canvas'):
            return
            
        try:
            # Clear previous gates
            self.circuit_canvas.delete("gate")
            
            # Draw gates at current positions
            for i, (x, color, label) in enumerate(zip(self.gate_positions, self.gate_colors, self.gate_labels)):
                y = 15 + i * 25  # Match the wire positions
                
                # Gate rectangle - slightly smaller
                self.circuit_canvas.create_rectangle(x-18, y-12, x+18, y+12,
                                                fill=color, outline='#ffffff', width=2, tags="gate")
                
                # Gate label
                self.circuit_canvas.create_text(x, y, text=label, fill='#000000',
                                            font=('Arial', 10, 'bold'), tags="gate")
        except tk.TclError:
            # Canvas has been destroyed, stop animation
            self.animation_active = False
    
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
                        self.splash.after(800, lambda: update_text(index + 1))
            except tk.TclError:
                # Widget has been destroyed, stop animation
                self.text_animation_active = False
        
        update_text()
    
    def animate_gates(self):
        """Animate the quantum gates movement"""
        def move_gates():
            # Check if animation should continue
            if not self.animation_active:
                return
                
            try:
                if hasattr(self, 'circuit_canvas') and self.circuit_canvas.winfo_exists():
                    # Move gates slightly
                    for i in range(len(self.gate_positions)):
                        self.gate_positions[i] += 2
                        if self.gate_positions[i] > 350:  # Adjusted for smaller canvas
                            self.gate_positions[i] = 80
                    
                    self.draw_animated_gates()
                    
                    # Continue animation if still active
                    if self.animation_active:
                        self.splash.after(100, move_gates)
            except tk.TclError:
                # Widget has been destroyed, stop animation
                self.animation_active = False
        
        move_gates()
    
    def close_splash(self):
        """Close the splash screen and show game mode selection"""
        # Stop all animations before destroying the window
        self.animation_active = False
        self.text_animation_active = False
        
        # Stop progress bar
        try:
            self.progress.stop()
        except:
            pass
        
        # Small delay to ensure all animations stop
        self.splash.after(100, self._destroy_and_continue)
    
    def _destroy_and_continue(self):
        """Destroy splash screen and continue to game mode selection"""
        try:
            self.splash.destroy()
        except:
            pass
        
        # Show game mode selection
        self.show_game_mode_selection()
    
    def show_game_mode_selection(self):
        """Show the game mode selection window"""
        from game_mode_selection import GameModeSelection
        selection_window = GameModeSelection()
        selection_window.run()
    
    def run(self):
        """Run the splash screen"""
        self.splash.mainloop()

def show_splash_screen():
    """Show the splash screen before the game mode selection"""
    splash = SplashScreen()
    splash.run()

if __name__ == "__main__":
    show_splash_screen()