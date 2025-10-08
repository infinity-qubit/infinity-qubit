#!/usr/bin/env python3
"""
Tutorial Mode for Infinity Qubit
Allows users to learn about quantum computing concepts.
"""

import os
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import sys
import json
import pygame
import datetime
import tkinter as tk
from qiskit_aer import Aer
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

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
            'current_step': 0,  # 0=bit intro, 1=logic gates, 2=qubit intro, 3=quantum gates
            'completed_gates': [],
            'unlocked_gates': ['H'],
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
        self.window.title("Quantum Gates Tutorial")

        # Set fullscreen mode
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()

        # Make window fullscreen without title bar (same as other game modes)
        self.window.overrideredirect(True)
        self.window.geometry(f"{screen_width}x{screen_height}+0+0")
        self.window.configure(bg=palette['background'])
        self.window.resizable(False, False)

        # Store dimensions (use full screen)
        self.window_width = screen_width
        self.window_height = screen_height

        # Make window visible and focused immediately
        self.window.lift()
        self.window.focus_force()

        # Gate information
        self.gate_info = {
            'H': {
                'name': 'Hadamard Gate',
                'description': 'Creates superposition by transforming |0⟩ to |+⟩ and |1⟩ to |-⟩',
                'example': 'H|0⟩ = |+⟩ = (|0⟩ + |1⟩)/√2',
                'input_state': '|0⟩',
                'target_state': '|+⟩',
                'color': palette['gate_color']
            },
            'S': {
                'name': 'S Gate (Phase)',
                'description': 'Applies a 90° phase shift to |1⟩ state',
                'example': 'S|1⟩ = i|1⟩',
                'input_state': '|1⟩',
                'target_state': 'i|1⟩',
                'color': palette['gate_color']
            },
            'T': {
                'name': 'T Gate (π/8)',
                'description': 'Applies a 45° phase shift to |1⟩ state',
                'example': 'T|1⟩ = e^(iπ/4)|1⟩',
                'input_state': '|1⟩',
                'target_state': 'e^(iπ/4)|1⟩',
                'color': palette['gate_color']
            },
            'CZ': {
                'name': 'Controlled-Z Gate',
                'description': 'Applies Z gate to target qubit if control qubit is |1⟩',
                'example': 'CZ|11⟩ = -|11⟩',
                'input_state': '|11⟩',
                'target_state': '-|11⟩',
                'color': palette['gate_color']
            },
            'X': {
                'name': 'Pauli-X Gate (NOT)',
                'description': 'Flips qubit state: |0⟩↔|1⟩',
                'example': 'X|0⟩ = |1⟩, X|1⟩ = |0⟩',
                'input_state': '|0⟩',
                'target_state': '|1⟩',
                'color': palette['gate_color']
            },
            'Y': {
                'name': 'Pauli-Y Gate',
                'description': 'Combination of X and Z gates with phase',
                'example': 'Y|0⟩ = i|1⟩, Y|1⟩ = -i|0⟩',
                'input_state': '|0⟩',
                'target_state': 'i|1⟩',
                'color': palette['gate_color']
            },
            'Z': {
                'name': 'Pauli-Z Gate',
                'description': 'Applies phase flip to |1⟩ state',
                'example': 'Z|0⟩ = |0⟩, Z|1⟩ = -|1⟩',
                'input_state': '|1⟩',
                'target_state': '-|1⟩',
                'color': palette['gate_color']
            },
            'CNOT': {
                'name': 'Controlled-NOT Gate',
                'description': 'Flips target qubit if control qubit is |1⟩',
                'example': 'CNOT|10⟩ = |11⟩, CNOT|00⟩ = |00⟩',
                'input_state': '|10⟩',
                'target_state': '|11⟩',
                'color': palette['gate_color']
            }
        }

        # Start with intro instead of main UI
        if self.user_progress['current_step'] < 4:
            self.show_intro_step()
        else:
            self.setup_ui()

        # Ensure window is visible and on top
        self.window.lift()
        self.window.focus_force()

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
        self.user_progress['current_step'] = 4
        self.save_progress()
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
            self.show_logic_gates_explanation()
        elif self.user_progress['current_step'] == 2:
            self.show_qubit_explanation()
        elif self.user_progress['current_step'] == 3:
            self.show_quantum_notation_explanation()


    def show_bit_explanation(self):
        """Step 1 - What's a bit?"""
        # Clear window EXCEPT background
        for widget in self.window.winfo_children():
            widget.destroy()

        # Main container
        main_frame = tk.Frame(self.window, bg=palette['background'])
        main_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Title
        title = tk.Label(main_frame, text="Step 1 — What's a bit?",
                        font=('Arial', max(24, int(self.window_width / 60)), 'bold'),
                        fg=palette['main_title_color'], bg=palette['background'])
        title.place(relx=0.5, rely=0.08, anchor='center')

        # Explanation text
        explanation = """A bit is the smallest piece of information a computer understands.

    It can only be 0 or 1 — like an on/off switch or a light bulb that's either off (0) or on (1).

    When you watch a video, play a game, or open an app, your computer is just working with billions of these 0s and 1s."""

        text_label = tk.Label(main_frame, text=explanation,
                            font=('Arial', max(14, int(self.window_width / 100))),
                            fg=palette['explanation_text_color'], bg=palette['background'],
                            wraplength=int(self.window_width * 0.7), justify=tk.CENTER)
        text_label.place(relx=0.5, rely=0.25, anchor='center')

        # Analogy section
        analogy_text = """Analogy: Imagine a coin lying flat on a table. If heads = 1 and tails = 0,
    then the coin represents a bit — but it can only show one face at a time."""

        analogy_label = tk.Label(main_frame, text=analogy_text,
                                font=('Arial', max(14, int(self.window_width / 100)), 'italic'),
                                fg=palette['gate_color'], bg=palette['background'],
                                wraplength=int(self.window_width * 0.8), justify=tk.CENTER)
        analogy_label.place(relx=0.5, rely=0.4, anchor='center')

        # Visual demonstration area
        visual_frame = tk.Frame(main_frame, bg=palette['background_2'], relief=tk.RAISED, bd=2)
        visual_frame.place(relx=0.2, rely=0.5, relwidth=0.6, relheight=0.25)

        # Interactive bit demonstration
        self.create_bit_demo(visual_frame)

        # Next button - UPDATED TEXT
        next_canvas = tk.Canvas(main_frame, width=350, height=70,
                            bg=palette['gate_color'], highlightthickness=0, relief=tk.FLAT, bd=0)
        next_canvas.place(relx=0.5, rely=0.85, anchor='center')

        next_rect_id = next_canvas.create_rectangle(2, 2, 348, 68,
                                                fill=palette['gate_color'], outline=palette['gate_color'], width=0)
        next_text_id = next_canvas.create_text(175, 35, text="Next: Learn Logic Gates →",  # UPDATED
                                            font=('Arial', max(12, int(self.window_width / 120)), 'bold'),
                                            fill=palette['background_3'])

        next_canvas.bind("<Button-1>", lambda e: self.next_intro_step())
        next_canvas.bind("<Enter>", lambda e: (next_canvas.itemconfig(next_rect_id, fill=palette['gate_button_active_background']),
                                            next_canvas.itemconfig(next_text_id, fill=palette['background_3'])))
        next_canvas.bind("<Leave>", lambda e: (next_canvas.itemconfig(next_rect_id, fill=palette['gate_color']),
                                            next_canvas.itemconfig(next_text_id, fill=palette['background_3'])))
        next_canvas.configure(cursor='hand2')


    def create_bit_demo(self, parent):
        """Create interactive bit demonstration"""
        demo_title = tk.Label(parent, text="Interactive Bit Demo",
                            font=('Arial', max(14, int(self.window_width / 100)), 'bold'),
                            fg=palette['main_title_color'], bg=palette['background_2'])
        demo_title.place(relx=0.5, rely=0.15, anchor='center')  # Moved down slightly from 0.1

        # Bit state display
        self.bit_state = 0
        self.bit_display = tk.Label(parent, text="0",
                                font=('Arial', 48, 'bold'),
                                fg=palette['background_3'], bg=palette['gate_color' if self.bit_state else 'gate_color'],
                                width=3, height=1, relief=tk.RAISED, bd=3)
        self.bit_display.place(relx=0.3, rely=0.45, anchor='center')  # Moved down from 0.4

        # Flip button - INCREASED SIZE for touchscreen
        flip_canvas = tk.Canvas(parent, width=150, height=60,  # Increased from 100x40
                            bg=palette['gate_color'], highlightthickness=0, relief=tk.FLAT, bd=0)
        flip_canvas.place(relx=0.7, rely=0.45, anchor='center')  # Moved down from 0.4

        flip_rect_id = flip_canvas.create_rectangle(2, 2, 148, 58,  # Updated coordinates
                                                fill=palette['gate_color'], outline=palette['gate_color'], width=0)
        flip_text_id = flip_canvas.create_text(75, 30, text="Flip Bit",  # Updated center coordinates
                                            font=('Arial', max(16, int(self.window_width / 100)), 'bold'),  # Increased font size
                                            fill=palette['background_3'])

        flip_canvas.bind("<Button-1>", lambda e: self.flip_bit())
        flip_canvas.bind("<Enter>", lambda e: (flip_canvas.itemconfig(flip_rect_id, fill=palette['button_hover_background']),
                                            flip_canvas.itemconfig(flip_text_id, fill=palette['button_hover_text_color'])))
        flip_canvas.bind("<Leave>", lambda e: (flip_canvas.itemconfig(flip_rect_id, fill=palette['gate_color']),
                                            flip_canvas.itemconfig(flip_text_id, fill=palette['background_3'])))
        flip_canvas.configure(cursor='hand2')

        # State label - INCREASED SIZE and moved down
        self.bit_label = tk.Label(parent, text="State: OFF",
                                font=('Arial', max(16, int(self.window_width / 100))),  # Increased from max(10, ...)
                                fg=palette['explanation_text_color'], bg=palette['background_2'])
        self.bit_label.place(relx=0.5, rely=0.75, anchor='center')  # Moved down from 0.7


    def flip_bit(self):
        """Flip the bit state"""
        self.bit_state = 1 - self.bit_state
        self.bit_display.configure(text=str(self.bit_state),
                                  bg=palette['gate_color'] if self.bit_state else palette['gate_color'])
        self.bit_label.configure(text=f"State: {'ON' if self.bit_state else 'OFF'}")
        self.play_sound('button_click')


    def show_logic_gates_explanation(self):
        """Step 2 - Logic Gates (Classical Computing)"""
        # Clear window EXCEPT background
        for widget in self.window.winfo_children():
            widget.destroy()

        # Main container
        main_frame = tk.Frame(self.window, bg=palette['background'])
        main_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Title
        title = tk.Label(main_frame, text="Step 2 — Logic Gates (Classical Computing)",
                        font=('Arial', max(24, int(self.window_width / 60)), 'bold'),
                        fg=palette['main_title_color'], bg=palette['background'])
        title.place(relx=0.5, rely=0.06, anchor='center')

        # Explanation text
        explanation = """Now that you understand bits, let's explore how computers use them with logic gates.

    Logic gates are the building blocks of all digital circuits. They take bits as input and produce bits as output.

    You probably remember these from school, but let's refresh your memory!"""

        text_label = tk.Label(main_frame, text=explanation,
                            font=('Arial', max(14, int(self.window_width / 100))),
                            fg=palette['explanation_text_color'], bg=palette['background'],
                            wraplength=int(self.window_width * 0.8), justify=tk.CENTER)
        text_label.place(relx=0.5, rely=0.18, anchor='center')

        # Logic gates demonstration area
        demo_frame = tk.Frame(main_frame, bg=palette['background_2'], relief=tk.RAISED, bd=2)
        demo_frame.place(relx=0.1, rely=0.32, relwidth=0.8, relheight=0.45)

        self.create_logic_gates_demo(demo_frame)

        # Navigation buttons
        # Back button
        back_canvas = tk.Canvas(main_frame, width=140, height=60,
                            bg=palette['background_2'], highlightthickness=0, relief=tk.FLAT, bd=0)
        back_canvas.place(relx=0.25, rely=0.92, anchor='center')

        back_rect_id = back_canvas.create_rectangle(2, 2, 137, 58,
                                                fill=palette['background_2'], outline=palette['background_2'], width=0)
        back_text_id = back_canvas.create_text(60, 30, text="← Back",
                                            font=('Arial', max(14, int(self.window_width / 100)), 'bold'),
                                            fill=palette['explanation_text_color'])

        back_canvas.bind("<Button-1>", lambda e: self.prev_intro_step())
        back_canvas.bind("<Enter>", lambda e: (back_canvas.itemconfig(back_rect_id, fill=palette['button_hover_background']),
                                            back_canvas.itemconfig(back_text_id, fill=palette['button_hover_text_color'])))
        back_canvas.bind("<Leave>", lambda e: (back_canvas.itemconfig(back_rect_id, fill=palette['background_2']),
                                            back_canvas.itemconfig(back_text_id, fill=palette['explanation_text_color'])))
        back_canvas.configure(cursor='hand2')

        # Next button
        next_canvas = tk.Canvas(main_frame, width=280, height=60,
                            bg=palette['gate_color'], highlightthickness=0, relief=tk.FLAT, bd=0)
        next_canvas.place(relx=0.75, rely=0.92, anchor='center')

        next_rect_id = next_canvas.create_rectangle(2, 2, 278, 58,
                                                fill=palette['gate_color'], outline=palette['gate_color'], width=0)
        next_text_id = next_canvas.create_text(140, 30, text="Next: Enter the Qubit →",
                                            font=('Arial', max(12, int(self.window_width / 120)), 'bold'),
                                            fill=palette['background_3'])

        next_canvas.bind("<Button-1>", lambda e: self.next_intro_step())
        next_canvas.bind("<Enter>", lambda e: (next_canvas.itemconfig(next_rect_id, fill=palette['button_hover_background']),
                                            next_canvas.itemconfig(next_text_id, fill=palette['button_hover_text_color'])))
        next_canvas.bind("<Leave>", lambda e: (next_canvas.itemconfig(next_rect_id, fill=palette['gate_color']),
                                            next_canvas.itemconfig(next_text_id, fill=palette['background_3'])))
        next_canvas.configure(cursor='hand2')


    def create_logic_gates_demo(self, parent):
        """Create interactive logic gates demonstration with improved layout"""
        demo_title = tk.Label(parent, text="Interactive Logic Gates Demo",
                            font=('Arial', max(16, int(self.window_width / 80)), 'bold'),
                            fg=palette['main_title_color'], bg=palette['background_2'])
        demo_title.place(relx=0.5, rely=0.08, anchor='center')

        # Initialize gate states
        self.input_a = 0
        self.input_b = 0
        self.selected_gate = None
        self.gate_selected = False
        self.output_computed = False

        # Gate selection section - LEFT SIDE ONLY
        gate_frame = tk.Frame(parent, bg=palette['background_2'])
        gate_frame.place(relx=0.05, rely=0.2, relwidth=0.25, relheight=0.7)

        tk.Label(gate_frame, text="Choose Logic Gate:\n",
                font=('Arial', max(14, int(self.window_width / 100)), 'bold'),
                fg=palette['main_title_color'], bg=palette['background_2']).place(relx=0.5, rely=0.1, anchor='center')

        # Gate buttons - vertical layout with MAXIMUM SPACING
        gates = ["AND", "OR", "XOR", "NOT"]
        self.gate_buttons = {}

        for i, gate in enumerate(gates):
            gate_canvas = tk.Canvas(gate_frame, width=200, height=80,  # Keep the bigger size
                                bg=palette['gate_color'], highlightthickness=0, relief=tk.FLAT, bd=0)
            gate_canvas.place(relx=0.5, rely=0.25 + i * 0.22, anchor='center')  # INCREASED spacing from 0.2 to 0.22

            gate_rect = gate_canvas.create_rectangle(2, 2, 198, 78,
                                                fill=palette['gate_color'], outline=palette['gate_color'], width=0)
            gate_text = gate_canvas.create_text(100, 40, text=gate,
                                            font=('Arial', max(18, int(self.window_width / 80)), 'bold'),
                                            fill=palette['background_3'])

            # Store references for later highlighting
            self.gate_buttons[gate] = {'canvas': gate_canvas, 'rect': gate_rect, 'text': gate_text}

            gate_canvas.bind("<Button-1>", lambda e, g=gate: self.select_gate_new(g))
            gate_canvas.bind("<Enter>", lambda e, canvas=gate_canvas, rect=gate_rect, text=gate_text:
                            (canvas.itemconfig(rect, fill=palette['button_hover_background']),
                            canvas.itemconfig(text, fill=palette['button_hover_text_color'])))
            gate_canvas.bind("<Leave>", lambda e, canvas=gate_canvas, rect=gate_rect, text=gate_text, g=gate:
                            self.restore_gate_color(g, canvas, rect, text))
            gate_canvas.configure(cursor='hand2')

        # Dynamic content area - RIGHT SIDE (initially empty)
        self.dynamic_frame = tk.Frame(parent, bg=palette['background_2'])
        self.dynamic_frame.place(relx=0.35, rely=0.2, relwidth=0.6, relheight=0.7)

        # Show initial instruction
        self.show_initial_instruction()


    def restore_gate_color(self, gate, canvas, rect, text):
        """Restore gate color based on selection state"""
        if self.selected_gate == gate:
            # Keep selected color with WHITE text
            canvas.itemconfig(rect, fill=palette['gate_button_active_background'])
            canvas.itemconfig(text, fill='white')  # CHANGED: Use white for selected text
        else:
            # Restore normal color
            canvas.itemconfig(rect, fill=palette['gate_color'])
            canvas.itemconfig(text, fill=palette['background_3'])


    def show_initial_instruction(self):
        """Show initial instruction when no gate is selected"""
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()

        instruction_label = tk.Label(self.dynamic_frame,
                                    text="← Select a logic gate\nto begin exploring!",
                                    font=('Arial', max(16, int(self.window_width / 90)), 'italic'),
                                    fg=palette['explanation_text_color'], bg=palette['background_2'],
                                    justify=tk.CENTER)
        instruction_label.place(relx=0.15, rely=0.5, anchor='center')


    def select_gate_new(self, gate):
        """Select logic gate and show inputs"""
        self.selected_gate = gate
        self.gate_selected = True
        self.output_computed = False
        self.play_sound('button_click')

        # Update gate button appearance
        self.update_gate_buttons()

        # Show inputs for selected gate
        self.show_gate_inputs()


    def update_gate_buttons(self):
        """Update gate button colors to show selection"""
        for gate, button_info in self.gate_buttons.items():
            if gate == self.selected_gate:
                # Highlight selected gate with WHITE text for better visibility
                button_info['canvas'].itemconfig(button_info['rect'], fill=palette['gate_button_active_background'])
                button_info['canvas'].itemconfig(button_info['text'], fill='white')  # CHANGED: Use  white for selected text
            else:
                # Normal color for unselected gates
                button_info['canvas'].itemconfig(button_info['rect'], fill=palette['gate_color'])
                button_info['canvas'].itemconfig(button_info['text'], fill=palette['background_3'])


    def show_gate_inputs(self):
        """Show input controls after gate selection"""
        # Clear dynamic area
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()

        # Title for current gate - MOVED FURTHER LEFT TO CENTER IN DEMO BOX
        gate_title = tk.Label(self.dynamic_frame, text=f"{self.selected_gate} Gate Inputs",
                            font=('Arial', max(14, int(self.window_width / 100)), 'bold'),
                            fg=palette['main_title_color'], bg=palette['background_2'])
        gate_title.place(relx=0.25, rely=0.08, anchor='center')

        # Input A section - MOVED FURTHER LEFT
        input_a_frame = tk.Frame(self.dynamic_frame, bg=palette['background_2'])
        if self.selected_gate != "NOT":
            # For two-input gates: position Input A further left
            input_a_frame.place(relx=0.05, rely=0.25, relwidth=0.2, relheight=0.35)
        else:
            # For NOT gate: center Input A further left
            input_a_frame.place(relx=0.15, rely=0.25, relwidth=0.2, relheight=0.35)

        # MOVED INPUT A DISPLAY HIGHER TO CREATE SEPARATION
        self.input_a_display = tk.Label(input_a_frame, text=str(self.input_a),
                                    font=('Arial', 32, 'bold'),
                                    fg=palette['background_3'], bg=palette['gate_color'],
                                    width=2, height=1, relief=tk.RAISED, bd=2)
        self.input_a_display.place(relx=0.5, rely=0.25, anchor='center')  # MOVED UP from 0.35 to 0.25

        # Input A toggle button - MOVED UP TO PREVENT CUTOFF
        toggle_a_canvas = tk.Canvas(input_a_frame, width=120, height=50,  # INCREASED from 80x35 to 120x50
                                bg=palette['gate_color'], highlightthickness=0, relief=tk.FLAT, bd=0)
        toggle_a_canvas.place(relx=0.5, rely=0.82, anchor='center')  # MOVED UP from 0.9 to 0.82

        toggle_a_rect = toggle_a_canvas.create_rectangle(2, 2, 118, 48,  # UPDATED coordinates
                                                        fill=palette['gate_color'], outline=palette['gate_color'], width=0)
        toggle_a_text = toggle_a_canvas.create_text(60, 25, text="Toggle",  # UPDATED center coordinates
                                                font=('Arial', max(14, int(self.window_width / 120)), 'bold'),  # INCREASED font size
                                                fill=palette['background_3'])

        toggle_a_canvas.bind("<Button-1>", lambda e: self.toggle_input_a_new())
        toggle_a_canvas.bind("<Enter>", lambda e: (toggle_a_canvas.itemconfig(toggle_a_rect, fill=palette['button_hover_background']),
                                                toggle_a_canvas.itemconfig(toggle_a_text, fill=palette['button_hover_text_color'])))
        toggle_a_canvas.bind("<Leave>", lambda e: (toggle_a_canvas.itemconfig(toggle_a_rect, fill=palette['gate_color']),
                                                toggle_a_canvas.itemconfig(toggle_a_text, fill=palette['background_3'])))
        toggle_a_canvas.configure(cursor='hand2')

        # Input B section (only for gates that need 2 inputs) - MOVED FURTHER LEFT
        if self.selected_gate != "NOT":
            input_b_frame = tk.Frame(self.dynamic_frame, bg=palette['background_2'])
            input_b_frame.place(relx=0.25, rely=0.25, relwidth=0.2, relheight=0.35)

            # MOVED INPUT B DISPLAY HIGHER TO CREATE SEPARATION
            self.input_b_display = tk.Label(input_b_frame, text=str(self.input_b),
                                        font=('Arial', 32, 'bold'),
                                        fg=palette['background_3'], bg=palette['gate_color'],
                                        width=2, height=1, relief=tk.RAISED, bd=2)
            self.input_b_display.place(relx=0.5, rely=0.25, anchor='center')  # MOVED UP from 0.35 to 0.25

            # Input B toggle button - MOVED UP TO PREVENT CUTOFF
            toggle_b_canvas = tk.Canvas(input_b_frame, width=120, height=50,  # INCREASED from 80x35 to 120x50
                                    bg=palette['gate_color'], highlightthickness=0, relief=tk.FLAT, bd=0)
            toggle_b_canvas.place(relx=0.5, rely=0.82, anchor='center')  # MOVED UP from 0.9 to 0.82

            toggle_b_rect = toggle_b_canvas.create_rectangle(2, 2, 118, 48,  # UPDATED coordinates
                                                            fill=palette['gate_color'], outline=palette['gate_color'], width=0)
            toggle_b_text = toggle_b_canvas.create_text(60, 25, text="Toggle",  # UPDATED center coordinates
                                                    font=('Arial', max(14, int(self.window_width / 120)), 'bold'),  # INCREASED font size
                                                    fill=palette['background_3'])

            toggle_b_canvas.bind("<Button-1>", lambda e: self.toggle_input_b_new())
            toggle_b_canvas.bind("<Enter>", lambda e: (toggle_b_canvas.itemconfig(toggle_b_rect, fill=palette['button_hover_background']),
                                                    toggle_b_canvas.itemconfig(toggle_b_text, fill=palette['button_hover_text_color'])))
            toggle_b_canvas.bind("<Leave>", lambda e: (toggle_b_canvas.itemconfig(toggle_b_rect, fill=palette['gate_color']),
                                                    toggle_b_canvas.itemconfig(toggle_b_text, fill=palette['background_3'])))
            toggle_b_canvas.configure(cursor='hand2')

        # Compute button - MOVED EVEN LOWER
        compute_canvas = tk.Canvas(self.dynamic_frame, width=200, height=70,  # INCREASED from 150x50 to 200x70
                                bg=palette['gate_color'], highlightthickness=0, relief=tk.FLAT, bd=0)
        compute_canvas.place(relx=0.25, rely=0.8, anchor='center')  # MOVED DOWN from 0.75 to 0.8

        compute_rect = compute_canvas.create_rectangle(2, 2, 198, 68,  # UPDATED coordinates
                                                    fill=palette['gate_color'], outline=palette['gate_color'], width=0)
        compute_text = compute_canvas.create_text(100, 35, text="Compute",  # UPDATED center coordinates
                                                font=('Arial', max(18, int(self.window_width / 90)), 'bold'),  # INCREASED font size
                                                fill=palette['background_3'])

        compute_canvas.bind("<Button-1>", lambda e: self.compute_output())
        compute_canvas.bind("<Enter>", lambda e: (compute_canvas.itemconfig(compute_rect, fill=palette['button_hover_background']),
                                                compute_canvas.itemconfig(compute_text, fill=palette['button_hover_text_color'])))
        compute_canvas.bind("<Leave>", lambda e: (compute_canvas.itemconfig(compute_rect, fill=palette['gate_color']),
                                                compute_canvas.itemconfig(compute_text, fill=palette['background_3'])))
        compute_canvas.configure(cursor='hand2')


    def toggle_input_a_new(self):
        """Toggle input A and reset output"""
        self.input_a = 1 - self.input_a
        self.input_a_display.configure(text=str(self.input_a))
        self.output_computed = False
        self.play_sound('button_click')


    def toggle_input_b_new(self):
        """Toggle input B and reset output"""
        self.input_b = 1 - self.input_b
        if hasattr(self, 'input_b_display'):
            self.input_b_display.configure(text=str(self.input_b))
        self.output_computed = False
        self.play_sound('button_click')


    def compute_output(self):
        """Compute and display the output with truth table"""
        if not self.selected_gate:
            return

        # Calculate output
        if self.selected_gate == "AND":
            output = self.input_a & self.input_b
            truth_data = [
                ["Input 1", "Input 2", "Output"],
                ["0", "0", "0"],
                ["0", "1", "0"],
                ["1", "0", "0"],
                ["1", "1", "1"]
            ]
        elif self.selected_gate == "OR":
            output = self.input_a | self.input_b
            truth_data = [
                ["Input 1", "Input 2", "Output"],
                ["0", "0", "0"],
                ["0", "1", "1"],
                ["1", "0", "1"],
                ["1", "1", "1"]
            ]
        elif self.selected_gate == "XOR":
            output = self.input_a ^ self.input_b
            truth_data = [
                ["Input 1", "Input 2", "Output"],
                ["0", "0", "0"],
                ["0", "1", "1"],
                ["1", "0", "1"],
                ["1", "1", "0"]
            ]
        elif self.selected_gate == "NOT":
            output = 1 - self.input_a
            truth_data = [
                ["Input 1", "Output"],
                ["0", "1"],
                ["1", "0"]
            ]
        else:
            output = 0
            truth_data = []

        self.output_computed = True
        self.play_sound('success')

        # Show output and truth table
        self.show_output_and_truth_table(output, truth_data)


    def show_output_and_truth_table(self, output, truth_data):
        """Display output and formatted truth table"""
        # Output section - MOVED UP AND RIGHT TO ALIGN WITH OTHER TITLES
        output_frame = tk.Frame(self.dynamic_frame, bg=palette['background_2'])
        output_frame.place(relx=0.65, rely=0.01, relwidth=0.2, relheight=0.25)  # Moved further right and higher

        tk.Label(output_frame, text="Output:",
                font=('Arial', max(14, int(self.window_width / 100)), 'bold'),
                fg=palette['main_title_color'], bg=palette['background_2']).place(relx=0.5, rely=0.15, anchor='center')  # Moved higher

        output_display = tk.Label(output_frame, text=str(output),
                                font=('Arial', 42, 'bold'),
                                fg=palette['background_3'], bg=palette['gate_color'],
                                width=2, height=1, relief=tk.RAISED, bd=3)
        output_display.place(relx=0.5, rely=0.7, anchor='center')

        # Truth table section - MOVED FURTHER RIGHT TO CENTER WITH OUTPUT
        table_frame = tk.Frame(self.dynamic_frame, bg=palette['background_3'], relief=tk.RAISED, bd=2)
        table_frame.place(relx=0.55, rely=0.28, relwidth=0.4, relheight=0.65)  # Moved right from 0.45 to 0.55, reduced width from 0.5 to 0.4

        # Create actual table
        self.create_truth_table(table_frame, truth_data)


    def create_truth_table(self, parent, truth_data):
        """Create a properly formatted truth table"""
        if not truth_data:
            return

        # Calculate table dimensions
        rows = len(truth_data)
        cols = len(truth_data[0])

        # Table container - REPOSITIONED MUCH LOWER FOR BETTER VISIBILITY
        table_container = tk.Frame(parent, bg=palette['background_3'])
        table_container.place(relx=0.5, rely=0.4, anchor='center')  # Moved down from 0.45 to 0.4 and centered properly

        # Create table cells with BIGGER SIZE for better visibility
        for row_idx, row_data in enumerate(truth_data):
            for col_idx, cell_data in enumerate(row_data):
                # Header row styling - FIXED: Only apply to actual header row
                if row_idx == 0:
                    cell_bg = palette['gate_color']
                    cell_fg = palette['background_3']
                    font_weight = 'bold'
                    font_size = max(14, int(self.window_width / 110))  # INCREASED font size even more
                else:
                    # Data row styling - FIXED: Default styling for all data rows
                    cell_bg = palette['background_2']
                    cell_fg = palette['explanation_text_color']
                    font_weight = 'normal'
                    font_size = max(13, int(self.window_width / 120))  # INCREASED font size even more

                # Create cell with EVEN BIGGER SIZE for better visibility
                cell = tk.Label(table_container, text=cell_data,
                            font=('Arial', font_size, font_weight),
                            fg=cell_fg, bg=cell_bg,
                            width=7, height=1, relief=tk.RAISED, bd=2)  # INCREASED width from 8 to 10, height from 2 to 3, border from 1 to 2
                cell.grid(row=row_idx, column=col_idx, padx=3, pady=3)  # INCREASED padding from 2 to 3


    def show_qubit_explanation(self):
        """Step 3 - Enter the qubit"""
        # Clear window
        for widget in self.window.winfo_children():
            widget.destroy()

        # Main container
        main_frame = tk.Frame(self.window, bg=palette['background'])
        main_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Title
        title = tk.Label(main_frame, text="Step 3 — Enter the qubit",
                        font=('Arial', max(24, int(self.window_width / 60)), 'bold'),
                        fg=palette['main_title_color'], bg=palette['background'])
        title.place(relx=0.5, rely=0.08, anchor='center')

        # Explanation
        explanation = """Now comes the quantum bit, or qubit.
    It's like a bit, but… it follows the rules of quantum physics, which are very different from the everyday world.

    The magic property of a qubit is superposition:

    Instead of being just 0 or just 1, a qubit can be in a combination of 0 and 1 at the same time.

    This is revolutionary because it allows quantum computers to process multiple possibilities simultaneously,
    making them exponentially more powerful for certain problems than classical computers."""

        text_label = tk.Label(main_frame, text=explanation,
                            font=('Arial', max(14, int(self.window_width / 100))),
                            fg=palette['explanation_text_color'], bg=palette['background'],
                            wraplength=int(self.window_width * 0.7), justify=tk.CENTER)
        text_label.place(relx=0.5, rely=0.28, anchor='center')

        # Analogy - MOVED UP AND INCREASED SIZE
        analogy_text = """Analogy: Imagine our coin spinning in the air instead of lying flat.
    While spinning, it's kind of both heads and tails until you catch it and look."""

        analogy_label = tk.Label(main_frame, text=analogy_text,
                                font=('Arial', max(14, int(self.window_width / 100)), 'italic'),  # INCREASED from 12 to 14
                                fg=palette['gate_color'], bg=palette['background'],
                                wraplength=int(self.window_width * 0.8), justify=tk.CENTER)
        analogy_label.place(relx=0.5, rely=0.45, anchor='center')  # MOVED UP from 0.48 to 0.45

        # Spinning coin animation area - CENTERED
        animation_frame = tk.Frame(main_frame, bg=palette['background_2'], relief=tk.RAISED, bd=2)
        animation_frame.place(relx=0.05, rely=0.55, relwidth=0.6, relheight=0.25)  # Moved left and reduced width

        self.create_spinning_coin_demo(animation_frame)

        # State display box - MOVED TO THE RIGHT of demo box
        state_frame = tk.Frame(main_frame, bg=palette['background_2'], relief=tk.RAISED, bd=2)
        state_frame.place(relx=0.7, rely=0.55, relwidth=0.25, relheight=0.25)  # Right side box

        state_title = tk.Label(state_frame, text="Current State",
                            font=('Arial', max(14, int(self.window_width / 100)), 'bold'),
                            fg=palette['main_title_color'], bg=palette['background_2'])
        state_title.place(relx=0.5, rely=0.15, anchor='center')

        # State label - MOVED to separate box
        self.coin_label = tk.Label(state_frame, text="State: Heads (|0⟩)",
                                font=('Arial', max(12, int(self.window_width / 120)), 'bold'),
                                fg=palette['explanation_text_color'], bg=palette['background_2'],
                                wraplength=200, justify=tk.CENTER)
        self.coin_label.place(relx=0.5, rely=0.6, anchor='center')

        # Navigation buttons using canvas for macOS compatibility
        # Back button
        back_canvas = tk.Canvas(main_frame, width=140, height=60,
                            bg=palette['background_2'], highlightthickness=0, relief=tk.FLAT, bd=0)
        back_canvas.place(relx=0.25, rely=0.92, anchor='center')

        back_rect_id = back_canvas.create_rectangle(2, 2, 137, 58,
                                                fill=palette['background_2'], outline=palette['background_2'], width=0)
        back_text_id = back_canvas.create_text(60, 30, text="← Back",
                                            font=('Arial', max(12, int(self.window_width / 120)), 'bold'),
                                            fill=palette['explanation_text_color'])

        back_canvas.bind("<Button-1>", lambda e: self.prev_intro_step())
        back_canvas.bind("<Enter>", lambda e: (back_canvas.itemconfig(back_rect_id, fill=palette['button_hover_background']),
                                            back_canvas.itemconfig(back_text_id, fill=palette['button_hover_text_color'])))
        back_canvas.bind("<Leave>", lambda e: (back_canvas.itemconfig(back_rect_id, fill=palette['background_2']),
                                            back_canvas.itemconfig(back_text_id, fill=palette['explanation_text_color'])))
        back_canvas.configure(cursor='hand2')

        # Next button - FIXED: Changed to call next_intro_step instead of start_gates_tutorial
        next_canvas = tk.Canvas(main_frame, width=360, height=60,
                            bg=palette['gate_color'], highlightthickness=0, relief=tk.FLAT, bd=0)
        next_canvas.place(relx=0.75, rely=0.92, anchor='center')

        next_rect_id = next_canvas.create_rectangle(2, 2, 358, 58,
                                                fill=palette['gate_color'], outline=palette['gate_color'], width=0)
        next_text_id = next_canvas.create_text(180, 30, text="Next: Learn Quantum Notation →",  # Updated text
                                            font=('Arial', max(12, int(self.window_width / 120)), 'bold'),
                                            fill=palette['background_3'])

        # FIXED: Changed from start_gates_tutorial to next_intro_step
        next_canvas.bind("<Button-1>", lambda e: self.next_intro_step())
        next_canvas.bind("<Enter>", lambda e: (next_canvas.itemconfig(next_rect_id, fill=palette['button_hover_background']),
                                            next_canvas.itemconfig(next_text_id, fill=palette['button_hover_text_color'])))
        next_canvas.bind("<Leave>", lambda e: (next_canvas.itemconfig(next_rect_id, fill=palette['gate_color']),
                                            next_canvas.itemconfig(next_text_id, fill=palette['background_3'])))
        next_canvas.configure(cursor='hand2')


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

        # Spin button - INCREASED SIZE
        spin_canvas = tk.Canvas(parent, width=280, height=50,  # INCREASED from 220x40 to 300x60
                            bg=palette['gate_color'], highlightthickness=0, relief=tk.FLAT, bd=0)
        spin_canvas.place(relx=0.7, rely=0.4, anchor='center')

        spin_rect_id = spin_canvas.create_rectangle(2, 2, 258, 48,  # UPDATED coordinates
                                                fill=palette['gate_color'], outline=palette['gate_color'], width=0)
        spin_text_id = spin_canvas.create_text(140, 25, text="Spin Coin (Superposition)",  # UPDATED center coordinates
                                            font=('Arial', max(12, int(self.window_width / 120)), 'bold'),  # INCREASED font size from 11 to 16
                                            fill=palette['background_3'])

        spin_canvas.bind("<Button-1>", lambda e: self.spin_coin())
        spin_canvas.bind("<Enter>", lambda e: (spin_canvas.itemconfig(spin_rect_id, fill=palette['button_hover_background']),
                                            spin_canvas.itemconfig(spin_text_id, fill=palette['button_hover_text_color'])))
        spin_canvas.bind("<Leave>", lambda e: (spin_canvas.itemconfig(spin_rect_id, fill=palette['gate_color']),
                                            spin_canvas.itemconfig(spin_text_id, fill=palette['background_3'])))
        spin_canvas.configure(cursor='hand2')

        # Measure button
        measure_canvas = tk.Canvas(parent, width=280, height=50,  # INCREASED from 180x40 to 260x60
                                bg=palette['gate_color'], highlightthickness=0, relief=tk.FLAT, bd=0)
        measure_canvas.place(relx=0.7, rely=0.6, anchor='center')

        measure_rect_id = measure_canvas.create_rectangle(2, 2, 258, 48,  # UPDATED coordinates
                                                        fill=palette['gate_color'], outline=palette['gate_color'], width=0)
        measure_text_id = measure_canvas.create_text(140, 25, text="Measure (Collapse)",
                                                    font=('Arial', max(12, int(self.window_width / 120)), 'bold'),
                                                    fill=palette['background_3'])

        measure_canvas.bind("<Button-1>", lambda e: self.measure_coin())
        measure_canvas.bind("<Enter>", lambda e: (measure_canvas.itemconfig(measure_rect_id, fill=palette['button_hover_background']),
                                                measure_canvas.itemconfig(measure_text_id, fill=palette['button_hover_text_color'])))
        measure_canvas.bind("<Leave>", lambda e: (measure_canvas.itemconfig(measure_rect_id, fill=palette['gate_color']),
                                                measure_canvas.itemconfig(measure_text_id, fill=palette['background_3'])))
        measure_canvas.configure(cursor='hand2')


    def draw_coin(self):
        """Draw the coin on canvas"""
        self.coin_canvas.delete("all")

        # Coin circle
        if self.coin_spinning:
            # Draw spinning coin (ellipse to show rotation)
            self.coin_canvas.create_oval(25, 50, 125, 100,
                                        fill=palette['gate_color'], outline=palette['background_3'], width=3)
            self.coin_canvas.create_text(75, 75, text="?",
                                        font=('Arial', 24, 'bold'), fill=palette['background_3'])
        else:
            # Draw static coin
            color = palette['gate_color'] if self.coin_state == "H" else palette['gate_color']
            self.coin_canvas.create_oval(25, 25, 125, 125,
                                        fill=color, outline=palette['background_3'], width=3)
            self.coin_canvas.create_text(75, 75, text=self.coin_state,
                                        font=('Arial', 32, 'bold'), fill=palette['background_3'])


    def spin_coin(self):
        """Start spinning animation (superposition)"""
        if not self.coin_spinning:
            self.coin_spinning = True
            self.coin_label.configure(text="State: Superposition")
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
            state_text = "Heads (0)" if self.coin_state == "H" else "Tails (1)"
            self.coin_label.configure(text=f"State: {state_text}")

            self.draw_coin()
            self.play_sound('success')


    def animate_spin(self):
        """Animate the spinning coin"""
        if self.coin_spinning:
            self.draw_coin()
            # Continue animation
            self.animation_id = self.window.after(200, self.animate_spin)


    def show_quantum_notation_explanation(self):
        """Step 4 - Learn Quantum Notations"""
        # Clear window
        for widget in self.window.winfo_children():
            widget.destroy()

        # Main container
        main_frame = tk.Frame(self.window, bg=palette['background'])
        main_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Title
        title = tk.Label(main_frame, text="Step 4 — Learn Quantum Notations",
                        font=('Arial', max(24, int(self.window_width / 60)), 'bold'),
                        fg=palette['main_title_color'], bg=palette['background'])
        title.place(relx=0.5, rely=0.08, anchor='center')

        # Explanation
        explanation = """Before diving into quantum gates, let's understand the mathematical language of quantum computing.

    Quantum states are written using a special notation called "Dirac notation" or "bra-ket notation."

    This notation helps us describe the quantum states precisely and understand what quantum gates do."""

        text_label = tk.Label(main_frame, text=explanation,
                            font=('Arial', max(14, int(self.window_width / 100))),
                            fg=palette['explanation_text_color'], bg=palette['background'],
                            wraplength=int(self.window_width * 0.7), justify=tk.CENTER)
        text_label.place(relx=0.5, rely=0.25, anchor='center')

        # Interactive notation demo area
        demo_frame = tk.Frame(main_frame, bg=palette['background_2'], relief=tk.RAISED, bd=2)
        demo_frame.place(relx=0.1, rely=0.4, relwidth=0.8, relheight=0.4)

        self.create_notation_demo(demo_frame)

        # Navigation buttons using canvas for macOS compatibility
        # Back button
        back_canvas = tk.Canvas(main_frame, width=140, height=60,
                            bg=palette['background_2'], highlightthickness=0, relief=tk.FLAT, bd=0)
        back_canvas.place(relx=0.25, rely=0.92, anchor='center')

        back_rect_id = back_canvas.create_rectangle(2, 2, 137, 58,
                                                fill=palette['background_2'], outline=palette['background_2'], width=0)
        back_text_id = back_canvas.create_text(60, 30, text="← Back",
                                            font=('Arial', max(12, int(self.window_width / 120)), 'bold'),
                                            fill=palette['explanation_text_color'])

        back_canvas.bind("<Button-1>", lambda e: self.prev_intro_step())
        back_canvas.bind("<Enter>", lambda e: (back_canvas.itemconfig(back_rect_id, fill=palette['button_hover_background']),
                                            back_canvas.itemconfig(back_text_id, fill=palette['button_hover_text_color'])))
        back_canvas.bind("<Leave>", lambda e: (back_canvas.itemconfig(back_rect_id, fill=palette['background_2']),
                                            back_canvas.itemconfig(back_text_id, fill=palette['explanation_text_color'])))
        back_canvas.configure(cursor='hand2')

        # Next button
        next_canvas = tk.Canvas(main_frame, width=320, height=60,
                            bg=palette['gate_color'], highlightthickness=0, relief=tk.FLAT, bd=0)
        next_canvas.place(relx=0.75, rely=0.92, anchor='center')

        next_rect_id = next_canvas.create_rectangle(2, 2, 318, 58,
                                                fill=palette['gate_color'], outline=palette['gate_color'], width=0)
        next_text_id = next_canvas.create_text(160, 30, text="Next: Start Learning Gates →",
                                            font=('Arial', max(12, int(self.window_width / 120)), 'bold'),
                                            fill=palette['background_3'])

        next_canvas.bind("<Button-1>", lambda e: self.start_gates_tutorial())
        next_canvas.bind("<Enter>", lambda e: (next_canvas.itemconfig(next_rect_id, fill=palette['button_hover_background']),
                                            next_canvas.itemconfig(next_text_id, fill=palette['button_hover_text_color'])))
        next_canvas.bind("<Leave>", lambda e: (next_canvas.itemconfig(next_rect_id, fill=palette['gate_color']),
                                            next_canvas.itemconfig(next_text_id, fill=palette['background_3'])))
        next_canvas.configure(cursor='hand2')


    def create_notation_demo(self, parent):
        """Create interactive quantum notation demonstration"""
        demo_title = tk.Label(parent, text="Interactive Quantum Notation Guide",
                            font=('Arial', max(16, int(self.window_width / 80)), 'bold'),
                            fg=palette['main_title_color'], bg=palette['background_2'])
        demo_title.place(relx=0.5, rely=0.08, anchor='center')

        # Notation sections layout
        self.current_notation = 0  # Track current section
        self.notation_sections = [
            {
                'title': 'Basic States: |0⟩ and |1⟩',
                'content': '|0⟩ represents the "ground state" or classical bit 0\n|1⟩ represents the "excited state" or classical bit 1\n\nThink of them as the two definite positions our quantum coin can be in.',
                'visual': '0',
                'visual_desc': 'Classical bit 0 = |0⟩'
            },
            {
                'title': 'Superposition States: |+⟩ and |-⟩',
                'content': '|+⟩ = (|0⟩ + |1⟩)/√2  →  Equal mix of 0 and 1\n|-⟩ = (|0⟩ - |1⟩)/√2  →  Equal mix with opposite phase\n\nThese represent our spinning coin - both states at once!',
                'visual': '+',
                'visual_desc': 'Superposition = |+⟩'
            },
            {
                'title': 'Mathematical Meaning',
                'content': 'The brackets |⟩ are called "kets"\nThe symbols inside describe the quantum state\nThe √2 ensures probabilities add up to 1\n\nThis notation lets us do precise quantum math!',
                'visual': '|ψ⟩',
                'visual_desc': 'General quantum state'
            },
            {
                'title': 'Measurement Results',
                'content': 'When we measure |0⟩ → always get 0\nWhen we measure |1⟩ → always get 1\nWhen we measure |+⟩ → get 0 or 1 with 50% chance each\n\nSuperposition collapses to definite values!',
                'visual': '?→0/1',
                'visual_desc': 'Measurement collapses'
            }
        ]

        # Current section display
        self.section_frame = tk.Frame(parent, bg=palette['background_2'])
        self.section_frame.place(relx=0.05, rely=0.2, relwidth=0.6, relheight=0.65)

        # Visual representation area
        self.visual_frame = tk.Frame(parent, bg=palette['background_3'], relief=tk.RAISED, bd=2)
        self.visual_frame.place(relx=0.7, rely=0.2, relwidth=0.25, relheight=0.65)

        # Navigation controls
        self.nav_frame = tk.Frame(parent, bg=palette['background_2'])
        self.nav_frame.place(relx=0.05, rely=0.88, relwidth=0.9, relheight=0.1)

        # Previous button
        prev_canvas = tk.Canvas(self.nav_frame, width=140, height=50,
                            bg=palette['gate_color'], highlightthickness=0, relief=tk.FLAT, bd=0)
        prev_canvas.place(relx=0.2, rely=0.5, anchor='center')

        prev_rect_id = prev_canvas.create_rectangle(2, 2, 138, 48,
                                                fill=palette['gate_color'], outline=palette['gate_color'], width=0)
        prev_text_id = prev_canvas.create_text(70, 25, text="← Previous",
                                            font=('Arial', max(12, int(self.window_width / 120)), 'bold'),
                                            fill=palette['background_3'])

        prev_canvas.bind("<Button-1>", lambda e: self.prev_notation())
        prev_canvas.bind("<Enter>", lambda e: (prev_canvas.itemconfig(prev_rect_id, fill=palette['button_hover_background']),
                                            prev_canvas.itemconfig(prev_text_id, fill=palette['button_hover_text_color'])))
        prev_canvas.bind("<Leave>", lambda e: (prev_canvas.itemconfig(prev_rect_id, fill=palette['gate_color']),
                                            prev_canvas.itemconfig(prev_text_id, fill=palette['background_3'])))
        prev_canvas.configure(cursor='hand2')

        # Next button
        next_canvas = tk.Canvas(self.nav_frame, width=120, height=50,
                            bg=palette['gate_color'], highlightthickness=0, relief=tk.FLAT, bd=0)
        next_canvas.place(relx=0.8, rely=0.5, anchor='center')

        next_rect_id = next_canvas.create_rectangle(2, 2, 118, 48,
                                                fill=palette['gate_color'], outline=palette['gate_color'], width=0)
        next_text_id = next_canvas.create_text(60, 25, text="Next →",
                                            font=('Arial', max(12, int(self.window_width / 120)), 'bold'),
                                            fill=palette['background_3'])

        next_canvas.bind("<Button-1>", lambda e: self.next_notation())
        next_canvas.bind("<Enter>", lambda e: (next_canvas.itemconfig(next_rect_id, fill=palette['button_hover_background']),
                                            next_canvas.itemconfig(next_text_id, fill=palette['button_hover_text_color'])))
        next_canvas.bind("<Leave>", lambda e: (next_canvas.itemconfig(next_rect_id, fill=palette['gate_color']),
                                            next_canvas.itemconfig(next_text_id, fill=palette['background_3'])))
        next_canvas.configure(cursor='hand2')

        # Progress indicator
        self.progress_label = tk.Label(self.nav_frame, text="",
                                    font=('Arial', max(10, int(self.window_width / 150))),
                                    fg=palette['explanation_text_color'], bg=palette['background_2'])
        self.progress_label.place(relx=0.5, rely=0.5, anchor='center')

        # Initialize display
        self.update_notation_display()


    def prev_notation(self):
        """Go to previous notation section"""
        if self.current_notation > 0:
            self.current_notation -= 1
            self.update_notation_display()
            self.play_sound('button_click')


    def next_notation(self):
        """Go to next notation section"""
        if self.current_notation < len(self.notation_sections) - 1:
            self.current_notation += 1
            self.update_notation_display()
            self.play_sound('button_click')


    def update_notation_display(self):
        """Update the notation display with current section"""
        section = self.notation_sections[self.current_notation]

        # Clear section frame
        for widget in self.section_frame.winfo_children():
            widget.destroy()

        # Clear visual frame
        for widget in self.visual_frame.winfo_children():
            widget.destroy()

        # Section title
        title_label = tk.Label(self.section_frame, text=section['title'],
                            font=('Arial', max(16, int(self.window_width / 90)), 'bold'),
                            fg=palette['main_title_color'], bg=palette['background_2'])
        title_label.place(relx=0.5, rely=0.1, anchor='center')

        # Section content
        content_label = tk.Label(self.section_frame, text=section['content'],
                            font=('Arial', max(12, int(self.window_width / 120))),
                            fg=palette['explanation_text_color'], bg=palette['background_2'],
                            wraplength=int(self.window_width * 0.45), justify=tk.LEFT)
        content_label.place(relx=0.05, rely=0.25, anchor='nw')

        # Visual representation
        visual_title = tk.Label(self.visual_frame, text="Visual:",
                            font=('Arial', max(12, int(self.window_width / 120)), 'bold'),
                            fg=palette['main_title_color'], bg=palette['background_3'])
        visual_title.place(relx=0.5, rely=0.1, anchor='center')

        # Large visual symbol
        visual_display = tk.Label(self.visual_frame, text=section['visual'],
                                font=('Arial', max(48, int(self.window_width / 40)), 'bold'),
                                fg=palette['gate_color'], bg=palette['background_3'])
        visual_display.place(relx=0.5, rely=0.4, anchor='center')

        # Visual description
        visual_desc = tk.Label(self.visual_frame, text=section['visual_desc'],
                            font=('Arial', max(10, int(self.window_width / 150))),
                            fg=palette['explanation_text_color'], bg=palette['background_3'],
                            wraplength=int(self.window_width * 0.2), justify=tk.CENTER)
        visual_desc.place(relx=0.5, rely=0.75, anchor='center')

        # Update progress indicator
        self.progress_label.configure(text=f"{self.current_notation + 1} of {len(self.notation_sections)}")


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
                'success': get_resource_path('resources/sounds/correct.wav'),
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

        gates_title = tk.Label(gates_frame, text="Interactive Gate Tutorials",
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
        title_label = tk.Label(header_frame, text="Quantum Gates Tutorial",
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
            # Main Menu button - moved to where help button was
            button_width = max(120, int(self.window_width / 12))
            button_height = max(35, int(self.window_height / 25))

            main_menu_canvas = tk.Canvas(header_frame,
                                    width=button_width,
                                    height=button_height,
                                    bg=palette['gate_color'],
                                    highlightthickness=0,
                                    bd=0)
            main_menu_canvas.place(relx=1, rely=0.5, anchor='e')

            # Draw button background
            menu_rect_id = main_menu_canvas.create_rectangle(2, 2, button_width-2, button_height-2,
                                            fill=palette['gate_color'],
                                            outline="#2b3340", width=1,
                                            tags="menu_bg")

            # Add text to button
            menu_text_id = main_menu_canvas.create_text(button_width//2, button_height//2,
                                    text="Main Menu",
                                    font=('Arial', max(10, int(self.window_width / 150)), 'bold'),
                                    fill=palette['background_3'],
                                    tags="menu_text")

            # Bind click events
            main_menu_canvas.bind("<Button-1>", lambda e: self.return_to_main_menu())
            main_menu_canvas.bind("<Enter>", lambda e: (main_menu_canvas.itemconfig(menu_rect_id, fill=palette['button_hover_background']),
                                                    main_menu_canvas.itemconfig(menu_text_id, fill=palette['button_hover_text_color']),
                                                    main_menu_canvas.configure(cursor="hand2")))
            main_menu_canvas.bind("<Leave>", lambda e: (main_menu_canvas.itemconfig(menu_rect_id, fill=palette['gate_color']),
                                                    main_menu_canvas.itemconfig(menu_text_id, fill=palette['background_3']),
                                                    main_menu_canvas.configure(cursor="")))

        else:
            # Close Tutorial button
            close_canvas = tk.Canvas(header_frame, width=160, height=40,
                                bg=palette['gate_color'], highlightthickness=0, relief=tk.FLAT, bd=0)
            close_canvas.place(relx=1, rely=0.5, anchor='e')

            close_rect_id = close_canvas.create_rectangle(2, 2, 158, 38,
                                                        fill=palette['gate_color'], outline=palette['gate_color'], width=0)
            close_text_id = close_canvas.create_text(80, 20, text="Close Tutorial",
                                                    font=('Arial', max(10, int(self.window_width / 150)), 'bold'),
                                                    fill=palette['background_3'])

            close_canvas.bind("<Button-1>", lambda e: self.window.destroy())
            close_canvas.bind("<Enter>", lambda e: (close_canvas.itemconfig(close_rect_id, fill=palette['button_hover_background']),
                                                close_canvas.itemconfig(close_text_id, fill=palette['button_hover_text_color'])))
            close_canvas.bind("<Leave>", lambda e: (close_canvas.itemconfig(close_rect_id, fill=palette['gate_color']),
                                                close_canvas.itemconfig(close_text_id, fill=palette['background_3'])))
            close_canvas.configure(cursor='hand2')


    def return_to_main_menu(self):
        """Return to main menu with confirmation dialog"""
        self.play_sound('button_click')

        # Create custom confirmation dialog without decorations
        dialog = tk.Toplevel(self.window)
        dialog.title("Return to Main Menu")
        dialog.overrideredirect(True)  # Remove window decorations
        dialog.configure(bg=palette['background'])
        dialog.transient(self.window)

        # Make dialog 50% bigger for touch screens (matching puzzle mode)
        dialog_width = 900
        dialog_height = 400
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

        # Main container with border (matching puzzle mode style)
        main_frame = tk.Frame(dialog, bg=palette['background_2'], relief=tk.RAISED, bd=3)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Title - bigger text for touch screens (matching puzzle mode)
        title_label = tk.Label(main_frame, text="Return to Main Menu",
                            font=('Arial', 20, 'bold'),
                            fg=palette['main_title_color'], bg=palette['background_2'])
        title_label.pack(pady=(20, 15))

        # Message - bigger text and more padding (matching puzzle mode)
        message_label = tk.Label(main_frame,
                            text="Are you sure you want to return to the main menu?\nYour tutorial progress will be saved.",
                            font=('Arial', 16),
                            fg=palette['main_subtitle_color'], bg=palette['background_2'],
                            justify=tk.CENTER)
        message_label.pack(pady=20)

        # Button frame (matching puzzle mode)
        button_frame = tk.Frame(main_frame, bg=palette['background_2'])
        button_frame.pack(pady=(20, 10))

        def confirm_return():
            result[0] = True
            dialog.destroy()

        def cancel_return():
            result[0] = False
            dialog.destroy()

        # Make buttons bigger for touch screens (matching puzzle mode size)
        yes_canvas = self.create_canvas_dialog_button(
            button_frame, "✓ Yes, Return",
            confirm_return,
            palette['return_to_gamemode_button_background'],  # Use tutorial H color
            palette['return_to_gamemode_button_text_color'],
            width=270, height=90, font_size=24
        )
        yes_canvas.pack(side=tk.LEFT, padx=30)

        no_canvas = self.create_canvas_dialog_button(
            button_frame, "✗ No, Stay",
            cancel_return,
            palette['close_gamemode_button_background'],
            palette['close_gamemode_button_hover_text_color'],
            width=270, height=90, font_size=24
        )
        no_canvas.pack(side=tk.LEFT, padx=30)

        # Reset Tutorial Progress Button (matching puzzle mode spacing)
        reset_frame = tk.Frame(main_frame, bg=palette['background_2'])
        reset_frame.pack(pady=(25, 15))  # Same spacing as puzzle mode

        # Handle ESC key to cancel (matching puzzle mode)
        dialog.bind('<Escape>', lambda e: cancel_return())

        # Wait for dialog to close and get result
        dialog.wait_window()

        # Process result (same logic as before)
        if result[0]:
            # Save the progress before exiting
            self.save_progress()
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

            locked_btn = tk.Label(gate_container, text="Locked",
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
        self.window.title(f" {gate_info['name']} Tutorial")

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
                'gate_place': get_resource_path('resources/sounds/add_gate.wav'),
                'success': get_resource_path('resources/sounds/correct.wav'),
                'error': get_resource_path('resources/sounds/wrong.wav'),
                'clear': get_resource_path('resources/sounds/clear.wav'),
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
        """Create simplified header for gate tutorial"""
        header_frame = tk.Frame(parent, bg=palette['main_container_background'])
        header_frame.place(relx=0.05, rely=0.02, relwidth=0.9, relheight=0.12)

        # Gate tutorial title
        title_label = tk.Label(header_frame, text=f"{self.gate_info['name']} Tutorial",
                            font=('Arial', max(20, int(self.window_width / 80)), 'bold'),
                            fg=palette['main_title_color'], bg=palette['main_container_background'])
        title_label.place(relx=0, rely=0.3, anchor='w')

        # Subtitle
        subtitle_label = tk.Label(header_frame, text="Interactive quantum gate learning",
                                font=('Arial', max(11, int(self.window_width / 140)), 'italic'),
                                fg=palette['main_subtitle_color'], bg=palette['main_container_background'])
        subtitle_label.place(relx=0, rely=0.7, anchor='w')

        # FIXED: Close button with correct colors
        close_canvas = tk.Canvas(header_frame, width=120, height=40,
                            bg=palette['gate_color'], highlightthickness=0, relief=tk.FLAT, bd=0)
        close_canvas.place(relx=1, rely=0.5, anchor='e')

        close_rect_id = close_canvas.create_rectangle(2, 2, 118, 38,
                                                    fill=palette['gate_color'],
                                                    outline=palette['gate_color'], width=0)
        close_text_id = close_canvas.create_text(60, 20, text="← Back",
                                            font=('Arial', max(12, int(self.window_width / 150)), 'bold'),
                                            fill=palette['background_3'])  # FIXED: Use background_3

        close_canvas.bind("<Button-1>", lambda e: self.close_tutorial())
        close_canvas.bind("<Enter>", lambda e: (close_canvas.itemconfig(close_rect_id, fill=palette['button_hover_background']),
                                            close_canvas.itemconfig(close_text_id, fill=palette['button_hover_text_color'])))
        close_canvas.bind("<Leave>", lambda e: (close_canvas.itemconfig(close_rect_id, fill=palette['gate_color']),
                                            close_canvas.itemconfig(close_text_id, fill=palette['background_3'])))
        close_canvas.configure(cursor='hand2')


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

        desc_title = tk.Label(desc_frame, text="Gate Description",
                            font=('Arial', max(16, int(self.window_width / 90)), 'bold'),  # INCREASED from 14 to 16
                            fg=palette['description_title_text_color'], bg=palette['main_container_background'])
        desc_title.place(relx=0.5, rely=0.15, anchor='center')

        desc_label = tk.Label(desc_frame, text=self.gate_info['description'],
                            font=('Arial', max(14, int(self.window_width / 100))),  # INCREASED from 12 to 14
                            fg=palette['description_text_color'], bg=palette['main_container_background'],
                            wraplength=int(self.window_width * 0.8), justify=tk.CENTER)
        desc_label.place(relx=0.5, rely=0.5, anchor='center')

        example_label = tk.Label(desc_frame, text=f"Example: {self.gate_info['example']}",
                                font=('Arial', max(13, int(self.window_width / 110)), 'italic'),  # INCREASED from 11 to 13
                                fg=self.gate_info['color'], bg=palette['main_container_background'])
        example_label.place(relx=0.5, rely=0.8, anchor='center')


    def setup_circuit_section(self, parent):
        """Setup circuit visualization section using relative positioning"""
        circuit_frame = tk.Frame(parent, bg=palette['main_container_background'], relief=tk.RAISED, bd=2)
        circuit_frame.place(relx=0, rely=0.25, relwidth=1, relheight=0.3)

        circuit_title = tk.Label(circuit_frame, text="Interactive Circuit Visualization",
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
        controls_title = tk.Label(parent, text="Gate Controls",
                                font=('Arial', max(14, int(self.window_width / 100)), 'bold'),
                                fg=palette['controls_title_text_color'], bg=palette['main_container_background'])
        controls_title.place(relx=0.5, rely=0.1, anchor='center')

        # Button container
        button_container = tk.Frame(parent, bg=palette['main_container_background'])
        button_container.place(relx=0.15, rely=0.25, relwidth=0.7, relheight=0.65)

        # Gate placement button
        self.gate_canvas = tk.Canvas(button_container, highlightthickness=0, bd=0)
        self.gate_canvas.place(relx=0.5, rely=0.2, anchor='center', relwidth=0.3, relheight=0.3)

        # Draw gate button (same as before)
        def draw_gate_button(event=None):
            self.gate_canvas.delete("all")
            width = self.gate_canvas.winfo_width()
            height = self.gate_canvas.winfo_height()
            if width > 1 and height > 1:
                bg_color = self.gate_info['color']
                text_color = palette['background_3']
                self.gate_canvas.create_rectangle(0, 0, width, height, fill=bg_color, outline='#2b3340', width=2, tags="bg")
                self.gate_canvas.create_text(width//2, height//2, text=f"Add {self.gate} Gate",
                                        font=('Arial', max(12, int(self.window_width / 120)), 'bold'),
                                        fill=text_color, tags="text")

        # Bind configure event and initial draw
        self.gate_canvas.bind('<Configure>', draw_gate_button)
        self.gate_canvas.after(10, draw_gate_button)

        def on_gate_click(event):
            self.add_gate()

        def on_gate_enter(event):
            self.gate_canvas.delete("bg")
            width = self.gate_canvas.winfo_width()
            height = self.gate_canvas.winfo_height()
            if width > 1 and height > 1:
                self.gate_canvas.create_rectangle(0, 0, width, height, fill=palette['button_hover_background'], outline='#2b3340', width=2, tags="bg")
            self.gate_canvas.configure(cursor='hand2')
            self.gate_canvas.tag_lower("bg")

        def on_gate_leave(event):
            self.gate_canvas.delete("bg")
            width = self.gate_canvas.winfo_width()
            height = self.gate_canvas.winfo_height()
            if width > 1 and height > 1:
                self.gate_canvas.create_rectangle(0, 0, width, height, fill=self.gate_info['color'], outline='#2b3340', width=2, tags="bg")
            self.gate_canvas.configure(cursor='')
            self.gate_canvas.tag_lower("bg")

        self.gate_canvas.bind("<Button-1>", on_gate_click)
        self.gate_canvas.bind("<Enter>", on_gate_enter)
        self.gate_canvas.bind("<Leave>", on_gate_leave)

        # FIXED: Run button with correct colors and positioning
        run_canvas = tk.Canvas(button_container, highlightthickness=0, bd=0)
        run_canvas.place(relx=0.5, rely=0.6, anchor='center', relwidth=0.3, relheight=0.3)  # Moved up to replace clear button

        # Draw run button
        def draw_run_button(event=None):
            run_canvas.delete("all")
            width = run_canvas.winfo_width()
            height = run_canvas.winfo_height()
            if width > 1 and height > 1:
                bg_color = palette['gate_color']  # FIXED: Use gate_color
                text_color = palette['background_3']  # FIXED: Use background_3
                run_canvas.create_rectangle(0, 0, width, height, fill=bg_color, outline='#2b3340', width=2, tags="bg")
                run_canvas.create_text(width//2, height//2, text="Run Circuit",
                                    font=('Arial', max(11, int(self.window_width / 130)), 'bold'),
                                    fill=text_color, tags="text")

        # Bind configure event and initial draw
        run_canvas.bind('<Configure>', draw_run_button)
        run_canvas.after(10, draw_run_button)

        def on_run_click(event):
            self.run_circuit()

        def on_run_enter(event):
            run_canvas.itemconfig("bg", fill=palette['button_hover_background'])  # FIXED: Use button_hover_background
            run_canvas.configure(cursor='hand2')

        def on_run_leave(event):
            run_canvas.itemconfig("bg", fill=palette['gate_color'])  # FIXED: Use gate_color
            run_canvas.configure(cursor='')

        run_canvas.bind("<Button-1>", on_run_click)
        run_canvas.bind("<Enter>", on_run_enter)
        run_canvas.bind("<Leave>", on_run_leave)


    def setup_results_area(self, parent):
        """Setup results display area using relative positioning"""
        results_title = tk.Label(parent, text="Quantum State Analysis",
                                font=('Arial', max(16, int(self.window_width / 90)), 'bold'),  # INCREASED from 14 to 16
                                fg=palette['results_title_text_color'], bg=palette['main_container_background'])
        results_title.place(relx=0.5, rely=0.06, anchor='center')  # MOVED UP from 0.08 to 0.06

        # Results container with styling - MADE BIGGER
        results_container = tk.Frame(parent, bg=palette['background'], relief=tk.SUNKEN, bd=3)
        results_container.place(relx=0.05, rely=0.14, relwidth=0.9, relheight=0.82)  # INCREASED height from 0.75 to 0.82

        # Results text with scrollbar
        text_frame = tk.Frame(results_container, bg=palette['background'])
        text_frame.place(relx=0.02, rely=0.02, relwidth=0.96, relheight=0.96)

        self.results_text = tk.Text(text_frame, font=('Consolas', max(11, int(self.window_width / 160))),  # INCREASED from 9 to 11
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
        qubit_spacing = max(80, self.canvas_height // (num_qubits + 1))  # INCREASED spacing from 60 to 80

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

            # Enhanced qubit label with background - MADE MORE VISIBLE
            label_bg = self.canvas.create_rectangle(wire_start - 70, y_pos - 20,  # INCREASED size
                                                wire_start - 10, y_pos + 20,
                                                fill=palette['background_2'], outline=color, width=3)

            self.canvas.create_text(wire_start - 40, y_pos,
                                text=f"q{qubit}", fill=palette['main_title_color'],  # CHANGED to more visible color
                                font=('Arial', 14, 'bold'))  # INCREASED font size

        # Draw enhanced gates
        self.draw_enhanced_gates(wire_start, qubit_spacing, num_qubits)


    def draw_enhanced_gates(self, wire_start, qubit_spacing, num_qubits):
        """Draw gates with enhanced 3D styling"""
        gate_x_start = wire_start + 140  # Increased spacing from wire start
        gate_spacing = 100  # INCREASED from 80 to 100 for better visibility

        for i, gate in enumerate(self.placed_gates):
            x = gate_x_start + i * gate_spacing
            color = self.gate_info['color']

            if gate in ['CNOT', 'CZ'] and num_qubits > 1:
                # Two-qubit gates - MADE MORE VISIBLE
                control_y = qubit_spacing
                target_y = 2 * qubit_spacing

                if gate == 'CNOT':
                    # Enhanced control dot - MADE BIGGER
                    self.canvas.create_oval(x - 15, control_y - 15, x + 15, control_y + 15,  # INCREASED from 10 to 15
                                        fill=palette['background_3'], outline='')
                    self.canvas.create_oval(x - 12, control_y - 12, x + 12, control_y + 12,  # INCREASED from 8 to 12
                                        fill=palette['main_title_color'], outline=palette['background_3'], width=3)  # CHANGED colors for visibility

                    # Enhanced connection line - MADE THICKER
                    self.canvas.create_line(x, control_y, x, target_y,
                                        fill=palette['background_3'], width=6)  # INCREASED from 4 to 6
                    self.canvas.create_line(x, control_y, x, target_y,
                                        fill=palette['main_title_color'], width=4)  # INCREASED from 2 to 4

                    # Enhanced target - MADE BIGGER
                    self.canvas.create_oval(x - 30, target_y - 30, x + 30, target_y + 30,  # INCREASED from 22 to 30
                                        fill=palette['background_3'], outline='')
                    self.canvas.create_oval(x - 25, target_y - 25, x + 25, target_y + 25,  # INCREASED from 20 to 25
                                        fill='', outline=palette['main_title_color'], width=4)  # INCREASED width from 3 to 4

                    # X symbol - MADE BIGGER
                    self.canvas.create_line(x - 18, target_y - 18, x + 18, target_y + 18,  # INCREASED from 12 to 18
                                        fill=palette['main_title_color'], width=4)  # INCREASED from 3 to 4
                    self.canvas.create_line(x - 18, target_y + 18, x + 18, target_y - 18,  # INCREASED from 12 to 18
                                        fill=palette['main_title_color'], width=4)  # INCREASED from 3 to 4

                elif gate == 'CZ':
                    # Enhanced CZ gate visualization - MADE MORE VISIBLE
                    self.canvas.create_oval(x - 15, control_y - 15, x + 15, control_y + 15,  # INCREASED from 10 to 15
                                        fill=palette['background_3'], outline='')
                    self.canvas.create_oval(x - 12, control_y - 12, x + 12, control_y + 12,  # INCREASED from 8 to 12
                                        fill=palette['main_title_color'], outline=palette['background_3'], width=3)

                    self.canvas.create_line(x, control_y, x, target_y,
                                        fill=palette['background_3'], width=6)  # INCREASED from 4 to 6
                    self.canvas.create_line(x, control_y, x, target_y,
                                        fill=palette['main_title_color'], width=4)  # INCREASED from 2 to 4

                    self.canvas.create_oval(x - 15, target_y - 15, x + 15, target_y + 15,  # INCREASED from 10 to 15
                                        fill=palette['background_3'], outline='')
                    self.canvas.create_oval(x - 12, target_y - 12, x + 12, target_y + 12,  # INCREASED from 8 to 12
                                        fill=palette['main_title_color'], outline=palette['background_3'], width=3)
            else:
                # Enhanced single qubit gates
                y_pos = qubit_spacing

                # 3D shadow effect
                self.canvas.create_rectangle(x - 32, y_pos - 27, x + 32, y_pos + 27,  # INCREASED from 27, 22 to 32, 27
                                            fill=palette['background_3'], outline='')

                # Main gate with gradient effect
                self.canvas.create_rectangle(x - 30, y_pos - 25, x + 30, y_pos + 25,  # INCREASED from 25, 20 to 30, 25
                                            fill=color, outline=palette['background_3'], width=3)  # INCREASED width from 2 to 3

                # Inner highlight
                self.canvas.create_rectangle(x - 28, y_pos - 23, x + 28, y_pos + 23,  # INCREASED from 23, 18 to 28, 23
                                            fill='', outline=palette['background_3'], width=1)

                # Gate symbol with shadow
                self.canvas.create_text(x + 1, y_pos + 1, text=gate,
                                    fill=palette['background'], font=('Arial', 16, 'bold'))  # INCREASED from 14 to 16
                self.canvas.create_text(x, y_pos, text=gate,
                                    fill=palette['background_3'], font=('Arial', 18, 'bold'))  # INCREASED from 16 to 18


    def mark_completed(self):
        """Mark this gate tutorial as completed"""
        if self.completion_callback:
            self.completion_callback()


    def run_circuit(self):
        """Run the quantum circuit and show results"""
        if not self.placed_gates:
            self.results_text.configure(state=tk.NORMAL)
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "No gates placed. Add some gates first!\n")
            self.results_text.configure(state=tk.DISABLED)
            self.play_sound('error')
            return

        try:
            # Update results display
            self.results_text.configure(state=tk.NORMAL)
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "Running quantum circuit...\n\n")
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

            self.mark_completed()

        except Exception as e:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"Error: {str(e)}\n")
            self.play_sound('error')
        finally:
            self.results_text.configure(state=tk.DISABLED)


    def get_educational_message(self):
        """Get educational message based on the gate - MORE CONCISE"""
        messages = {
            'H': "Superposition created! Qubit is now both |0⟩ and |1⟩.",
            'X': "Qubit flipped! Quantum NOT gate applied.",
            'Y': "Complex rotation with X and Z plus phase applied.",
            'Z': "Phase flip applied! |1⟩ state now has negative phase.",
            'S': "90° phase rotation applied to |1⟩ state.",
            'T': "45° phase rotation - great for quantum algorithms!",
            'CNOT': "Entanglement created! Qubits are now correlated.",
            'CZ': "Conditional phase flip - another entanglement method!"
        }
        return messages.get(self.gate, "Great quantum exploration!")


    def display_results(self, state_vector, num_qubits):
        """Display the quantum state results with enhanced formatting - MORE CONCISE"""
        self.results_text.delete(1.0, tk.END)

        self.results_text.insert(tk.END, f"✓ Circuit Executed Successfully!\n\n")
        self.results_text.insert(tk.END, f"Gates: {' → '.join(self.placed_gates)} (Total: {len(self.placed_gates)})\n")  # CONDENSED
        self.results_text.insert(tk.END, "=" * 40 + "\n\n")  # SHORTENED from 50 to 40

        # More concise state vector display
        self.results_text.insert(tk.END, f"Final Quantum State:\n")
        for i, amplitude in enumerate(state_vector):
            if abs(amplitude) > 0.001:
                basis_state = f"|{i:0{num_qubits}b}⟩"
                real_part = amplitude.real
                imag_part = amplitude.imag

                if abs(imag_part) < 0.001:
                    self.results_text.insert(tk.END, f"{basis_state}: {real_part:.3f}\n")  # REDUCED precision from 4 to 3
                else:
                    self.results_text.insert(tk.END, f"{basis_state}: {real_part:.3f} + {imag_part:.3f}i\n")

        # More concise probabilities
        self.results_text.insert(tk.END, f"\nMeasurement Probabilities:\n")
        for i, amplitude in enumerate(state_vector):
            probability = abs(amplitude) ** 2
            if probability > 0.001:
                basis_state = f"|{i:0{num_qubits}b}⟩"
                self.results_text.insert(tk.END, f"{basis_state}: {probability*100:.1f}%\n")  # REMOVED redundant decimal display

        # Shorter educational insight
        self.results_text.insert(tk.END, f"\n💡 Key Insight:\n")
        self.results_text.insert(tk.END, f"{self.get_educational_message()}\n")


    def display_initial_info(self):
        """Display initial information with enhanced formatting - MORE CONCISE"""
        self.results_text.configure(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)

        self.results_text.insert(tk.END, f"{self.gate_info['name']} Tutorial\n\n")
        self.results_text.insert(tk.END, f"Description:\n{self.gate_info['description']}\n\n")
        self.results_text.insert(tk.END, f"Example: {self.gate_info['example']}\n\n")
        self.results_text.insert(tk.END, "=" * 40 + "\n\n")  # SHORTENED from 50 to 40
        self.results_text.insert(tk.END, "Quick Start:\n")
        self.results_text.insert(tk.END, "• Add Gate → Run Circuit → See Results\n")  # CONDENSED instructions
        self.results_text.insert(tk.END, "• Try multiple gates for cumulative effects\n\n")
        self.results_text.insert(tk.END, "Ready to explore quantum mechanics!\n")

        self.results_text.configure(state=tk.DISABLED)


def show_tutorial(parent, return_callback=None):
    """Show the tutorial window"""
    TutorialWindow(parent, return_callback)
