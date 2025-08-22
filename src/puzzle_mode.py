import tkinter as tk
from tkinter import ttk, messagebox
import json
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
import pygame
from PIL import Image, ImageTk
import sys

sys.path.append('..')
from run import PROJECT_ROOT, get_resource_path

class PuzzleMode:
    def __init__(self, root):
        self.root = root
        self.root.title("🧩 Infinity Qubit - Puzzle Mode")

        # Initialize pygame mixer for sound
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.sound_enabled = True
            self.load_sounds()
        except pygame.error:
            print("Warning: Could not initialize sound system")
            self.sound_enabled = False

        # Get screen dimensions and set adaptive window size (increased height)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        window_width = int(screen_width * 0.85)  # Slightly wider
        window_height = int(screen_height * 0.85)  # Increased from 0.75 to 0.85

        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.configure(bg='#1a1a1a')

        self.window_width = window_width
        self.window_height = window_height

        # Game state
        self.current_level = 0
        self.placed_gates = []
        self.score = 0
        self.levels = self.load_puzzle_levels()
        self.max_gates_used = {}  # Track efficiency

        # Initialize UI
        self.setup_ui()
        self.load_level(self.current_level)

    def load_puzzle_levels(self):
        """Load puzzle levels from JSON file"""
        try:
            with open('puzzle_levels_temp.json', 'r', encoding='utf-8') as f:
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

    # ...existing code... (load_sounds, play_sound, create_puzzle_levels methods remain the same)

    def load_sounds(self):
        """Load sound effects for the puzzle mode"""
        try:
            # Define sound file paths
            sound_files = {
                'button_click': get_resource_path('resources/sounds/click.wav'),
                'gate_place': get_resource_path('resources/sounds/click.wav'),
                'success': get_resource_path('resources/sounds/success.wav'),
                'error': get_resource_path('resources/sounds/error.wav'),
                'clear': get_resource_path('resources/sounds/clear.wav'),
                'level_complete': get_resource_path('resources/sounds/success.wav')
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
        """Setup the user interface with sandbox-style layout"""
        # Main container with gradient-like effect
        main_frame = tk.Frame(self.root, bg='#0a0a0a')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Add subtle top border
        top_border = tk.Frame(main_frame, bg='#ff6b6b', height=3)
        top_border.pack(fill=tk.X)

        # Content frame
        content_frame = tk.Frame(main_frame, bg='#2a2a2a')
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Create header
        self.create_header(content_frame)

        # Main content container
        main_container = tk.Frame(content_frame, bg='#2a2a2a')
        main_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=(0, 25))

        # Level info panel (replaces control panel)
        self.setup_level_info_panel(main_container)

        # Circuit display area
        self.setup_circuit_area(main_container)

        # Bottom section with gate palette, controls, and state analysis
        self.setup_bottom_section(main_container)

        # Set up window close protocol
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)

    def create_header(self, parent):
        """Create header with title and navigation"""
        header_frame = tk.Frame(parent, bg='#2a2a2a')
        header_frame.pack(fill=tk.X, padx=25, pady=(15, 10))

        nav_frame = tk.Frame(header_frame, bg='#2a2a2a')
        nav_frame.pack(fill=tk.X)

        # Title on the left
        title_label = tk.Label(nav_frame, text="🧩 Infinity Qubit - Puzzle Mode",
                            font=('Arial', 20, 'bold'),
                            fg='#ff6b6b', bg='#2a2a2a')
        title_label.pack(side=tk.LEFT)

        # Subtitle below title
        subtitle_label = tk.Label(nav_frame,
                                text="Solve quantum puzzles with increasing difficulty",
                                font=('Arial', 11, 'italic'),
                                fg='#4ecdc4', bg='#2a2a2a')
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0))

        # Back to Main Menu button - top right
        main_menu_btn = tk.Button(nav_frame, text="🏠 Main Menu",
                                command=self.return_to_main_menu,
                                font=('Arial', 10, 'bold'),
                                bg='#3a3a3a', fg='#4ecdc4',
                                padx=15, pady=8,
                                cursor='hand2',
                                relief=tk.FLAT,
                                borderwidth=1)
        main_menu_btn.pack(side=tk.RIGHT)

        # Add hover effect
        def on_nav_enter(event):
            main_menu_btn.configure(bg='#4ecdc4', fg='#000000')
        def on_nav_leave(event):
            main_menu_btn.configure(bg='#3a3a3a', fg='#4ecdc4')

        main_menu_btn.bind("<Enter>", on_nav_enter)
        main_menu_btn.bind("<Leave>", on_nav_leave)

    def setup_level_info_panel(self, parent):
        """Setup the level information panel (replaces control panel)"""
        info_frame = tk.Frame(parent, bg='#2a2a2a', relief=tk.RAISED, bd=2)
        info_frame.pack(fill=tk.X, pady=(0, 20))

        # Title
        info_title = tk.Label(info_frame, text="🎯 Level Information",
                            font=('Arial', 16, 'bold'), fg='#ff6b6b', bg='#2a2a2a')
        info_title.pack(pady=(15, 10))

        # Main info container
        info_container = tk.Frame(info_frame, bg='#2a2a2a')
        info_container.pack(padx=20, pady=(0, 15))

        # Level details - left side
        level_frame = tk.Frame(info_container, bg='#3a3a3a', relief=tk.RAISED, bd=1)
        level_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15), pady=5, ipadx=15, ipady=10)

        self.level_label = tk.Label(level_frame, text="Level: 1",
                                font=('Arial', 14, 'bold'), fg='#ffffff', bg='#3a3a3a')
        self.level_label.pack(pady=(0, 5))

        self.level_name_label = tk.Label(level_frame, text="Level Name",
                                    font=('Arial', 12, 'bold'), fg='#00ff88', bg='#3a3a3a')
        self.level_name_label.pack(pady=2)

        self.level_description_label = tk.Label(level_frame, text="Description",
                                            font=('Arial', 10), fg='#ffffff', bg='#3a3a3a',
                                            wraplength=200)
        self.level_description_label.pack(pady=2)

        # Difficulty and score - right side
        stats_frame = tk.Frame(info_container, bg='#3a3a3a', relief=tk.RAISED, bd=1)
        stats_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5, ipadx=15, ipady=10)

        self.difficulty_label = tk.Label(stats_frame, text="Difficulty: Beginner",
                                    font=('Arial', 12, 'bold'), fg='#4ecdc4', bg='#3a3a3a')
        self.difficulty_label.pack(pady=(0, 5))

        self.score_label = tk.Label(stats_frame, text="Score: 0",
                                font=('Arial', 12, 'bold'), fg='#ffd700', bg='#3a3a3a')
        self.score_label.pack(pady=2)

        self.gates_limit_label = tk.Label(stats_frame, text="Max Gates: 1",
                                        font=('Arial', 10), fg='#ffffff', bg='#3a3a3a')
        self.gates_limit_label.pack(pady=2)

    def setup_circuit_area(self, parent):
        """Setup the circuit visualization area"""
        circuit_frame = tk.Frame(parent, bg='#2a2a2a', relief=tk.RAISED, bd=2)
        circuit_frame.pack(fill=tk.X, pady=(0, 15))

        # Title
        circuit_title = tk.Label(circuit_frame, text="🔧 Quantum Circuit Designer",
                                font=('Arial', 14, 'bold'), fg='#ff6b6b', bg='#2a2a2a')
        circuit_title.pack(pady=(10, 8))

        # Circuit canvas
        canvas_container = tk.Frame(circuit_frame, bg='#1a1a1a', relief=tk.SUNKEN, bd=3)
        canvas_container.pack(padx=20, pady=(0, 10))

        canvas_width = int(self.window_width * 0.85)
        canvas_height = int(self.window_height * 0.25)

        self.circuit_canvas = tk.Canvas(canvas_container, width=canvas_width, height=canvas_height,
                                       bg='#0a0a0a', highlightthickness=0)
        self.circuit_canvas.pack(padx=5, pady=5)

        self.canvas_width = canvas_width
        self.canvas_height = canvas_height

    def setup_bottom_section(self, parent):
        """Setup the bottom section with gate palette, controls, and state analysis"""
        bottom_frame = tk.Frame(parent, bg='#2a2a2a')
        bottom_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Left side - Gate Palette (40% width)
        gate_frame = tk.Frame(bottom_frame, bg='#2a2a2a', relief=tk.RAISED, bd=2)
        gate_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        tk.Label(gate_frame, text="🎨 Available Gates",
                font=('Arial', 14, 'bold'), fg='#f39c12', bg='#2a2a2a').pack(pady=(10, 10))

        # Gate buttons container
        self.gates_container = tk.Frame(gate_frame, bg='#2a2a2a')
        self.gates_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Middle section - Puzzle Controls (30% width)
        controls_frame = tk.Frame(bottom_frame, bg='#2a2a2a', relief=tk.RAISED, bd=2)
        controls_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)

        self.setup_puzzle_controls(controls_frame)

        # Right side - Quantum State Analysis (30% width)
        results_frame = tk.Frame(bottom_frame, bg='#2a2a2a', relief=tk.RAISED, bd=2)
        results_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.setup_state_analysis(results_frame)

    def setup_puzzle_controls(self, parent):
        """Setup puzzle control buttons"""
        # Title
        control_title = tk.Label(parent, text="🎮 Puzzle Controls",
                               font=('Arial', 14, 'bold'), fg='#ff6b6b', bg='#2a2a2a')
        control_title.pack(pady=(10, 15))

        # Create buttons container
        control_frame = tk.Frame(parent, bg='#2a2a2a', width=250, height=400)
        control_frame.pack(pady=(0, 15), padx=15)
        control_frame.pack_propagate(False)

        # Control buttons
        buttons_data = [
            ("🚀 Run Circuit", self.run_circuit, '#00ff88', '#000000'),
            ("🔄 Clear Circuit", self.clear_circuit, '#ff6b6b', '#ffffff'),
            ("💡 Hint", self.show_hint, '#4ecdc4', '#000000'),
            ("⏭️ Skip Level", self.skip_level, '#f39c12', '#000000')
        ]

        for i, (text, command, bg_color, fg_color) in enumerate(buttons_data):
            btn_container = tk.Frame(control_frame, bg='#3a3a3a', relief=tk.RAISED, bd=2)
            btn_container.pack(fill=tk.X, pady=12, padx=5)

            btn = tk.Button(btn_container, text=text, command=command,
                           font=('Arial', 11, 'bold'), bg=bg_color, fg=fg_color,
                           padx=15, pady=12, cursor='hand2', relief=tk.FLAT, bd=0)
            btn.pack(padx=4, pady=4, fill=tk.X)

            # Add hover effects
            original_bg = bg_color
            def create_hover_functions(button, orig_color, orig_fg):
                def on_enter(event):
                    button.configure(bg='#ffffff', fg='#000000')
                def on_leave(event):
                    button.configure(bg=orig_color, fg=orig_fg)
                return on_enter, on_leave

            on_enter, on_leave = create_hover_functions(btn, original_bg, fg_color)
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)

        # Status info
        status_frame = tk.Frame(control_frame, bg='#3a3a3a', relief=tk.SUNKEN, bd=1)
        status_frame.pack(fill=tk.X, pady=(20, 0), padx=5)

        status_title = tk.Label(status_frame, text="📊 Circuit Status",
                               font=('Arial', 10, 'bold'), fg='#4ecdc4', bg='#3a3a3a')
        status_title.pack(pady=(5, 3))

        self.gates_count_label = tk.Label(status_frame, text="Gates: 0",
                                         font=('Arial', 9), fg='#ffffff', bg='#3a3a3a')
        self.gates_count_label.pack(pady=2)

        self.gates_used_label = tk.Label(status_frame, text="Used: 0/1",
                                        font=('Arial', 9), fg='#ffffff', bg='#3a3a3a')
        self.gates_used_label.pack(pady=(0, 5))

    def setup_state_analysis(self, parent):
        """Setup quantum state analysis area"""
        # Title
        analysis_title = tk.Label(parent, text="📊 Quantum State Analysis",
                                font=('Arial', 14, 'bold'), fg='#ff6b6b', bg='#2a2a2a')
        analysis_title.pack(pady=(10, 15))

        # Analysis container
        analysis_container = tk.Frame(parent, bg='#1a1a1a', relief=tk.SUNKEN, bd=3)
        analysis_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Text area with scrollbar
        text_frame = tk.Frame(analysis_container, bg='#1a1a1a')
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.state_display = tk.Text(text_frame, width=40,
                                   font=('Consolas', 9), bg='#0a0a0a', fg='#00ff88',
                                   relief=tk.FLAT, bd=0, insertbackground='#00ff88',
                                   selectbackground='#4ecdc4', selectforeground='#000000',
                                   wrap=tk.WORD)

        scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.state_display.yview,
                                bg='#3a3a3a', troughcolor='#1a1a1a', activebackground='#4ecdc4')
        self.state_display.configure(yscrollcommand=scrollbar.set)

        self.state_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_gates(self, available_gates):
        """Setup available gate buttons for current level"""
        # Clear existing gates
        for widget in self.gates_container.winfo_children():
            widget.destroy()

        gate_colors = {
            'H': '#ff6b6b', 'X': '#4ecdc4', 'Y': '#45b7d1', 'Z': '#96ceb4',
            'S': '#feca57', 'T': '#ff9ff3', 'CNOT': '#ffeaa7', 'CZ': '#a29bfe',
            'Toffoli': '#fd79a8'
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

        # Separate single and multi-qubit gates
        single_gates = [gate for gate in available_gates if gate in ['H', 'X', 'Y', 'Z', 'S', 'T']]
        multi_gates = [gate for gate in available_gates if gate in ['CNOT', 'CZ', 'Toffoli']]

        # Store gates for toggle functionality
        self.single_gates = single_gates
        self.multi_gates = multi_gates
        self.current_gate_view = 'single'  # Start with single-qubit gates

        # Create toggle button if both types of gates are available
        if single_gates and multi_gates:
            toggle_frame = tk.Frame(self.gates_container, bg='#2a2a2a')
            toggle_frame.pack(pady=(5, 15))

            self.toggle_btn = tk.Button(toggle_frame, text="🔄 Show Multi-Qubit Gates",
                                    command=self.toggle_gate_view,
                                    font=('Arial', 11, 'bold'),
                                    bg='#4ecdc4', fg='#000000',
                                    padx=20, pady=8,
                                    cursor='hand2', relief=tk.FLAT)
            self.toggle_btn.pack()

            # Add hover effect for toggle button
            def on_toggle_enter(event):
                self.toggle_btn.configure(bg='#ffffff', fg='#000000')
            def on_toggle_leave(event):
                self.toggle_btn.configure(bg='#4ecdc4', fg='#000000')

            self.toggle_btn.bind("<Enter>", on_toggle_enter)
            self.toggle_btn.bind("<Leave>", on_toggle_leave)

        # Create container for gate display
        self.gate_display_frame = tk.Frame(self.gates_container, bg='#2a2a2a')
        self.gate_display_frame.pack(fill=tk.BOTH, expand=True)

        # Show initial gate set
        self.display_current_gates()

    def display_current_gates(self):
        """Display the current set of gates (single or multi-qubit)"""
        # Clear existing gate display
        for widget in self.gate_display_frame.winfo_children():
            widget.destroy()

        gate_colors = {
            'H': '#ff6b6b', 'X': '#4ecdc4', 'Y': '#45b7d1', 'Z': '#96ceb4',
            'S': '#feca57', 'T': '#ff9ff3', 'CNOT': '#ffeaa7', 'CZ': '#a29bfe',
            'Toffoli': '#fd79a8'
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
                                font=('Arial', 12, 'bold'), fg='#ffffff', bg='#2a2a2a')
            single_title.pack(pady=(5, 10))

            # Create grid for single gates
            single_frame = tk.Frame(self.gate_display_frame, bg='#2a2a2a')
            single_frame.pack()

            cols = 3
            for i, gate in enumerate(self.single_gates):
                row = i // cols
                col = i % cols
                
                if col == 0:  # Create new row frame
                    row_frame = tk.Frame(single_frame, bg='#2a2a2a')
                    row_frame.pack(pady=5)

                color = gate_colors.get(gate, '#ffffff')
                description = gate_descriptions.get(gate, '')

                btn_container = tk.Frame(row_frame, bg='#3a3a3a', relief=tk.RAISED, bd=1)
                btn_container.pack(side=tk.LEFT, padx=8, pady=2)

                btn = tk.Button(btn_container, text=gate,
                            command=lambda g=gate: self.add_gate(g),
                            font=('Arial', 12, 'bold'),
                            bg=color, fg='#000000',
                            width=8, height=2, cursor='hand2',
                            relief=tk.FLAT, bd=0)
                btn.pack(padx=3, pady=3)

                desc_label = tk.Label(btn_container, text=description,
                                    font=('Arial', 8), fg='#cccccc', bg='#3a3a3a')
                desc_label.pack(pady=(0, 3))

                # Add hover effect
                def create_hover_effect(button, orig_color):
                    def on_enter(event):
                        button.configure(bg='#ffffff')
                    def on_leave(event):
                        button.configure(bg=orig_color)
                    return on_enter, on_leave

                on_enter, on_leave = create_hover_effect(btn, color)
                btn.bind("<Enter>", on_enter)
                btn.bind("<Leave>", on_leave)

        elif self.current_gate_view == 'multi' and self.multi_gates:
            # Display multi-qubit gates in grid layout (same as single gates)
            multi_title = tk.Label(self.gate_display_frame, text="Multi-Qubit Gates:",
                                font=('Arial', 12, 'bold'), fg='#ffffff', bg='#2a2a2a')
            multi_title.pack(pady=(5, 10))

            # Create grid for multi gates (same structure as single gates)
            multi_frame = tk.Frame(self.gate_display_frame, bg='#2a2a2a')
            multi_frame.pack()

            cols = 3  # Same number of columns as single gates
            for i, gate in enumerate(self.multi_gates):
                row = i // cols
                col = i % cols
                
                if col == 0:  # Create new row frame
                    row_frame = tk.Frame(multi_frame, bg='#2a2a2a')
                    row_frame.pack(pady=5)

                color = gate_colors.get(gate, '#ffffff')
                description = gate_descriptions.get(gate, '')

                btn_container = tk.Frame(row_frame, bg='#3a3a3a', relief=tk.RAISED, bd=1)
                btn_container.pack(side=tk.LEFT, padx=8, pady=2)

                btn = tk.Button(btn_container, text=gate,
                            command=lambda g=gate: self.add_gate(g),
                            font=('Arial', 12, 'bold'),
                            bg=color, fg='#000000',
                            width=8, height=2, cursor='hand2',  # Same size as single gates
                            relief=tk.FLAT, bd=0)
                btn.pack(padx=3, pady=3)

                desc_label = tk.Label(btn_container, text=description,
                                    font=('Arial', 8), fg='#cccccc', bg='#3a3a3a')
                desc_label.pack(pady=(0, 3))

                # Add hover effect
                def create_hover_effect_multi(button, orig_color):
                    def on_enter(event):
                        button.configure(bg='#ffffff')
                    def on_leave(event):
                        button.configure(bg=orig_color)
                    return on_enter, on_leave

                on_enter, on_leave = create_hover_effect_multi(btn, color)
                btn.bind("<Enter>", on_enter)
                btn.bind("<Leave>", on_leave)

        # If only one type of gates is available, show them without toggle
        elif not self.multi_gates and self.single_gates:
            # Only single gates available, show them directly
            self.current_gate_view = 'single'
            single_title = tk.Label(self.gate_display_frame, text="Available Gates:",
                                font=('Arial', 12, 'bold'), fg='#ffffff', bg='#2a2a2a')
            single_title.pack(pady=(5, 10))

            single_frame = tk.Frame(self.gate_display_frame, bg='#2a2a2a')
            single_frame.pack()

            cols = 3
            for i, gate in enumerate(self.single_gates):
                row = i // cols
                col = i % cols
                
                if col == 0:
                    row_frame = tk.Frame(single_frame, bg='#2a2a2a')
                    row_frame.pack(pady=5)

                color = gate_colors.get(gate, '#ffffff')
                description = gate_descriptions.get(gate, '')

                btn_container = tk.Frame(row_frame, bg='#3a3a3a', relief=tk.RAISED, bd=1)
                btn_container.pack(side=tk.LEFT, padx=8, pady=2)

                btn = tk.Button(btn_container, text=gate,
                            command=lambda g=gate: self.add_gate(g),
                            font=('Arial', 12, 'bold'),
                            bg=color, fg='#000000',
                            width=8, height=2, cursor='hand2',
                            relief=tk.FLAT, bd=0)
                btn.pack(padx=3, pady=3)

                desc_label = tk.Label(btn_container, text=description,
                                    font=('Arial', 8), fg='#cccccc', bg='#3a3a3a')
                desc_label.pack(pady=(0, 3))

        elif not self.single_gates and self.multi_gates:
            # Only multi gates available, show them directly in grid
            self.current_gate_view = 'multi'
            multi_title = tk.Label(self.gate_display_frame, text="Available Gates:",
                                font=('Arial', 12, 'bold'), fg='#ffffff', bg='#2a2a2a')
            multi_title.pack(pady=(5, 10))

            multi_frame = tk.Frame(self.gate_display_frame, bg='#2a2a2a')
            multi_frame.pack()

            cols = 3
            for i, gate in enumerate(self.multi_gates):
                row = i // cols
                col = i % cols
                
                if col == 0:
                    row_frame = tk.Frame(multi_frame, bg='#2a2a2a')
                    row_frame.pack(pady=5)

                color = gate_colors.get(gate, '#ffffff')
                description = gate_descriptions.get(gate, '')

                btn_container = tk.Frame(row_frame, bg='#3a3a3a', relief=tk.RAISED, bd=1)
                btn_container.pack(side=tk.LEFT, padx=8, pady=2)

                btn = tk.Button(btn_container, text=gate,
                            command=lambda g=gate: self.add_gate(g),
                            font=('Arial', 12, 'bold'),
                            bg=color, fg='#000000',
                            width=8, height=2, cursor='hand2',
                            relief=tk.FLAT, bd=0)
                btn.pack(padx=3, pady=3)

                desc_label = tk.Label(btn_container, text=description,
                                    font=('Arial', 9), fg='#cccccc', bg='#3a3a3a')
                desc_label.pack(pady=(0, 5))

    def toggle_gate_view(self):
        """Toggle between single-qubit and multi-qubit gate views"""
        if self.current_gate_view == 'single':
            self.current_gate_view = 'multi'
            self.toggle_btn.config(text="🔄 Show Single-Qubit Gates")
        else:
            self.current_gate_view = 'single'
            self.toggle_btn.config(text="🔄 Show Multi-Qubit Gates")
        
        self.display_current_gates()

    def add_gate(self, gate):
        """Add a gate to the circuit"""
        level = self.levels[self.current_level]
        max_gates = level.get('max_gates', 999)
        
        # Check gate limit
        if len(self.placed_gates) >= max_gates:
            self.play_sound('error')
            messagebox.showwarning("Gate Limit", f"Maximum {max_gates} gates allowed for this level!")
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
            messagebox.showerror("Error", f"{gate} gate requires at least 2 qubits!")
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
            messagebox.showerror("Error", "Toffoli gate requires at least 3 qubits!")
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

    def ask_qubit_selection(self, prompt, num_qubits, available_qubits=None):
        """Ask user to select a qubit"""
        if available_qubits is None:
            available_qubits = list(range(num_qubits))
        
        if len(available_qubits) == 1:
            return available_qubits[0]
        
        # Create a simple selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Qubit")
        dialog.geometry("300x150")
        dialog.configure(bg='#2a2a2a')
        dialog.transient(self.root)
        dialog.grab_set()
        
        result = [None]
        
        tk.Label(dialog, text=prompt, font=('Arial', 12), 
                fg='#ffffff', bg='#2a2a2a').pack(pady=10)
        
        button_frame = tk.Frame(dialog, bg='#2a2a2a')
        button_frame.pack(pady=10)
        
        def select_qubit(qubit):
            result[0] = qubit
            dialog.destroy()
        
        for qubit in available_qubits:
            btn = tk.Button(button_frame, text=f"Qubit {qubit}", 
                           command=lambda q=qubit: select_qubit(q),
                           font=('Arial', 10), bg='#4ecdc4', fg='#000000',
                           padx=15, pady=5, cursor='hand2')
            btn.pack(side=tk.LEFT, padx=5)
        
        # Cancel button
        cancel_btn = tk.Button(button_frame, text="Cancel", 
                              command=dialog.destroy,
                              font=('Arial', 10), bg='#ff6b6b', fg='#ffffff',
                              padx=15, pady=5, cursor='hand2')
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
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
            messagebox.showinfo("No Circuit", "Please add some gates to your circuit first!")
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
            messagebox.showerror("Circuit Error", f"Error running circuit: {str(e)}")

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
        
        self.state_display.insert(tk.END, "🔬 Circuit Results\n")
        self.state_display.insert(tk.END, "═" * 30 + "\n\n")
        
        # Display state vector
        self.state_display.insert(tk.END, "📊 Final Quantum State:\n")
        state_data = state_vector.data
        
        for i, amplitude in enumerate(state_data):
            if abs(amplitude) > 0.001:  # Only show significant amplitudes
                binary = format(i, f'0{level["qubits"]}b')
                prob = abs(amplitude) ** 2
                self.state_display.insert(tk.END, f"|{binary}⟩: {amplitude:.3f} (prob: {prob:.3f})\n")
        
        self.state_display.insert(tk.END, f"\n🎯 Target: {level['target_state']}\n")
        self.state_display.insert(tk.END, "❌ Puzzle not solved yet. Try adjusting your circuit!\n")
        
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

    def show_level_complete_dialog(self, level, level_score, max_gates):
        """Show a custom styled level complete dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("🎉 Level Complete!")
        dialog.geometry("600x500")  # Increased from 500x400 to 600x500
        dialog.configure(bg='#1a1a1a')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog in the middle of the screen
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - 600) // 2  # Updated for new width
        y = (screen_height - 500) // 2  # Updated for new height
        dialog.geometry(f"600x500+{x}+{y}")
        
        # Main container with border
        main_frame = tk.Frame(dialog, bg='#2a2a2a', relief=tk.RAISED, bd=3)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Header with celebration emoji
        header_frame = tk.Frame(main_frame, bg='#2a2a2a')
        header_frame.pack(fill=tk.X, pady=(20, 15))
        
        celebration_label = tk.Label(header_frame, text="🎉✨🏆✨🎉",
                                font=('Arial', 28), fg='#ffd700', bg='#2a2a2a')  # Increased font size
        celebration_label.pack()
        
        title_label = tk.Label(header_frame, text="LEVEL COMPLETE!",
                            font=('Arial', 24, 'bold'), fg='#00ff88', bg='#2a2a2a')  # Increased font size
        title_label.pack(pady=(10, 0))
        
        # Content frame
        content_frame = tk.Frame(main_frame, bg='#3a3a3a', relief=tk.SUNKEN, bd=2)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Level info
        info_text = f"""🎯 {level['name']}
        
    ⚡ Gates Used: {len(self.placed_gates)}/{max_gates}
    🏅 Level Score: +{level_score}
    💰 Total Score: {self.score}

    {self.get_performance_message(len(self.placed_gates), max_gates)}"""
        
        info_label = tk.Label(content_frame, text=info_text,
                            font=('Arial', 16), fg='#ffffff', bg='#3a3a3a',  # Increased font size
                            justify=tk.CENTER)
        info_label.pack(expand=True, pady=30)  # Increased padding
        
        # Button frame with more space
        button_frame = tk.Frame(main_frame, bg='#2a2a2a')
        button_frame.pack(fill=tk.X, pady=(20, 25))  # Increased padding
        
        # Button container for horizontal layout
        btn_container = tk.Frame(button_frame, bg='#2a2a2a')
        btn_container.pack()
        
        # Next Level button - larger size
        next_btn = tk.Button(btn_container, text="🚀 Next Level",
                        command=lambda: [dialog.destroy(), self.proceed_to_next_level()],
                        font=('Arial', 16, 'bold'),  # Increased font size
                        bg='#00ff88', fg='#000000',
                        padx=40, pady=15,  # Increased padding
                        cursor='hand2', relief=tk.FLAT)
        next_btn.pack(side=tk.LEFT, padx=20)  # Increased spacing
        
        # Close button - larger size
        close_btn = tk.Button(btn_container, text="❌ Close",
                            command=dialog.destroy,
                            font=('Arial', 16, 'bold'),  # Increased font size
                            bg='#ff6b6b', fg='#ffffff',
                            padx=40, pady=15,  # Increased padding
                            cursor='hand2', relief=tk.FLAT)
        close_btn.pack(side=tk.LEFT, padx=20)  # Increased spacing
        
        # Add hover effects
        def on_next_enter(event):
            next_btn.configure(bg='#ffffff', fg='#000000')
        def on_next_leave(event):
            next_btn.configure(bg='#00ff88', fg='#000000')
            
        def on_close_enter(event):
            close_btn.configure(bg='#ffffff', fg='#000000')
        def on_close_leave(event):
            close_btn.configure(bg='#ff6b6b', fg='#ffffff')
            
        next_btn.bind("<Enter>", on_next_enter)
        next_btn.bind("<Leave>", on_next_leave)
        close_btn.bind("<Enter>", on_close_enter)
        close_btn.bind("<Leave>", on_close_leave)
        
        # Hide next level button if this is the last level
        if self.current_level + 1 >= len(self.levels):
            next_btn.config(text="🏆 Game Complete!", state='disabled', bg='#888888')
            
        # Make dialog resizable in case user needs even more space
        dialog.resizable(True, True)
        dialog.minsize(800, 650)  # Set minimum size

    def proceed_to_next_level(self):
        """Proceed to the next level"""
        if self.current_level + 1 < len(self.levels):
            self.load_level(self.current_level + 1)
        else:
            self.game_complete()

    def get_performance_message(self, gates_used, max_gates):
        """Get a performance message based on gate efficiency"""
        if gates_used <= max_gates * 0.5:
            return "🌟 PERFECT! Outstanding efficiency!"
        elif gates_used <= max_gates * 0.75:
            return "⭐ EXCELLENT! Great optimization!"
        elif gates_used <= max_gates:
            return "✅ GOOD! You solved it!"
        else:
            return "💪 COMPLETED! Keep practicing!"

    def game_complete(self):
        """Handle game completion with styled dialog"""
        # Create custom styled dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("🏆 Game Complete!")
        dialog.geometry("450x350")
        dialog.configure(bg='#1a1a1a')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+{}+{}".format(
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 50
        ))
        
        # Main container with border
        main_frame = tk.Frame(dialog, bg='#2a2a2a', relief=tk.RAISED, bd=3)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header with celebration
        header_frame = tk.Frame(main_frame, bg='#2a2a2a')
        header_frame.pack(fill=tk.X, pady=(15, 10))
        
        celebration_label = tk.Label(header_frame, text="🏆🎊🌟🎊🏆",
                                   font=('Arial', 24), fg='#ffd700', bg='#2a2a2a')
        celebration_label.pack()
        
        title_label = tk.Label(header_frame, text="QUANTUM MASTER!",
                             font=('Arial', 20, 'bold'), fg='#ff6b6b', bg='#2a2a2a')
        title_label.pack(pady=(5, 0))
        
        # Content frame
        content_frame = tk.Frame(main_frame, bg='#3a3a3a', relief=tk.SUNKEN, bd=2)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Completion message
        completion_text = f"""🎉 CONGRATULATIONS! 🎉

You've mastered all quantum puzzle levels!

🏅 Final Score: {self.score}
🧩 Levels Completed: {len(self.levels)}
⚡ You're now a Quantum Circuit Master!

Thank you for playing Infinity Qubit! 💫"""
        
        completion_label = tk.Label(content_frame, text=completion_text,
                                  font=('Arial', 12), fg='#ffffff', bg='#3a3a3a',
                                  justify=tk.CENTER)
        completion_label.pack(expand=True, pady=20)
        
        # Button frame
        button_frame = tk.Frame(main_frame, bg='#2a2a2a')
        button_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Return to menu button
        menu_btn = tk.Button(button_frame, text="🏠 Return to Main Menu",
                           command=lambda: [dialog.destroy(), self.go_back_to_menu()],
                           font=('Arial', 12, 'bold'),
                           bg='#4ecdc4', fg='#000000',
                           padx=30, pady=10,
                           cursor='hand2', relief=tk.FLAT)
        menu_btn.pack(pady=10)
        
        # Add hover effect
        def on_enter(event):
            menu_btn.configure(bg='#ffffff', fg='#000000')
        def on_leave(event):
            menu_btn.configure(bg='#4ecdc4', fg='#000000')
            
        menu_btn.bind("<Enter>", on_enter)
        menu_btn.bind("<Leave>", on_leave)
    def show_hint(self):
        """Show hint for current level"""
        level = self.levels[self.current_level]
        hint = level.get('hint', 'No hint available for this level.')
        messagebox.showinfo("💡 Hint", hint)

    def skip_level(self):
        """Skip to next level"""
        result = messagebox.askyesno("Skip Level", 
                                   "Are you sure you want to skip this level?\n"
                                   "You won't earn points for skipping.")
        if result:
            if self.current_level + 1 < len(self.levels):
                self.load_level(self.current_level + 1)
            else:
                self.game_complete()

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
            'Beginner': '#4ecdc4',
            'Intermediate': '#f39c12', 
            'Advanced': '#e74c3c',
            'Expert': '#9b59b6',
            'Master': '#ff6b6b'
        }
        self.difficulty_label.config(fg=diff_colors.get(level['difficulty'], '#ffffff'))

        # Clear previous state
        self.placed_gates = []
        self.clear_circuit()

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
        
        self.state_display.insert(tk.END, f"🎯 Puzzle Goal\n")
        self.state_display.insert(tk.END, "─" * 30 + "\n\n")
        self.state_display.insert(tk.END, f"Transform: {level['input_state']} → {level['target_state']}\n\n")
        
        self.state_display.insert(tk.END, f"📝 Level Details:\n")
        self.state_display.insert(tk.END, f"• Input State: {level['input_state']}\n")
        self.state_display.insert(tk.END, f"• Target State: {level['target_state']}\n")
        self.state_display.insert(tk.END, f"• Qubits: {level['qubits']}\n")
        self.state_display.insert(tk.END, f"• Max Gates: {level.get('max_gates', 'Unlimited')}\n")
        self.state_display.insert(tk.END, f"• Available Gates: {', '.join(level['available_gates'])}\n\n")
        
        self.state_display.insert(tk.END, "💡 Ready to solve!\n")
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
        result = messagebox.askyesno("Return to Main Menu", 
                                "Are you sure you want to return to the main menu? Your progress will be lost.")
        if result:
            self.go_back_to_menu()

    def on_window_close(self):
        """Handle window close event (X button)"""
        self.go_back_to_menu()

    def go_back_to_menu(self):
        """Navigate back to the game mode selection"""
        self.root.destroy()
        try:
            from game_mode_selection import GameModeSelection
            GameModeSelection()
        except ImportError:
            print("Could not return to main menu - game_mode_selection module not found")
        except Exception as e:
            print(f"Error returning to main menu: {e}")

    # ...rest of the existing methods remain the same (add_gate, run_circuit, etc.)
    # Just need to update the draw_circuit method to match the enhanced style from sandbox

    def draw_circuit(self):
        """Draw the quantum circuit visualization with enhanced graphics"""
        self.circuit_canvas.delete("all")
        
        level = self.levels[self.current_level]
        num_qubits = level['qubits']
        
        if num_qubits == 0:
            return

        # Enhanced circuit drawing parameters
        wire_start = 60
        wire_end = self.canvas_width - 60
        qubit_spacing = max(40, self.canvas_height // (num_qubits + 2))

        # Draw enhanced background grid
        for i in range(0, self.canvas_width, 50):
            self.circuit_canvas.create_line(i, 0, i, self.canvas_height,
                                          fill='#1a1a1a', width=1)

        # Draw enhanced qubit wires with colors
        wire_colors = ['#ff6b6b', '#4ecdc4', '#f39c12', '#a29bfe']

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
                                               fill='#3a3a3a', outline=color, width=2)

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
            'H': '#ff6b6b', 'X': '#4ecdc4', 'Y': '#45b7d1', 'Z': '#96ceb4',
            'S': '#feca57', 'T': '#ff9ff3', 'CNOT': '#ffeaa7', 'CZ': '#a29bfe',
            'Toffoli': '#fd79a8'
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
                                       fill='#000000', font=('Arial', 12, 'bold'))

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

    # ...rest of existing methods remain the same...
    # (load_sounds, play_sound, create_puzzle_levels, add_gate methods, etc.)