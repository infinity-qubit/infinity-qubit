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
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")

import os
import sys
import json
import datetime

from q_utils import get_colors_from_file, extract_color_palette

sys.path.append('..')
from run import PROJECT_ROOT, get_resource_path

# Get color palette
color_file_path = get_resource_path('config/color_palette.json')
palette = extract_color_palette(get_colors_from_file(color_file_path), 'tutorial_mode')

class TutorialWindow:
    SAVE_FILE = os.path.expanduser("resources/saves/infinity_qubit_tutorial_save.json")

    def __init__(self, parent, return_callback=None):
        self.parent = parent
        self.return_callback = return_callback

        # Add progress tracking with default values
        self.user_progress = {
            'current_step': 0,  # 0=bit intro, 1=qubit intro, 2=gates
            'completed_gates': [],
            'unlocked_gates': ['H'],  # Start with only H gate unlocked
            'achievements': []
        }

        # Try to load saved progress
        try:
            if os.path.exists(self.SAVE_FILE):
                with open(self.SAVE_FILE, "r") as f:
                    saved_data = json.load(f)
                    self.user_progress['completed_gates'] = saved_data.get('completed_gates', [])
                    self.user_progress['unlocked_gates'] = saved_data.get('unlocked_gates', ['H'])
                    self.user_progress['current_step'] = saved_data.get('current_step', 0)
                print("✅ Tutorial progress loaded.")
        except Exception as e:
            print(f"❌ Could not load tutorial progress: {e}")

        # Gate unlock order
        self.gate_unlock_order = ['H', 'X', 'Y', 'Z', 'S', 'T', 'CNOT', 'CZ']

        # Initialize sound system
        self.init_sound_system()

        # Create independent window instead of Toplevel
        self.window = tk.Tk()
        self.window.title("🎓 Quantum Gates Tutorial")

        # Get screen dimensions for fullscreen
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()

        # Make window fullscreen without title bar (same as other game modes)
        self.window.overrideredirect(True)
        self.window.geometry(f"{screen_width}x{screen_height}+0+0")
        self.window.configure(bg=palette['background'])

        # Store dimensions
        self.window_width = screen_width
        self.window_height = screen_height

        # Make window visible and focused immediately
        self.window.lift()
        self.window.focus_force()

        # Handle window close event
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Handle ESC key to exit fullscreen
        self.window.bind('<Escape>', lambda e: self.on_closing())


        # Gate information
        self.gate_info = {
            'H': {
                'name': 'Hadamard Gate',
                'description': 'Creates superposition by transforming |0⟩ to |+⟩ and |1⟩ to |-⟩',
                'example': 'H|0⟩ = |+⟩ = (|0⟩ + |1⟩)/√2',
                'input_state': '|0⟩',
                'target_state': '|+⟩',
                'color': palette['H_color']
            },
            'S': {
                'name': 'S Gate (Phase)',
                'description': 'Applies a 90° phase shift to |1⟩ state',
                'example': 'S|1⟩ = i|1⟩',
                'input_state': '|1⟩',
                'target_state': 'i|1⟩',
                'color': palette['S_color']
            },
            'T': {
                'name': 'T Gate (π/8)',
                'description': 'Applies a 45° phase shift to |1⟩ state',
                'example': 'T|1⟩ = e^(iπ/4)|1⟩',
                'input_state': '|1⟩',
                'target_state': 'e^(iπ/4)|1⟩',
                'color': palette['T_color']
            },
            'CZ': {
                'name': 'Controlled-Z Gate',
                'description': 'Applies Z gate to target qubit if control qubit is |1⟩',
                'example': 'CZ|11⟩ = -|11⟩',
                'input_state': '|11⟩',
                'target_state': '-|11⟩',
                'color': palette['CZ_color']
            },
            'X': {
                'name': 'Pauli-X Gate (NOT)',
                'description': 'Flips qubit state: |0⟩↔|1⟩',
                'example': 'X|0⟩ = |1⟩, X|1⟩ = |0⟩',
                'input_state': '|0⟩',
                'target_state': '|1⟩',
                'color': palette['X_color']
            },
            'Y': {
                'name': 'Pauli-Y Gate',
                'description': 'Combination of X and Z gates with phase',
                'example': 'Y|0⟩ = i|1⟩, Y|1⟩ = -i|0⟩',
                'input_state': '|0⟩',
                'target_state': 'i|1⟩',
                'color': palette['Y_color']
            },
            'Z': {
                'name': 'Pauli-Z Gate',
                'description': 'Applies phase flip to |1⟩ state',
                'example': 'Z|0⟩ = |0⟩, Z|1⟩ = -|1⟩',
                'input_state': '|1⟩',
                'target_state': '-|1⟩',
                'color': palette['Z_color']
            },
            'CNOT': {
                'name': 'Controlled-NOT Gate',
                'description': 'Flips target qubit if control qubit is |1⟩',
                'example': 'CNOT|10⟩ = |11⟩, CNOT|00⟩ = |00⟩',
                'input_state': '|10⟩',
                'target_state': '|11⟩',
                'color': palette['CNOT_color']
            }
        }

        # Start with intro instead of main UI
        if self.user_progress['current_step'] < 2:
            self.show_intro_step()
        else:
            self.setup_ui()

        # Ensure window is visible and on top
        self.window.lift()
        self.window.focus_force()

        # Play welcome sound
        self.play_sound('clear')

    def save_progress(self):
        """Save tutorial progress to file."""
        try:
            # Ensure save directory exists
            save_dir = os.path.dirname(self.SAVE_FILE)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            data = {
                'completed_gates': self.user_progress['completed_gates'],
                'unlocked_gates': self.user_progress['unlocked_gates'],
                'current_step': self.user_progress['current_step'],
                'last_updated': datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            }
            with open(self.SAVE_FILE, "w") as f:
                json.dump(data, f)
            print("✅ Tutorial progress saved.")
        except Exception as e:
            print(f"❌ Could not save tutorial progress: {e}")

    def next_intro_step(self):
        """Move to next intro step"""
        self.play_sound('button_click')
        self.user_progress['current_step'] += 1
        self.save_progress()  # Save after step change
        self.show_intro_step()

    def prev_intro_step(self):
        """Move to previous intro step"""
        self.play_sound('button_click')
        self.user_progress['current_step'] -= 1
        self.save_progress()  # Save after step change
        self.show_intro_step()

    def start_gates_tutorial(self):
        """Start the gates tutorial"""
        self.play_sound('success')
        self.user_progress['current_step'] = 2
        self.save_progress()  # Save after starting gates
        self.setup_ui()

    def on_gate_completed(self, gate):
        """Handle gate completion"""
        if gate not in self.user_progress['completed_gates']:
            self.user_progress['completed_gates'].append(gate)
            self.unlock_next_gate()
            self.save_progress()  # Save after completing a gate

    def show_intro_step(self):
        """Show the current intro step"""
        if self.user_progress['current_step'] == 0:
            self.show_bit_explanation()
        elif self.user_progress['current_step'] == 1:
            self.show_qubit_explanation()

    def show_bit_explanation(self):
        """Step 1 - What's a bit?"""
        # Clear window
        for widget in self.window.winfo_children():
            widget.destroy()

        # Main container
        main_frame = tk.Frame(self.window, bg=palette['background'])
        main_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Title
        title = tk.Label(main_frame, text="Step 1 — What's a bit?",
                        font=('Arial', max(24, int(self.window_width / 60)), 'bold'),
                        fg=palette['main_title_color'], bg=palette['background'])
        title.place(relx=0.5, rely=0.1, anchor='center')

        # Explanation text
        explanation = """A bit is the smallest piece of information a computer understands.

It can only be 0 or 1 — like an on/off switch or a light bulb that's either off (0) or on (1).

When you watch a video, play a game, or open an app, your computer is just working with billions of these 0s and 1s."""

        text_label = tk.Label(main_frame, text=explanation,
                             font=('Arial', max(14, int(self.window_width / 100))),
                             fg=palette['explanation_text_color'], bg=palette['background'],
                             wraplength=int(self.window_width * 0.7), justify=tk.CENTER)
        text_label.place(relx=0.5, rely=0.35, anchor='center')

        # Visual demonstration area
        visual_frame = tk.Frame(main_frame, bg=palette['background_2'], relief=tk.RAISED, bd=2)
        visual_frame.place(relx=0.2, rely=0.55, relwidth=0.6, relheight=0.25)

        # Interactive bit demonstration
        self.create_bit_demo(visual_frame)

        # Analogy section
        analogy_text = """💡 Analogy: Imagine a coin lying flat on a table. If heads = 1 and tails = 0,
then the coin represents a bit — but it can only show one face at a time."""

        analogy_label = tk.Label(main_frame, text=analogy_text,
                                font=('Arial', max(12, int(self.window_width / 120)), 'italic'),
                                fg=palette['T_color'], bg=palette['background'],
                                wraplength=int(self.window_width * 0.8), justify=tk.CENTER)
        analogy_label.place(relx=0.5, rely=0.85, anchor='center')

        # Next button
        next_btn = tk.Button(main_frame, text="Next: What's a Qubit? →",
                           command=self.next_intro_step,
                           font=('Arial', max(12, int(self.window_width / 120)), 'bold'),
                           bg=palette['H_color'], fg=palette['background_3'],
                           padx=20, pady=10, cursor='hand2')
        next_btn.place(relx=0.5, rely=0.95, anchor='center')

    def create_bit_demo(self, parent):
        """Create interactive bit demonstration"""
        demo_title = tk.Label(parent, text="Interactive Bit Demo",
                             font=('Arial', max(14, int(self.window_width / 100)), 'bold'),
                             fg=palette['main_title_color'], bg=palette['background_2'])
        demo_title.place(relx=0.5, rely=0.1, anchor='center')

        # Bit state display
        self.bit_state = 0
        self.bit_display = tk.Label(parent, text="0",
                                   font=('Arial', 48, 'bold'),
                                   fg=palette['background_3'], bg=palette['X_color' if self.bit_state else 'H_color'],
                                   width=3, height=1, relief=tk.RAISED, bd=3)
        self.bit_display.place(relx=0.3, rely=0.5, anchor='center')

        # Flip button
        flip_btn = tk.Button(parent, text="Flip Bit",
                           command=self.flip_bit,
                           font=('Arial', max(12, int(self.window_width / 120)), 'bold'),
                           bg=palette['X_color'], fg=palette['background_3'],
                           cursor='hand2')
        flip_btn.place(relx=0.7, rely=0.5, anchor='center')

        # State label
        self.bit_label = tk.Label(parent, text="State: OFF",
                                 font=('Arial', max(10, int(self.window_width / 150))),
                                 fg=palette['explanation_text_color'], bg=palette['background_2'])
        self.bit_label.place(relx=0.5, rely=0.8, anchor='center')

    def flip_bit(self):
        """Flip the bit state"""
        self.bit_state = 1 - self.bit_state
        self.bit_display.configure(text=str(self.bit_state),
                                  bg=palette['X_color'] if self.bit_state else palette['H_color'])
        self.bit_label.configure(text=f"State: {'ON' if self.bit_state else 'OFF'}")
        self.play_sound('button_click')

    def show_qubit_explanation(self):
        """Step 2 - Enter the qubit"""
        # Clear window
        for widget in self.window.winfo_children():
            widget.destroy()

        # Main container
        main_frame = tk.Frame(self.window, bg=palette['background'])
        main_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Title
        title = tk.Label(main_frame, text="Step 2 — Enter the qubit",
                        font=('Arial', max(24, int(self.window_width / 60)), 'bold'),
                        fg=palette['main_title_color'], bg=palette['background'])
        title.place(relx=0.5, rely=0.08, anchor='center')

        # Explanation
        explanation = """Now comes the quantum bit, or qubit.
It's like a bit, but… it follows the rules of quantum physics, which are very different from the everyday world.

The magic property of a qubit is superposition:

Instead of being just 0 or just 1, a qubit can be in a combination of 0 and 1 at the same time."""

        text_label = tk.Label(main_frame, text=explanation,
                             font=('Arial', max(14, int(self.window_width / 100))),
                             fg=palette['explanation_text_color'], bg=palette['background'],
                             wraplength=int(self.window_width * 0.7), justify=tk.CENTER)
        text_label.place(relx=0.5, rely=0.3, anchor='center')

        # Spinning coin animation area
        animation_frame = tk.Frame(main_frame, bg=palette['background_2'], relief=tk.RAISED, bd=2)
        animation_frame.place(relx=0.2, rely=0.5, relwidth=0.6, relheight=0.25)

        self.create_spinning_coin_demo(animation_frame)

        # Analogy
        analogy_text = """💫 Analogy: Imagine our coin spinning in the air instead of lying flat.
While spinning, it's kind of both heads and tails until you catch it and look."""

        analogy_label = tk.Label(main_frame, text=analogy_text,
                                font=('Arial', max(12, int(self.window_width / 120)), 'italic'),
                                fg=palette['S_color'], bg=palette['background'],
                                wraplength=int(self.window_width * 0.8), justify=tk.CENTER)
        analogy_label.place(relx=0.5, rely=0.8, anchor='center')

        # Navigation buttons
        back_btn = tk.Button(main_frame, text="← Back",
                           command=self.prev_intro_step,
                           font=('Arial', max(12, int(self.window_width / 120)), 'bold'),
                           bg=palette['background_2'], fg=palette['explanation_text_color'],
                           padx=15, pady=8, cursor='hand2')
        back_btn.place(relx=0.3, rely=0.95, anchor='center')

        next_btn = tk.Button(main_frame, text="Start Learning Gates →",
                           command=self.start_gates_tutorial,
                           font=('Arial', max(12, int(self.window_width / 120)), 'bold'),
                           bg=palette['H_color'], fg=palette['background_3'],
                           padx=20, pady=10, cursor='hand2')
        next_btn.place(relx=0.7, rely=0.95, anchor='center')

    def create_spinning_coin_demo(self, parent):
        """Create spinning coin animation demonstration"""
        demo_title = tk.Label(parent, text="Interactive Qubit Demo",
                            font=('Arial', max(14, int(self.window_width / 100)), 'bold'),
                            fg=palette['main_title_color'], bg=palette['background_2'])
        demo_title.place(relx=0.5, rely=0.1, anchor='center')

        # Coin state display (spinning animation)
        self.coin_spinning = False
        self.coin_state = "H"  # H for heads, T for tails
        self.animation_id = None

        # Create canvas for coin animation
        self.coin_canvas = tk.Canvas(parent, width=150, height=150,
                                    bg=palette['background_2'], highlightthickness=0)
        self.coin_canvas.place(relx=0.3, rely=0.5, anchor='center')

        # Initial coin drawing
        self.draw_coin()

        # Control buttons
        spin_btn = tk.Button(parent, text="Spin Coin (Superposition)",
                            command=self.spin_coin,
                            font=('Arial', max(11, int(self.window_width / 130)), 'bold'),
                            bg=palette['H_color'], fg=palette['background_3'],
                            cursor='hand2')
        spin_btn.place(relx=0.7, rely=0.4, anchor='center')

        measure_btn = tk.Button(parent, text="Measure (Collapse)",
                            command=self.measure_coin,
                            font=('Arial', max(11, int(self.window_width / 130)), 'bold'),
                            bg=palette['X_color'], fg=palette['background_3'],
                            cursor='hand2')
        measure_btn.place(relx=0.7, rely=0.6, anchor='center')

        # State label
        self.coin_label = tk.Label(parent, text="State: Heads (|0⟩)",
                                font=('Arial', max(10, int(self.window_width / 150))),
                                fg=palette['explanation_text_color'], bg=palette['background_2'])
        self.coin_label.place(relx=0.5, rely=0.85, anchor='center')

    def draw_coin(self):
        """Draw the coin on canvas"""
        self.coin_canvas.delete("all")

        # Coin circle
        if self.coin_spinning:
            # Draw spinning coin (ellipse to show rotation)
            self.coin_canvas.create_oval(25, 50, 125, 100,
                                        fill=palette['S_color'], outline=palette['background_3'], width=3)
            self.coin_canvas.create_text(75, 75, text="?",
                                        font=('Arial', 24, 'bold'), fill=palette['background_3'])
        else:
            # Draw static coin
            color = palette['H_color'] if self.coin_state == "H" else palette['X_color']
            self.coin_canvas.create_oval(25, 25, 125, 125,
                                        fill=color, outline=palette['background_3'], width=3)
            self.coin_canvas.create_text(75, 75, text=self.coin_state,
                                        font=('Arial', 32, 'bold'), fill=palette['background_3'])

    def spin_coin(self):
        """Start spinning animation (superposition)"""
        if not self.coin_spinning:
            self.coin_spinning = True
            self.coin_label.configure(text="State: Superposition (|0⟩ + |1⟩)")
            self.animate_spin()
            self.play_sound('button_click')

    def measure_coin(self):
        """Stop spinning and collapse to definite state"""
        if self.coin_spinning:
            self.coin_spinning = False
            if self.animation_id:
                self.window.after_cancel(self.animation_id)

            # Random collapse to H or T
            import random
            self.coin_state = "H" if random.random() < 0.5 else "T"
            state_text = "Heads (|0⟩)" if self.coin_state == "H" else "Tails (|1⟩)"
            self.coin_label.configure(text=f"State: {state_text}")

            self.draw_coin()
            self.play_sound('success')

    def animate_spin(self):
        """Animate the spinning coin"""
        if self.coin_spinning:
            self.draw_coin()
            # Continue animation
            self.animation_id = self.window.after(200, self.animate_spin)

    def next_intro_step(self):
        """Move to next intro step"""
        self.play_sound('button_click')
        self.user_progress['current_step'] += 1
        self.show_intro_step()

    def prev_intro_step(self):
        """Move to previous intro step"""
        self.play_sound('button_click')
        self.user_progress['current_step'] -= 1
        self.show_intro_step()

    def start_gates_tutorial(self):
        """Start the gates tutorial"""
        self.play_sound('success')
        self.user_progress['current_step'] = 2
        self.setup_ui()

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


    def setup_ui(self):
        """Setup the tutorial interface with enhanced layout using relative positioning"""
        # Main container with gradient-like effect
        main_frame = tk.Frame(self.window, bg=palette['main_frame_background'])
        main_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Add subtle top border
        top_border = tk.Frame(main_frame, bg=palette['top_border_color'])
        top_border.place(relx=0, rely=0, relwidth=1, relheight=0.005)

        # Content frame
        content_frame = tk.Frame(main_frame, bg=palette['main_container_background'])
        content_frame.place(relx=0, rely=0.005, relwidth=1, relheight=0.995)

        # Create header with navigation
        self.create_header(content_frame)

        # Main content container - moved up and made larger since we removed explanation
        main_container = tk.Frame(content_frame, bg=palette['main_container_background'])
        main_container.place(relx=0.05, rely=0.15, relwidth=0.9, relheight=0.8)

        # Remove the explanation_frame section entirely
        # Gates section with enhanced styling - now takes full space
        gates_frame = tk.Frame(main_container, bg=palette['main_container_background'], relief=tk.RAISED, bd=2)
        gates_frame.place(relx=0, rely=0, relwidth=1, relheight=1)  # Changed to take full space

        gates_title = tk.Label(gates_frame, text="🎨 Interactive Gate Tutorials",
                            font=('Arial', max(16, int(self.window_width / 80)), 'bold'),
                            fg=palette['gates_title_color'], bg=palette['main_container_background'])
        gates_title.place(relx=0.5, rely=0.1, anchor='center')

        # Gates grid with better organization
        gates_container = tk.Frame(gates_frame, bg=palette['main_container_background'])
        gates_container.place(relx=0.1, rely=0.25, relwidth=0.8, relheight=0.65)

        # Gate order
        gate_order = [
            ['H', 'X', 'Y', 'Z'],      # First row: H → X → Y → Z
            ['S', 'T', 'CNOT', 'CZ']   # Second row: S → T → CNOT → CZ
        ]

        # Create gates using relative positioning in 2x4 grid
        for row_idx, row in enumerate(gate_order):
            for col_idx, gate in enumerate(row):
                relx = col_idx * 0.25 + 0.125  # Center each gate in its column
                rely = row_idx * 0.5 + 0.25    # Center each gate in its row
                self.create_enhanced_gate_button(gates_container, gate, relx, rely)


    def create_header(self, parent):
        """Create header with navigation using relative positioning"""
        header_frame = tk.Frame(parent, bg=palette['main_container_background'])
        header_frame.place(relx=0.05, rely=0.02, relwidth=0.9, relheight=0.12)

        # Title on the left
        title_label = tk.Label(header_frame, text="🎓 Quantum Gates Tutorial",
                            font=('Arial', max(20, int(self.window_width / 80)), 'bold'),
                            fg=palette['main_title_color'], bg=palette['main_container_background'])
        title_label.place(relx=0, rely=0.2, anchor='w')

        # Subtitle below title
        subtitle_label = tk.Label(header_frame,
                                text="Learn quantum gates through interactive examples",
                                font=('Arial', max(11, int(self.window_width / 140)), 'italic'),
                                fg=palette['main_subtitle_color'], bg=palette['main_container_background'])
        subtitle_label.place(relx=0, rely=0.7, anchor='w')

        # Navigation buttons on the right
        if self.return_callback:
            # Add Help/Info button - styled like Load Circuit dialog
            help_btn = tk.Button(header_frame, text="? Help",
                            command=self.show_help,
                            font=('Arial', max(10, int(self.window_width / 150)), 'bold'),
                            bg=palette['background_3'], fg=palette['main_title_color'],  # Dark bg, green text
                            padx=12, pady=6,
                            cursor='hand2',
                            relief=tk.RAISED,
                            bd=2)
            help_btn.place(relx=0.88, rely=0.5, anchor='e')  # Positioned closer to main menu

            main_menu_btn = tk.Button(header_frame, text="🏠 Main Menu",
                                    command=self.return_to_main_menu,
                                    font=('Arial', max(10, int(self.window_width / 150)), 'bold'),
                                    bg=palette['background_2'], fg=palette['main_menu_button_text_color'],
                                    padx=15, pady=8,
                                    cursor='hand2',
                                    relief=tk.FLAT,
                                    borderwidth=1)
            main_menu_btn.place(relx=1, rely=0.5, anchor='e')

            # Add hover effects for both buttons
            def on_help_enter(event):
                help_btn.configure(bg=palette['main_title_color'], fg=palette['background_3'])
                self.play_sound('gate_hover')
            def on_help_leave(event):
                help_btn.configure(bg=palette['background_3'], fg=palette['main_title_color'])

            def on_nav_enter(event):
                main_menu_btn.configure(bg=palette['main_menu_button_text_color'], fg=palette['background_3'])
                self.play_sound('gate_hover')
            def on_nav_leave(event):
                main_menu_btn.configure(bg=palette['background_2'], fg=palette['main_menu_button_text_color'])

            help_btn.bind("<Enter>", on_help_enter)
            help_btn.bind("<Leave>", on_help_leave)
            main_menu_btn.bind("<Enter>", on_nav_enter)
            main_menu_btn.bind("<Leave>", on_nav_leave)
        else:
            close_btn = tk.Button(header_frame, text="❌ Close Tutorial",
                                command=self.window.destroy,
                                font=('Arial', max(10, int(self.window_width / 150)), 'bold'),
                                bg=palette['background_2'], fg=palette['close_button_text_color'],
                                padx=15, pady=8,
                                cursor='hand2',
                                relief=tk.FLAT,
                                borderwidth=1)
            close_btn.place(relx=1, rely=0.5, anchor='e')

            # Add hover effect
            def on_close_enter(event):
                close_btn.configure(bg=palette['close_button_text_color'], fg=palette['close_button_hover_text_color'])
                self.play_sound('gate_hover')
            def on_close_leave(event):
                close_btn.configure(bg=palette['background_2'], fg=palette['close_button_text_color'])

            close_btn.bind("<Enter>", on_close_enter)
            close_btn.bind("<Leave>", on_close_leave)


    def show_help(self):
        """Show help information in a custom styled popup"""
        self.play_sound('button_click')

        # Create custom help window
        help_window = tk.Toplevel()
        help_window.title("Tutorial Help")
        help_window.configure(bg=palette['background'])
        help_window.transient(self.window)
        help_window.grab_set()

        # Make it fullscreen
        screen_width = help_window.winfo_screenwidth()
        screen_height = help_window.winfo_screenheight()
        help_window.overrideredirect(True)  # Remove window decorations for fullscreen
        help_window.geometry(f"{screen_width}x{screen_height}+0+0")

        # Make it always on top
        help_window.attributes('-topmost', True)
        help_window.update_idletasks()

        # Main container with border
        main_frame = tk.Frame(help_window, bg=palette['main_container_background'], relief=tk.RAISED, bd=3)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Header section with back button
        header_frame = tk.Frame(main_frame, bg=palette['background_3'], height=80)
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        header_frame.pack_propagate(False)

        # Back button in top-left corner of header
        back_btn = tk.Button(header_frame, text="← Back",
                            command=help_window.destroy,
                            font=('Arial', 12, 'bold'),
                            bg=palette['background_2'], fg=palette['main_title_color'],
                            padx=20, pady=8, cursor='hand2',
                            relief=tk.RAISED, bd=2)
        back_btn.place(relx=0.02, rely=0.5, anchor='w')

        # Title with icon (centered)
        title_label = tk.Label(header_frame, text="🎓 Quantum Gates Tutorial Help",
                            font=('Arial', 24, 'bold'),
                            fg=palette['main_title_color'], bg=palette['background_3'])
        title_label.place(relx=0.5, rely=0.5, anchor='center')

        # Content area with scrollbar
        content_frame = tk.Frame(main_frame, bg=palette['main_container_background'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create scrollable text area
        canvas = tk.Canvas(content_frame, bg=palette['main_frame_background'], highlightthickness=0)
        scrollbar = tk.Scrollbar(content_frame, orient="vertical", command=canvas.yview,
                                bg=palette['background_2'], troughcolor=palette['background'],
                                activebackground=palette['scrollbar_active_background'])
        scrollable_frame = tk.Frame(canvas, bg=palette['main_frame_background'])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Help content sections
        help_sections = [
            {
                'title': '📚 What are Quantum Gates?',
                'content': 'Quantum gates are the fundamental building blocks of quantum circuits. Unlike classical logic gates that work with bits (0 or 1), quantum gates operate on qubits that can exist in superposition states.',
                'color': palette['main_title_color']
            },
            {
                'title': '🎮 How to Use:',
                'content': '• Click on unlocked gates to open interactive tutorials\n• Complete gates in order: H → X → Y → Z → S → T → CNOT → CZ\n• Each gate tutorial includes circuit building and results\n• Experiment with multiple gates to see cumulative effects',
                'color': palette['H_color']
            },
            {
                'title': '🔒 Gate Unlocking:',
                'content': 'Gates unlock progressively as you complete previous ones. Start with the Hadamard (H) gate to begin your quantum journey!',
                'color': palette['X_color']
            },
            {
                'title': '🌟 Tips:',
                'content': '• Take your time to understand each gate\'s effect\n• Try different combinations in the circuit builder\n• Read the mathematical examples for deeper understanding\n• Run circuits multiple times to see consistent results',
                'color': palette['Y_color']
            },
            {
                'title': '⚡ Quick Reference:',
                'content': 'H Gate: Creates superposition\nX Gate: Flips qubit (NOT gate)\nY Gate: Complex rotation with phase\nZ Gate: Phase flip\nS Gate: 90° phase shift\nT Gate: 45° phase shift\nCNOT: Controlled NOT (entanglement)\nCZ: Controlled Z (entanglement)',
                'color': palette['Z_color']
            }
        ]

        # Add sections to scrollable frame
        for i, section in enumerate(help_sections):
            # Section container with styling - remove left/right padding to span full width
            section_frame = tk.Frame(scrollable_frame, bg=palette['background_2'], relief=tk.RAISED, bd=2)
            section_frame.pack(fill=tk.X, padx=0, pady=12)  # Changed padx from 15 to 0

            # Section header - full width colored line
            header_bg = tk.Frame(section_frame, bg=section['color'], height=8)  # Made slightly thicker
            header_bg.pack(fill=tk.X, padx=0, pady=0)  # No padding to span full width

            # Title
            title_frame = tk.Frame(section_frame, bg=palette['background_2'])
            title_frame.pack(fill=tk.X, padx=20, pady=(15, 8))

            title_label = tk.Label(title_frame, text=section['title'],
                                font=('Arial', 16, 'bold'),
                                fg=section['color'], bg=palette['background_2'],
                                anchor='w')
            title_label.pack(fill=tk.X)

            # Content
            content_frame_inner = tk.Frame(section_frame, bg=palette['background_2'])
            content_frame_inner.pack(fill=tk.X, padx=20, pady=(0, 20))

            content_label = tk.Label(content_frame_inner, text=section['content'],
                                    font=('Arial', 13),
                                    fg=palette['explanation_text_color'], bg=palette['background_2'],
                                    anchor='w', justify=tk.LEFT, wraplength=screen_width-100)
            content_label.pack(fill=tk.X)

        # Button frame
        button_frame = tk.Frame(main_frame, bg=palette['main_container_background'], height=80)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        button_frame.pack_propagate(False)

        # Close button with styling
        close_btn = tk.Button(button_frame, text="Close Help 🚀",
                            command=help_window.destroy,
                            font=('Arial', 14, 'bold'),
                            bg=palette['H_color'], fg=palette['background_3'],
                            padx=40, pady=15, cursor='hand2',
                            relief=tk.RAISED, bd=3)
        close_btn.pack(pady=20)

        # Button hover effects for both buttons
        def on_back_enter(event):
            back_btn.configure(bg=palette['main_title_color'], fg=palette['background_3'])
        def on_back_leave(event):
            back_btn.configure(bg=palette['background_2'], fg=palette['main_title_color'])

        def on_close_enter(event):
            close_btn.configure(bg=palette['main_title_color'], fg=palette['background_3'])
        def on_close_leave(event):
            close_btn.configure(bg=palette['H_color'], fg=palette['background_3'])

        back_btn.bind("<Enter>", on_back_enter)
        back_btn.bind("<Leave>", on_back_leave)
        close_btn.bind("<Enter>", on_close_enter)
        close_btn.bind("<Leave>", on_close_leave)

        # Handle window close and ESC key
        def close_help():
            help_window.destroy()

        help_window.protocol("WM_DELETE_WINDOW", close_help)
        help_window.bind('<Escape>', lambda e: close_help())

        # Bind mouse wheel to canvas for scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        # Bind mousewheel events
        def bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")

        canvas.bind('<Enter>', bind_mousewheel)
        canvas.bind('<Leave>', unbind_mousewheel)

        # Focus and show
        help_window.focus_force()
        help_window.lift()


    def return_to_main_menu(self):
        """Return to main menu"""
        self.play_sound('button_click')
        if self.return_callback:
            try:
                # Create main menu FIRST
                from game_mode_selection import GameModeSelection
                selection_window = GameModeSelection()

                # Make sure new window is visible
                selection_window.root.update()
                selection_window.root.lift()
                selection_window.root.focus_force()

                # THEN destroy current window
                self.window.destroy()

                # Start the main menu mainloop
                selection_window.run()

            except ImportError as e:
                print(f"Error importing game mode selection: {e}")
                self.window.destroy()
            except Exception as e:
                print(f"Error returning to main menu: {e}")
                self.window.destroy()
        else:
            self.window.destroy()


    def on_closing(self):
        """Handle window close event"""
        self.play_sound('button_click')
        if self.return_callback:
            try:
                # Create main menu FIRST
                from game_mode_selection import GameModeSelection
                selection_window = GameModeSelection()

                # Make sure new window is visible
                selection_window.root.update()
                selection_window.root.lift()
                selection_window.root.focus_force()

                # THEN destroy current window
                self.window.destroy()

                # Start the main menu mainloop
                selection_window.run()

            except ImportError as e:
                print(f"Error importing game mode selection: {e}")
                self.window.destroy()
            except Exception as e:
                print(f"Error returning to main menu: {e}")
                self.window.destroy()
        else:
            self.window.destroy()

    def create_enhanced_gate_button(self, parent, gate, relx, rely):
        """Create enhanced gate button - only if unlocked"""
        if gate not in self.user_progress['unlocked_gates']:
            # Show locked gate
            gate_container = tk.Frame(parent, bg=palette['background'], relief=tk.RAISED, bd=2)
            gate_container.place(relx=relx, rely=rely, anchor='center', relwidth=0.15, relheight=0.45)

            locked_btn = tk.Label(gate_container, text="🔒",
                                 font=('Arial', max(16, int(self.window_width / 100))),
                                 bg=palette['background'], fg=palette['explanation_text_color'])
            locked_btn.place(relx=0.5, rely=0.35, anchor='center')

            locked_label = tk.Label(gate_container, text="Complete previous gate",
                                   font=('Arial', max(6, int(self.window_width / 220))),
                                   fg=palette['explanation_text_color'], bg=palette['background'])
            locked_label.place(relx=0.5, rely=0.8, anchor='center')
            return

        gate_container = tk.Frame(parent, bg=palette['background_2'], relief=tk.RAISED, bd=2)
        gate_container.place(relx=relx, rely=rely, anchor='center', relwidth=0.15, relheight=0.45)

        # Gate button with enhanced styling
        gate_info = self.gate_info[gate]
        btn = tk.Button(gate_container, text=gate,
                       command=lambda g=gate: self.open_gate_tutorial_with_progress(g),
                       font=('Arial', max(16, int(self.window_width / 100)), 'bold'),
                       bg=gate_info['color'], fg=palette['background_3'],
                       relief=tk.FLAT, bd=0,
                       cursor='hand2',
                       activebackground=palette['gate_button_active_background'], activeforeground=palette['background_3'])
        btn.place(relx=0.5, rely=0.35, anchor='center', relwidth=0.85, relheight=0.6)

        # Gate name label with better styling
        name_label = tk.Label(gate_container, text=gate_info['name'],
                             font=('Arial', max(8, int(self.window_width / 180)), 'bold'),
                             fg=palette['gate_name_label_color'], bg=palette['background_2'])
        name_label.place(relx=0.5, rely=0.8, anchor='center')

        # Add hover effects
        original_bg = gate_info['color']

        def on_enter(event):
            btn.configure(bg=palette['gate_button_active_background'], fg=palette['background_3'])
            self.play_sound('gate_hover')

        def on_leave(event):
            btn.configure(bg=original_bg, fg=palette['background_3'])

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

    def open_gate_tutorial_with_progress(self, gate):
        """Open gate tutorial with progress tracking"""
        self.play_sound('button_click')
        tutorial = GateTutorial(self.window, gate, self.gate_info[gate],
                            completion_callback=lambda: self.on_gate_completed(gate))

    def on_gate_completed(self, gate):
        """Handle gate completion"""
        if gate not in self.user_progress['completed_gates']:
            self.user_progress['completed_gates'].append(gate)
            self.unlock_next_gate()
            self.save_progress()

    def unlock_next_gate(self):
        """Unlock the next gate in sequence"""
        current_index = len(self.user_progress['unlocked_gates']) - 1
        if current_index + 1 < len(self.gate_unlock_order):
            next_gate = self.gate_unlock_order[current_index + 1]
            if next_gate not in self.user_progress['unlocked_gates']:
                self.user_progress['unlocked_gates'].append(next_gate)
                self.setup_ui()  # Refresh UI to show new gate


class GateTutorial:
    def __init__(self, parent, gate, gate_info, completion_callback=None):
        self.parent = parent
        self.gate = gate
        self.gate_info = gate_info
        self.placed_gates = []
        self.completion_callback = completion_callback  # Add this line
        self.return_callback = None

        # Initialize sound system
        self.init_sound_system()

        # Get screen dimensions for fullscreen
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()

        self.window = tk.Toplevel(parent)
        self.window.title(f"🎓 {gate_info['name']} Tutorial")

        # Make window fullscreen without title bar
        self.window.overrideredirect(True)
        self.window.geometry(f"{screen_width}x{screen_height}+0+0")
        self.window.configure(bg=palette['background'])

        # Store dimensions
        self.window_width = screen_width
        self.window_height = screen_height

        # Make window modal
        self.window.transient(parent)
        self.window.grab_set()
        self.window.focus_set()

        # Handle ESC key to exit fullscreen
        self.window.bind('<Escape>', lambda e: self.close_tutorial())

        self.setup_ui()

        # Play welcome sound
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
        """Setup the gate tutorial interface with fullscreen layout using relative positioning"""
        # Main container with gradient-like effect
        main_frame = tk.Frame(self.window, bg=palette['main_frame_background'])
        main_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Add subtle top border
        top_border = tk.Frame(main_frame, bg=palette['top_border_color'])
        top_border.place(relx=0, rely=0, relwidth=1, relheight=0.005)

        # Content frame
        content_frame = tk.Frame(main_frame, bg=palette['main_container_background'])
        content_frame.place(relx=0, rely=0.005, relwidth=1, relheight=0.995)

        # Create header
        self.create_header(content_frame)

        # Main content container
        main_container = tk.Frame(content_frame, bg=palette['main_container_background'])
        main_container.place(relx=0.05, rely=0.12, relwidth=0.9, relheight=0.83)

        # Description section
        self.setup_description_section(main_container)

        # Circuit area
        self.setup_circuit_section(main_container)

        # Bottom section with controls and results
        self.setup_bottom_section(main_container)

    def create_header(self, parent):
        """Create header using relative positioning"""
        header_frame = tk.Frame(parent, bg=palette['main_container_background'])
        header_frame.place(relx=0.05, rely=0.02, relwidth=0.9, relheight=0.08)

        # Title on the left
        title_label = tk.Label(header_frame, text=f"🎓 {self.gate_info['name']} Tutorial",
                            font=('Arial', max(18, int(self.window_width / 90)), 'bold'),
                            fg=palette['main_title_color'], bg=palette['main_container_background'])
        title_label.place(relx=0, rely=0.2, anchor='w')

        # Subtitle
        subtitle_label = tk.Label(header_frame,
                                text="Interactive quantum gate exploration",
                                font=('Arial', max(10, int(self.window_width / 150)), 'italic'),
                                fg=palette['main_subtitle_color'], bg=palette['main_container_background'])
        subtitle_label.place(relx=0, rely=0.7, anchor='w')

        # Close button on the right
        close_btn = tk.Button(header_frame, text="❌ Close",
                             command=self.close_tutorial,
                             font=('Arial', max(10, int(self.window_width / 150)), 'bold'),
                             bg=palette['background_2'], fg=palette['close_button_text_color'],
                             padx=15, pady=8,
                             cursor='hand2',
                             relief=tk.FLAT,
                             borderwidth=1)
        close_btn.place(relx=1, rely=0.5, anchor='e')

        # Add hover effect
        def on_close_enter(event):
            close_btn.configure(bg=palette['close_button_text_color'], fg=palette['close_button_hover_text_color'])
        def on_close_leave(event):
            close_btn.configure(bg=palette['background_2'], fg=palette['close_button_text_color'])

        close_btn.bind("<Enter>", on_close_enter)
        close_btn.bind("<Leave>", on_close_leave)


    def close_tutorial(self):
        """Close the gate tutorial"""
        self.play_sound('button_click')
        # Exit fullscreen before closing
        try:
            self.window.overrideredirect(False)
        except:
            pass
        self.window.destroy()


    def setup_description_section(self, parent):
        """Setup description section using relative positioning"""
        desc_frame = tk.Frame(parent, bg=palette['main_container_background'], relief=tk.RAISED, bd=2)
        desc_frame.place(relx=0, rely=0, relwidth=1, relheight=0.2)

        desc_title = tk.Label(desc_frame, text="📋 Gate Description",
                             font=('Arial', max(14, int(self.window_width / 100)), 'bold'),
                             fg=palette['description_title_text_color'], bg=palette['main_container_background'])
        desc_title.place(relx=0.5, rely=0.15, anchor='center')

        desc_label = tk.Label(desc_frame, text=self.gate_info['description'],
                             font=('Arial', max(12, int(self.window_width / 120))),
                             fg=palette['description_text_color'], bg=palette['main_container_background'],
                             wraplength=int(self.window_width * 0.8), justify=tk.CENTER)
        desc_label.place(relx=0.5, rely=0.5, anchor='center')

        example_label = tk.Label(desc_frame, text=f"Example: {self.gate_info['example']}",
                                font=('Arial', max(11, int(self.window_width / 130)), 'italic'),
                                fg=self.gate_info['color'], bg=palette['main_container_background'])
        example_label.place(relx=0.5, rely=0.8, anchor='center')

    def setup_circuit_section(self, parent):
        """Setup circuit visualization section using relative positioning"""
        circuit_frame = tk.Frame(parent, bg=palette['main_container_background'], relief=tk.RAISED, bd=2)
        circuit_frame.place(relx=0, rely=0.25, relwidth=1, relheight=0.3)

        circuit_title = tk.Label(circuit_frame, text="🔧 Interactive Circuit Visualization",
                                font=('Arial', max(14, int(self.window_width / 100)), 'bold'),
                                fg=palette['circuit_title_text_color'], bg=palette['main_container_background'])
        circuit_title.place(relx=0.5, rely=0.1, anchor='center')

        # Canvas container with enhanced styling
        canvas_container = tk.Frame(circuit_frame, bg=palette['background'], relief=tk.SUNKEN, bd=3)
        canvas_container.place(relx=0.05, rely=0.25, relwidth=0.9, relheight=0.65)

        canvas_width = int(self.window_width * 0.85)
        canvas_height = int(self.window_height * 0.18)

        self.canvas = tk.Canvas(canvas_container, width=canvas_width, height=canvas_height,
                               bg=palette['main_frame_background'], highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor='center')

        self.canvas_width = canvas_width
        self.canvas_height = canvas_height

    def setup_bottom_section(self, parent):
        """Setup bottom section with controls and results using relative positioning"""
        bottom_frame = tk.Frame(parent, bg=palette['main_container_background'])
        bottom_frame.place(relx=0, rely=0.6, relwidth=1, relheight=0.4)

        # Left side - Gate Controls (40% width)
        controls_frame = tk.Frame(bottom_frame, bg=palette['main_container_background'], relief=tk.RAISED, bd=2)
        controls_frame.place(relx=0, rely=0, relwidth=0.48, relheight=1)

        self.setup_gate_controls(controls_frame)

        # Right side - Results (60% width)
        results_frame = tk.Frame(bottom_frame, bg=palette['main_container_background'], relief=tk.RAISED, bd=2)
        results_frame.place(relx=0.52, rely=0, relwidth=0.48, relheight=1)

        self.setup_results_area(results_frame)

    def setup_gate_controls(self, parent):
        """Setup gate control buttons using relative positioning"""
        controls_title = tk.Label(parent, text="🎮 Gate Controls",
                                 font=('Arial', max(14, int(self.window_width / 100)), 'bold'),
                                 fg=palette['controls_title_text_color'], bg=palette['main_container_background'])
        controls_title.place(relx=0.5, rely=0.1, anchor='center')

        # Button container
        button_container = tk.Frame(parent, bg=palette['main_container_background'])
        button_container.place(relx=0.15, rely=0.25, relwidth=0.7, relheight=0.65)

        # Gate placement button
        self.gate_btn = tk.Button(button_container, text=f"Add {self.gate} Gate",
                                 command=self.add_gate,
                                 font=('Arial', max(12, int(self.window_width / 120)), 'bold'),
                                 bg=self.gate_info['color'], fg=palette['background_3'],
                                 cursor='hand2',
                                 relief=tk.RAISED, bd=2)
        self.gate_btn.place(relx=0.5, rely=0.15, anchor='center', relwidth=0.3, relheight=0.3)

        # Run button
        run_btn = tk.Button(button_container, text="🚀 Run Circuit",
                           command=self.run_circuit,
                           font=('Arial', max(11, int(self.window_width / 130)), 'bold'),
                           bg=palette['run_button_background'], fg=palette['background_3'],
                           cursor='hand2',
                           relief=tk.RAISED, bd=2)
        run_btn.place(relx=0.5, rely=0.5, anchor='center', relwidth=0.3, relheight=0.3)

        # Clear button
        clear_btn = tk.Button(button_container, text="🔄 Clear Circuit",
                             command=self.clear_circuit,
                             font=('Arial', max(11, int(self.window_width / 130)), 'bold'),
                             bg=palette['clear_button_background'], fg=palette['clear_button_text_color'],
                             cursor='hand2',
                             relief=tk.RAISED, bd=2)
        clear_btn.place(relx=0.5, rely=0.85, anchor='center', relwidth=0.3, relheight=0.3)

        # Add hover effects
        def create_hover_effect(button, original_bg, original_fg):
            def on_enter(event):
                button.configure(bg=palette['clear_button_text_color'], fg=palette['background_3'])
            def on_leave(event):
                button.configure(bg=original_bg, fg=original_fg)
            return on_enter, on_leave

        # Apply hover effects
        for btn, orig_bg, orig_fg in [(self.gate_btn, self.gate_info['color'], palette['background_3']),
                                      (run_btn, palette['run_button_background'], palette['background_3']),
                                      (clear_btn, palette['clear_button_background'], palette['clear_button_text_color'])]:
            on_enter, on_leave = create_hover_effect(btn, orig_bg, orig_fg)
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)

    def setup_results_area(self, parent):
        """Setup results display area using relative positioning"""
        results_title = tk.Label(parent, text="📊 Quantum State Analysis",
                                font=('Arial', max(14, int(self.window_width / 100)), 'bold'),
                                fg=palette['results_title_text_color'], bg=palette['main_container_background'])
        results_title.place(relx=0.5, rely=0.08, anchor='center')

        # Results container with styling
        results_container = tk.Frame(parent, bg=palette['background'], relief=tk.SUNKEN, bd=3)
        results_container.place(relx=0.05, rely=0.18, relwidth=0.9, relheight=0.75)

        # Results text with scrollbar
        text_frame = tk.Frame(results_container, bg=palette['background'])
        text_frame.place(relx=0.02, rely=0.02, relwidth=0.96, relheight=0.96)

        self.results_text = tk.Text(text_frame, font=('Consolas', max(9, int(self.window_width / 180))),
                                   bg=palette['main_frame_background'], fg=palette['results_text_color'],
                                   relief=tk.FLAT, bd=0, insertbackground=palette['results_background'],
                                   selectbackground=palette['results_select_background'], selectforeground=palette['background_3'],
                                   wrap=tk.WORD)

        # Add scrollbar
        scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.results_text.yview,
                                bg=palette['background_2'], troughcolor=palette['background'],
                                activebackground=palette['scrollbar_active_background'])
        self.results_text.configure(yscrollcommand=scrollbar.set)

        self.results_text.place(relx=0, rely=0, relwidth=0.97, relheight=1)
        scrollbar.place(relx=0.97, rely=0, relwidth=0.03, relheight=1)

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

        # Circuit dimensions with better spacing
        wire_start = 120  # Increased from 80 to add more left margin
        wire_end = self.canvas_width - 80
        qubit_spacing = max(60, self.canvas_height // (num_qubits + 2))

        # Draw enhanced background grid
        for i in range(0, self.canvas_width, 40):
            self.canvas.create_line(i, 0, i, self.canvas_height,
                                  fill=palette['background'], width=1)

        # Draw quantum wires with colors
        wire_colors = [palette['quantum_wire_1'],
                       palette['quantum_wire_2'],
                       palette['quantum_wire_3'],
                       palette['quantum_wire_4']
        ]

        for qubit in range(num_qubits):
            y_pos = (qubit + 1) * qubit_spacing
            color = wire_colors[qubit % len(wire_colors)]

            # Enhanced wire with gradient effect
            for thickness in [6, 4, 2]:
                self.canvas.create_line(wire_start, y_pos, wire_end, y_pos,
                                      fill=color, width=thickness)

            # Enhanced qubit label with background
            label_bg = self.canvas.create_rectangle(wire_start - 60, y_pos - 15,
                                                  wire_start - 20, y_pos + 15,
                                                  fill=palette['background_2'], outline=color, width=2)

            self.canvas.create_text(wire_start - 40, y_pos,
                                  text=f"q{qubit}", fill=palette['circuit_canvas_text_fill'],
                                  font=('Arial', 12, 'bold'))

        # Draw enhanced gates
        self.draw_enhanced_gates(wire_start, qubit_spacing, num_qubits)

    def draw_enhanced_gates(self, wire_start, qubit_spacing, num_qubits):
        """Draw gates with enhanced 3D styling"""
        gate_x_start = wire_start + 140  # Increased spacing from wire start
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
                                           fill=palette['background_3'], outline='')
                    self.canvas.create_oval(x - 8, control_y - 8, x + 8, control_y + 8,
                                           fill=palette['CNOT_control_dot_fill'], outline=palette['CNOT_control_dot_outline'], width=2)

                    # Enhanced connection line
                    self.canvas.create_line(x, control_y, x, target_y,
                                           fill=palette['CNOT_connection_line_fill'], width=4)
                    self.canvas.create_line(x, control_y, x, target_y,
                                           fill=color, width=2)

                    # Enhanced target
                    self.canvas.create_oval(x - 22, target_y - 22, x + 22, target_y + 22,
                                           fill=palette['background_3'], outline='')
                    self.canvas.create_oval(x - 20, target_y - 20, x + 20, target_y + 20,
                                           fill='', outline=palette['CNOT_target_outline'], width=3)

                    # X symbol
                    self.canvas.create_line(x - 12, target_y - 12, x + 12, target_y + 12,
                                           fill=palette['CNOT_X_fill'], width=3)
                    self.canvas.create_line(x - 12, target_y + 12, x + 12, target_y - 12,
                                           fill=palette['CNOT_X_fill'], width=3)

                elif gate == 'CZ':
                    # Enhanced CZ gate visualization
                    self.canvas.create_oval(x - 10, control_y - 10, x + 10, control_y + 10,
                                           fill=palette['background_3'], outline='')
                    self.canvas.create_oval(x - 8, control_y - 8, x + 8, control_y + 8,
                                           fill=palette['CZ_fill_1'], outline=palette['CZ_fill_2'], width=2)

                    self.canvas.create_line(x, control_y, x, target_y,
                                           fill=palette['CZ_fill_1'], width=4)
                    self.canvas.create_line(x, control_y, x, target_y,
                                           fill=color, width=2)

                    self.canvas.create_oval(x - 10, target_y - 10, x + 10, target_y + 10,
                                           fill=palette['background_3'], outline='')
                    self.canvas.create_oval(x - 8, target_y - 8, x + 8, target_y + 8,
                                           fill=palette['CZ_fill_1'], outline=palette['CZ_fill_2'], width=2)
            else:
                # Enhanced single qubit gates
                y_pos = qubit_spacing

                # 3D shadow effect
                self.canvas.create_rectangle(x - 27, y_pos - 22, x + 27, y_pos + 22,
                                            fill=palette['background_3'], outline='')

                # Main gate with gradient effect
                self.canvas.create_rectangle(x - 25, y_pos - 20, x + 25, y_pos + 20,
                                            fill=color, outline=palette['normal_gate_fill'], width=2)

                # Inner highlight
                self.canvas.create_rectangle(x - 23, y_pos - 18, x + 23, y_pos + 18,
                                            fill='', outline=palette['normal_gate_fill'], width=1)

                # Gate symbol with shadow
                self.canvas.create_text(x + 1, y_pos + 1, text=gate,
                                       fill=palette['background_3'], font=('Arial', 14, 'bold'))
                self.canvas.create_text(x, y_pos, text=gate,
                                       fill=palette['background_3'], font=('Arial', 16, 'bold'))

    def mark_completed(self):
        """Mark this gate tutorial as completed"""
        if self.completion_callback:
            self.completion_callback()

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

            self.mark_completed()

        except Exception as e:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"❌ Error: {str(e)}\n")
            self.play_sound('error')
        finally:
            self.results_text.configure(state=tk.DISABLED)


    def restore_fullscreen(self):
        """Restore fullscreen mode"""
        self.window.deiconify()  # Show window again
        self.window.overrideredirect(True)
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        self.window.geometry(f"{screen_width}x{screen_height}+0+0")
        self.window.lift()
        self.window.focus_force()


    def get_educational_message(self):
        """Get educational message based on the gate"""
        messages = {
            'H': "You've created superposition! The qubit is now in both |0⟩ and |1⟩ states simultaneously.",
            'X': "You've flipped the qubit! This is the quantum equivalent of a classical NOT gate.",
            'Y': "You've applied a complex rotation that combines X and Z transformations with phase.",
            'Z': "You've applied a phase flip! The |1⟩ state now has a negative phase.",
            'S': "You've applied a 90° phase rotation to the |1⟩ state.",
            'T': "You've applied a 45° phase rotation - useful for quantum algorithms!",
            'CNOT': "You've created quantum entanglement! The qubits are now correlated.",
            'CZ': "You've applied conditional phase flip - another way to create entanglement!"
        }
        return messages.get(self.gate, "Great job exploring quantum mechanics!")


    def continue_learning(self, congrats_window):
        """Continue to next gate and mark current as completed"""
        congrats_window.destroy()
        self.mark_completed()
        self.close_tutorial()


    def try_again(self, congrats_window):
        """Clear circuit and try again"""
        congrats_window.destroy()
        self.clear_circuit()


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