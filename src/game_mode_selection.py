#!/usr/bin/env python3
"""
Game Mode Selection Window for Infinity Qubit
Allows users to choose between different game modes.
"""

import os
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import sys
import pygame
import tkinter as tk
import tkinter.messagebox as messagebox

from q_utils import get_colors_from_file, extract_color_palette

sys.path.append('..')
from run import PROJECT_ROOT, get_resource_path

# Get color palette
color_file_path = get_resource_path('config/color_palette.json')
palette = extract_color_palette(get_colors_from_file(color_file_path), 'game_mode_selection')


class GameModeSelection:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Infinity Qubit - Game Mode Selection")

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

        # Animation control flag - start as False for pre-loading
        self.animations_running = False
        self.pre_loading = True

        # Initialize sound system
        try:
            pygame.mixer.init()
            self.sound_enabled = True
        except:
            self.sound_enabled = False

        # Setup background and UI
        self.setup_video_background()
        self.create_selection_ui()

        # Make sure window is focused and on top
        self.root.lift()
        self.root.focus_force()

        self.start_animations()


    def setup_video_background(self):
        self.create_fallback_background()  # Create fallback background first


    def return_to_main_menu(self):
        """Return to the main menu from tutorial"""
        try:
            # Make sure window is ready
            if hasattr(self, 'root') and self.root:
                self.root.deiconify()
                self.root.lift()
                self.root.focus_set()
                self.root.update()  # Force update
        except Exception as e:
            print(f"Error returning to main menu: {e}")


    def create_fallback_background(self):
        """Create animated quantum-themed background"""
        try:
            # Create animated quantum-themed background
            canvas = tk.Canvas(self.root, width=self.window_width, height=self.window_height,
                            bg=palette['background'], highlightthickness=0)
            canvas.place(x=0, y=0)

            # Draw animated particles/quantum effects - fix particle structure
            self.particles = []
            particle_count = max(20, int(self.window_width * self.window_height / 20000))  # Scale with resolution
            for i in range(particle_count):
                x = __import__('random').randint(0, self.window_width)
                y = __import__('random').randint(0, self.window_height)
                dx = __import__('random').uniform(-2, 2)
                dy = __import__('random').uniform(-2, 2)

                # Change this line to yellowish red colors
                color = __import__('random').choice(['#ff6b47', '#ff7f4f', '#ff9347', '#ff8c42', '#ff7849'])

                # Use consistent dictionary structure
                self.particles.append({
                    'x': x,
                    'y': y,
                    'dx': dx,
                    'dy': dy,
                    'color': color
                })

            self.animate_particles(canvas)
            return canvas
        except Exception as e:
            print(f"Error creating fallback background: {e}")
            # Create simple static background as last resort
            simple_canvas = tk.Canvas(self.root, width=self.window_width, height=self.window_height,
                                    bg=palette['background'], highlightthickness=0)
            simple_canvas.place(x=0, y=0)
            return simple_canvas


    def update_info_display(self, mode_key):
        """Update the info display with selected mode information"""
        # Clear existing content
        for widget in self.info_frame.winfo_children():
            widget.destroy()

        # Mode information dictionary
        mode_info = {
            'tutorial': {
                'title': 'Tutorial Mode',
                'description': 'Perfect for beginners! Learn quantum computing fundamentals through interactive lessons and guided exercises.',
                'features': ['• Step-by-step quantum gate tutorials', '• Interactive circuit builder', '• Qubit visualization'],
                'difficulty': 'Beginner'
            },
            'puzzle': {
                'title': 'Puzzle Mode',
                'description': 'Challenge yourself with quantum puzzles! Solve increasingly complex quantum circuit problems.',
                'features': ['• 30+ quantum puzzles', '• Multiple difficulty levels', '• Scoring system'],
                'difficulty': 'Intermediate'
            },
            'sandbox': {
                'title': 'Sandbox Mode',
                'description': 'Unlimited creativity! Build and experiment with quantum circuits without restrictions.',
                'features': ['• Free-form circuit design', '• Real quantum simulation', '• Visualize circuits in 3D'],
                'difficulty': 'Advanced'
            },
            'learn_hub': {
                'title': 'Learn Hub',
                'description': 'Comprehensive learning center with courses, documentation, and advanced quantum concepts.',
                'features': ['• Reference materials', '• Advanced algorithms', '• Research papers'],
                'difficulty': 'All Levels'
            }
        }

        info = mode_info.get(mode_key, {})
        if not info:
            return

        # Title
        title_label = tk.Label(self.info_frame,
                            text=info['title'],
                            font=('Arial', max(16, int(self.window_width / 70)), 'bold'),
                            fg=palette['title_color'],
                            bg=palette['background'])
        title_label.place(relx=0.5, rely=0.08, anchor='n')

        # Difficulty badge
        difficulty_label = tk.Label(self.info_frame,
                                text=f"Difficulty: {info['difficulty']}",
                                font=('Arial', max(10, int(self.window_width / 120)), 'italic'),
                                fg=palette['subtitle_color_2'],
                                bg=palette['background'])
        difficulty_label.place(relx=0.5, rely=0.18, anchor='n')

        # Description
        desc_label = tk.Label(self.info_frame,
                            text=info['description'],
                            font=('Arial', max(11, int(self.window_width / 110))),
                            fg=palette['description_text_color'],
                            bg=palette['background'],
                            wraplength=int(self.window_width * 0.2),
                            justify=tk.CENTER)
        desc_label.place(relx=0.3, rely=0.4, anchor='w')

        # Features
        features_text = '\n'.join(info['features'])
        features_label = tk.Label(self.info_frame,
                                text=features_text,
                                font=('Arial', max(9, int(self.window_width / 130))),
                                fg=palette['features_text_color'],
                                bg=palette['background'],
                                justify=tk.CENTER)
        features_label.place(relx=0.5, rely=0.55, anchor='n')

        # Start button - canvas-based for color control
        start_canvas_width = max(200, int(self.window_width * 0.15))
        start_canvas_height = max(50, int(self.window_height / 15))

        start_canvas = tk.Canvas(self.info_frame,
                               width=start_canvas_width,
                               height=start_canvas_height,
                               bg=palette['background'],
                               highlightthickness=0,
                               bd=0)
        start_canvas.place(relx=0.5, rely=0.9, anchor='s')

        # Draw start button background
        start_canvas.create_rectangle(2, 2, start_canvas_width-2, start_canvas_height-2,
                                    fill=palette.get('start_button_color', '#ffb86b'),  # Use orange as fallback
                                    outline="#2b3340", width=1,
                                    tags="start_bg")

        # Add text to start button
        start_canvas.create_text(start_canvas_width//2, start_canvas_height//2,
                               text=f"Start {info['title'].split(' ', 1)[1]}",
                               font=('Arial', max(12, int(self.window_width / 100)), 'bold'),
                               fill=palette['black'],
                               tags="start_text")

        # Bind click events for start button
        def on_start_click(event):
            self.execute_command(self.selected_command)

        def on_start_enter(event):
            start_canvas.itemconfig("start_bg", fill=palette.get('start_button_hover_color', '#ffd08f'))  # Use palette hover color
            start_canvas.configure(cursor="hand2")

        def on_start_leave(event):
            start_canvas.itemconfig("start_bg", fill=palette.get('start_button_color', '#ffb86b'))  # Use palette color, fallback to orange
            start_canvas.configure(cursor="")

        start_canvas.bind("<Button-1>", on_start_click)
        start_canvas.bind("<Enter>", on_start_enter)
        start_canvas.bind("<Leave>", on_start_leave)


    def animate_particles(self, canvas):
        """Animate background particles - only if not pre-loading"""
        if self.pre_loading:
            return

        def update_particles():
            try:
                if (self.animations_running and hasattr(self, 'root') and
                    self.root.winfo_exists() and hasattr(self, 'particles')):
                    canvas.delete("particle")

                    for particle in self.particles:
                        particle['x'] = (particle['x'] + particle['dx']) % self.window_width
                        particle['y'] = (particle['y'] + particle['dy']) % self.window_height

                        dot_size = max(2, int(self.window_width / 500))
                        x, y = particle['x'], particle['y']
                        canvas.create_oval(x-dot_size, y-dot_size, x+dot_size, y+dot_size,
                                        fill=particle['color'], outline='#ff8c42',
                                        tags="particle", width=2)

                    if self.animations_running:
                        self.root.after(50, update_particles)
            except (tk.TclError, AttributeError, KeyError) as e:
                self.animations_running = False

        update_particles()


    def start_animations(self):
        """Start all animations after pre-loading is complete"""
        self.pre_loading = False
        self.animations_running = True

        # Start subtitle animation
        self.animate_subtitle()

        # Start particle animation
        if hasattr(self, 'particles'):
            for widget in self.root.winfo_children():
                if isinstance(widget, tk.Canvas):
                    self.animate_particles(widget)
                    break


    def play_sound(self, sound_type="click"):
        """Play a simple click sound"""
        if self.sound_enabled:
            try:
                import numpy as np

                # Create a simple click sound
                duration = 0.1
                sample_rate = 22050
                frequency = 440
                frames = int(duration * sample_rate)
                arr = np.sin(2 * np.pi * frequency * np.linspace(0, duration, frames))
                arr = (arr * 16383).astype(np.int16)
                sound = pygame.sndarray.make_sound(arr)
                sound.set_volume(0.3)
                sound.play()
            except:
                pass


    def create_selection_ui(self):
        """Create the game mode selection interface with glassmorphism effect using relative positioning"""
        # Main container with semi-transparent background using relative positioning
        main_frame = tk.Frame(self.root, bg=palette['background'])
        main_frame.place(relx=0.05, rely=0.05, anchor='nw',
                        relwidth=0.9, relheight=0.9)

        # Create glassmorphism background
        glass_canvas = tk.Canvas(main_frame, highlightthickness=0, bg=palette['background'])
        glass_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Draw glassmorphism background
        # Update glass background with configure event binding
        glass_canvas.bind('<Configure>', self.on_glass_configure)

        # Content frame with relative positioning
        content_frame = tk.Frame(main_frame, bg=palette['background'])
        content_frame.place(relx=0.05, rely=0.05, anchor='nw', relwidth=0.9, relheight=0.9)

        # Enhanced title with glow effect - positioned at top
        title_frame = tk.Frame(content_frame, bg=palette['background'])
        title_frame.place(relx=0.5, rely=0.05, anchor='n')

        # Calculate font sizes based on screen resolution
        title_font_size = max(24, int(self.window_width / 40))
        subtitle_font_size = max(14, int(self.window_width / 80))

        # Shadow title for glow effect
        shadow_title = tk.Label(title_frame, text="Infinity Qubit",
                            font=('Arial', title_font_size, 'bold'),
                            fg=palette['shadow_title_color'], bg=palette['background'])
        shadow_title.place(x=3, y=3)

        # Main title
        title_label = tk.Label(title_frame, text="Infinity Qubit",
                            font=('Arial', title_font_size, 'bold'),
                            fg=palette['title_color'], bg=palette['background'])
        title_label.pack()

        # Enhanced subtitle with animation - positioned below title
        self.subtitle_label = tk.Label(content_frame, text="Choose Your Quantum Adventure",
                                    font=('Arial', subtitle_font_size, 'italic'),
                                    fg=palette['subtitle_color_1'], bg=palette['background'])
        self.subtitle_label.place(relx=0.5, rely=0.15, anchor='n')

        # Animate subtitle
        self.animate_subtitle()

        # NEW: Central split frame container
        central_frame = tk.Frame(content_frame, bg=palette['background'], relief=tk.RAISED, bd=2)
        central_frame.place(relx=0.5, rely=0.55, anchor='center', relwidth=0.85, relheight=0.6)

        # LEFT HALF: Game mode buttons
        buttons_frame = tk.Frame(central_frame, bg=palette['background'], relief=tk.SUNKEN, bd=1)
        buttons_frame.place(relx=0, rely=0, relwidth=0.3, relheight=1)

        # RIGHT HALF: Game mode information display
        self.info_frame = tk.Frame(central_frame, bg=palette['background'], relief=tk.SUNKEN, bd=1)
        self.info_frame.place(relx=0.3, rely=0, relwidth=0.7, relheight=1)

        # Create enhanced game mode buttons
        self.create_enhanced_game_mode_buttons(buttons_frame)

        # Create initial info display
        self.create_info_display()

        # Footer with enhanced styling - positioned at bottom
        footer_frame = tk.Frame(content_frame, bg=palette['background'])
        footer_frame.place(relx=0.5, rely=0.95, anchor='s', relwidth=0.9)

        # Enhanced exit button - relative positioning
        # Create canvas-based exit button for better color control
        exit_canvas = tk.Canvas(footer_frame,
                               width=max(150, int(self.window_width / 8)),
                               height=max(40, int(self.window_height / 20)),
                               bg=palette['exit_button_color'],
                               highlightthickness=0,
                               bd=0)
        exit_canvas.pack(side=tk.RIGHT, padx=10, pady=5)

        # Draw exit button background
        canvas_width = max(150, int(self.window_width / 8))
        canvas_height = max(40, int(self.window_height / 20))

        exit_canvas.create_rectangle(2, 2, canvas_width-2, canvas_height-2,
                                   fill=palette['exit_button_color'],
                                   outline="#2b3340", width=1,
                                   tags="exit_bg")

        # Add text to exit button
        exit_canvas.create_text(canvas_width//2, canvas_height//2,
                              text="Exit Game",
                              font=('Arial', max(10, int(self.window_width / 120)), 'bold'),
                              fill=palette['exit_text_color'],
                              tags="exit_text")

        # Bind click events for exit button
        def on_exit_click(event):
            self.exit_game()

        def on_exit_enter(event):
            exit_canvas.itemconfig("exit_bg", fill=palette['exit_button_hover_color'])
            exit_canvas.configure(cursor="hand2")

        def on_exit_leave(event):
            exit_canvas.itemconfig("exit_bg", fill=palette['exit_button_color'])
            exit_canvas.configure(cursor="")

        exit_canvas.bind("<Button-1>", on_exit_click)
        exit_canvas.bind("<Enter>", on_exit_enter)
        exit_canvas.bind("<Leave>", on_exit_leave)

        # Version info with enhanced styling - relative positioning
        version_label = tk.Label(footer_frame, text="Version 1.0 | Built with Qiskit & OpenCV",
                                font=('Arial', max(8, int(self.window_width / 150))),
                                fg=palette['version_text_color'], bg=palette['background'])
        version_label.pack(side=tk.LEFT)


    def update_glass_background(self, canvas):
        """Update glassmorphism background when canvas is resized"""
        canvas.delete("glass")
        canvas.update_idletasks()
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width > 1 and height > 1:
            canvas.create_rectangle(0, 0, width, height,
                                  fill=palette['background'], stipple='gray50',
                                  outline=palette['main_box_outline'], width=2, tags="glass")


    def animate_subtitle(self):
        """Animate subtitle with color cycling - only if not pre-loading"""
        if self.pre_loading:
            return

        colors = [palette['subtitle_color_1'], palette['subtitle_color_2'], palette['subtitle_color_3'],
                 palette['subtitle_color_4'], palette['subtitle_color_5']]
        color_index = [0]

        def cycle_color():
            try:
                if (self.animations_running and hasattr(self, 'subtitle_label') and
                    self.subtitle_label.winfo_exists() and hasattr(self, 'root') and
                    self.root.winfo_exists()):
                    self.subtitle_label.configure(fg=colors[color_index[0] % len(colors)])
                    color_index[0] += 1
                    self.root.after(1500, cycle_color)
            except tk.TclError:
                pass

        cycle_color()


    def create_enhanced_game_mode_buttons(self, parent):
        """Create enhanced game mode selection buttons in a vertical list layout"""
        # Store selected mode for info display
        self.selected_mode = None

        button_configs = [
            {
                'title': 'Tutorial Mode',
                'command': self.start_tutorial_mode,
                'mode_key': 'tutorial'
            },
            {
                'title': 'Puzzle Mode',
                'command': self.start_puzzle_mode,
                'mode_key': 'puzzle'
            },
            {
                'title': 'Sandbox Mode',
                'command': self.start_sandbox_mode,
                'mode_key': 'sandbox'
            },
            {
                'title': 'Learn Hub',
                'command': self.start_learn_hub_mode,
                'mode_key': 'learn_hub'
            }
        ]

        # Calculate font sizes
        normal_font_size = max(10, int(self.window_width / 100))
        selected_font_size = max(12, int(self.window_width / 85))

        # Vertical list positions
        start_y = 0.025
        button_height = 0.2
        spacing = 0.05

        # Store button references for selection highlighting
        self.mode_buttons = {}

        # Create buttons directly in the buttons_frame using canvas approach like exit button
        for i, config in enumerate(button_configs):
            rely = start_y + i * (button_height + spacing)

            # Choose palette keys for bg and fg
            mode_key = config['mode_key']

            # Map mode keys to palette keys
            def get_palette_key(mode, suffix):
                if mode == 'learn_hub':
                    return f'learn_hub_{suffix}'
                else:
                    return f'{mode}_mode_{suffix}'

            # Colors for canvas-based buttons (use palette colors)
            bg_color = palette[get_palette_key(mode_key, 'button_color')]  # Orange background from palette
            fg_color = palette[get_palette_key(mode_key, 'button_text_color')]  # Text color from palette

            # Create canvas-based button (same approach as exit button)
            canvas_width = int(self.window_width * 0.9)
            canvas_height = int(self.window_height * button_height)

            button_canvas = tk.Canvas(parent,
                                    width=canvas_width,
                                    height=canvas_height,
                                    bg=palette['background'],
                                    highlightthickness=0,
                                    bd=0)

            button_canvas.place(relx=0.05, rely=rely, anchor='nw',
                              relwidth=0.9, relheight=button_height)

            # Draw button background
            button_canvas.create_rectangle(5, 5, canvas_width-5, canvas_height-5,
                                         fill=bg_color, outline="#2b3340", width=2,
                                         tags=f"button_bg_{mode_key}")

            # Create a Label widget for text (positioned over canvas)
            text_size = max(16, int(self.window_width / 70))
            text_label = tk.Label(parent,
                                text=config['title'],
                                font=('Arial', text_size, 'bold'),
                                fg=fg_color,
                                bg=bg_color,
                                relief=tk.FLAT,
                                bd=0)

            # Position the label over the canvas
            text_label.place(relx=0.05, rely=rely, anchor='nw',
                           relwidth=0.9, relheight=button_height)

            # Make the label clickable and bind the same events
            def make_click_handler(mk, cmd):
                def on_button_click(event):
                    self.select_mode(mk, cmd)
                return on_button_click

            def make_label_click_handler(mk, cmd):
                def on_label_click(event):
                    self.select_mode(mk, cmd)
                return on_label_click

            def make_label_hover_handlers(canvas, label, mk):
                def on_enter(event):
                    hover_key = get_palette_key(mk, 'button_hover_color')
                    canvas.itemconfig(f"button_bg_{mk}", fill=palette[hover_key])  # Use palette hover color
                    canvas.configure(cursor="hand2")
                    label.configure(cursor="hand2")
                def on_leave(event):
                    normal_key = get_palette_key(mk, 'button_color')
                    canvas.itemconfig(f"button_bg_{mk}", fill=palette[normal_key])  # Use palette normal color
                    canvas.configure(cursor="")
                    label.configure(cursor="")
                return on_enter, on_leave

            # Bind events to both canvas and label
            click_handler = make_click_handler(mode_key, config['command'])
            label_click_handler = make_label_click_handler(mode_key, config['command'])
            enter_handler, leave_handler = make_label_hover_handlers(button_canvas, text_label, mode_key)

            button_canvas.bind("<Button-1>", click_handler)
            button_canvas.bind("<Enter>", enter_handler)
            button_canvas.bind("<Leave>", leave_handler)

            text_label.bind("<Button-1>", label_click_handler)
            text_label.bind("<Enter>", enter_handler)
            text_label.bind("<Leave>", leave_handler)

            # Create command function for this button
            def make_click_handler(mk, cmd):
                def on_button_click(event):
                    self.select_mode(mk, cmd)
                return on_button_click

            def make_hover_handlers(canvas, mk):
                def on_enter(event):
                    hover_key = get_palette_key(mk, 'button_hover_color')
                    canvas.itemconfig(f"button_bg_{mk}", fill=palette[hover_key])  # Use palette hover color
                    canvas.configure(cursor="hand2")
                def on_leave(event):
                    normal_key = get_palette_key(mk, 'button_color')
                    canvas.itemconfig(f"button_bg_{mk}", fill=palette[normal_key])  # Use palette normal color
                    canvas.configure(cursor="")
                return on_enter, on_leave

            # Bind events
            click_handler = make_click_handler(mode_key, config['command'])
            enter_handler, leave_handler = make_hover_handlers(button_canvas, mode_key)

            button_canvas.bind("<Button-1>", click_handler)
            button_canvas.bind("<Enter>", enter_handler)
            button_canvas.bind("<Leave>", leave_handler)

            # Store canvas and label references
            self.mode_buttons[mode_key] = {
                'button': button_canvas,
                'canvas': button_canvas,
                'label': text_label,
                'command': config['command'],
                'normal_font_size': normal_font_size,
                'selected_font_size': selected_font_size
            }


    def select_mode(self, mode_key, command):
        """Select a game mode and update the info display"""
        self.play_sound()

        # Map mode keys to palette keys
        def get_palette_key(mode, suffix):
            if mode == 'learn_hub':
                return f'learn_hub_{suffix}'
            else:
                return f'{mode}_mode_{suffix}'

        # Reset all buttons to normal state
        for key, btn_info in self.mode_buttons.items():
            canvas = btn_info['canvas']
            label = btn_info['label']

            # Update canvas appearance to normal state
            normal_color_key = get_palette_key(key, 'button_color')
            text_color_key = get_palette_key(key, 'button_text_color')
            canvas.itemconfig(f"button_bg_{key}", fill=palette[normal_color_key], outline='#2b3340', width=2)

            # Update label appearance
            label.configure(
                font=('Arial', btn_info['normal_font_size'], 'bold'),
                fg=palette[text_color_key],  # Use palette text color
                bg=palette[normal_color_key]   # Use palette background color
            )

        # Highlight selected button
        selected_canvas = self.mode_buttons[mode_key]['canvas']
        selected_label = self.mode_buttons[mode_key]['label']

        # Update canvas for selected state
        hover_color_key = get_palette_key(mode_key, 'button_hover_color')
        text_color_key = get_palette_key(mode_key, 'button_text_color')
        selected_canvas.itemconfig(f"button_bg_{mode_key}", fill=palette[hover_color_key], outline='#ffd08f', width=3)

        # Update label for selected state
        selected_label.configure(
            font=('Arial', self.mode_buttons[mode_key]['selected_font_size'], 'bold'),
            fg=palette[text_color_key],  # Use palette text color
            bg=palette[hover_color_key]   # Use palette hover background
        )

        self.selected_mode = mode_key
        self.selected_command = command
        self.update_info_display(mode_key)


    def execute_command(self, command):
        """Execute button command with sound effect"""
        self.play_sound()
        # Stop animations before executing command
        self.animations_running = False
        # Small delay to allow current animation cycles to finish
        def execute_delayed():
            command()
        self.root.after(100, execute_delayed)


    def on_glass_configure(self, event):
        """Handle glass canvas configure event"""
        self.update_glass_background(event.widget)


    def create_info_display(self):
        """Create the initial info display area"""
        # Clear existing content
        for widget in self.info_frame.winfo_children():
            widget.destroy()

        # Default welcome message
        welcome_label = tk.Label(self.info_frame,
                            text="Select a game mode\nto see details",
                            font=('Arial', max(14, int(self.window_width / 80)), 'italic'),
                            fg=palette['subtitle_color_1'],
                            bg=palette['background'],
                            justify=tk.CENTER)
        welcome_label.place(relx=0.5, rely=0.5, anchor='center')


    def start_tutorial_mode(self):
        """Start the tutorial mode"""
        print("📚 Starting Tutorial Mode...")
        try:
            # Create tutorial window first
            from tutorial import TutorialWindow
            tutorial_window = TutorialWindow(self.root, self.return_to_main_menu)

            # Only hide main window after tutorial is ready
            self.root.withdraw()

        except ImportError as e:
            print(f"❌ Error importing tutorial: {e}")
            messagebox.showerror("Import Error", f"Could not import tutorial module: {e}")
        except Exception as e:
            print(f"❌ Error starting tutorial: {e}")
            messagebox.showerror("Error", f"Failed to start tutorial: {e}")
            self.root.deiconify()


    def return_to_main_menu(self):
        """Return to the main menu from tutorial"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_set()


    def start_puzzle_mode(self):
        """Start the puzzle mode"""
        print("📚 Starting Puzzle Mode...")
        try:
            from puzzle_mode import PuzzleMode

            # Create new window first
            puzzle_root = tk.Tk()
            puzzle_app = PuzzleMode(puzzle_root)

            # Make sure new window is visible before closing this one
            puzzle_root.update()
            puzzle_root.lift()
            puzzle_root.focus_force()

            # Now safely close main window
            self.root.destroy()

            # Start the puzzle mode mainloop
            puzzle_root.mainloop()

        except ImportError:
            print("❌ Puzzle mode module not found")
            messagebox.showerror("Error", "Puzzle mode module not available")
        except Exception as e:
            print(f"❌ Error starting puzzle mode: {e}")
            messagebox.showerror("Error", f"Error starting puzzle mode: {str(e)}")


    def start_sandbox_mode(self):
        """Start the sandbox mode"""
        print("🛠️ Starting Sandbox Mode...")
        try:
            from sandbox_mode import SandboxMode

            # Create new window first
            sandbox_root = tk.Tk()
            sandbox_app = SandboxMode(sandbox_root)

            # Make sure new window is visible before closing this one
            sandbox_root.update()
            sandbox_root.lift()
            sandbox_root.focus_force()

            # Now safely close main window
            self.root.destroy()

            # Start the sandbox mainloop
            sandbox_root.mainloop()

        except ImportError:
            print("❌ Sandbox module not found")
            messagebox.showerror("Error", "Sandbox module not available")
        except Exception as e:
            print(f"❌ Error starting sandbox: {e}")
            messagebox.showerror("Error", f"Error starting sandbox: {str(e)}")


    def start_learn_hub_mode(self):
        """Start the learn hub mode"""
        print("🚀 Starting Learn Hub...")
        try:
            from learn_hub import LearnHub

            # Create new window first
            learn_hub_root = tk.Tk()
            learn_hub_app = LearnHub(learn_hub_root)

            # Make sure new window is visible before closing this one
            learn_hub_root.update()
            learn_hub_root.lift()
            learn_hub_root.focus_force()

            # Now safely close main window
            self.root.destroy()

            # Start the learn hub mainloop
            learn_hub_root.mainloop()

        except ImportError:
            print("❌ Learn Hub module not found")
            messagebox.showerror("Error", "Learn Hub module not available")
        except Exception as e:
            print(f"❌ Error starting Learn Hub: {e}")
            messagebox.showerror("Error", f"Error starting Learn Hub: {str(e)}")


    def exit_game(self):
        """Exit the game"""
        print("👋 Exiting game...")
        self.root.quit()
        self.root.destroy()
        sys.exit(0)


    def run(self):
        """Run the game mode selection window"""
        self.root.mainloop()


def main():
    """For testing the game mode selection independently"""
    app = GameModeSelection()
    app.run()


if __name__ == "__main__":
    main()
