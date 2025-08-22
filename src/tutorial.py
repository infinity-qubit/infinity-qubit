import tkinter as tk
from tkinter import ttk, messagebox
import json
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import Aer
from qiskit.quantum_info import Statevector
import math
from PIL import Image, ImageTk
import pygame
import os
import sys

sys.path.append('..')
from run import PROJECT_ROOT, get_resource_path

class TutorialWindow:
    def __init__(self, parent, return_callback=None):
        self.parent = parent
        self.return_callback = return_callback
        
        # Initialize sound system
        self.init_sound_system()
        
        # Create the window as a Toplevel but make it independent
        self.window = tk.Toplevel(parent)
        self.window.title("🎓 Quantum Gates Tutorial")
        self.window.geometry("1920x1080")
        self.window.configure(bg='#1a1a1a')
        self.window.resizable(False, False)
        
        # Make window independent and visible even if parent is withdrawn
        self.window.transient()  # Remove parent dependency
        self.window.grab_set()
        self.window.focus_set()
        
        # Handle window close event
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Center window on screen instead of parent
        self.center_window_on_screen()
        
        # Gate information
        self.gate_info = {
            'H': {
                'name': 'Hadamard Gate',
                'description': 'Creates superposition by transforming |0⟩ to |+⟩ and |1⟩ to |-⟩',
                'example': 'H|0⟩ = |+⟩ = (|0⟩ + |1⟩)/√2',
                'input_state': '|0⟩',
                'target_state': '|+⟩',
                'color': '#ff6b6b'
            },
            'S': {
                'name': 'S Gate (Phase)',
                'description': 'Applies a 90° phase shift to |1⟩ state',
                'example': 'S|1⟩ = i|1⟩',
                'input_state': '|1⟩',
                'target_state': 'i|1⟩',
                'color': '#74b9ff'
            },
            'T': {
                'name': 'T Gate (π/8)',
                'description': 'Applies a 45° phase shift to |1⟩ state',
                'example': 'T|1⟩ = e^(iπ/4)|1⟩',
                'input_state': '|1⟩',
                'target_state': 'e^(iπ/4)|1⟩',
                'color': '#a29bfe'
            },
            'CZ': {
                'name': 'Controlled-Z Gate',
                'description': 'Applies Z gate to target qubit if control qubit is |1⟩',
                'example': 'CZ|11⟩ = -|11⟩',
                'input_state': '|11⟩',
                'target_state': '-|11⟩',
                'color': '#fd79a8'
            },
            'X': {
                'name': 'Pauli-X Gate (NOT)',
                'description': 'Flips qubit state: |0⟩↔|1⟩',
                'example': 'X|0⟩ = |1⟩, X|1⟩ = |0⟩',
                'input_state': '|0⟩',
                'target_state': '|1⟩',
                'color': '#4ecdc4'
            },
            'Y': {
                'name': 'Pauli-Y Gate',
                'description': 'Combination of X and Z gates with phase',
                'example': 'Y|0⟩ = i|1⟩, Y|1⟩ = -i|0⟩',
                'input_state': '|0⟩',
                'target_state': 'i|1⟩',
                'color': '#55a3ff'
            },
            'Z': {
                'name': 'Pauli-Z Gate',
                'description': 'Applies phase flip to |1⟩ state',
                'example': 'Z|0⟩ = |0⟩, Z|1⟩ = -|1⟩',
                'input_state': '|1⟩',
                'target_state': '-|1⟩',
                'color': '#45b7d1'
            },
            'CNOT': {
                'name': 'Controlled-NOT Gate',
                'description': 'Flips target qubit if control qubit is |1⟩',
                'example': 'CNOT|10⟩ = |11⟩, CNOT|00⟩ = |00⟩',
                'input_state': '|10⟩',
                'target_state': '|11⟩',
                'color': '#ffeaa7'
            }
        }
        
        self.setup_ui()
        
        # Ensure window is visible and on top
        self.window.lift()
        self.window.focus_force()
        
        # Play welcome sound
        # self.play_sound('tutorial_open')
        self.play_sound('clear')

    def init_sound_system(self):
        """Initialize the sound system (same as puzzle_mode)"""
        try:
            # Initialize pygame mixer
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.sound_enabled = True
            self.load_sounds()
        except pygame.error:
            print("Warning: Could not initialize sound system")
            self.sound_enabled = False

    def load_sounds(self):
        """Load sound effects for the tutorial mode (same as puzzle_mode)"""
        try:
            # Define sound file paths
            sound_files = {
                'button_click': get_resource_path('resources/sounds/click.wav'),
                'gate_place': get_resource_path('resources/sounds/click.wav'),
                'success': get_resource_path('resources/sounds/success.wav'),
                'error': get_resource_path('resources/sounds/error.wav'),
                'clear': get_resource_path('resources/sounds/clear.wav'),
                'tutorial_open': get_resource_path('resources/sounds/clear.wav'),
                'gate_hover': None
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
        """Play a sound effect (same as puzzle_mode)"""
        if not self.sound_enabled:
            return
        
        try:
            if sound_name in self.sounds and self.sounds[sound_name] is not None:
                self.sounds[sound_name].play()
            else:
                print(f"⚠️ Sound '{sound_name}' not available")
        except Exception as e:
            print(f"Warning: Could not play sound {sound_name}: {e}")

    def center_window(self):
        """Center the window on the parent"""
        self.window.update_idletasks()
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        x = parent_x + (parent_width // 2) - 450
        y = parent_y + (parent_height // 2) - 350
        self.window.geometry(f"900x700+{x}+{y}")

    def center_window_on_screen(self):
        """Center the window on the screen"""
        self.window.update_idletasks()
        
        # Get screen dimensions
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # Get window dimensions
        window_width = 1100
        window_height = 800
        
        # Calculate position
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def setup_ui(self):
        """Setup the tutorial interface with enhanced layout matching sandbox"""
        # Main container with gradient-like effect
        main_frame = tk.Frame(self.window, bg='#0a0a0a')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Add subtle top border
        top_border = tk.Frame(main_frame, bg='#00ff88', height=3)
        top_border.pack(fill=tk.X)

        # Content frame
        content_frame = tk.Frame(main_frame, bg='#2a2a2a')
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Create header with navigation
        self.create_header(content_frame)

        # Main content container
        main_container = tk.Frame(content_frame, bg='#2a2a2a')
        main_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=(0, 25))

        # Explanation text box
        explanation_frame = tk.Frame(main_container, bg='#2a2a2a', relief=tk.RAISED, bd=2)
        explanation_frame.pack(fill=tk.X, pady=(0, 20))
        
        explanation_title = tk.Label(explanation_frame, text="📚 About Quantum Gates",
                                   font=('Arial', 14, 'bold'), fg='#00ff88', bg='#2a2a2a')
        explanation_title.pack(pady=(15, 10))
        
        explanation_text = tk.Text(explanation_frame, height=6, width=80,
                                  font=('Arial', 11), bg='#1a1a1a', fg='#ffffff',
                                  wrap=tk.WORD, relief=tk.FLAT, padx=15, pady=10)
        explanation_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Insert explanation text
        explanation = """Quantum gates are the fundamental building blocks of quantum circuits. Unlike classical logic gates that work with bits (0 or 1), quantum gates operate on qubits that can exist in superposition states. 

Each gate performs a specific transformation on quantum states:
• Single-qubit gates (H, X, Y, Z, S, T) operate on individual qubits
• Two-qubit gates (CNOT, CZ) create entanglement between qubits
• Gates are reversible and preserve quantum information

Click on any gate below to see an interactive demonstration of how it works!"""
        
        explanation_text.insert(tk.END, explanation)
        explanation_text.config(state=tk.DISABLED)
        
        # Gates section with enhanced styling
        gates_frame = tk.Frame(main_container, bg='#2a2a2a', relief=tk.RAISED, bd=2)
        gates_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        gates_title = tk.Label(gates_frame, text="🎨 Interactive Gate Tutorials",
                              font=('Arial', 16, 'bold'), fg='#00ff88', bg='#2a2a2a')
        gates_title.pack(pady=(15, 20))
        
        # Gates grid with better organization
        gates_container = tk.Frame(gates_frame, bg='#2a2a2a')
        gates_container.pack(expand=True)
        
        # Gate order: H S T CZ (top row), X Y Z CNOT (bottom row)
        gate_order = [
            ['H', 'S', 'T', 'CZ'],
            ['X', 'Y', 'Z', 'CNOT']
        ]
        
        for row_idx, row in enumerate(gate_order):
            row_frame = tk.Frame(gates_container, bg='#2a2a2a')
            row_frame.pack(pady=15)
            
            for col_idx, gate in enumerate(row):
                self.create_enhanced_gate_button(row_frame, gate)

    def create_header(self, parent):
        """Create header with navigation matching sandbox style"""
        header_frame = tk.Frame(parent, bg='#2a2a2a')
        header_frame.pack(fill=tk.X, padx=25, pady=(15, 10))

        # Navigation bar
        nav_frame = tk.Frame(header_frame, bg='#2a2a2a')
        nav_frame.pack(fill=tk.X)

        # Title on the left
        title_label = tk.Label(nav_frame, text="🎓 Quantum Gates Tutorial",
                            font=('Arial', 20, 'bold'),
                            fg='#00ff88', bg='#2a2a2a')
        title_label.pack(side=tk.LEFT)

        # Subtitle below title
        subtitle_label = tk.Label(nav_frame,
                                text="Learn quantum gates through interactive examples",
                                font=('Arial', 11, 'italic'),
                                fg='#4ecdc4', bg='#2a2a2a')
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0))

        # Navigation buttons on the right
        if self.return_callback:
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
                self.play_sound('gate_hover')
            def on_nav_leave(event):
                main_menu_btn.configure(bg='#3a3a3a', fg='#4ecdc4')

            main_menu_btn.bind("<Enter>", on_nav_enter)
            main_menu_btn.bind("<Leave>", on_nav_leave)
        else:
            close_btn = tk.Button(nav_frame, text="❌ Close Tutorial",
                                 command=self.window.destroy,
                                 font=('Arial', 10, 'bold'),
                                 bg='#3a3a3a', fg='#ff6b6b',
                                 padx=15, pady=8,
                                 cursor='hand2',
                                 relief=tk.FLAT,
                                 borderwidth=1)
            close_btn.pack(side=tk.RIGHT)

            # Add hover effect
            def on_close_enter(event):
                close_btn.configure(bg='#ff6b6b', fg='#ffffff')
                self.play_sound('gate_hover')
            def on_close_leave(event):
                close_btn.configure(bg='#3a3a3a', fg='#ff6b6b')

            close_btn.bind("<Enter>", on_close_enter)
            close_btn.bind("<Leave>", on_close_leave)
    
    def return_to_main_menu(self):
        """Return to main menu"""
        self.play_sound('button_click')
        if self.return_callback:
            self.window.destroy()
            self.return_callback()

    def on_closing(self):
        """Handle window close event"""
        self.play_sound('button_click')
        if self.return_callback:
            self.window.destroy()
            self.return_callback()
        else:
            self.window.destroy()

    def create_enhanced_gate_button(self, parent, gate):
        """Create enhanced gate button matching sandbox style"""
        gate_container = tk.Frame(parent, bg='#3a3a3a', relief=tk.RAISED, bd=2)
        gate_container.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Gate button with enhanced styling
        gate_info = self.gate_info[gate]
        btn = tk.Button(gate_container, text=gate,
                       command=lambda g=gate: self.open_gate_tutorial(g),
                       font=('Arial', 16, 'bold'), 
                       bg=gate_info['color'], fg='#000000',
                       width=6, height=3, relief=tk.FLAT, bd=0,
                       cursor='hand2',
                       activebackground='#ffffff', activeforeground='#000000')
        btn.pack(padx=8, pady=8)
        
        # Gate name label with better styling
        name_label = tk.Label(gate_container, text=gate_info['name'],
                             font=('Arial', 10, 'bold'), fg='#ffffff', bg='#3a3a3a')
        name_label.pack(pady=(0, 8))

        # Add hover effects
        original_bg = gate_info['color']
        
        def on_enter(event):
            btn.configure(bg='#ffffff', fg='#000000')
            self.play_sound('gate_hover')
        
        def on_leave(event):
            btn.configure(bg=original_bg, fg='#000000')
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

    def create_gate_button(self, parent, gate):
        """Create a clickable gate button"""
        gate_frame = tk.Frame(parent, bg='#1a1a1a')
        gate_frame.pack(side=tk.LEFT, padx=15, pady=10)
        
        # Gate button
        gate_info = self.gate_info[gate]
        btn = tk.Button(gate_frame, text=gate,
                       command=lambda g=gate: self.open_gate_tutorial(g),
                       font=('Arial', 18, 'bold'), 
                       bg=gate_info['color'], fg='#000000',
                       width=4, height=2, relief=tk.RAISED, bd=3)
        btn.pack()
        
        # Gate name label
        name_label = tk.Label(gate_frame, text=gate_info['name'],
                             font=('Arial', 10, 'bold'), fg='#ffffff', bg='#1a1a1a')
        name_label.pack(pady=(5, 0))
    
    def open_gate_tutorial(self, gate):
        """Open individual gate tutorial"""
        self.play_sound('button_click')
        GateTutorial(self.window, gate, self.gate_info[gate])


