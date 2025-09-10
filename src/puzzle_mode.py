#!/usr/bin/env python3
"""
Puzzle Mode for Infinity Qubit
Allows users to solve puzzles related to quantum circuits.
"""

import os
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import sys
import json
import pygame
import numpy as np
import tkinter as tk
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

sys.path.append('..')
from run import PROJECT_ROOT, get_resource_path
from q_utils import get_colors_from_file, extract_color_palette

# Get color palette
color_file_path = get_resource_path('config/color_palette.json')
palette = extract_color_palette(get_colors_from_file(color_file_path), 'puzzle_mode')


class PuzzleMode:
    SAVE_FILE = os.path.expanduser("resources/saves/infinity_qubit_puzzle_save.json")


    def __init__(self, root):
        self.root = root
        self.root.title("Infinity Qubit - Puzzle Mode")

        # Initialize pygame mixer for sound
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.sound_enabled = True
            self.load_sounds()
        except pygame.error:
            print("Warning: Could not initialize sound system")
            self.sound_enabled = False

        # Set fullscreen mode
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Enable fullscreen
        self.root.overrideredirect(True)
        self.root.geometry(f"{screen_width}x{screen_height}")
        self.root.configure(bg=palette['background'])
        self.root.resizable(False, False)  # Fixed size window

        # Store dimensions (use full screen)
        self.window_width = screen_width
        self.window_height = screen_height

        # Handle ESC key to exit
        self.root.bind('<Escape>', lambda e: self.return_to_main_menu())

        # Game state
        self.current_level = 0
        self.placed_gates = []
        self.score = 0
        self.levels = self.load_puzzle_levels()
        self.max_gates_used = {}  # Track efficiency

        # Initialize UI
        self.setup_ui()

        # Load saved progress if available (after UI and levels are set up)
        self.load_progress()

        self.load_level(self.current_level)
        if self.placed_gates:
            # Redraw the circuit with loaded gates
            self.draw_circuit()


    def save_progress(self):
        """Save current progress to a file."""
        data = {
            "current_level": self.current_level,
            "score": self.score,
            "placed_gates": self.placed_gates,
        }
        try:
            with open(self.SAVE_FILE, "w") as f:
                json.dump(data, f)
            print("✅ Progress saved.")
        except Exception as e:
            print(f"❌ Could not save progress: {e}")


    def load_progress(self):
        """Load progress from file if it exists."""
        if os.path.exists(self.SAVE_FILE):
            try:
                with open(self.SAVE_FILE, "r") as f:
                    data = json.load(f)
                self.current_level = data.get("current_level", 0)
                self.score = data.get("score", 0)
                self.placed_gates = data.get("placed_gates", [])
                print("✅ Progress loaded.")
            except Exception as e:
                print(f"❌ Could not load progress: {e}")


    def create_canvas_dialog_button(self, parent, text, command, bg_color, text_color,
                                   width=120, height=40, font_size=12, font_weight='bold'):
        """Create a canvas-based button for dialogs and popup windows"""
        # Create canvas for the button
        canvas = tk.Canvas(parent, width=width, height=height,
                          highlightthickness=0, bd=0, bg=parent['bg'])

        # Draw button background and text with proper closure
        def create_draw_function(canvas, bg, txt, txt_color, w, h, fs, fw):
            def draw_button(event=None):
                canvas.delete("all")
                canvas_width = canvas.winfo_width()
                canvas_height = canvas.winfo_height()
                if canvas_width > 1 and canvas_height > 1:
                    canvas.create_rectangle(2, 2, canvas_width-2, canvas_height-2,
                                          fill=bg, outline="#2b3340", width=1, tags="bg")
                    canvas.create_text(canvas_width//2, canvas_height//2, text=txt,
                                     font=('Arial', fs, fw), fill=txt_color, tags="text")
            return draw_button

        draw_function = create_draw_function(canvas, bg_color, text, text_color, width, height, font_size, font_weight)

        # Bind configure event and initial draw
        canvas.bind('<Configure>', draw_function)
        canvas.after(10, draw_function)

        # Click handler
        def on_click(event):
            command()

        # Hover effects with proper closure
        def create_hover_functions(canvas, bg, hover_bg):
            def on_enter(event):
                canvas.delete("bg")
                canvas_width = canvas.winfo_width()
                canvas_height = canvas.winfo_height()
                if canvas_width > 1 and canvas_height > 1:
                    canvas.create_rectangle(2, 2, canvas_width-2, canvas_height-2,
                                          fill=hover_bg, outline="#2b3340", width=1, tags="bg")
                canvas.configure(cursor='hand2')
                canvas.tag_lower("bg")

            def on_leave(event):
                canvas.delete("bg")
                canvas_width = canvas.winfo_width()
                canvas_height = canvas.winfo_height()
                if canvas_width > 1 and canvas_height > 1:
                    canvas.create_rectangle(2, 2, canvas_width-2, canvas_height-2,
                                          fill=bg, outline="#2b3340", width=1, tags="bg")
                canvas.configure(cursor='')
                canvas.tag_lower("bg")

            return on_enter, on_leave

        hover_color = palette.get('button_hover_background', '#ffd08f')
        on_enter, on_leave = create_hover_functions(canvas, bg_color, hover_color)

        # Bind events
        canvas.bind("<Button-1>", on_click)
        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)

        return canvas


    def load_puzzle_levels(self):
        """Load puzzle levels from JSON file"""
        try:
            with open(get_resource_path('config/puzzle_levels_temp.json'), 'r', encoding='utf-8') as f:
                levels = json.load(f)
            print(f"✅ Loaded {len(levels)} puzzle levels from JSON")
            return levels
        except FileNotFoundError:
            print("❌ puzzle_levels_temp.json not found, falling back to default levels")
            return self.create_puzzle_levels()
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing puzzle_levels_temp.json: {e}")
            return self.create_puzzle_levels()
        except Exception as e:
            print(f"❌ Error loading puzzle levels: {e}")
            return self.create_puzzle_levels()


    def create_puzzle_levels(self):
        """Fallback method to create default puzzle levels if JSON loading fails"""
        return [
            {
                "name": "Basic Bit Flip",
                "description": "Transform |0⟩ into |1⟩ using the X gate",
                "input_state": "|0⟩",
                "target_state": "|1⟩",
                "available_gates": ["X"],
                "qubits": 1,
                "hint": "The X gate flips |0⟩ to |1⟩",
                "max_gates": 1,
                "difficulty": "Beginner"
            },
            {
                "name": "Superposition",
                "description": "Create equal superposition from |0⟩",
                "input_state": "|0⟩",
                "target_state": "|+⟩",
                "available_gates": ["H"],
                "qubits": 1,
                "hint": "The Hadamard gate creates superposition",
                "max_gates": 1,
                "difficulty": "Beginner"
            }
        ]


    def load_sounds(self):
        """Load sound effects for the puzzle mode"""
        try:
            # Define sound file paths
            sound_files = {
                'button_click': get_resource_path('resources/sounds/click.wav'),
                'gate_place': get_resource_path('resources/sounds/add_gate.wav'),
                'success': get_resource_path('resources/sounds/correct.wav'),
                'error': get_resource_path('resources/sounds/wrong.wav'),
                'clear': get_resource_path('resources/sounds/clear.wav'),
                'level_complete': get_resource_path('resources/sounds/correct.wav')
            }

            # Load sounds into pygame
            self.sounds = {}
            for sound_name, file_path in sound_files.items():
                try:
                    self.sounds[sound_name] = pygame.mixer.Sound(file_path)
                    print(f"✅ Loaded sound: {sound_name}")
                except pygame.error as e:
                    print(f"⚠️ Could not load {sound_name} from {file_path}: {e}")
                    # Create a placeholder/dummy sound or skip this sound
                    self.sounds[sound_name] = None

        except Exception as e:
            print(f"Warning: Could not load sounds: {e}")
            self.sound_enabled = False
            self.sounds = {}


    def play_sound(self, sound_name):
        """Play a sound effect"""
        if not self.sound_enabled:
            return

        try:
            if sound_name in self.sounds and self.sounds[sound_name] is not None:
                self.sounds[sound_name].play()
            else:
                print(f"⚠️ Sound '{sound_name}' not available")
        except Exception as e:
            print(f"Warning: Could not play sound {sound_name}: {e}")


    def setup_ui(self):
        """Setup the user interface with relative positioning"""
        # Main container with gradient-like effect
        main_frame = tk.Frame(self.root, bg=palette['main_frame_background'])
        main_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Add subtle top border
        top_border = tk.Frame(main_frame, bg=palette['top_border_color'])
        top_border.place(relx=0, rely=0, relwidth=1, relheight=0.005)

        # Content frame
        content_frame = tk.Frame(main_frame, bg=palette['background_2'])
        content_frame.place(relx=0, rely=0.005, relwidth=1, relheight=0.995)

        # Create header
        self.create_header(content_frame)

        # Main content container
        main_container = tk.Frame(content_frame, bg=palette['background_2'])
        main_container.place(relx=0.05, rely=0.12, relwidth=0.9, relheight=0.83)

        # Level info panel (replaces control panel)
        self.setup_level_info_panel(main_container)

        # Circuit display area
        self.setup_circuit_area(main_container)

        # Bottom section with gate palette, controls, and state analysis
        self.setup_bottom_section(main_container)

        # Set up window close protocol
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)


    def create_header(self, parent):
        """Create header with title and navigation using relative positioning"""
        header_frame = tk.Frame(parent, bg=palette['background_2'])
        header_frame.place(relx=0.05, rely=0.02, relwidth=0.9, relheight=0.08)

        # Title on the left
        title_label = tk.Label(header_frame, text="Infinity Qubit - Puzzle Mode",
                            font=('Arial', max(20, int(self.window_width / 80)), 'bold'),
                            fg=palette['title_color'], bg=palette['background_2'])
        title_label.place(relx=0, rely=0.2, anchor='w')

        # Subtitle below title
        subtitle_label = tk.Label(header_frame,
                                text="Solve quantum puzzles with increasing difficulty",
                                font=('Arial', max(11, int(self.window_width / 140)), 'italic'),
                                fg=palette['subtitle_color'], bg=palette['background_2'])
        subtitle_label.place(relx=0, rely=0.7, anchor='w')

        # Back to Main Menu button - top right
        # Canvas-based main menu button for better color control on macOS
        button_width = max(120, int(self.window_width / 12))
        button_height = max(35, int(self.window_height / 25))

        main_menu_canvas = tk.Canvas(header_frame,
                                   width=button_width,
                                   height=button_height,
                                   bg=palette['puzzle_mode_button_color'],
                                   highlightthickness=0,
                                   bd=0)
        main_menu_canvas.place(relx=1, rely=0.5, anchor='e')

        # Draw button background
        main_menu_canvas.create_rectangle(2, 2, button_width-2, button_height-2,
                                        fill=palette['puzzle_mode_button_color'],
                                        outline=palette['puzzle_mode_button_color'], width=1,
                                        tags="menu_bg")

        # Add text to button
        main_menu_canvas.create_text(button_width//2, button_height//2,
                                   text="Main Menu",
                                   font=('Arial', max(10, int(self.window_width / 150)), 'bold'),
                                   fill=palette['puzzle_mode_button_text_color'],
                                   tags="menu_text")

        # Bind click events
        def on_menu_click(event):
            self.return_to_main_menu()

        def on_menu_enter(event):
            main_menu_canvas.itemconfig("menu_bg", fill=palette['puzzle_mode_button_hover_color'])
            main_menu_canvas.configure(cursor="hand2")

        def on_menu_leave(event):
            main_menu_canvas.itemconfig("menu_bg", fill=palette['puzzle_mode_button_color'])
            main_menu_canvas.configure(cursor="")

        main_menu_canvas.bind("<Button-1>", on_menu_click)
        main_menu_canvas.bind("<Enter>", on_menu_enter)
        main_menu_canvas.bind("<Leave>", on_menu_leave)


    def setup_level_info_panel(self, parent):
        """Setup the level information panel using relative positioning"""
        info_frame = tk.Frame(parent, bg=palette['background_2'], relief=tk.RAISED, bd=2)
        info_frame.place(relx=0, rely=0, relwidth=1, relheight=0.18)

        # Title
        info_title = tk.Label(info_frame, text="Level Information",
                            font=('Arial', max(16, int(self.window_width / 100)), 'bold'),
                            fg=palette['info_title_color'], bg=palette['background_2'])
        info_title.place(relx=0.5, rely=0.15, anchor='center')

        # Main info container
        info_container = tk.Frame(info_frame, bg=palette['background_2'])
        info_container.place(relx=0.1, rely=0.35, relwidth=0.8, relheight=0.6)

        # Level details - left side
        level_frame = tk.Frame(info_container, bg=palette['background_3'], relief=tk.RAISED, bd=1)
        level_frame.place(relx=0, rely=0, relwidth=0.48, relheight=1)

        self.level_label = tk.Label(level_frame, text="Level: 1",
                                font=('Arial', max(14, int(self.window_width / 120)), 'bold'),
                                fg=palette['level_counter_color'], bg=palette['background_3'])
        self.level_label.place(relx=0.5, rely=0.15, anchor='center')

        self.level_name_label = tk.Label(level_frame, text="Level Name",
                                    font=('Arial', max(12, int(self.window_width / 130)), 'bold'),
                                    fg=palette['level_name_color'], bg=palette['background_3'])
        self.level_name_label.place(relx=0.5, rely=0.4, anchor='center')

        self.level_description_label = tk.Label(level_frame, text="Description",
                                            font=('Arial', max(10, int(self.window_width / 150))),
                                            fg=palette['description_title_color'], bg=palette['background_3'],
                                            wraplength=int(self.window_width * 0.35))
        self.level_description_label.place(relx=0.5, rely=0.75, anchor='center')

        # Difficulty and score - right side
        stats_frame = tk.Frame(info_container, bg=palette['background_3'], relief=tk.RAISED, bd=1)
        stats_frame.place(relx=0.52, rely=0, relwidth=0.48, relheight=1)

        self.difficulty_label = tk.Label(stats_frame, text="Difficulty: Beginner",
                                    font=('Arial', max(12, int(self.window_width / 130)), 'bold'),
                                    fg=palette['difficulty_title_color'], bg=palette['background_3'])
        self.difficulty_label.place(relx=0.5, rely=0.15, anchor='center')

        self.score_label = tk.Label(stats_frame, text="Score: 0",
                                font=('Arial', max(12, int(self.window_width / 130)), 'bold'),
                                fg=palette['score_counter_color'], bg=palette['background_3'])
        self.score_label.place(relx=0.5, rely=0.4, anchor='center')

        self.gates_limit_label = tk.Label(stats_frame, text="Max Gates: 1",
                                        font=('Arial', max(10, int(self.window_width / 150))),
                                        fg=palette['max_gates_counter_color'], bg=palette['background_3'])
        self.gates_limit_label.place(relx=0.5, rely=0.65, anchor='center')


    def setup_circuit_area(self, parent):
        """Setup the circuit visualization area using relative positioning"""
        circuit_frame = tk.Frame(parent, bg=palette['background_2'], relief=tk.RAISED, bd=2)
        circuit_frame.place(relx=0, rely=0.2, relwidth=1, relheight=0.3)

        # Title
        circuit_title = tk.Label(circuit_frame, text="Quantum Circuit Designer",
                                font=('Arial', max(14, int(self.window_width / 100)), 'bold'),
                                fg=palette['main_circuit_title_color'], bg=palette['background_2'])
        circuit_title.place(relx=0.5, rely=0.1, anchor='center')

        # Circuit canvas
        canvas_container = tk.Frame(circuit_frame, bg=palette['background'], relief=tk.SUNKEN, bd=3)
        canvas_container.place(relx=0.05, rely=0.25, relwidth=0.9, relheight=0.65)

        canvas_width = int(self.window_width * 0.85)
        canvas_height = int(self.window_height * 0.18)

        self.circuit_canvas = tk.Canvas(canvas_container, width=canvas_width, height=canvas_height,
                                       bg=palette['background_4'], highlightthickness=0)
        self.circuit_canvas.place(relx=0.5, rely=0.5, anchor='center')

        self.canvas_width = canvas_width
        self.canvas_height = canvas_height


    def setup_bottom_section(self, parent):
        """Setup the bottom section with gate palette, controls, and state analysis using relative positioning"""
        bottom_frame = tk.Frame(parent, bg=palette['background_2'])
        bottom_frame.place(relx=0, rely=0.55, relwidth=1, relheight=0.45)

        # Left side - Gate Palette (40% width)
        gate_frame = tk.Frame(bottom_frame, bg=palette['background_2'], relief=tk.RAISED, bd=2)
        gate_frame.place(relx=0, rely=0, relwidth=0.4, relheight=1)

        tk.Label(gate_frame, text="Available Gates",
                font=('Arial', max(14, int(self.window_width / 100)), 'bold'),
                fg=palette['available_gates_title_color'], bg=palette['background_2']).place(relx=0.5, rely=0.08, anchor='center')

        # Gate buttons container
        self.gates_container = tk.Frame(gate_frame, bg=palette['background_2'])
        self.gates_container.place(relx=0.05, rely=0.18, relwidth=0.9, relheight=0.75)

        # Middle section - Puzzle Controls (30% width)
        controls_frame = tk.Frame(bottom_frame, bg=palette['background_2'], relief=tk.RAISED, bd=2)
        controls_frame.place(relx=0.42, rely=0, relwidth=0.26, relheight=1)

        self.setup_puzzle_controls(controls_frame)

        # Right side - Quantum State Analysis (30% width)
        results_frame = tk.Frame(bottom_frame, bg=palette['background_2'], relief=tk.RAISED, bd=2)
        results_frame.place(relx=0.7, rely=0, relwidth=0.3, relheight=1)

        self.setup_state_analysis(results_frame)


    def setup_puzzle_controls(self, parent):
        """Setup puzzle control buttons using relative positioning"""
        # Title
        control_title = tk.Label(parent, text="Puzzle Controls",
                            font=('Arial', max(14, int(self.window_width / 100)), 'bold'),
                            fg=palette['controls_title_text_color'], bg=palette['background_2'])
        control_title.place(relx=0.5, rely=0.08, anchor='center')

        # Create buttons container
        control_frame = tk.Frame(parent, bg=palette['background_2'])
        control_frame.place(relx=0.1, rely=0.18, relwidth=0.8, relheight=0.80)

        # Control buttons - FIXED Clear Circuit colors
        buttons_data = [
            ("Run Circuit", self.run_circuit, palette['run_button_background'], palette['run_button_text_color']),
            ("Clear Circuit", self.clear_circuit, palette['puzzle_mode_button_color'], palette['puzzle_mode_button_text_color']),  # FIXED: Use puzzle button colors instead of clear_button colors
            ("Hint", self.show_hint, palette['hint_button_background'], palette['hint_button_text_color']),
            ("Skip Level", self.skip_level, palette['skip_button_background'], palette['skip_button_text_color'])
        ]

        for i, (text, command, bg_color, fg_color) in enumerate(buttons_data):
            btn_container = tk.Frame(control_frame, bg=palette['background_3'], relief=tk.RAISED, bd=2)
            btn_container.place(relx=0.5, rely=0.09 + i * 0.22, anchor='center', relwidth=0.9, relheight=0.18)

            # Create canvas-based button instead of tk.Button
            btn_canvas = tk.Canvas(btn_container, bg=bg_color, highlightthickness=0, relief=tk.FLAT, bd=0)
            btn_canvas.place(relx=0.5, rely=0.5, anchor='center', relwidth=0.9, relheight=0.8)

            # Calculate canvas dimensions for text centering
            btn_container.update_idletasks()
            canvas_width = int(btn_container.winfo_width() * 0.9)
            canvas_height = int(btn_container.winfo_height() * 0.8)

            # Create button rectangle and text
            font_size = max(11, int(self.window_width / 140))
            rect_id = btn_canvas.create_rectangle(2, 2, canvas_width-2, canvas_height-2,
                                                fill=bg_color, outline=bg_color, width=0)
            text_id = btn_canvas.create_text(canvas_width//2, canvas_height//2, text=text,
                                        font=('Arial', font_size, 'bold'), fill=fg_color)

            # Add click handler with proper closure
            def create_click_handler(cmd):
                return lambda event: cmd()

            btn_canvas.bind("<Button-1>", create_click_handler(command))
            btn_canvas.configure(cursor='hand2')

            # Add hover effects
            original_bg = bg_color
            def create_hover_functions(canvas, rect_id, text_id, orig_color, orig_fg):
                def on_enter(event):
                    canvas.itemconfig(rect_id, fill=palette['button_hover_background'])
                    canvas.itemconfig(text_id, fill=palette['button_hover_text_color'])
                def on_leave(event):
                    canvas.itemconfig(rect_id, fill=orig_color)
                    canvas.itemconfig(text_id, fill=orig_fg)
                return on_enter, on_leave

            on_enter, on_leave = create_hover_functions(btn_canvas, rect_id, text_id, original_bg, fg_color)
            btn_canvas.bind("<Enter>", on_enter)
            btn_canvas.bind("<Leave>", on_leave)

        # Status info
        status_frame = tk.Frame(control_frame, bg=palette['background_3'], relief=tk.SUNKEN, bd=1)
        status_frame.place(relx=0.5, rely=0.95, anchor='center', relwidth=0.9, relheight=0.12)

        status_title = tk.Label(status_frame, text="Circuit Status",
                               font=('Arial', max(10, int(self.window_width / 160)), 'bold'),
                               fg=palette['circuit_status_title_color'], bg=palette['background_3'])
        status_title.place(relx=0.5, rely=0.25, anchor='center')

        self.gates_count_label = tk.Label(status_frame, text="Gates: 0",
                                         font=('Arial', max(9, int(self.window_width / 180))),
                                         fg=palette['gates_counter_color'], bg=palette['background_3'])
        self.gates_count_label.place(relx=0.3, rely=0.7, anchor='center')

        self.gates_used_label = tk.Label(status_frame, text="Used: 0/1",
                                        font=('Arial', max(9, int(self.window_width / 180))),
                                        fg=palette['used_gates_counter_color'], bg=palette['background_3'])
        self.gates_used_label.place(relx=0.7, rely=0.7, anchor='center')


    def setup_state_analysis(self, parent):
        """Setup quantum state analysis area using relative positioning"""
        # Title
        analysis_title = tk.Label(parent, text="Quantum State Analysis",
                                font=('Arial', max(14, int(self.window_width / 100)), 'bold'),
                                fg=palette['state_analysis_title_color'], bg=palette['background_2'])
        analysis_title.place(relx=0.5, rely=0.08, anchor='center')

        # Analysis container
        analysis_container = tk.Frame(parent, bg=palette['background'], relief=tk.SUNKEN, bd=3)
        analysis_container.place(relx=0.05, rely=0.18, relwidth=0.9, relheight=0.75)

        # Text area with scrollbar
        text_frame = tk.Frame(analysis_container, bg=palette['background'])
        text_frame.place(relx=0.02, rely=0.02, relwidth=0.96, relheight=0.96)

        self.state_display = tk.Text(text_frame,
                                   font=('Consolas', max(9, int(self.window_width / 200))),
                                   bg=palette['background_4'], fg=palette['state_display_text_color'],
                                   relief=tk.FLAT, bd=0, insertbackground=palette['state_display_insert_background'],
                                   selectbackground=palette['state_display_select_background'],
                                   selectforeground=palette['state_display_select_foreground'],
                                   wrap=tk.WORD)

        scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.state_display.yview,
                                bg=palette['background_3'], troughcolor=palette['background'],
                                activebackground=palette['state_scrollbar_active_background'])
        self.state_display.configure(yscrollcommand=scrollbar.set)

        self.state_display.place(relx=0, rely=0, relwidth=0.97, relheight=1)
        scrollbar.place(relx=0.97, rely=0, relwidth=0.03, relheight=1)


    def setup_gates(self, available_gates):
        """Setup available gate buttons for current level"""
        # Clear existing gates
        for widget in self.gates_container.winfo_children():
            widget.destroy()

        # Separate single and multi-qubit gates
        single_gates = [gate for gate in available_gates if gate in ['H', 'X', 'Y', 'Z', 'S', 'T']]
        multi_gates = [gate for gate in available_gates if gate in ['CNOT', 'CZ', 'Toffoli']]

        # Store gates for toggle functionality
        self.single_gates = single_gates
        self.multi_gates = multi_gates
        self.current_gate_view = 'single'  # Start with single-qubit gates

        # Create toggle button if both types of gates are available
        if single_gates and multi_gates:
            toggle_frame = tk.Frame(self.gates_container, bg=palette['background_2'])
            toggle_frame.pack(pady=(5, 15))

            # Canvas toggle button
            self.toggle_canvas = tk.Canvas(toggle_frame, highlightthickness=0, bd=0, width=250, height=40)
            self.toggle_canvas.pack()

            def draw_toggle_button():
                self.toggle_canvas.delete("all")
                width = 250
                height = 40
                bg_color = palette['show_multi_qubit_gates_button_background']
                text_color = palette['show_multi_qubit_gates_button_text_color']
                self.toggle_canvas.create_rectangle(0, 0, width, height, fill=bg_color, outline=bg_color, tags="bg")
                self.toggle_canvas.create_text(width//2, height//2, text="Show Multi-Qubit Gates",
                                             font=('Arial', 11, 'bold'),
                                             fill=text_color, tags="text")

            draw_toggle_button()

            # Click handler
            def on_toggle_click(event):
                self.toggle_gate_view()

            # Hover effects for toggle button
            def on_toggle_enter(event):
                self.toggle_canvas.itemconfig("bg", fill=palette['button_hover_background'])
                self.toggle_canvas.configure(cursor='hand2')

            def on_toggle_leave(event):
                self.toggle_canvas.itemconfig("bg", fill=palette['show_multi_qubit_gates_button_background'])
                self.toggle_canvas.configure(cursor='')

            # Bind events
            self.toggle_canvas.bind("<Button-1>", on_toggle_click)
            self.toggle_canvas.bind("<Enter>", on_toggle_enter)
            self.toggle_canvas.bind("<Leave>", on_toggle_leave)

        # Create container for gate display
        self.gate_display_frame = tk.Frame(self.gates_container, bg=palette['background_2'])
        self.gate_display_frame.pack(fill=tk.BOTH, expand=True)

        # Show initial gate set
        self.display_current_gates()


    def create_canvas_gate_button(self, parent, gate, color, description, relx, rely, relwidth, relheight):
        """Helper method to create a canvas-based gate button with proper closures"""
        # Container for the gate button using relative positioning
        btn_container = tk.Frame(parent, bg=palette['background_3'], relief=tk.RAISED, bd=1)
        btn_container.place(relx=relx, rely=rely, anchor='center', relwidth=relwidth, relheight=relheight)

        # Canvas button using relative positioning within its container
        btn_canvas = tk.Canvas(btn_container, highlightthickness=0, bd=0, bg=color)
        btn_canvas.place(relx=0.5, rely=0.4, anchor='center', relwidth=0.85, relheight=0.7)

        # Create button background and text with proper closure
        def create_draw_function(canvas, gate_color, gate_text):
            def draw_button(event=None):
                canvas.delete("all")
                width = canvas.winfo_width()
                height = canvas.winfo_height()
                if width > 1 and height > 1:  # Only draw if we have valid dimensions
                    canvas.create_rectangle(0, 0, width, height, fill=gate_color, outline=gate_color, tags="bg")
                    canvas.create_text(width//2, height//2, text=gate_text,
                                     font=('Arial', max(12, int(self.window_width / 140)), 'bold'),
                                     fill=palette['gate_symbol_color'], tags="text")
            return draw_button

        draw_button = create_draw_function(btn_canvas, color, gate)

        # Bind configure event to redraw when size changes
        btn_canvas.bind('<Configure>', draw_button)
        # Initial draw after the widget is mapped
        btn_canvas.after(10, draw_button)

        # Click handler with proper closure
        def create_click_handler(gate_name):
            def on_button_click(event):
                self.add_gate(gate_name)
            return on_button_click

        click_handler = create_click_handler(gate)

        # Hover effects with proper closure
        def create_hover_handlers(canvas, gate_color):
            def on_enter(event):
                canvas.delete("bg")
                width = canvas.winfo_width()
                height = canvas.winfo_height()
                if width > 1 and height > 1:
                    canvas.create_rectangle(0, 0, width, height, fill=palette['button_hover_background'], outline=palette['button_hover_background'], tags="bg")
                canvas.configure(cursor='hand2')
                canvas.tag_lower("bg")  # Ensure background is behind text

            def on_leave(event):
                canvas.delete("bg")
                width = canvas.winfo_width()
                height = canvas.winfo_height()
                if width > 1 and height > 1:
                    canvas.create_rectangle(0, 0, width, height, fill=gate_color, outline=gate_color, tags="bg")
                canvas.configure(cursor='')
                canvas.tag_lower("bg")  # Ensure background is behind text

            return on_enter, on_leave

        on_enter, on_leave = create_hover_handlers(btn_canvas, color)

        # Bind events
        btn_canvas.bind("<Button-1>", click_handler)
        btn_canvas.bind("<Enter>", on_enter)
        btn_canvas.bind("<Leave>", on_leave)

        # Description label using relative positioning
        desc_label = tk.Label(btn_container, text=description,
                            font=('Arial', max(8, int(self.window_width / 200))),
                            fg=palette['gate_description_color'], bg=palette['background_3'])
        desc_label.place(relx=0.5, rely=0.85, anchor='center')

        return btn_container, btn_canvas


    def display_current_gates(self):
        """Display the current set of gates (single or multi-qubit)"""
        # Clear existing gate display
        for widget in self.gate_display_frame.winfo_children():
            widget.destroy()

        gate_colors = {
            'H': palette['H_color'], 'X': palette['X_color'], 'Y': palette['Y_color'], 'Z': palette['Z_color'],
            'S': palette['S_color'], 'T': palette['T_color'], 'CNOT': palette['CNOT_color'], 'CZ': palette['CZ_color'],
            'Toffoli': palette['Toffoli_color']
        }

        gate_descriptions = {
            'H': 'Hadamard',
            'X': 'Pauli-X',
            'Y': 'Pauli-Y',
            'Z': 'Pauli-Z',
            'S': 'S Gate',
            'T': 'T Gate',
            'CNOT': 'CNOT',
            'CZ': 'CZ Gate',
            'Toffoli': 'Toffoli'
        }

        if self.current_gate_view == 'single' and self.single_gates:
            # Display single-qubit gates
            single_title = tk.Label(self.gate_display_frame, text="Single-Qubit Gates:",
                                font=('Arial', 12, 'bold'), fg=palette['single_qubit_gates_title_color'], bg=palette['background_2'])
            single_title.pack(pady=(5, 10))

            # Create main container for gates using relative positioning
            gates_main_container = tk.Frame(self.gate_display_frame, bg=palette['background_2'])
            gates_main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            # Calculate positions for 3-column grid
            cols = 3
            for i, gate in enumerate(self.single_gates):
                row = i // cols
                col = i % cols

                # Calculate relative positions
                relx = col * 0.33 + 0.165  # Center each button in its column (0.165, 0.495, 0.825)
                rely = row * 0.45 + 0.20   # Space rows evenly

                color = gate_colors.get(gate, '#ffffff')
                description = gate_descriptions.get(gate, '')

                # Create canvas button using helper method
                self.create_canvas_gate_button(gates_main_container, gate, color, description,
                                             relx, rely, 0.28, 0.4)

        elif self.current_gate_view == 'multi' and self.multi_gates:
            # Display multi-qubit gates in grid layout (same structure as single gates)
            multi_title = tk.Label(self.gate_display_frame, text="Multi-Qubit Gates:",
                                font=('Arial', 12, 'bold'), fg=palette['multi_qubit_gates_title_color'], bg=palette['background_2'])
            multi_title.pack(pady=(5, 10))

            # Create main container for gates using relative positioning
            gates_main_container = tk.Frame(self.gate_display_frame, bg=palette['background_2'])
            gates_main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            # Calculate positions for 3-column grid
            cols = 3
            for i, gate in enumerate(self.multi_gates):
                row = i // cols
                col = i % cols

                # Calculate relative positions
                relx = col * 0.33 + 0.165  # Center each button in its column
                rely = row * 0.25 + 0.15   # Space rows evenly

                color = gate_colors.get(gate, '#ffffff')
                description = gate_descriptions.get(gate, '')

                # Create canvas button using helper method
                self.create_canvas_gate_button(gates_main_container, gate, color, description,
                                             relx, rely, 0.28, 0.2)

        # If only one type of gates is available, show them without toggle
        elif not self.multi_gates and self.single_gates:
            # Only single gates available, show them directly
            self.current_gate_view = 'single'
            single_title = tk.Label(self.gate_display_frame, text="Available Gates:",
                                font=('Arial', 12, 'bold'), fg=palette['available_gates_title_color'], bg=palette['background_2'])
            single_title.pack(pady=(5, 10))

            # Create main container for gates using relative positioning
            gates_main_container = tk.Frame(self.gate_display_frame, bg=palette['background_2'])
            gates_main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            # Calculate positions for 3-column grid
            cols = 3
            for i, gate in enumerate(self.single_gates):
                row = i // cols
                col = i % cols

                # Calculate relative positions
                relx = col * 0.33 + 0.165  # Center each button in its column
                rely = row * 0.25 + 0.15   # Space rows evenly

                color = gate_colors.get(gate, '#ffffff')
                description = gate_descriptions.get(gate, '')

                # Create canvas button using helper method
                self.create_canvas_gate_button(gates_main_container, gate, color, description,
                                             relx, rely, 0.28, 0.2)

        elif not self.single_gates and self.multi_gates:
            # Only multi gates available, show them directly in grid
            self.current_gate_view = 'multi'
            multi_title = tk.Label(self.gate_display_frame, text="Available Gates:",
                                font=('Arial', 12, 'bold'), fg=palette['available_gates_title_color'], bg=palette['background_2'])
            multi_title.pack(pady=(5, 10))

            # Create main container for gates using relative positioning
            gates_main_container = tk.Frame(self.gate_display_frame, bg=palette['background_2'])
            gates_main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            # Calculate positions for 3-column grid
            cols = 3
            for i, gate in enumerate(self.multi_gates):
                row = i // cols
                col = i % cols

                # Calculate relative positions
                relx = col * 0.33 + 0.165  # Center each button in its column
                rely = row * 0.25 + 0.15   # Space rows evenly

                color = gate_colors.get(gate, '#ffffff')
                description = gate_descriptions.get(gate, '')

                # Create canvas button using helper method
                self.create_canvas_gate_button(gates_main_container, gate, color, description,
                                             relx, rely, 0.28, 0.2)


    def toggle_gate_view(self):
        """Toggle between single-qubit and multi-qubit gate views"""
        if self.current_gate_view == 'single':
            self.current_gate_view = 'multi'
            # Update canvas text
            self.toggle_canvas.itemconfig("text", text="Show Single-Qubit Gates")
        else:
            self.current_gate_view = 'single'
            # Update canvas text
            self.toggle_canvas.itemconfig("text", text="Show Multi-Qubit Gates")

        self.display_current_gates()


    def add_gate(self, gate):
        """Add a gate to the circuit"""
        level = self.levels[self.current_level]
        max_gates = level.get('max_gates', 999)

        # Check gate limit
        if len(self.placed_gates) >= max_gates:
            self.play_sound('error')
            self.show_gate_limit_warning(max_gates)
            return

        # Handle multi-qubit gates
        if gate in ['CNOT', 'CZ']:
            self.add_two_qubit_gate(gate)
        elif gate == 'Toffoli':
            self.add_toffoli_gate(gate)
        else:
            self.add_single_qubit_gate(gate)

        self.play_sound('gate_place')
        self.draw_circuit()


    def show_gate_limit_warning(self, max_gates):
        """Show a styled gate limit warning dialog without decorations"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Gate Limit Reached")
        dialog.overrideredirect(True)  # Remove window decorations
        dialog.configure(bg=palette['background'])
        dialog.transient(self.root)

        # FIXED: Calculate center position BEFORE creating geometry (30% bigger)
        dialog_width = 900  # 30% bigger than 600
        dialog_height = 750  # 30% bigger than 500
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - dialog_width) // 2
        y = (screen_height - dialog_height) // 2

        # FIXED: Set geometry immediately with center position - no update_idletasks before
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

        # Ensure dialog is on top and visible BEFORE grab_set
        dialog.lift()
        dialog.attributes("-topmost", True)
        dialog.update_idletasks()  # Make sure dialog is rendered
        dialog.deiconify()  # Ensure it's visible

        # NOW set grab and focus after dialog is fully visible
        dialog.grab_set()
        dialog.focus_set()

        # Main container with border
        main_frame = tk.Frame(dialog, bg=palette['background_2'], relief=tk.RAISED, bd=3)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Header with warning icon (30% bigger fonts)
        header_frame = tk.Frame(main_frame, bg=palette['background_2'])
        header_frame.pack(fill=tk.X, pady=(20, 15))

        warning_label = tk.Label(header_frame, text="WARNING",
                            font=('Arial', 31), fg='#ff6b6b', bg=palette['background_2'])  # 30% bigger: 24 -> 31
        warning_label.pack()

        title_label = tk.Label(header_frame, text="GATE LIMIT REACHED!",
                            font=('Arial', 23, 'bold'), fg='#ff6b6b', bg=palette['background_2'])  # 30% bigger: 18 -> 23
        title_label.pack(pady=(5, 0))

        # Content frame
        content_frame = tk.Frame(main_frame, bg=palette['background_3'], relief=tk.SUNKEN, bd=2)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=15)

        # Warning message (30% bigger font and wraplength)
        warning_text = f"""You have reached the maximum gate limit for this level.

    Current limit: {max_gates} gates
    Clear some gates to add new ones
    Or try optimizing your circuit

    Remember: Efficient solutions earn bonus points!"""

        warning_message = tk.Label(content_frame, text=warning_text,
                                font=('Arial', 17),  # 30% bigger: 13 -> 17
                                fg=palette['level_complete_info_label_text_color'],
                                bg=palette['background_3'],
                                justify=tk.CENTER,
                                wraplength=int(dialog_width * 0.8))  # 30% bigger wrapping
        warning_message.pack(expand=True, pady=20)

        # Button frame
        button_frame = tk.Frame(main_frame, bg=palette['background_2'])
        button_frame.pack(pady=(10, 15))

        # Clear circuit button (30% bigger)
        clear_canvas = self.create_canvas_dialog_button(
            button_frame, "Clear Circuit",
            lambda: [self.clear_circuit(), dialog.destroy()],
            palette['puzzle_mode_button_color'],  # Fixed color
            palette['puzzle_mode_button_text_color'],  # Fixed color
            width=208, height=52, font_size=16  # 30% bigger: 160x40, font 12 -> 208x52, font 16
        )
        clear_canvas.pack(side=tk.LEFT, padx=10)

        # OK button (30% bigger)
        ok_canvas = self.create_canvas_dialog_button(
            button_frame, "Got it!",
            dialog.destroy,
            palette['return_to_gamemode_button_background'],
            palette['return_to_gamemode_button_text_color'],
            width=156, height=52, font_size=16  # 30% bigger: 120x40, font 12 -> 156x52, font 16
        )
        ok_canvas.pack(side=tk.LEFT, padx=10)

        # Handle ESC key to close
        dialog.bind('<Escape>', lambda e: dialog.destroy())


    def add_single_qubit_gate(self, gate):
        """Add a single qubit gate with target selection"""
        level = self.levels[self.current_level]
        num_qubits = level['qubits']

        if num_qubits == 1:
            # Only one qubit, add directly
            gate_info = {'gate': gate, 'qubits': [0]}
            self.placed_gates.append(gate_info)
        else:
            # Multiple qubits, ask user to select target
            target = self.ask_qubit_selection("Select target qubit:", num_qubits)
            if target is not None:
                gate_info = {'gate': gate, 'qubits': [target]}
                self.placed_gates.append(gate_info)


    def add_two_qubit_gate(self, gate):
        """Add a two-qubit gate with control and target selection"""
        level = self.levels[self.current_level]
        num_qubits = level['qubits']

        if num_qubits < 2:
            self.show_error_dialog(f"{gate} gate requires at least 2 qubits!")
            return

        # Ask for control and target qubits
        control = self.ask_qubit_selection("Select control qubit:", num_qubits)
        if control is None:
            return

        available_targets = [i for i in range(num_qubits) if i != control]
        target = self.ask_qubit_selection("Select target qubit:", num_qubits, available_targets)
        if target is None:
            return

        gate_info = {'gate': gate, 'qubits': [control, target]}
        self.placed_gates.append(gate_info)


    def add_toffoli_gate(self, gate):
        """Add a Toffoli gate with two controls and one target"""
        level = self.levels[self.current_level]
        num_qubits = level['qubits']

        if num_qubits < 3:
            self.show_error_dialog("Toffoli gate requires at least 3 qubits!")
            return

        # Ask for two control qubits and one target
        control1 = self.ask_qubit_selection("Select first control qubit:", num_qubits)
        if control1 is None:
            return

        available_control2 = [i for i in range(num_qubits) if i != control1]
        control2 = self.ask_qubit_selection("Select second control qubit:", num_qubits, available_control2)
        if control2 is None:
            return

        available_targets = [i for i in range(num_qubits) if i not in [control1, control2]]
        target = self.ask_qubit_selection("Select target qubit:", num_qubits, available_targets)
        if target is None:
            return

        gate_info = {'gate': gate, 'qubits': [control1, control2, target]}
        self.placed_gates.append(gate_info)


    def show_error_dialog(self, message):
        """Show a styled error dialog without decorations"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Error")
        dialog.overrideredirect(True)  # Remove window decorations
        dialog.geometry("400x200")
        dialog.configure(bg=palette['background'])
        dialog.transient(self.root)

        # Center the dialog on screen
        dialog.update_idletasks()
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 200) // 2
        dialog.geometry(f"400x200+{x}+{y}")

        # Ensure dialog is on top and visible BEFORE grab_set
        dialog.lift()
        dialog.attributes("-topmost", True)
        dialog.update_idletasks()  # Make sure dialog is rendered
        dialog.deiconify()  # Ensure it's visible

        # NOW set grab and focus after dialog is fully visible
        dialog.grab_set()
        dialog.focus_set()

        # Main container with border
        main_frame = tk.Frame(dialog, bg=palette['background_2'], relief=tk.RAISED, bd=3)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Header with error icon
        header_frame = tk.Frame(main_frame, bg=palette['background_2'])
        header_frame.pack(fill=tk.X, pady=(15, 10))

        error_label = tk.Label(header_frame, text="️ ERROR",
                            font=('Arial', 20), fg='#ff6b6b', bg=palette['background_2'])
        error_label.pack()

        title_label = tk.Label(header_frame, text="ERROR",
                            font=('Arial', 16, 'bold'), fg='#ff6b6b', bg=palette['background_2'])
        title_label.pack(pady=(5, 0))

        # Content frame
        content_frame = tk.Frame(main_frame, bg=palette['background_3'], relief=tk.SUNKEN, bd=2)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Error message
        error_message = tk.Label(content_frame, text=message,
                            font=('Arial', 12),
                            fg=palette['level_complete_info_label_text_color'],
                            bg=palette['background_3'],
                            wraplength=350, justify=tk.CENTER)
        error_message.pack(expand=True, pady=15)

        # OK button using canvas
        ok_canvas = self.create_canvas_dialog_button(
            main_frame, "OK",
            dialog.destroy,
            palette['return_to_gamemode_button_background'],
            palette['return_to_gamemode_button_text_color'],
            width=120, height=40, font_size=12
        )
        ok_canvas.pack(pady=(10, 15))

        # Handle ESC key to close
        dialog.bind('<Escape>', lambda e: dialog.destroy())


    def ask_qubit_selection(self, prompt, num_qubits, available_qubits=None):
        """Ask user to select a qubit with no decorations dialog"""
        if available_qubits is None:
            available_qubits = list(range(num_qubits))

        if len(available_qubits) == 1:
            return available_qubits[0]

        # Create a simple selection dialog without decorations
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Qubit")
        dialog.overrideredirect(True)  # Remove window decorations
        dialog.geometry("300x150")
        dialog.configure(bg=palette['background_2'])
        dialog.transient(self.root)
        dialog.grab_set()

        # Center the dialog on screen
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 300) // 2
        y = (dialog.winfo_screenheight() - 150) // 2
        dialog.geometry(f"300x150+{x}+{y}")

        result = [None]

        tk.Label(dialog, text=prompt, font=('Arial', 12),
                fg=palette['prompt_text_color'], bg=palette['background_2']).pack(pady=10)

        button_frame = tk.Frame(dialog, bg=palette['background_2'])
        button_frame.pack(pady=10)

        def select_qubit(qubit):
            result[0] = qubit
            dialog.destroy()

        for qubit in available_qubits:
            canvas_btn = self.create_canvas_dialog_button(
                button_frame, f"Qubit {qubit}",
                lambda q=qubit: select_qubit(q),
                palette['qubit_selection_button_background'],
                palette['qubit_selection_button_text_color'],
                width=80, height=35, font_size=10
            )
            canvas_btn.pack(side=tk.LEFT, padx=5)

        # Cancel button
        cancel_canvas = self.create_canvas_dialog_button(
            button_frame, "Cancel",
            dialog.destroy,
            palette['cancel_selection_button_background'],
            palette['cancel_selection_button_text_color'],
            width=80, height=35, font_size=10
        )
        cancel_canvas.pack(side=tk.LEFT, padx=5)

        dialog.wait_window()
        return result[0]


    def clear_circuit(self):
        """Clear all gates from the circuit"""
        self.placed_gates = []
        self.play_sound('clear')
        self.draw_circuit()


    def run_circuit(self):
        """Run the quantum circuit and check if puzzle is solved"""
        level = self.levels[self.current_level]

        if not self.placed_gates:
            self.show_info_dialog("No Circuit", "Please add some gates to your circuit first!")
            return

        try:
            # Create quantum circuit
            qc = QuantumCircuit(level['qubits'])

            # Set initial state
            self.set_initial_state(qc, level['input_state'])

            # Add gates
            for gate_info in self.placed_gates:
                gate = gate_info['gate']
                qubits = gate_info['qubits']

                if gate == 'H':
                    qc.h(qubits[0])
                elif gate == 'X':
                    qc.x(qubits[0])
                elif gate == 'Y':
                    qc.y(qubits[0])
                elif gate == 'Z':
                    qc.z(qubits[0])
                elif gate == 'S':
                    qc.s(qubits[0])
                elif gate == 'T':
                    qc.t(qubits[0])
                elif gate == 'CNOT':
                    qc.cx(qubits[0], qubits[1])
                elif gate == 'CZ':
                    qc.cz(qubits[0], qubits[1])
                elif gate == 'Toffoli':
                    qc.ccx(qubits[0], qubits[1], qubits[2])

            # Get final state
            state_vector = Statevector.from_instruction(qc)

            # Check if puzzle is solved
            if self.check_solution(state_vector, level):
                self.level_complete()
            else:
                self.display_circuit_results(state_vector, level)

        except Exception as e:
            self.show_error_dialog(f"Error running circuit: {str(e)}")


    def show_info_dialog(self, title, message):
        """Show a styled info dialog without decorations"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.overrideredirect(True)  # Remove window decorations
        dialog.configure(bg=palette['background'])
        dialog.transient(self.root)

        # FIXED: Increased dialog size by 40% (was 400x200)
        dialog_width = 560  # 40% bigger: 400 -> 560
        dialog_height = 280  # 40% bigger: 200 -> 280

        # Center the dialog on screen
        dialog.update_idletasks()
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - dialog_width) // 2
        y = (screen_height - dialog_height) // 2
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

        # Ensure dialog is on top and visible BEFORE grab_set
        dialog.lift()
        dialog.attributes("-topmost", True)
        dialog.update_idletasks()  # Make sure dialog is rendered
        dialog.deiconify()  # Ensure it's visible

        # NOW set grab and focus after dialog is fully visible
        dialog.grab_set()
        dialog.focus_set()

        # Rest of the dialog implementation...
        # Main container with border
        main_frame = tk.Frame(dialog, bg=palette['background_2'], relief=tk.RAISED, bd=3)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # FIXED: Bigger title font
        title_label = tk.Label(main_frame, text=title,
                            font=('Arial', 20, 'bold'),  # Increased from 16
                            fg=palette['title_color'], bg=palette['background_2'])
        title_label.pack(pady=(20, 15))  # More padding

        # FIXED: Bigger message font with better wrapping
        message_label = tk.Label(main_frame, text=message,
                            font=('Arial', 16),  # Increased from 12
                            fg=palette['level_complete_info_label_text_color'],
                            bg=palette['background_2'],
                            wraplength=int(dialog_width * 0.85), justify=tk.CENTER)  # Better wrapping
        message_label.pack(expand=True, pady=20)  # More padding

        # FIXED: Bigger OK button
        ok_canvas = self.create_canvas_dialog_button(
            main_frame, "OK",
            dialog.destroy,
            palette['return_to_gamemode_button_background'],
            palette['return_to_gamemode_button_text_color'],
            width=160, height=50, font_size=16  # Bigger button: 120x40 -> 160x50, font 12 -> 16
        )
        ok_canvas.pack(pady=(15, 20))  # More padding

        # Handle ESC key to close
        dialog.bind('<Escape>', lambda e: dialog.destroy())


    def set_initial_state(self, qc, initial_state):
        """Set the initial state of the quantum circuit"""
        if initial_state == '|1⟩':
            qc.x(0)
        elif initial_state == '|+⟩':
            qc.h(0)
        elif initial_state == '|-⟩':
            qc.x(0)
            qc.h(0)
        elif initial_state == '|10⟩':
            qc.x(0)
        elif initial_state == '|110⟩':
            qc.x(0)
            qc.x(1)
        elif initial_state == '|+0⟩':
            qc.h(0)
        # Add more initial states as needed for your JSON levels
        # |0⟩, |00⟩, |000⟩, |0000⟩ are default, no preparation needed


    def check_solution(self, state_vector, level):
        """Check if the current state matches the target state"""
        target_state = level['target_state']
        state_data = state_vector.data
        tolerance = 0.01  # Tolerance for floating point comparisons

        # Single qubit states
        if target_state == '|1⟩' and level['qubits'] == 1:
            # |1⟩ state: [0, 1]
            return (abs(state_data[1]) > 0.99 and abs(state_data[0]) < tolerance and
                    abs(np.real(state_data[1]) - 1.0) < tolerance and
                    abs(np.imag(state_data[1])) < tolerance)

        elif target_state == '|0⟩' and level['qubits'] == 1:
            # |0⟩ state: [1, 0]
            return (abs(state_data[0]) > 0.99 and abs(state_data[1]) < tolerance and
                    abs(np.real(state_data[0]) - 1.0) < tolerance and
                    abs(np.imag(state_data[0])) < tolerance)

        elif target_state == '|+⟩' and level['qubits'] == 1:
            # |+⟩ = (|0⟩ + |1⟩)/√2: [1/√2, 1/√2]
            expected_amp = 1/np.sqrt(2)
            return (abs(abs(state_data[0]) - expected_amp) < tolerance and
                    abs(abs(state_data[1]) - expected_amp) < tolerance and
                    abs(np.real(state_data[0]) - expected_amp) < tolerance and
                    abs(np.imag(state_data[0])) < tolerance and
                    abs(np.real(state_data[1]) - expected_amp) < tolerance and
                    abs(np.imag(state_data[1])) < tolerance)

        elif target_state == '|-⟩' and level['qubits'] == 1:
            # |-⟩ = (|0⟩ - |1⟩)/√2: [1/√2, -1/√2]
            expected_amp = 1/np.sqrt(2)
            return (abs(abs(state_data[0]) - expected_amp) < tolerance and
                    abs(abs(state_data[1]) - expected_amp) < tolerance and
                    abs(np.real(state_data[0]) - expected_amp) < tolerance and
                    abs(np.imag(state_data[0])) < tolerance and
                    abs(np.real(state_data[1]) + expected_amp) < tolerance and
                    abs(np.imag(state_data[1])) < tolerance)

        elif target_state == '|i·1⟩' and level['qubits'] == 1:
            # Y|0⟩ = i|1⟩: [0, i]
            return (abs(state_data[0]) < tolerance and
                    abs(state_data[1]) > 0.99 and
                    abs(np.real(state_data[1])) < tolerance and
                    abs(np.imag(state_data[1]) - 1.0) < tolerance)

        elif target_state == '|+i⟩' and level['qubits'] == 1:
            # S|+⟩ = (|0⟩ + i|1⟩)/√2: [1/√2, i/√2]
            expected_amp = 1/np.sqrt(2)
            return (abs(abs(state_data[0]) - expected_amp) < tolerance and
                    abs(abs(state_data[1]) - expected_amp) < tolerance and
                    abs(np.real(state_data[0]) - expected_amp) < tolerance and
                    abs(np.imag(state_data[0])) < tolerance and
                    abs(np.real(state_data[1])) < tolerance and
                    abs(np.imag(state_data[1]) - expected_amp) < tolerance)

        elif target_state == '|T+⟩' and level['qubits'] == 1:
            # T|+⟩ = (|0⟩ + e^(iπ/4)|1⟩)/√2
            expected_amp = 1/np.sqrt(2)
            expected_phase = np.exp(1j * np.pi / 4)  # e^(iπ/4)
            expected_1_state = expected_amp * expected_phase
            return (abs(abs(state_data[0]) - expected_amp) < tolerance and
                    abs(abs(state_data[1]) - expected_amp) < tolerance and
                    abs(np.real(state_data[0]) - expected_amp) < tolerance and
                    abs(np.imag(state_data[0])) < tolerance and
                    abs(state_data[1] - expected_1_state) < tolerance)

        # Two qubit states
        elif target_state == '|11⟩' and level['qubits'] == 2:
            # |11⟩ state: [0, 0, 0, 1]
            return (abs(state_data[3]) > 0.99 and
                    abs(state_data[0]) < tolerance and abs(state_data[1]) < tolerance and
                    abs(state_data[2]) < tolerance and
                    abs(np.real(state_data[3]) - 1.0) < tolerance and
                    abs(np.imag(state_data[3])) < tolerance)

        elif target_state == '|++⟩' and level['qubits'] == 2:
            # |++⟩ = |+⟩⊗|+⟩ = (|00⟩ + |01⟩ + |10⟩ + |11⟩)/2
            expected_amp = 0.5
            return all(abs(abs(state_data[i]) - expected_amp) < tolerance and
                        abs(np.real(state_data[i]) - expected_amp) < tolerance and
                        abs(np.imag(state_data[i])) < tolerance
                        for i in range(4))

        elif target_state == '|Φ+⟩' and level['qubits'] == 2:
            # |Φ+⟩ = (|00⟩ + |11⟩)/√2: [1/√2, 0, 0, 1/√2]
            expected_amp = 1/np.sqrt(2)
            return (abs(abs(state_data[0]) - expected_amp) < tolerance and
                    abs(state_data[1]) < tolerance and abs(state_data[2]) < tolerance and
                    abs(abs(state_data[3]) - expected_amp) < tolerance and
                    abs(np.real(state_data[0]) - expected_amp) < tolerance and
                    abs(np.imag(state_data[0])) < tolerance and
                    abs(np.real(state_data[3]) - expected_amp) < tolerance and
                    abs(np.imag(state_data[3])) < tolerance)

        elif target_state == '|Φ-⟩' and level['qubits'] == 2:
            # |Φ-⟩ = (|00⟩ - |11⟩)/√2: [1/√2, 0, 0, -1/√2]
            expected_amp = 1/np.sqrt(2)
            return (abs(abs(state_data[0]) - expected_amp) < tolerance and
                    abs(state_data[1]) < tolerance and abs(state_data[2]) < tolerance and
                    abs(abs(state_data[3]) - expected_amp) < tolerance and
                    abs(np.real(state_data[0]) - expected_amp) < tolerance and
                    abs(np.imag(state_data[0])) < tolerance and
                    abs(np.real(state_data[3]) + expected_amp) < tolerance and
                    abs(np.imag(state_data[3])) < tolerance)

        elif target_state == '|Ψ+⟩' and level['qubits'] == 2:
            # |Ψ+⟩ = (|01⟩ + |10⟩)/√2: [0, 1/√2, 1/√2, 0]
            expected_amp = 1/np.sqrt(2)
            return (abs(state_data[0]) < tolerance and
                    abs(abs(state_data[1]) - expected_amp) < tolerance and
                    abs(abs(state_data[2]) - expected_amp) < tolerance and
                    abs(state_data[3]) < tolerance and
                    abs(np.real(state_data[1]) - expected_amp) < tolerance and
                    abs(np.imag(state_data[1])) < tolerance and
                    abs(np.real(state_data[2]) - expected_amp) < tolerance and
                    abs(np.imag(state_data[2])) < tolerance)

        elif target_state == '|Ψ-⟩' and level['qubits'] == 2:
            # |Ψ-⟩ = (|01⟩ - |10⟩)/√2: [0, 1/√2, -1/√2, 0]
            expected_amp = 1/np.sqrt(2)
            return (abs(state_data[0]) < tolerance and
                    abs(abs(state_data[1]) - expected_amp) < tolerance and
                    abs(abs(state_data[2]) - expected_amp) < tolerance and
                    abs(state_data[3]) < tolerance and
                    abs(np.real(state_data[1]) - expected_amp) < tolerance and
                    abs(np.imag(state_data[1])) < tolerance and
                    abs(np.real(state_data[2]) + expected_amp) < tolerance and
                    abs(np.imag(state_data[2])) < tolerance)

        elif target_state == '|-0⟩' and level['qubits'] == 2:
            # |-0⟩ = |-⟩ ⊗ |0⟩ = (|00⟩ - |10⟩)/√2: [1/√2, 0, -1/√2, 0]
            expected_amp = 1/np.sqrt(2)
            return (abs(abs(state_data[0]) - expected_amp) < tolerance and
                    abs(state_data[1]) < tolerance and
                    abs(abs(state_data[2]) - expected_amp) < tolerance and
                    abs(state_data[3]) < tolerance and
                    abs(np.real(state_data[0]) - expected_amp) < tolerance and
                    abs(np.imag(state_data[0])) < tolerance and
                    abs(np.real(state_data[2]) + expected_amp) < tolerance and
                    abs(np.imag(state_data[2])) < tolerance)

        # Three qubit states
        elif target_state == '|111⟩' and level['qubits'] == 3:
            # |111⟩ state: [0,0,0,0,0,0,0,1]
            return (abs(state_data[7]) > 0.99 and
                    all(abs(state_data[i]) < tolerance for i in range(7)) and
                    abs(np.real(state_data[7]) - 1.0) < tolerance and
                    abs(np.imag(state_data[7])) < tolerance)

        elif target_state == '|0Φ+⟩' and level['qubits'] == 3:
            # |0⟩ ⊗ |Φ+⟩ = |0⟩ ⊗ (|00⟩ + |11⟩)/√2 = (|000⟩ + |011⟩)/√2
            expected_amp = 1/np.sqrt(2)
            return (abs(abs(state_data[0]) - expected_amp) < tolerance and  # |000⟩
                    abs(state_data[1]) < tolerance and abs(state_data[2]) < tolerance and
                    abs(abs(state_data[3]) - expected_amp) < tolerance and  # |011⟩
                    abs(state_data[4]) < tolerance and abs(state_data[5]) < tolerance and
                    abs(state_data[6]) < tolerance and abs(state_data[7]) < tolerance and
                    abs(np.real(state_data[0]) - expected_amp) < tolerance and
                    abs(np.imag(state_data[0])) < tolerance and
                    abs(np.real(state_data[3]) - expected_amp) < tolerance and
                    abs(np.imag(state_data[3])) < tolerance)

        elif target_state == '|GHZ⟩' and level['qubits'] == 3:
            # |GHZ⟩ = (|000⟩ + |111⟩)/√2: [1/√2, 0, 0, 0, 0, 0, 0, 1/√2]
            expected_amp = 1/np.sqrt(2)
            return (abs(abs(state_data[0]) - expected_amp) < tolerance and  # |000⟩
                    abs(state_data[1]) < tolerance and abs(state_data[2]) < tolerance and
                    abs(state_data[3]) < tolerance and abs(state_data[4]) < tolerance and
                    abs(state_data[5]) < tolerance and abs(state_data[6]) < tolerance and
                    abs(abs(state_data[7]) - expected_amp) < tolerance and  # |111⟩
                    abs(np.real(state_data[0]) - expected_amp) < tolerance and
                    abs(np.imag(state_data[0])) < tolerance and
                    abs(np.real(state_data[7]) - expected_amp) < tolerance and
                    abs(np.imag(state_data[7])) < tolerance)

        # Custom/Placeholder states - these need specific implementations
        elif target_state == '|W⟩' and level['qubits'] == 3:
            # W state = (|001⟩ + |010⟩ + |100⟩)/√3
            expected_amp = 1/np.sqrt(3)
            return (abs(state_data[0]) < tolerance and  # |000⟩
                    abs(abs(state_data[1]) - expected_amp) < tolerance and  # |001⟩
                    abs(abs(state_data[2]) - expected_amp) < tolerance and  # |010⟩
                    abs(state_data[3]) < tolerance and  # |011⟩
                    abs(abs(state_data[4]) - expected_amp) < tolerance and  # |100⟩
                    abs(state_data[5]) < tolerance and  # |101⟩
                    abs(state_data[6]) < tolerance and  # |110⟩
                    abs(state_data[7]) < tolerance)  # |111⟩

        # Placeholder implementations for undefined states
        # These return True for now but should be properly defined
        elif target_state in ['|err⟩', '|QFT⟩', '|MaxEnt⟩', '|Secret⟩',
                                '|Interference⟩', '|ErrorCode⟩', '|Ultimate⟩']:
            # For these custom states, we need to define what they actually represent
            # For now, return True to allow level progression during development
            print(f"Warning: Target state '{target_state}' not fully implemented")

            # Placeholder logic - you can replace these with actual state definitions
            if target_state == '|QFT⟩' and level['qubits'] == 2:
                # 2-qubit QFT of |00⟩ should give equal superposition with phases
                return all(abs(abs(state_data[i]) - 0.5) < tolerance for i in range(4))

            elif target_state == '|MaxEnt⟩' and level['qubits'] == 4:
                # Maximally entangled 4-qubit state - check for equal superposition
                expected_amp = 1/4
                return all(abs(abs(state_data[i]) - expected_amp) < tolerance for i in range(16))

            # For other undefined states, return True (temporary)
            return True

        # Default case - should not happen with proper target states
        else:
            print(f"Warning: Unknown target state '{target_state}' for {level['qubits']} qubits")
            return False


    def display_circuit_results(self, state_vector, level):
        """Display the results of running the circuit"""
        self.state_display.config(state=tk.NORMAL)
        self.state_display.delete(1.0, tk.END)

        self.state_display.insert(tk.END, "Circuit Results\n")
        self.state_display.insert(tk.END, "═" * 30 + "\n\n")

        # Display state vector
        self.state_display.insert(tk.END, "Final Quantum State:\n")
        state_data = state_vector.data

        for i, amplitude in enumerate(state_data):
            if abs(amplitude) > 0.001:  # Only show significant amplitudes
                binary = format(i, f'0{level["qubits"]}b')
                prob = abs(amplitude) ** 2
                self.state_display.insert(tk.END, f"|{binary}⟩: {amplitude:.3f} (prob: {prob:.3f})\n")

        self.state_display.insert(tk.END, f"\nTarget: {level['target_state']}\n")
        self.state_display.insert(tk.END, "Puzzle not solved yet. Try adjusting your circuit!\n")
        self.play_sound('error')
        self.state_display.config(state=tk.DISABLED)


    def level_complete(self):
        """Handle level completion with styled dialog"""
        self.play_sound('level_complete')
        level = self.levels[self.current_level]

        # Calculate score based on efficiency
        max_gates = level.get('max_gates', len(self.placed_gates))
        efficiency_bonus = max(0, (max_gates - len(self.placed_gates)) * 10)
        level_score = 100 + efficiency_bonus
        self.score += level_score

        # Update score display
        self.score_label.config(text=f"Score: {self.score}")

        # Create custom styled dialog
        self.show_level_complete_dialog(level, level_score, max_gates)

        # Note: We no longer automatically proceed to next level here
        # The user must click the "Next Level" button or close the dialog

        # Save progress after level completion
        self.save_progress()


    def show_level_complete_dialog(self, level, level_score, max_gates):
        """Show a custom styled level complete dialog without decorations"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Level Complete!")
        dialog.overrideredirect(True)  # Remove window decorations
        dialog_dimensions = (1050, 900)  # 50% bigger (was 700x600)
        dialog.geometry(f"{dialog_dimensions[0]}x{dialog_dimensions[1]}")
        dialog.configure(bg=palette['background'])
        dialog.transient(self.root)

        # Center the dialog in the middle of the screen
        dialog.update_idletasks()
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - dialog_dimensions[0]) // 2
        y = (screen_height - dialog_dimensions[1]) // 2
        dialog.geometry(f"{dialog_dimensions[0]}x{dialog_dimensions[1]}+{x}+{y}")

        # Ensure dialog is on top and visible BEFORE grab_set
        dialog.lift()
        dialog.attributes("-topmost", True)
        dialog.update_idletasks()  # Make sure dialog is rendered
        dialog.deiconify()  # Ensure it's visible

        # NOW set grab and focus after dialog is fully visible
        dialog.grab_set()
        dialog.focus_set()

        # Main container with border
        main_frame = tk.Frame(dialog, bg=palette['background_2'], relief=tk.RAISED, bd=3)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Header with celebration emoji
        header_frame = tk.Frame(main_frame, bg=palette['background_2'])
        header_frame.pack(fill=tk.X, pady=(20, 15))

        celebration_label = tk.Label(header_frame, text="LEVEL COMPLETE!",
                                font=('Arial', 28), fg='#ffd700', bg=palette['background_2'])
        celebration_label.pack()

        # Content frame
        content_frame = tk.Frame(main_frame, bg=palette['background_3'], relief=tk.SUNKEN, bd=2)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Level info
        info_text = f"""{level['name']}

    Gates Used: {len(self.placed_gates)}/{max_gates}
    Level Score: +{level_score}
    Total Score: {self.score}

    {self.get_performance_message(len(self.placed_gates), max_gates)}"""

        info_label = tk.Label(content_frame, text=info_text,
                            font=('Arial', 35), fg=palette['level_complete_info_label_text_color'], bg=palette['background_3'],
                            justify=tk.CENTER)
        info_label.pack(expand=True, pady=30)

        # Button frame with more space
        button_frame = tk.Frame(main_frame, bg=palette['background_2'])
        button_frame.pack(fill=tk.X, pady=(20, 25))

        # Button container for horizontal layout
        btn_container = tk.Frame(button_frame, bg=palette['background_2'])
        btn_container.pack()

        # Next Level button - canvas-based
        next_canvas = self.create_canvas_dialog_button(
            btn_container, "Next Level",
            lambda: [dialog.destroy(), self.proceed_to_next_level()],
            palette['return_to_gamemode_button_background'], palette['return_to_gamemode_button_text_color'],
            width=300, height=75, font_size=24  # 50% bigger (was 200x50, font 16)
        )
        next_canvas.pack(side=tk.LEFT, padx=30)

        close_canvas = self.create_canvas_dialog_button(
            btn_container, "Close",
            dialog.destroy,
            palette['close_gamemode_button_background'], palette['close_gamemode_button_hover_text_color'],
            width=210, height=75, font_size=24  # 50% bigger (was 140x50, font 16)
        )
        close_canvas.pack(side=tk.LEFT, padx=30)

        # Hide next level button if this is the last level
        if self.current_level + 1 >= len(self.levels):
            # Update the text on the canvas button
            def update_next_button():
                next_canvas.delete("all")
                canvas_width = next_canvas.winfo_width()
                canvas_height = next_canvas.winfo_height()
                if canvas_width > 1 and canvas_height > 1:
                    next_canvas.create_rectangle(2, 2, canvas_width-2, canvas_height-2,
                                            fill='#888888', outline="#2b3340", width=1, tags="bg")
                    next_canvas.create_text(canvas_width//2, canvas_height//2, text="Game Complete!",
                                        font=('Arial', 16, 'bold'), fill='#ffffff', tags="text")
            next_canvas.after(10, update_next_button)
            # Disable the button by removing click binding
            next_canvas.unbind("<Button-1>")


    def proceed_to_next_level(self):
        """Proceed to the next level"""
        if self.current_level + 1 < len(self.levels):
            self.load_level(self.current_level + 1)
        else:
            self.game_complete()


    def get_performance_message(self, gates_used, max_gates):
        """Get a performance message based on gate efficiency"""
        if gates_used <= max_gates * 0.5:
            return "PERFECT! Outstanding efficiency!"
        elif gates_used <= max_gates * 0.75:
            return "EXCELLENT! Great optimization!"
        elif gates_used <= max_gates:
            return "GOOD! You solved it!"
        else:
            return "COMPLETED! Keep practicing!"


    def game_complete(self):
        """Handle game completion with styled dialog without decorations"""
        # Create custom styled dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Game Complete!")
        dialog.overrideredirect(True)  # Remove window decorations
        dialog.geometry("450x350")
        dialog.configure(bg=palette['background'])
        dialog.transient(self.root)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - 450) // 2
        y = (screen_height - 350) // 2
        dialog.geometry(f"450x350+{x}+{y}")

        # Main container with border
        main_frame = tk.Frame(dialog, bg=palette['background_2'], relief=tk.RAISED, bd=3)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Header with celebration
        header_frame = tk.Frame(main_frame, bg=palette['background_2'])
        header_frame.pack(fill=tk.X, pady=(15, 10))

        celebration_label = tk.Label(header_frame, text="QUANTUM MASTER!",
                                   font=('Arial', 24), fg='#ffd700', bg=palette['background_2'])
        celebration_label.pack()

        title_label = tk.Label(header_frame, text="QUANTUM MASTER!",
                             font=('Arial', 20, 'bold'), fg=palette['quantum_master_title_color'], bg=palette['background_2'])
        title_label.pack(pady=(5, 0))

        # Content frame
        content_frame = tk.Frame(main_frame, bg=palette['background_3'], relief=tk.SUNKEN, bd=2)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Completion message
        completion_text = f"""CONGRATULATIONS!

You've mastered all quantum puzzle levels!

Final Score: {self.score}
Levels Completed: {len(self.levels)}
You're now a Quantum Circuit Master!

Thank you for playing Infinity Qubit!"""

        completion_label = tk.Label(content_frame, text=completion_text,
                                  font=('Arial', 12), fg='#ffffff', bg=palette['background_3'],
                                  justify=tk.CENTER)
        completion_label.pack(expand=True, pady=20)

        # Button frame
        button_frame = tk.Frame(main_frame, bg=palette['background_2'])
        button_frame.pack(fill=tk.X, pady=(0, 15))

        # Return to menu button - canvas-based
        menu_canvas = self.create_canvas_dialog_button(
            button_frame, "Return to Main Menu",
            lambda: [dialog.destroy(), self.go_back_to_menu()],
            palette['run_button_background'], palette['run_button_text_color'],
            width=220, height=40, font_size=12
        )
        menu_canvas.pack(pady=10)


    def show_hint(self):
        """Show hint for current level"""
        level = self.levels[self.current_level]
        hint = level.get('hint', 'No hint available for this level.')

        # Create custom hint dialog without decorations
        dialog = tk.Toplevel(self.root)
        dialog.title("💡 Hint")
        dialog.overrideredirect(True)  # Remove window decorations
        dialog.configure(bg=palette['background'])
        dialog.transient(self.root)

        # FIXED: Calculate center position BEFORE creating geometry (30% bigger)
        dialog_width = 850  # 30% bigger than 500
        dialog_height = 600  # 30% bigger than 300
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - dialog_width) // 2
        y = (screen_height - dialog_height) // 2

        # FIXED: Set geometry immediately with center position
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

        # Ensure dialog is on top and visible BEFORE grab_set
        dialog.lift()
        dialog.attributes("-topmost", True)
        dialog.update_idletasks()  # Make sure dialog is rendered
        dialog.deiconify()  # Ensure it's visible

        # NOW set grab and focus after dialog is fully visible
        dialog.grab_set()
        dialog.focus_set()

        # Main container with border
        main_frame = tk.Frame(dialog, bg=palette['background_2'], relief=tk.RAISED, bd=3)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Title with icon (30% bigger)
        title_label = tk.Label(main_frame, text="💡 Hint",
                            font=('Arial', 23, 'bold'),  # 30% bigger: 18 -> 23
                            fg=palette['title_color'], bg=palette['background_2'])
        title_label.pack(pady=(15, 10))

        # Hint content frame
        content_frame = tk.Frame(main_frame, bg=palette['background_3'], relief=tk.SUNKEN, bd=2)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Hint text (30% bigger font and wraplength)
        hint_label = tk.Label(content_frame, text=hint,
                            font=('Arial', 18),  # 30% bigger: 14 -> 18
                            fg=palette['level_complete_info_label_text_color'],
                            bg=palette['background_3'],
                            wraplength=int(dialog_width * 0.85), justify=tk.CENTER)  # 30% bigger wrapping
        hint_label.pack(expand=True, pady=20)

        # Close button - canvas-based (30% bigger)
        close_canvas = self.create_canvas_dialog_button(
            main_frame, "Got it!",
            dialog.destroy,
            palette['return_to_gamemode_button_background'],
            palette['return_to_gamemode_button_text_color'],
            width=156, height=52, font_size=16  # 30% bigger: 120x40, font 12 -> 156x52, font 16
        )
        close_canvas.pack(pady=(10, 15))

        # Handle ESC key to close
        dialog.bind('<Escape>', lambda e: dialog.destroy())


    def skip_level(self):
        """Skip to next level"""
        # Create custom skip confirmation dialog without decorations
        dialog = tk.Toplevel(self.root)
        dialog.title("Skip Level")
        dialog.overrideredirect(True)  # Remove window decorations
        dialog.configure(bg=palette['background'])
        dialog.transient(self.root)

        # FIXED: Calculate center position BEFORE creating geometry (30% bigger)
        dialog_width = 850  # 30% bigger than 450
        dialog_height = 600  # 30% bigger than 250
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - dialog_width) // 2
        y = (screen_height - dialog_height) // 2

        # FIXED: Set geometry immediately with center position
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

        # Ensure dialog is on top and visible BEFORE grab_set
        dialog.lift()
        dialog.attributes("-topmost", True)
        dialog.update_idletasks()  # Make sure dialog is rendered
        dialog.deiconify()  # Ensure it's visible

        # NOW set grab and focus after dialog is fully visible
        dialog.grab_set()
        dialog.focus_set()

        result = [None]

        # Main container with border
        main_frame = tk.Frame(dialog, bg=palette['background_2'], relief=tk.RAISED, bd=3)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Reset Progress Button in its own frame - MOVED MUCH LOWER
        reset_frame = tk.Frame(main_frame, bg=palette['background_2'])
        reset_frame.pack(pady=(25, 15))  # INCREASED from 25 to 60 for more space

        tk.Label(reset_frame, text="", bg=palette['background_2']).pack()
        tk.Label(reset_frame, text="", bg=palette['background_2']).pack()
        tk.Label(reset_frame, text="", bg=palette['background_2']).pack()

        # FIXED: Centered title (30% bigger)
        title_label = tk.Label(main_frame, text="Skip Level",
                            font=('Arial', 35, 'bold'),  # 30% bigger: 16 -> 21
                            fg=palette['title_color'], bg=palette['background_2'])
        title_label.pack(pady=(30, 20))  # More top padding for centering

        # FIXED: Centered message (30% bigger font) with more space
        message_label = tk.Label(main_frame,
                            text="Are you sure you want to skip this level?\nYou won't earn points for skipping.",
                            font=('Arial', 18),  # Bigger font: 16 -> 18
                            fg=palette['subtitle_color'], bg=palette['background_2'],
                            justify=tk.CENTER)  # Ensure text is centered
        message_label.pack(pady=(40, 60))  # More padding for better centering

        # Button frame - centered
        button_frame = tk.Frame(main_frame, bg=palette['background_2'])
        button_frame.pack(pady=(20, 30))  # More bottom padding

        def confirm_skip():
            result[0] = True
            dialog.destroy()

        def cancel_skip():
            result[0] = False
            dialog.destroy()

        # Yes button - canvas-based (30% bigger)
        yes_canvas = self.create_canvas_dialog_button(
            button_frame, "Yes, Skip",
            confirm_skip,
            palette['return_to_gamemode_button_background'],
            palette['return_to_gamemode_button_text_color'],
            width=156, height=52, font_size=16  # 30% bigger: 120x40, font 12 -> 156x52, font 16
        )
        yes_canvas.pack(side=tk.LEFT, padx=20)  # More spacing

        # No button - canvas-based (30% bigger)
        no_canvas = self.create_canvas_dialog_button(
            button_frame, "No, Continue",
            cancel_skip,
            palette['close_gamemode_button_background'],
            palette['close_gamemode_button_hover_text_color'],
            width=182, height=52, font_size=16  # 30% bigger: 140x40, font 12 -> 182x52, font 16
        )
        no_canvas.pack(side=tk.LEFT, padx=20)  # More spacing

        # Handle ESC key to cancel
        dialog.bind('<Escape>', lambda e: cancel_skip())

        # Wait for dialog to close and get result
        dialog.wait_window()

        # Process result
        if result[0]:
            if self.current_level + 1 < len(self.levels):
                self.load_level(self.current_level + 1)
            else:
                self.game_complete()

        # Save the progress after skipping
        self.save_progress()


    def load_level(self, level_index):
        """Load a specific puzzle level"""
        if level_index >= len(self.levels):
            self.game_complete()
            return

        level = self.levels[level_index]
        self.current_level = level_index

        # Update level info UI
        self.level_label.config(text=f"Level: {level_index + 1}/{len(self.levels)}")
        self.level_name_label.config(text=level['name'])
        self.level_description_label.config(text=level['description'])
        self.difficulty_label.config(text=f"Difficulty: {level['difficulty']}")
        self.gates_limit_label.config(text=f"Max Gates: {level.get('max_gates', '∞')}")

        # Color code difficulty
        diff_colors = {
            'Beginner': palette['beginner_color'],
            'Intermediate': palette['intermediate_color'],
            'Advanced': palette['advanced_color'],
            'Expert': palette['expert_color'],
            'Master': palette['master_color']
        }
        self.difficulty_label.config(fg=diff_colors.get(level['difficulty'], palette['difficulty_label_color']))

        # Clear previous state
        self.placed_gates = []

        # Setup available gates for this level
        self.setup_gates(level['available_gates'])

        # Draw circuit
        self.draw_circuit()

        # Display initial state information
        self.display_states(level)


    def display_states(self, level):
        """Display level state information"""
        self.state_display.config(state=tk.NORMAL)
        self.state_display.delete(1.0, tk.END)

        self.state_display.insert(tk.END, f"Puzzle Goal\n")
        self.state_display.insert(tk.END, "─" * 30 + "\n\n")
        self.state_display.insert(tk.END, f"Transform: {level['input_state']} → {level['target_state']}\n\n")

        self.state_display.insert(tk.END, f"Level Details:\n")
        self.state_display.insert(tk.END, f"• Input State: {level['input_state']}\n")
        self.state_display.insert(tk.END, f"• Target State: {level['target_state']}\n")
        self.state_display.insert(tk.END, f"• Qubits: {level['qubits']}\n")
        self.state_display.insert(tk.END, f"• Max Gates: {level.get('max_gates', 'Unlimited')}\n")
        self.state_display.insert(tk.END, f"• Available Gates: {', '.join(level['available_gates'])}\n\n")

        self.state_display.insert(tk.END, "Ready to solve!\n")
        self.state_display.insert(tk.END, "Place gates and run your circuit to see the results.\n")

        self.state_display.config(state=tk.DISABLED)

        # Update status
        self.update_circuit_status()


    def update_circuit_status(self):
        """Update circuit status display"""
        level = self.levels[self.current_level]
        max_gates = level.get('max_gates', 999)

        self.gates_count_label.config(text=f"Gates: {len(self.placed_gates)}")
        self.gates_used_label.config(text=f"Used: {len(self.placed_gates)}/{max_gates}")


    def return_to_main_menu(self):
        """Return to main menu from button click"""
        self.play_sound('button_click')

        # Create custom confirmation dialog without decorations
        dialog = tk.Toplevel(self.root)
        dialog.title("Return to Main Menu")
        dialog.overrideredirect(True)  # Remove window decorations
        dialog.configure(bg=palette['background'])
        dialog.transient(self.root)

        # Make dialog 50% bigger than previous size
        dialog_width = 900  # 50% bigger
        dialog_height = 600  # 50% bigger
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - dialog_width) // 2
        y = (screen_height - dialog_height) // 2

        # Set geometry with calculated position immediately
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

        # Ensure dialog is on top and visible BEFORE grab_set
        dialog.lift()
        dialog.attributes("-topmost", True)
        dialog.update_idletasks()  # Make sure dialog is rendered
        dialog.deiconify()  # Ensure it's visible

        # NOW set grab and focus after dialog is fully visible
        dialog.grab_set()
        dialog.focus_set()

        result = [None]

        # Main container with border
        main_frame = tk.Frame(dialog, bg=palette['background_2'], relief=tk.RAISED, bd=3)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Title - bigger text for touch screens
        title_label = tk.Label(main_frame, text="Return to Main Menu",
                            font=('Arial', 20, 'bold'),  # Increased from 16
                            fg=palette['title_color'], bg=palette['background_2'])
        title_label.pack(pady=(20, 15))  # More padding

        # Message - bigger text and more padding
        message_label = tk.Label(main_frame,
                            text="Are you sure you want to return to the main menu?\nYour progress will be saved.",
                            font=('Arial', 16),  # Increased from 12
                            fg=palette['subtitle_color'], bg=palette['background_2'],
                            justify=tk.CENTER)
        message_label.pack(pady=20)  # More padding

        # Button frame
        button_frame = tk.Frame(main_frame, bg=palette['background_2'])
        button_frame.pack(pady=(20, 10))  # More top padding

        def confirm_return():
            result[0] = True
            dialog.destroy()

        def cancel_return():
            result[0] = False
            dialog.destroy()

        # Make buttons even bigger for the larger dialog
        yes_canvas = self.create_canvas_dialog_button(
            button_frame, "✓ Yes, Return",
            confirm_return,
            palette['return_to_gamemode_button_background'],
            palette['return_to_gamemode_button_text_color'],
            width=270, height=90, font_size=24  # 50% bigger buttons
        )
        yes_canvas.pack(side=tk.LEFT, padx=30)

        no_canvas = self.create_canvas_dialog_button(
            button_frame, "✗ No, Stay",
            cancel_return,
            palette['close_gamemode_button_background'],
            palette['close_gamemode_button_hover_text_color'],
            width=270, height=90, font_size=24  # 50% bigger buttons
        )
        no_canvas.pack(side=tk.LEFT, padx=30)

        # Reset Progress Button in its own frame - MOVED MUCH LOWER
        reset_frame = tk.Frame(main_frame, bg=palette['background_2'])
        reset_frame.pack(pady=(25, 15))  # INCREASED from 25 to 60 for more space

        # Add extra spacing with empty labels (like 3-4 "enters")
        tk.Label(reset_frame, text="", bg=palette['background_2']).pack()
        tk.Label(reset_frame, text="", bg=palette['background_2']).pack()
        tk.Label(reset_frame, text="", bg=palette['background_2']).pack()

        reset_label = tk.Label(reset_frame, text="Or reset your progress:",
                            font=('Arial', 14, 'italic'),  # Bigger text
                            fg=palette['subtitle_color'], bg=palette['background_2'])
        reset_label.pack(pady=(0, 10))  # More padding

        def reset_progress():
            if os.path.exists(self.SAVE_FILE):
                os.remove(self.SAVE_FILE)
            self.current_level = 0
            self.placed_gates = []
            self.score = 0
            self.save_progress()
            dialog.destroy()
            self.root.after(100, lambda: self.load_level(0))

        # Reset button - 50% bigger
        reset_canvas = self.create_canvas_dialog_button(
            reset_frame, "Reset Progress",
            reset_progress,
            palette['reset_button_background'],
            palette['reset_button_text_color'],
            width=330, height=90, font_size=24  # 50% bigger
        )
        reset_canvas.pack()

        # Handle ESC key to cancel
        dialog.bind('<Escape>', lambda e: cancel_return())

        # Wait for dialog to close and get result
        dialog.wait_window()

        # Process result
        if result[0]:
            # Save the progress before exiting
            self.save_progress()
            self.go_back_to_menu()


    def on_window_close(self):
        """Handle window close event (X button)"""
        # Save the progress before exiting
        self.save_progress()
        self.go_back_to_menu()


    def go_back_to_menu(self):
        """Navigate back to the game mode selection"""
        try:
            # Create main menu FIRST
            from game_mode_selection import GameModeSelection
            selection_window = GameModeSelection()

            # Make sure new window is visible
            selection_window.root.update()
            selection_window.root.lift()
            selection_window.root.focus_force()

            # Stop any pygame/sound processes before destroying
            if hasattr(self, 'sound_enabled') and self.sound_enabled:
                try:
                    pygame.mixer.quit()
                except:
                    pass

            # THEN destroy current window
            self.root.destroy()

            # Start the main menu mainloop
            selection_window.run()

        except ImportError:
            print("Could not return to main menu - game_mode_selection module not found")
            self.root.destroy()
        except Exception as e:
            print(f"Error returning to main menu: {e}")
            self.root.destroy()


    def draw_circuit(self):
        """Draw the quantum circuit visualization with enhanced graphics"""
        self.circuit_canvas.delete("all")

        level = self.levels[self.current_level]
        num_qubits = level['qubits']

        if num_qubits == 0:
            return

        # Enhanced circuit drawing parameters
        wire_start = 100
        wire_end = self.canvas_width - 60
        qubit_spacing = max(40, self.canvas_height // (num_qubits + 2))

        # Draw enhanced background grid
        for i in range(0, self.canvas_width, 50):
            self.circuit_canvas.create_line(i, 0, i, self.canvas_height,
                                          fill=palette['background'], width=1)

        # Draw enhanced qubit wires with colors
        wire_colors = [palette['quantum_wire_1'], palette['quantum_wire_2'], palette['quantum_wire_3'], palette['quantum_wire_4']]

        for qubit in range(num_qubits):
            y_pos = (qubit + 1) * qubit_spacing + 20
            color = wire_colors[qubit % len(wire_colors)]

            # Draw wire with gradient effect
            for thickness in [6, 4, 2]:
                self.circuit_canvas.create_line(wire_start, y_pos, wire_end, y_pos,
                                              fill=color, width=thickness)

            # Enhanced qubit label with background
            self.circuit_canvas.create_rectangle(wire_start - 35, y_pos - 12,
                                               wire_start - 5, y_pos + 12,
                                               fill=palette['background_3'], outline=color, width=2)

            self.circuit_canvas.create_text(wire_start - 20, y_pos,
                                          text=f"q{qubit}", fill='#ffffff',
                                          font=('Arial', 10, 'bold'))

        # Draw enhanced gates
        self.draw_enhanced_gates(wire_start, qubit_spacing, num_qubits)

        # Update status
        self.update_circuit_status()


    def draw_enhanced_gates(self, wire_start, qubit_spacing, num_qubits):
        """Draw gates with enhanced 3D styling"""
        gate_x_start = wire_start + 100
        gate_spacing = 100

        gate_colors = {
            'H': palette['H_color'], 'X': palette['X_color'], 'Y': palette['Y_color'], 'Z': palette['Z_color'],
            'S': palette['S_color'], 'T': palette['T_color'], 'CNOT': palette['CNOT_color'], 'CZ': palette['CZ_color'],
            'Toffoli': palette['Toffoli_color']
        }

        for i, gate_info in enumerate(self.placed_gates):
            x = gate_x_start + i * gate_spacing

            # Handle both old format (string) and new format (dict)
            if isinstance(gate_info, str):
                gate = gate_info
                qubits = [0]
            else:
                gate = gate_info['gate']
                qubits = gate_info['qubits']

            color = gate_colors.get(gate, '#ffffff')

            if gate in ['CNOT', 'CZ'] and len(qubits) >= 2:
                self.draw_two_qubit_gate_enhanced(x, qubit_spacing, gate, qubits, color)
            elif gate == 'Toffoli' and len(qubits) >= 3:
                self.draw_toffoli_gate_enhanced(x, qubit_spacing, qubits, color)
            else:
                self.draw_single_qubit_gate_enhanced(x, qubit_spacing, gate, qubits[0], color)


    def draw_single_qubit_gate_enhanced(self, x, qubit_spacing, gate, target_qubit, color):
        """Draw enhanced single qubit gate"""
        y_pos = (target_qubit + 1) * qubit_spacing + 20

        # 3D shadow effect
        self.circuit_canvas.create_rectangle(x - 22, y_pos - 17,
                                           x + 22, y_pos + 17,
                                           fill='#000000', outline='')

        # Main gate with gradient effect
        self.circuit_canvas.create_rectangle(x - 20, y_pos - 15,
                                           x + 20, y_pos + 15,
                                           fill=color, outline='#ffffff', width=2)

        # Inner highlight
        self.circuit_canvas.create_rectangle(x - 18, y_pos - 13,
                                           x + 18, y_pos + 13,
                                           fill='', outline='#ffffff', width=1)

        # Gate symbol
        self.circuit_canvas.create_text(x, y_pos, text=gate,
                                       fill=palette['gate_symbol_color'], font=('Arial', 12, 'bold'))


    def draw_two_qubit_gate_enhanced(self, x, qubit_spacing, gate, qubits, color):
        """Draw enhanced two-qubit gate"""
        control_qubit, target_qubit = qubits
        control_y = (control_qubit + 1) * qubit_spacing + 20
        target_y = (target_qubit + 1) * qubit_spacing + 20

        # Enhanced control dot
        self.circuit_canvas.create_oval(x - 10, control_y - 10,
                                       x + 10, control_y + 10,
                                       fill='#000000', outline='')
        self.circuit_canvas.create_oval(x - 8, control_y - 8,
                                       x + 8, control_y + 8,
                                       fill='#ffffff', outline='#cccccc', width=2)

        # Enhanced connection line
        self.circuit_canvas.create_line(x, control_y, x, target_y,
                                       fill='#ffffff', width=4)
        self.circuit_canvas.create_line(x, control_y, x, target_y,
                                       fill=color, width=2)

        if gate == 'CNOT':
            # Enhanced CNOT target
            self.circuit_canvas.create_oval(x - 17, target_y - 17,
                                           x + 17, target_y + 17,
                                           fill='#000000', outline='')
            self.circuit_canvas.create_oval(x - 15, target_y - 15,
                                           x + 15, target_y + 15,
                                           fill='', outline='#ffffff', width=3)

            # X symbol
            self.circuit_canvas.create_line(x - 8, target_y - 8,
                                           x + 8, target_y + 8,
                                           fill='#ffffff', width=3)
            self.circuit_canvas.create_line(x - 8, target_y + 8,
                                           x + 8, target_y - 8,
                                           fill='#ffffff', width=3)
        elif gate == 'CZ':
            # Enhanced CZ target
            self.circuit_canvas.create_oval(x - 10, target_y - 10,
                                           x + 10, target_y + 10,
                                           fill='#000000', outline='')
            self.circuit_canvas.create_oval(x - 8, target_y - 8,
                                           x + 8, target_y + 8,
                                           fill='#ffffff', outline='#cccccc', width=2)


    def draw_toffoli_gate_enhanced(self, x, qubit_spacing, qubits, color):
        """Draw enhanced Toffoli gate"""
        control1_qubit, control2_qubit, target_qubit = qubits

        y_positions = [
            (control1_qubit + 1) * qubit_spacing + 20,
            (control2_qubit + 1) * qubit_spacing + 20,
            (target_qubit + 1) * qubit_spacing + 20
        ]

        # Draw enhanced controls
        for i in range(2):
            self.circuit_canvas.create_oval(x - 10, y_positions[i] - 10,
                                           x + 10, y_positions[i] + 10,
                                           fill='#000000', outline='')
            self.circuit_canvas.create_oval(x - 8, y_positions[i] - 8,
                                           x + 8, y_positions[i] + 8,
                                           fill='#ffffff', outline='#cccccc', width=2)

        # Enhanced connection lines
        min_y = min(y_positions)
        max_y = max(y_positions)
        self.circuit_canvas.create_line(x, min_y, x, max_y,
                                       fill='#ffffff', width=4)
        self.circuit_canvas.create_line(x, min_y, x, max_y,
                                       fill=color, width=2)

        # Enhanced target (X symbol)
        target_y = y_positions[2]
        self.circuit_canvas.create_oval(x - 17, target_y - 17,
                                       x + 17, target_y + 17,
                                       fill='#000000', outline='')
        self.circuit_canvas.create_oval(x - 15, target_y - 15,
                                       x + 15, target_y + 15,
                                       fill='', outline='#ffffff', width=3)

        cross_size = 8
        self.circuit_canvas.create_line(x - cross_size, target_y - cross_size,
                                       x + cross_size, target_y + cross_size,
                                       fill='#ffffff', width=3)
        self.circuit_canvas.create_line(x - cross_size, target_y + cross_size,
                                       x + cross_size, target_y - cross_size,
                                       fill='#ffffff', width=3)