class GateTutorial:
    def __init__(self, parent, gate, gate_info):
        self.parent = parent
        self.gate = gate
        self.gate_info = gate_info
        self.placed_gates = []
        self.return_callback = None
        
        # Initialize sound system
        self.init_sound_system()
        
        # Get screen dimensions for adaptive sizing
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        
        self.window = tk.Toplevel(parent)
        self.window.title(f"🎓 {gate_info['name']} Tutorial")
        self.window.geometry(f"{window_width}x{window_height}")
        self.window.configure(bg='#1a1a1a')
        self.window.resizable(False, False)
        
        # Store dimensions
        self.window_width = window_width
        self.window_height = window_height
        
        # Make window modal
        self.window.transient(parent)
        self.window.grab_set()
        self.window.focus_set()
        
        self.center_window()
        self.setup_ui()
        
        # Play welcome sound
        # self.play_sound('tutorial_open')
        self.play_sound('clear')


    def init_sound_system(self):
        """Initialize the sound system (same as TutorialWindow)"""
        try:
            # Use parent's sound system if available
            if hasattr(self.parent, 'master') and hasattr(self.parent.master, 'sound_enabled'):
                self.sound_enabled = self.parent.master.sound_enabled
                self.sounds = getattr(self.parent.master, 'sounds', {})
                return
            
            # Initialize pygame mixer
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.sound_enabled = True
            self.load_sounds()
        except pygame.error:
            print("Warning: Could not initialize sound system")
            self.sound_enabled = False

    def load_sounds(self):
        """Load sound effects for the gate tutorial"""
        try:
            # Define sound file paths
            sound_files = {
                'button_click': get_resource_path('resources/sounds/click.wav'),
                'gate_place': get_resource_path('resources/sounds/click.wav'),
                'success': get_resource_path('resources/sounds/success.wav'),
                'error': get_resource_path('resources/sounds/error.wav'),
                'clear': get_resource_path('resources/sounds/clear.wav'),
                'tutorial_open': get_resource_path('resources/sounds/success.wav'),
                'circuit_run': get_resource_path('resources/sounds/success.wav')
            }
            
            # Load sounds into pygame
            self.sounds = {}
            for sound_name, file_path in sound_files.items():
                try:
                    self.sounds[sound_name] = pygame.mixer.Sound(file_path)
                except pygame.error as e:
                    print(f"⚠️ Could not load {sound_name} from {file_path}: {e}")
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
        except Exception as e:
            print(f"Warning: Could not play sound {sound_name}: {e}")
    
    def center_window(self):
        """Center the window on the screen"""
        self.window.update_idletasks()
        
        # Get screen dimensions
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # Calculate position
        x = (screen_width - self.window_width) // 2
        y = (screen_height - self.window_height) // 2
        
        self.window.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")
    
    def setup_ui(self):
        """Setup the gate tutorial interface with sandbox-style layout"""
        # Main container with gradient-like effect
        main_frame = tk.Frame(self.window, bg='#0a0a0a')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Add subtle top border
        top_border = tk.Frame(main_frame, bg='#00ff88', height=3)
        top_border.pack(fill=tk.X)

        # Content frame
        content_frame = tk.Frame(main_frame, bg='#2a2a2a')
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Create header
        self.create_header(content_frame)

        # Main content container
        main_container = tk.Frame(content_frame, bg='#2a2a2a')
        main_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=(0, 25))

        # Description section
        self.setup_description_section(main_container)

        # Circuit area
        self.setup_circuit_section(main_container)

        # Bottom section with controls and results
        self.setup_bottom_section(main_container)

    def create_header(self, parent):
        """Create header matching sandbox style"""
        header_frame = tk.Frame(parent, bg='#2a2a2a')
        header_frame.pack(fill=tk.X, padx=25, pady=(15, 10))

        # Navigation bar
        nav_frame = tk.Frame(header_frame, bg='#2a2a2a')
        nav_frame.pack(fill=tk.X)

        # Title on the left
        title_label = tk.Label(nav_frame, text=f"🎓 {self.gate_info['name']} Tutorial",
                            font=('Arial', 18, 'bold'),
                            fg='#00ff88', bg='#2a2a2a')
        title_label.pack(side=tk.LEFT)

        # Subtitle
        subtitle_label = tk.Label(nav_frame,
                                text="Interactive quantum gate exploration",
                                font=('Arial', 10, 'italic'),
                                fg='#4ecdc4', bg='#2a2a2a')
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0))

        # Close button on the right
        close_btn = tk.Button(nav_frame, text="❌ Close",
                             command=self.close_tutorial,
                             font=('Arial', 10, 'bold'),
                             bg='#3a3a3a', fg='#ff6b6b',
                             padx=15, pady=8,
                             cursor='hand2',
                             relief=tk.FLAT,
                             borderwidth=1)
        close_btn.pack(side=tk.RIGHT)

        # Add hover effect
        def on_close_enter(event):
            close_btn.configure(bg='#ff6b6b', fg='#ffffff')
        def on_close_leave(event):
            close_btn.configure(bg='#3a3a3a', fg='#ff6b6b')

        close_btn.bind("<Enter>", on_close_enter)
        close_btn.bind("<Leave>", on_close_leave)

    def close_tutorial(self):
        """Close the gate tutorial"""
        self.play_sound('button_click')
        self.window.destroy()

    def setup_description_section(self, parent):
        """Setup description section with enhanced styling"""
        desc_frame = tk.Frame(parent, bg='#2a2a2a', relief=tk.RAISED, bd=2)
        desc_frame.pack(fill=tk.X, pady=(0, 15))
        
        desc_title = tk.Label(desc_frame, text="📋 Gate Description",
                             font=('Arial', 14, 'bold'), fg='#00ff88', bg='#2a2a2a')
        desc_title.pack(pady=(15, 10))
        
        desc_label = tk.Label(desc_frame, text=self.gate_info['description'],
                             font=('Arial', 12), fg='#ffffff', bg='#2a2a2a',
                             wraplength=int(self.window_width * 0.8), justify=tk.CENTER)
        desc_label.pack(pady=(0, 8))
        
        example_label = tk.Label(desc_frame, text=f"Example: {self.gate_info['example']}",
                                font=('Arial', 11, 'italic'), fg=self.gate_info['color'], bg='#2a2a2a')
        example_label.pack(pady=(0, 12))

    def setup_circuit_section(self, parent):
        """Setup circuit visualization section"""
        circuit_frame = tk.Frame(parent, bg='#2a2a2a', relief=tk.RAISED, bd=2)
        circuit_frame.pack(fill=tk.X, pady=(0, 15))
        
        circuit_title = tk.Label(circuit_frame, text="🔧 Interactive Circuit Visualization",
                                font=('Arial', 14, 'bold'), fg='#00ff88', bg='#2a2a2a')
        circuit_title.pack(pady=(10, 8))
        
        # Canvas container with enhanced styling
        canvas_container = tk.Frame(circuit_frame, bg='#1a1a1a', relief=tk.SUNKEN, bd=3)
        canvas_container.pack(padx=20, pady=(0, 10))
        
        canvas_width = int(self.window_width * 0.85)
        canvas_height = int(self.window_height * 0.25)
        
        self.canvas = tk.Canvas(canvas_container, width=canvas_width, height=canvas_height,
                               bg='#0a0a0a', highlightthickness=0)
        self.canvas.pack(padx=5, pady=5)
        
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height

    def setup_bottom_section(self, parent):
        """Setup bottom section with controls and results side by side"""
        bottom_frame = tk.Frame(parent, bg='#2a2a2a')
        bottom_frame.pack(fill=tk.BOTH, expand=True)

        # Left side - Gate Controls (40% width)
        controls_frame = tk.Frame(bottom_frame, bg='#2a2a2a', relief=tk.RAISED, bd=2)
        controls_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.setup_gate_controls(controls_frame)

        # Right side - Results (60% width)
        results_frame = tk.Frame(bottom_frame, bg='#2a2a2a', relief=tk.RAISED, bd=2)
        results_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        self.setup_results_area(results_frame)

    def setup_gate_controls(self, parent):
        """Setup gate control buttons"""
        controls_title = tk.Label(parent, text="🎮 Gate Controls",
                                 font=('Arial', 14, 'bold'), fg='#00ff88', bg='#2a2a2a')
        controls_title.pack(pady=(15, 20))
        
        # Button container
        button_container = tk.Frame(parent, bg='#2a2a2a')
        button_container.pack(expand=True)
        
        # Gate placement button
        self.gate_btn = tk.Button(button_container, text=f"Add {self.gate} Gate",
                                 command=self.add_gate,
                                 font=('Arial', 12, 'bold'),
                                 bg=self.gate_info['color'], fg='#000000',
                                 padx=25, pady=12, cursor='hand2',
                                 relief=tk.RAISED, bd=2)
        self.gate_btn.pack(pady=10)
        
        # Control buttons
        controls_inner = tk.Frame(button_container, bg='#2a2a2a')
        controls_inner.pack(pady=20)
        
        run_btn = tk.Button(controls_inner, text="🚀 Run Circuit",
                           command=self.run_circuit,
                           font=('Arial', 11, 'bold'),
                           bg='#00ff88', fg='#000000',
                           padx=20, pady=8, cursor='hand2',
                           relief=tk.RAISED, bd=2)
        run_btn.pack(pady=5, fill=tk.X)
        
        clear_btn = tk.Button(controls_inner, text="🔄 Clear Circuit",
                             command=self.clear_circuit,
                             font=('Arial', 11, 'bold'),
                             bg='#ff6b6b', fg='#ffffff',
                             padx=20, pady=8, cursor='hand2',
                             relief=tk.RAISED, bd=2)
        clear_btn.pack(pady=5, fill=tk.X)

        # Add hover effects
        def create_hover_effect(button, original_bg, original_fg):
            def on_enter(event):
                button.configure(bg='#ffffff', fg='#000000')
            def on_leave(event):
                button.configure(bg=original_bg, fg=original_fg)
            return on_enter, on_leave

        # Apply hover effects
        for btn, orig_bg, orig_fg in [(self.gate_btn, self.gate_info['color'], '#000000'),
                                      (run_btn, '#00ff88', '#000000'),
                                      (clear_btn, '#ff6b6b', '#ffffff')]:
            on_enter, on_leave = create_hover_effect(btn, orig_bg, orig_fg)
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)

    def setup_results_area(self, parent):
        """Setup results display area"""
        results_title = tk.Label(parent, text="📊 Quantum State Analysis",
                                font=('Arial', 14, 'bold'), fg='#00ff88', bg='#2a2a2a')
        results_title.pack(pady=(15, 15))
        
        # Results container with styling
        results_container = tk.Frame(parent, bg='#1a1a1a', relief=tk.SUNKEN, bd=3)
        results_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Results text with scrollbar
        text_frame = tk.Frame(results_container, bg='#1a1a1a')
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.results_text = tk.Text(text_frame, font=('Consolas', 10),
                                   bg='#0a0a0a', fg='#00ff88',
                                   relief=tk.FLAT, bd=0, insertbackground='#00ff88',
                                   selectbackground='#4ecdc4', selectforeground='#000000',
                                   wrap=tk.WORD)
        
        # Add scrollbar
        scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.results_text.yview,
                                bg='#3a3a3a', troughcolor='#1a1a1a', activebackground='#4ecdc4')
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Initialize display
        self.draw_circuit()
        self.display_initial_info()
    
    def add_gate(self):
        """Add the tutorial gate to the circuit"""
        if len(self.placed_gates) < 5:  # Limit gates
            self.placed_gates.append(self.gate)
            self.draw_circuit()
            self.play_sound('gate_place')
    
    def clear_circuit(self):
        """Clear all gates"""
        self.placed_gates = []
        self.draw_circuit()
        self.display_initial_info()
        self.play_sound('clear')
    
    def draw_circuit(self):
        """Draw the quantum circuit with enhanced styling"""
        self.canvas.delete("all") 
        
        # Determine number of qubits based on gate
        num_qubits = 2 if self.gate in ['CNOT', 'CZ'] else 1
        
        # Circuit dimensions
        wire_start = 80
        wire_end = self.canvas_width - 80
        qubit_spacing = max(60, self.canvas_height // (num_qubits + 2))
        
        # Draw enhanced background grid
        for i in range(0, self.canvas_width, 40):
            self.canvas.create_line(i, 0, i, self.canvas_height,
                                  fill='#1a1a1a', width=1)
        
        # Draw quantum wires with colors
        wire_colors = ['#ff6b6b', '#4ecdc4', '#f39c12', '#a29bfe']
        
        for qubit in range(num_qubits):
            y_pos = (qubit + 1) * qubit_spacing
            color = wire_colors[qubit % len(wire_colors)]
            
            # Enhanced wire with gradient effect
            for thickness in [6, 4, 2]:
                self.canvas.create_line(wire_start, y_pos, wire_end, y_pos,
                                      fill=color, width=thickness)
            
            # Enhanced qubit label with background
            label_bg = self.canvas.create_rectangle(wire_start - 45, y_pos - 15,
                                                  wire_start - 5, y_pos + 15,
                                                  fill='#3a3a3a', outline=color, width=2)
            
            self.canvas.create_text(wire_start - 25, y_pos,
                                  text=f"q{qubit}", fill='#ffffff',
                                  font=('Arial', 12, 'bold'))
        
        # Draw enhanced gates
        self.draw_enhanced_gates(wire_start, qubit_spacing, num_qubits)

    def draw_enhanced_gates(self, wire_start, qubit_spacing, num_qubits):
        """Draw gates with enhanced 3D styling"""
        gate_x_start = wire_start + 120
        gate_spacing = 80
        
        for i, gate in enumerate(self.placed_gates):
            x = gate_x_start + i * gate_spacing
            color = self.gate_info['color']
            
            if gate in ['CNOT', 'CZ'] and num_qubits > 1:
                # Two-qubit gates
                control_y = qubit_spacing
                target_y = 2 * qubit_spacing
                
                if gate == 'CNOT':
                    # Enhanced control dot
                    self.canvas.create_oval(x - 10, control_y - 10, x + 10, control_y + 10,
                                           fill='#000000', outline='')
                    self.canvas.create_oval(x - 8, control_y - 8, x + 8, control_y + 8,
                                           fill='#ffffff', outline='#cccccc', width=2)
                    
                    # Enhanced connection line
                    self.canvas.create_line(x, control_y, x, target_y,
                                           fill='#ffffff', width=4)
                    self.canvas.create_line(x, control_y, x, target_y,
                                           fill=color, width=2)
                    
                    # Enhanced target
                    self.canvas.create_oval(x - 22, target_y - 22, x + 22, target_y + 22,
                                           fill='#000000', outline='')
                    self.canvas.create_oval(x - 20, target_y - 20, x + 20, target_y + 20,
                                           fill='', outline='#ffffff', width=3)
                    
                    # X symbol
                    self.canvas.create_line(x - 12, target_y - 12, x + 12, target_y + 12,
                                           fill='#ffffff', width=3)
                    self.canvas.create_line(x - 12, target_y + 12, x + 12, target_y - 12,
                                           fill='#ffffff', width=3)
                
                elif gate == 'CZ':
                    # Enhanced CZ gate visualization
                    self.canvas.create_oval(x - 10, control_y - 10, x + 10, control_y + 10,
                                           fill='#000000', outline='')
                    self.canvas.create_oval(x - 8, control_y - 8, x + 8, control_y + 8,
                                           fill='#ffffff', outline='#cccccc', width=2)
                    
                    self.canvas.create_line(x, control_y, x, target_y,
                                           fill='#ffffff', width=4)
                    self.canvas.create_line(x, control_y, x, target_y,
                                           fill=color, width=2)
                    
                    self.canvas.create_oval(x - 10, target_y - 10, x + 10, target_y + 10,
                                           fill='#000000', outline='')
                    self.canvas.create_oval(x - 8, target_y - 8, x + 8, target_y + 8,
                                           fill='#ffffff', outline='#cccccc', width=2)
            else:
                # Enhanced single qubit gates
                y_pos = qubit_spacing
                
                # 3D shadow effect
                self.canvas.create_rectangle(x - 27, y_pos - 22, x + 27, y_pos + 22,
                                            fill='#000000', outline='')
                
                # Main gate with gradient effect
                self.canvas.create_rectangle(x - 25, y_pos - 20, x + 25, y_pos + 20,
                                            fill=color, outline='#ffffff', width=2)
                
                # Inner highlight
                self.canvas.create_rectangle(x - 23, y_pos - 18, x + 23, y_pos + 18,
                                            fill='', outline='#ffffff', width=1)
                
                # Gate symbol with shadow
                self.canvas.create_text(x + 1, y_pos + 1, text=gate,
                                       fill='#000000', font=('Arial', 14, 'bold'))
                self.canvas.create_text(x, y_pos, text=gate,
                                       fill='#000000', font=('Arial', 16, 'bold'))
    
    def run_circuit(self):
        """Run the quantum circuit and show results"""
        if not self.placed_gates:
            self.results_text.configure(state=tk.NORMAL)
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "❌ No gates placed. Add some gates first!\n")
            self.results_text.configure(state=tk.DISABLED)
            self.play_sound('error')
            return
        
        try:
            # Update results display
            self.results_text.configure(state=tk.NORMAL)
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "🚀 Running quantum circuit...\n\n")
            self.results_text.update()
            
            # Determine circuit size
            num_qubits = 2 if self.gate in ['CNOT', 'CZ'] else 1
            qc = QuantumCircuit(num_qubits)
            
            # Set initial state based on gate
            if self.gate_info['input_state'] == '|1⟩':
                qc.x(0)
            elif self.gate_info['input_state'] == '|10⟩':
                qc.x(0)
            elif self.gate_info['input_state'] == '|11⟩':
                qc.x(0)
                qc.x(1)
            
            # Apply gates
            for gate in self.placed_gates:
                if gate == 'H':
                    qc.h(0)
                elif gate == 'X':
                    qc.x(0)
                elif gate == 'Y':
                    qc.y(0)
                elif gate == 'Z':
                    qc.z(0)
                elif gate == 'S':
                    qc.s(0)
                elif gate == 'T':
                    qc.t(0)
                elif gate == 'CNOT' and num_qubits > 1:
                    qc.cx(0, 1)
                elif gate == 'CZ' and num_qubits > 1:
                    qc.cz(0, 1)
            
            # Get final state
            final_state = Statevector(qc)
            
            # Display results
            self.display_results(final_state.data, num_qubits)
            self.play_sound('circuit_run')
            
        except Exception as e:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"❌ Error: {str(e)}\n")
            self.play_sound('error')
        finally:
            self.results_text.configure(state=tk.DISABLED)
    
    def display_results(self, state_vector, num_qubits):
        """Display the quantum state results with enhanced formatting"""
        self.results_text.delete(1.0, tk.END)
        
        self.results_text.insert(tk.END, f"✅ Circuit Executed Successfully!\n\n")
        self.results_text.insert(tk.END, f"📋 Circuit Summary:\n")
        self.results_text.insert(tk.END, f"Initial State: {self.gate_info['input_state']}\n")
        self.results_text.insert(tk.END, f"Gates Applied: {' → '.join(self.placed_gates)}\n")
        self.results_text.insert(tk.END, f"Total Gates: {len(self.placed_gates)}\n")
        self.results_text.insert(tk.END, "=" * 50 + "\n\n")
        
        self.results_text.insert(tk.END, f"📊 Final State Vector:\n")
        for i, amplitude in enumerate(state_vector):
            if abs(amplitude) > 0.001:
                basis_state = f"|{i:0{num_qubits}b}⟩"
                real_part = amplitude.real
                imag_part = amplitude.imag
                
                if abs(imag_part) < 0.001:
                    self.results_text.insert(tk.END, f"{basis_state}: {real_part:.4f}\n")
                else:
                    self.results_text.insert(tk.END, f"{basis_state}: {real_part:.4f} + {imag_part:.4f}i\n")
        
        self.results_text.insert(tk.END, f"\n🎯 Measurement Probabilities:\n")
        for i, amplitude in enumerate(state_vector):
            probability = abs(amplitude) ** 2
            if probability > 0.001:
                basis_state = f"|{i:0{num_qubits}b}⟩"
                self.results_text.insert(tk.END, f"{basis_state}: {probability:.3f} ({probability*100:.1f}%)\n")
        
        # Add educational insight
        self.results_text.insert(tk.END, f"\n💡 Educational Insight:\n")
        if self.gate == 'H':
            self.results_text.insert(tk.END, "The Hadamard gate creates superposition - the qubit is now in both |0⟩ and |1⟩ states simultaneously!\n")
        elif self.gate == 'X':
            self.results_text.insert(tk.END, "The X gate flipped the qubit state - it's the quantum equivalent of a NOT gate!\n")
        elif self.gate in ['CNOT', 'CZ']:
            self.results_text.insert(tk.END, "This two-qubit gate can create entanglement between qubits!\n")
        else:
            self.results_text.insert(tk.END, f"The {self.gate} gate applied a specific quantum transformation to the state!\n")
    
    def display_initial_info(self):
        """Display initial information with enhanced formatting"""
        self.results_text.configure(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        
        self.results_text.insert(tk.END, f"🎓 {self.gate_info['name']} Tutorial\n\n")
        self.results_text.insert(tk.END, f"📋 Description:\n{self.gate_info['description']}\n\n")
        self.results_text.insert(tk.END, f"📝 Mathematical Example:\n{self.gate_info['example']}\n\n")
        self.results_text.insert(tk.END, "=" * 50 + "\n\n")
        self.results_text.insert(tk.END, "🎮 Instructions:\n")
        self.results_text.insert(tk.END, "1. Click 'Add Gate' to place the gate on the circuit\n")
        self.results_text.insert(tk.END, "2. Click 'Run Circuit' to execute and see results\n")
        self.results_text.insert(tk.END, "3. Experiment with multiple gates to see cumulative effects\n")
        self.results_text.insert(tk.END, "4. Use 'Clear Circuit' to start over\n\n")
        self.results_text.insert(tk.END, "🌟 Ready to explore quantum mechanics!\n")
        
        self.results_text.configure(state=tk.DISABLED)

def show_tutorial(parent, return_callback=None):
    """Show the tutorial window"""
    TutorialWindow(parent, return_callback)