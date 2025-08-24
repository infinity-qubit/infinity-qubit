#!/usr/bin/env python3
"""
Learn Hub for Infinity Qubit
Educational resources and quantum computing concepts hub.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import webbrowser
import math
import random
import sys

sys.path.append('..')
from run import PROJECT_ROOT, get_resource_path
from q_utils import get_colors_from_file, extract_color_palette

color_file_path = get_resource_path('config/color_palette.json')
palette = extract_color_palette(get_colors_from_file(color_file_path), 'learn_hub')

class LearnHub:
    def __init__(self, root):
        self.root = root
        self.root.title("Infinity Qubit - Learn Hub")

        # Get screen dimensions for fullscreen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Make window fullscreen without title bar
        self.root.overrideredirect(True)
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        self.root.configure(bg=palette['background_2'])

        # Store dimensions for relative sizing
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.window_width = screen_width
        self.window_height = screen_height

        # Bind Escape key to exit fullscreen
        self.root.bind('<Escape>', self.exit_fullscreen)
        self.root.bind('<F11>', self.toggle_fullscreen)

        # Initialize particles for animation
        self.particles = []
        self.animation_running = False
        self.animation_id = None  # Track animation callback ID

        # Create the main interface
        self.create_learn_hub_ui()

        # Bind window resize event
        self.root.bind('<Configure>', self.on_window_resize)

        # Start background animations
        self.start_animations()

        # Make window focused
        self.root.lift()
        self.root.focus_force()

    def exit_fullscreen(self, event=None):
        """Exit fullscreen mode"""
        self.root.overrideredirect(False)
        self.root.state('normal')
        self.root.geometry("1200x800")
        
    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode"""
        is_fullscreen = self.root.overrideredirect()
        if is_fullscreen:
            self.root.overrideredirect(False)
            self.root.state('normal')
            self.root.geometry("1200x800")
        else:
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            self.root.overrideredirect(True)
            self.root.geometry(f"{screen_width}x{screen_height}+0+0")

    def start_animations(self):
        """Start background animations"""
        self.animation_running = True
        # Start circuit animation after UI is ready with a longer interval
        self.animation_id = self.root.after(500, self.animate_circuit)
        # Start subtitle animation
        self.root.after(1000, self.animate_subtitle)

    def on_window_resize(self, event):
        """Handle window resize events"""
        # Only respond to root window resize events, not child widgets
        if event.widget == self.root:
            # Cancel any pending animation
            if self.animation_id:
                self.root.after_cancel(self.animation_id)

            # Immediately redraw the circuit with new dimensions
            self.root.after_idle(self.draw_quantum_circuit)

            # Resume animation after a short delay
            self.animation_id = self.root.after(1000, self.animate_circuit)

    def create_learn_hub_ui(self):
        """Create the enhanced learn hub interface"""
        # Main container with gradient-like effect
        main_frame = tk.Frame(self.root, bg=palette['background_2'])
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Add subtle top border with relative height
        top_border = tk.Frame(main_frame, bg=palette['top_border_color'], height=int(self.screen_height * 0.003))
        top_border.pack(fill=tk.X)

        # Content frame - using relative padding
        content_frame = tk.Frame(main_frame, bg=palette['background_3'])
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Create animated header with internal padding
        self.create_animated_header(content_frame)

        # Create a container to center the notebook with relative padding
        notebook_container = tk.Frame(content_frame, bg=palette['background_3'])
        notebook_container.pack(fill=tk.BOTH, expand=True, 
                            padx=int(self.screen_width * 0.02), 
                            pady=(0, int(self.screen_height * 0.02)))

        # Create notebook for tabs - centered
        self.notebook = ttk.Notebook(notebook_container)
        self.notebook.pack(expand=True, fill=tk.BOTH)

        # Apply enhanced styling
        self.style_notebook()

        # Create tabs with enhanced design
        self.create_concepts_tab()
        self.create_gates_tab()
        self.create_algorithms_tab()
        self.create_resources_tab()

        # Enhanced footer
        self.create_enhanced_footer(content_frame)

    def create_animated_header(self, parent):
        """Create an animated quantum-themed header"""
        header_frame = tk.Frame(parent, bg=palette['background_3'])
        header_frame.pack(fill=tk.X, 
                        padx=int(self.screen_width * 0.02), 
                        pady=(int(self.screen_height * 0.02), int(self.screen_height * 0.015)))

        # Add a top navigation bar
        nav_frame = tk.Frame(header_frame, bg=palette['background_3'])
        nav_frame.pack(fill=tk.X, pady=(0, int(self.screen_height * 0.008)))

        # Back to Main Screen button - top right with relative sizing
        button_font_size = max(10, int(self.screen_width * 0.008))
        back_main_btn = tk.Button(nav_frame, text="🏠 Main Screen",
                                command=self.back_to_menu,
                                font=('Arial', button_font_size, 'bold'),
                                bg=palette['background_4'], fg=palette['main_menu_button_background'],
                                padx=int(self.screen_width * 0.012), 
                                pady=int(self.screen_height * 0.008),
                                cursor='hand2',
                                relief=tk.FLAT,
                                borderwidth=1,
                                bd=1)
        back_main_btn.pack(side=tk.RIGHT)

        # Add hover effect to top button
        def on_nav_enter(event):
            back_main_btn.configure(bg=palette['main_menu_button_background'], fg=palette['background_black'])
        def on_nav_leave(event):
            back_main_btn.configure(bg=palette['background_4'], fg=palette['main_menu_button_background'])

        back_main_btn.bind("<Enter>", on_nav_enter)
        back_main_btn.bind("<Leave>", on_nav_leave)

        # Quantum circuit animation canvas with relative height
        canvas_height = int(self.screen_height * 0.12)
        self.circuit_canvas = tk.Canvas(header_frame, height=canvas_height, bg=palette['background_3'],
                                    highlightthickness=0)
        self.circuit_canvas.pack(fill=tk.X, pady=(0, int(self.screen_height * 0.012)))

        # Draw quantum circuit after canvas is created
        self.root.after(100, self.draw_quantum_circuit)

        # Title with shadow effect and relative font size
        title_frame = tk.Frame(header_frame, bg=palette['background_3'])
        title_frame.pack()

        # Shadow title with relative font size
        title_font_size = max(24, int(self.screen_width * 0.025))
        shadow_title = tk.Label(title_frame, text="🚀 Quantum Computing Learn Hub",
                            font=('Arial', title_font_size, 'bold'),
                            fg='#003322', bg=palette['background_3'])
        shadow_title.place(x=3, y=3)

        # Main title with gradient-like effect
        main_title = tk.Label(title_frame, text="🚀 Quantum Computing Learn Hub",
                            font=('Arial', title_font_size, 'bold'),
                            fg=palette['title_color'], bg=palette['background_3'])
        main_title.pack(pady=(0, int(self.screen_height * 0.008)))

        # Enhanced subtitle with pulsing effect and relative font size
        subtitle_font_size = max(12, int(self.screen_width * 0.01))
        self.subtitle_label = tk.Label(header_frame,
                                    text="✨ Explore quantum computing concepts and resources ✨",
                                    font=('Arial', subtitle_font_size, 'italic'),
                                    fg=palette['subtitle_color'], bg=palette['background_3'])
        self.subtitle_label.pack()

        # Learning progress indicator
        self.create_learning_progress(header_frame)

    def draw_quantum_circuit(self):
        """Draw an animated quantum circuit - called only when needed"""
        if not hasattr(self, 'circuit_canvas') or not self.circuit_canvas.winfo_exists():
            return

        try:
            self.circuit_canvas.delete("all")

            # Force canvas to update its dimensions
            self.circuit_canvas.update_idletasks()
            width = self.circuit_canvas.winfo_width()
            height = self.circuit_canvas.winfo_height()

            # Use minimum dimensions if canvas isn't ready
            if width <= 1:
                width = 1150  # fallback width
            if height <= 1:
                height = 120   # fallback height

            # Draw quantum wires with glow effect
            wire_colors = [palette['quantum_wire_1'], palette['quantum_wire_2'], palette['quantum_wire_3']]
            wire_spacing = height // 4  # Adaptive spacing based on canvas height

            for i in range(3):
                y = wire_spacing + i * wire_spacing
                # Draw wire lines with decreasing thickness for glow effect
                for thickness in [6, 4, 2]:
                    color = wire_colors[i]
                    self.circuit_canvas.create_line(50, y, width-50, y,
                                                fill=color, width=thickness,
                                                tags="circuit")

            # Draw quantum gates with enhanced styling - adaptive positioning
            gate_spacing = (width - 200) // 4  # Adaptive gate spacing
            gate_info = [
                {'symbol': 'H', 'color': palette['H_color'], 'x': 100 + gate_spacing},
                {'symbol': 'X', 'color': palette['X_color'], 'x': 100 + 2 * gate_spacing},
                {'symbol': 'Z', 'color': palette['Z_color'], 'x': 100 + 3 * gate_spacing},
                {'symbol': 'CNOT', 'color': palette['CNOT_color'], 'x': 100 + 4 * gate_spacing, 'double': True}
            ]

            for gate in gate_info:
                gate['wire_spacing'] = wire_spacing  # Pass wire spacing to gate drawing
                self.draw_enhanced_gate(gate)

        except tk.TclError:
            # Canvas might be destroyed, ignore the error
            pass

    def draw_enhanced_gate(self, gate_info):
        """Draw enhanced quantum gates with 3D effect"""
        try:
            x = gate_info['x']
            color = gate_info['color']
            symbol = gate_info['symbol']
            wire_spacing = gate_info.get('wire_spacing', 30)

            if gate_info.get('double'):
                # CNOT gate - adaptive positioning
                y1 = wire_spacing  # First wire
                y2 = wire_spacing * 3  # Third wire

                # Control dot
                self.circuit_canvas.create_oval(x-8, y1-8, x+8, y1+8,
                                            fill=color, outline='white', width=2)
                # Target circle
                self.circuit_canvas.create_oval(x-15, y2-15, x+15, y2+15,
                                            fill='', outline=color, width=3)
                # Plus sign
                self.circuit_canvas.create_line(x-10, y2, x+10, y2, fill=color, width=3)
                self.circuit_canvas.create_line(x, y2-10, x, y2+10, fill=color, width=3)
                # Connection line
                self.circuit_canvas.create_line(x, y1, x, y2, fill=color, width=2)
            else:
                # Single qubit gate - adaptive positioning
                wire_index = 0 if symbol == 'H' else 1 if symbol == 'X' else 2
                y = wire_spacing + wire_index * wire_spacing

                # 3D shadow effect
                self.circuit_canvas.create_rectangle(x-17, y-12, x+17, y+12,
                                                fill=palette['background_black'], outline='')
                # Main gate
                self.circuit_canvas.create_rectangle(x-15, y-10, x+15, y+10,
                                                fill=color, outline='white', width=2)
                # Gate symbol
                self.circuit_canvas.create_text(x, y, text=symbol,
                                            fill='white', font=('Arial', 12, 'bold'))
        except tk.TclError:
            # Canvas might be destroyed, ignore the error
            pass

    def create_learning_progress(self, parent):
        """Create a visual learning progress indicator"""
        progress_frame = tk.Frame(parent, bg=palette['background_3'])
        progress_frame.pack(fill=tk.X, pady=(int(self.screen_height * 0.012), 0))

        # Title with relative font size
        progress_title_font_size = max(12, int(self.screen_width * 0.01))
        tk.Label(progress_frame, text="📈 Learning Journey",
                font=('Arial', progress_title_font_size, 'bold'),
                fg=palette['learning_journey_title_color'], bg=palette['background_3']).pack()

        # Progress steps with enhanced visuals
        steps_container = tk.Frame(progress_frame, bg=palette['background_3'])
        steps_container.pack(pady=int(self.screen_height * 0.008))

        steps = [
            ("Basics", True, "#00ff88", "🎯"),
            ("Gates", True, "#4ecdc4", "⚡"),
            ("Algorithms", False, "#666666", "🧠"),
            ("Advanced", False, "#333333", "🚀")
        ]

        for i, (step, completed, color, icon) in enumerate(steps):
            step_frame = tk.Frame(steps_container, bg=palette['background_3'])
            step_frame.pack(side=tk.LEFT, padx=int(self.screen_width * 0.012))

            # Enhanced circle with glow - relative sizing
            circle_size = int(self.screen_width * 0.025)
            canvas = tk.Canvas(step_frame, width=circle_size, height=circle_size,
                            bg=palette['background_3'], highlightthickness=0)
            canvas.pack()

            # Glow effect for completed steps
            if completed:
                canvas.create_oval(2, 2, circle_size-2, circle_size-2, fill=color, outline=color, width=3)
                canvas.create_oval(8, 8, circle_size-8, circle_size-8, fill=palette['background_3'], outline='white', width=2)
                canvas.create_text(circle_size//2, circle_size//2, text="✓", fill='white', 
                                font=('Arial', max(10, int(self.screen_width * 0.01)), 'bold'))
            else:
                canvas.create_oval(8, 8, circle_size-8, circle_size-8, fill='', outline=color, width=2)

            # Step label with icon and relative font size
            step_font_size = max(9, int(self.screen_width * 0.007))
            tk.Label(step_frame, text=f"{icon} {step}", fg=color, bg=palette['background_3'],
                    font=('Arial', step_font_size, 'bold')).pack(pady=(int(self.screen_height * 0.004), 0))

            # Connection line (except for last step)
            if i < len(steps) - 1:
                line_width = int(self.screen_width * 0.02)
                line_canvas = tk.Canvas(steps_container, width=line_width, height=5,
                                    bg=palette['background_3'], highlightthickness=0)
                line_canvas.pack(side=tk.LEFT)
                line_canvas.create_line(0, 2, line_width, 2, fill='#555555', width=2)

    def style_notebook(self):
        """Apply enhanced styling to the notebook"""
        style = ttk.Style()
        style.theme_use('clam')

        # Enhanced notebook styling - Updated for gray background
        style.configure('TNotebook',
                    background=palette['background_3'],  # Changed from #1a1a1a to #2a2a2a
                    borderwidth=0,
                    tabmargins=[2, 5, 2, 0])

        style.configure('TNotebook.Tab',
                    background=palette['background_4'],  # Slightly darker for contrast
                    foreground='#ffffff',
                    padding=[25, 15],
                    borderwidth=0,
                    font=('Arial', 11, 'bold'))

        style.map('TNotebook.Tab',
                background=[('selected', palette['tnotebook_selected_background']),
                            ('active', palette['tnotebook_active_background'])],
                foreground=[('selected', palette['background_black']),
                            ('active', palette['tnotebook_active_foreground'])])

        style.configure('TFrame', background=palette['background_3'])  # Changed from #1a1a1a to #2a2a2a

        # Center the tabs by configuring tab positioning
        style.configure('TNotebook', tabposition='n')

    def create_concepts_tab(self):
        """Create the enhanced basic concepts tab"""
        concepts_frame = ttk.Frame(self.notebook)
        self.notebook.add(concepts_frame, text="📚 Basic Concepts")

        # Main container with padding - changed to match text area background
        main_container = tk.Frame(concepts_frame, bg=palette['background_3'])  # Changed from #1a1a1a to #2a2a2a
        main_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

        # Enhanced scrollable text area
        text_frame = tk.Frame(main_container, bg=palette['background_3'], relief=tk.RAISED, bd=2)
        text_frame.pack(fill=tk.BOTH, expand=True)

        concepts_text = scrolledtext.ScrolledText(text_frame,
                                                wrap=tk.WORD,
                                                width=80, height=25,
                                                bg=palette['background_3'], fg=palette['concepts_text_color'],
                                                font=('Consolas', 11),
                                                insertbackground=palette['concepts_text_insert_background'],
                                                selectbackground=palette['concepts_text_select_background'],
                                                selectforeground=palette['background_black'],
                                                padx=20, pady=15)
        concepts_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Enhanced content with better formatting
        concepts_content = """
🔬 QUANTUM COMPUTING FUNDAMENTALS

🌟 What is Quantum Computing?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Quantum computing harnesses the principles of quantum mechanics to process information in
fundamentally different ways than classical computers. Instead of using bits that are either
0 or 1, quantum computers use quantum bits (qubits) that can exist in superposition.

🎯 KEY CONCEPTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔹 1. QUBIT (Quantum Bit)
   ┌─ The basic unit of quantum information
   ├─ Can be in state |0⟩, |1⟩, or a superposition of both
   └─ Represented as α|0⟩ + β|1⟩ where |α|² + |β|² = 1

🔹 2. SUPERPOSITION
   ┌─ A qubit can exist in multiple states simultaneously
   ├─ Enables quantum computers to process many possibilities at once
   └─ Collapses to a definite state when measured

🔹 3. ENTANGLEMENT
   ┌─ Quantum particles become correlated in impossible ways
   ├─ Measurement of one particle instantly affects its entangled partner
   └─ Key resource for quantum algorithms and communication

🔹 4. INTERFERENCE
   ┌─ Quantum states can interfere constructively or destructively
   ├─ Used in quantum algorithms to amplify correct answers
   └─ Cancels out wrong answers in many quantum computations

🔹 5. MEASUREMENT
   ┌─ The act of observing a quantum system
   ├─ Causes the quantum state to collapse to a classical state
   └─ Probabilistic outcome based on quantum amplitudes

🚀 WHY QUANTUM COMPUTING MATTERS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ Exponential speedup for certain problems
✨ Cryptography and security applications
✨ Drug discovery and molecular simulation
✨ Optimization problems
✨ Machine learning and AI
✨ Financial modeling

🔧 CURRENT CHALLENGES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ Quantum decoherence (qubits losing their quantum properties)
⚠️ Error rates in quantum operations
⚠️ Limited number of qubits in current systems
⚠️ Need for extremely low temperatures
⚠️ Quantum error correction

📈 THE FUTURE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Quantum computing represents a paradigm shift that could revolutionize how we solve
complex problems in science, technology, and beyond. The future is quantum! 🌟
        """

        concepts_text.insert(tk.END, concepts_content)
        concepts_text.config(state=tk.DISABLED)

    def create_gates_tab(self):
        """Create the enhanced quantum gates tab with all gates in one horizontal line"""
        gates_frame = ttk.Frame(self.notebook)
        self.notebook.add(gates_frame, text="⚡ Quantum Gates")

        # Main container - changed to match card background
        main_container = tk.Frame(gates_frame, bg=palette['background_3'])  # Changed from #1a1a1a to #2a2a2a
        main_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

        # Create a canvas for horizontal scrolling with enhanced styling
        canvas_frame = tk.Frame(main_container, bg=palette['background_3'], relief=tk.RAISED, bd=2)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        # Use horizontal scrollbar instead of vertical
        canvas = tk.Canvas(canvas_frame, bg=palette['background_3'], highlightthickness=0)  # Changed from #1a1a1a to #2a2a2a
        scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal", command=canvas.xview)
        scrollable_frame = tk.Frame(canvas, bg=palette['background_3'])  # Changed from #1a1a1a to #2a2a2a

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(xscrollcommand=scrollbar.set)  # Changed to xscrollcommand

        canvas.pack(side="top", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="bottom", fill="x")  # Changed to bottom and fill x

        # Enhanced gate definitions with more details
        gates = [
            ("X Gate (NOT)", "Flips |0⟩ ↔ |1⟩", "Pauli-X rotation", "#ff6b6b", "❌", 2),
            ("Y Gate", "Rotates around Y-axis", "Pauli-Y rotation", "#4ecdc4", "🔄", 3),
            ("Z Gate", "Phase flip: |1⟩ → -|1⟩", "Pauli-Z rotation", "#96ceb4", "⚡", 2),
            ("H Gate (Hadamard)", "Creates superposition", "|0⟩ → (|0⟩+|1⟩)/√2", "#f39c12", "🌟", 4),
            ("S Gate", "Phase gate: |1⟩ → i|1⟩", "90° Z rotation", "#9b59b6", "📐", 3),
            ("T Gate", "π/8 gate", "45° Z rotation", "#e74c3c", "🔺", 3),
            ("CNOT Gate", "Controlled NOT", "Entangles two qubits", "#00ff88", "🔗", 5),
            ("CZ Gate", "Controlled Z", "Conditional phase flip", "#ff9ff3", "⭐", 4),
        ]

        # Create one single row with all gates
        row_frame = tk.Frame(scrollable_frame, bg=palette['background_3'])  # Changed from #1a1a1a to #2a2a2a
        row_frame.pack(fill=tk.BOTH, expand=True, pady=20)

        # Add all gates to the single row
        for name, description, formula, color, icon, difficulty in gates:
            gate_container = tk.Frame(row_frame, bg=palette['background_3'])  # Changed from #1a1a1a to #2a2a2a
            gate_container.pack(side=tk.LEFT, fill=tk.Y, padx=15)

            self.create_enhanced_gate_card_horizontal(gate_container, name, description,
                                                    formula, color, icon, difficulty)

        # Enable mouse wheel scrolling on the canvas
        def on_mousewheel(event):
            canvas.xview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind("<MouseWheel>", on_mousewheel)
        # For Linux
        canvas.bind("<Button-4>", lambda e: canvas.xview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.xview_scroll(1, "units"))

    def create_enhanced_gate_card_horizontal(self, parent, name, description, formula, color, icon, difficulty):
        """Create enhanced cards for quantum gates with horizontal layout and hover effects"""
        card_frame = tk.Frame(parent, bg=palette['background_3'], relief=tk.FLAT, bd=0, width=200, height=250)  # Fixed size
        card_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=8)
        card_frame.pack_propagate(False)  # Maintain fixed size

        # Glow effect frame (initially hidden)
        glow_frame = tk.Frame(card_frame, bg=color, height=3)
        glow_frame.pack(fill=tk.X)
        glow_frame.pack_forget()

        # Main content frame
        content_frame = tk.Frame(card_frame, bg=palette['background_3'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=12)

        # Header with icon and title
        header_frame = tk.Frame(content_frame, bg=palette['background_3'])
        header_frame.pack(fill=tk.X, pady=(0, 8))

        # Gate icon - centered
        icon_label = tk.Label(header_frame, text=icon,
                            font=('Arial', 24), bg=palette['background_3'])  # Increased icon size
        icon_label.pack()

        # Title - centered
        name_label = tk.Label(header_frame, text=name,
                            font=('Arial', 12, 'bold'),  # Slightly smaller font
                            fg=color, bg=palette['background_3'])
        name_label.pack(pady=(5, 0))

        # Difficulty stars - centered
        stars = "⭐" * difficulty + "☆" * (5 - difficulty)
        difficulty_label = tk.Label(header_frame, text=f"{stars}",
                                font=('Arial', 8),  # Smaller font
                                fg=palette['difficulty_label_color'], bg=palette['background_3'])
        difficulty_label.pack()

        # Description - centered
        desc_label = tk.Label(content_frame, text=description,
                            font=('Arial', 9),  # Smaller font
                            fg=palette['description_label_color'], bg=palette['background_3'],
                            wraplength=170, justify=tk.CENTER)
        desc_label.pack(pady=(0, 5))

        # Formula - centered
        formula_label = tk.Label(content_frame, text=formula,
                                font=('Arial', 8, 'italic'),  # Smaller font
                                fg=palette['formula_label_color'], bg=palette['background_3'],
                                wraplength=170, justify=tk.CENTER)
        formula_label.pack()

        # Hover effects
        def on_enter(event):
            card_frame.configure(bg=palette['background_4'])
            content_frame.configure(bg=palette['background_4'])
            header_frame.configure(bg=palette['background_4'])
            for widget in [icon_label, name_label, difficulty_label, desc_label, formula_label]:
                widget.configure(bg=palette['background_4'])
            glow_frame.pack(fill=tk.X, before=content_frame)

        def on_leave(event):
            card_frame.configure(bg=palette['background_3'])
            content_frame.configure(bg=palette['background_3'])
            header_frame.configure(bg=palette['background_3'])
            for widget in [icon_label, name_label, difficulty_label, desc_label, formula_label]:
                widget.configure(bg=palette['background_3'])
            glow_frame.pack_forget()

        card_frame.bind("<Enter>", on_enter)
        card_frame.bind("<Leave>", on_leave)

        # Bind hover to all child widgets
        for widget in [content_frame, header_frame, icon_label, name_label, difficulty_label, desc_label, formula_label]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

    def create_algorithms_tab(self):
        """Create the enhanced algorithms tab"""
        algorithms_frame = ttk.Frame(self.notebook)
        self.notebook.add(algorithms_frame, text="🧠 Algorithms")

        # Main container - changed to match text area background
        main_container = tk.Frame(algorithms_frame, bg=palette['background_3'])  # Changed from #1a1a1a to #2a2a2a
        main_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

        # Enhanced scrollable text area
        text_frame = tk.Frame(main_container, bg=palette['background_3'], relief=tk.RAISED, bd=2)
        text_frame.pack(fill=tk.BOTH, expand=True)

        algorithms_text = scrolledtext.ScrolledText(text_frame,
                                                wrap=tk.WORD,
                                                width=80, height=25,
                                                bg=palette['background_3'], fg=palette['algorithms_text_color'],
                                                font=('Consolas', 11),
                                                insertbackground=palette['algorithms_text_insert_background'],
                                                selectbackground=palette['algorithms_text_select_background'],
                                                selectforeground=palette['background_black'],
                                                padx=20, pady=15)
        algorithms_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Enhanced algorithm content
        algorithms_content = """
🧠 FAMOUS QUANTUM ALGORITHMS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 1. SHOR'S ALGORITHM (1994) ⭐⭐⭐⭐⭐
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   🎯 Purpose: Integer factorization
   💥 Impact: Breaks RSA encryption
   🚀 Speedup: Exponential over classical methods

   🔑 Key Ideas:
   ┌─ Uses quantum Fourier transform
   ├─ Finds period of modular exponentiation
   └─ Factors large numbers efficiently

   📱 Applications:
   ┌─ Cryptography and security
   ├─ Breaking current encryption schemes
   └─ Motivating post-quantum cryptography

🔍 2. GROVER'S ALGORITHM (1996) ⭐⭐⭐⭐☆
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   🎯 Purpose: Database search
   💥 Impact: Quadratic speedup for search problems
   🚀 Speedup: √N instead of N comparisons

   🔑 Key Ideas:
   ┌─ Amplitude amplification
   ├─ Iteratively increases probability of correct answer
   └─ Uses quantum interference

   📱 Applications:
   ┌─ Unstructured search
   ├─ Optimization problems
   └─ Machine learning

🔍 3. DEUTSCH-JOZSA ALGORITHM ⭐⭐⭐☆☆
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   🎯 Purpose: Determine if function is constant or balanced
   💥 Impact: First quantum algorithm with exponential speedup
   🚀 Speedup: 1 query vs N/2 queries classically

   🔑 Key Ideas:
   ┌─ Uses quantum parallelism
   ├─ Evaluates function on all inputs simultaneously
   └─ Quantum interference reveals global property

🔍 4. VARIATIONAL QUANTUM EIGENSOLVER (VQE) ⭐⭐⭐⭐☆
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   🎯 Purpose: Find ground state of molecular systems
   💥 Impact: Near-term quantum chemistry applications
   🔄 Approach: Hybrid quantum-classical optimization

   🔑 Key Ideas:
   ┌─ Parametrized quantum circuits
   ├─ Classical optimization loop
   └─ Minimizes energy expectation value

🎯 ALGORITHM CATEGORIES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 Algebraic Algorithms:
   • Shor's Algorithm (factoring)
   • Hidden Subgroup Problem
   • Discrete logarithm

🔍 Search Algorithms:
   • Grover's Algorithm
   • Amplitude amplification
   • Quantum walks

🧮 Simulation Algorithms:
   • Quantum chemistry simulation
   • Many-body physics
   • Quantum field theory

🎲 Optimization Algorithms:
   • QAOA
   • VQE
   • Quantum annealing

🔮 FUTURE DIRECTIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ Fault-tolerant quantum algorithms
✨ Quantum machine learning
✨ Quantum error correction
✨ Distributed quantum computing

The quantum future awaits! 🌟🚀
        """

        algorithms_text.insert(tk.END, algorithms_content)
        algorithms_text.config(state=tk.DISABLED)

    def create_resources_tab(self):
        """Create the enhanced resources tab with horizontal layout"""
        resources_frame = ttk.Frame(self.notebook)
        self.notebook.add(resources_frame, text="🔗 Resources")

        # Main container
        main_container = tk.Frame(resources_frame, bg=palette['background_3'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

        # Create scrollable frame with horizontal scrolling
        canvas = tk.Canvas(main_container, bg=palette['background_3'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="horizontal", command=canvas.xview)
        scrollable_frame = tk.Frame(canvas, bg=palette['background_3'])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(xscrollcommand=scrollbar.set)

        canvas.pack(side="top", fill="both", expand=True)
        scrollbar.pack(side="bottom", fill="x")

        # Learning Resources section
        self.create_section_header_horizontal(scrollable_frame, "📚 Learning Resources", "#00ff88")

        # Resources in horizontal layout
        resources_row = tk.Frame(scrollable_frame, bg=palette['background_3'])
        resources_row.pack(fill=tk.X, pady=10)

        resources = [
            ("IBM Quantum Experience", "https://quantum-computing.ibm.com/",
            "Hands-on quantum programming", "🔬", 4),
            ("Microsoft Quantum Development Kit", "https://azure.microsoft.com/en-us/products/quantum/",
            "Q# programming language", "💻", 3),
            ("Google Cirq", "https://quantumai.google/cirq",
            "Python framework for quantum circuits", "🐍", 3),
            ("Qiskit Textbook", "https://qiskit.org/textbook/",
            "Comprehensive quantum computing textbook", "📖", 5),
            ("Nielsen & Chuang", "https://www.cambridge.org/core/books/quantum-computation-and-quantum-information/01E10196D0A682A6AEFFEA52D53BE9AE",
            "The quantum computing bible", "📚", 5),
        ]

        for title, url, description, icon, rating in resources:
            resource_container = tk.Frame(resources_row, bg=palette['background_3'])  # Changed from #1a1a1a to #2a2a2a
            resource_container.pack(side=tk.LEFT, fill=tk.Y, padx=10)
            self.create_enhanced_resource_card_horizontal(resource_container, title, url, description, icon, rating)

        # Separator with horizontal layout
        self.create_separator_horizontal(scrollable_frame)

        # Tools section
        self.create_section_header_horizontal(scrollable_frame, "🛠️ Quantum Computing Tools", "#f39c12")

        # Tools in horizontal layout
        tools_row = tk.Frame(scrollable_frame, bg=palette['background_3'])
        tools_row.pack(fill=tk.X, pady=10)

        tools = [
            ("Qiskit", "https://qiskit.org/",
            "Open-source quantum computing framework", "⚛️", 5),
            ("Cirq", "https://quantumai.google/cirq",
            "Google's quantum computing framework", "🔧", 4),
            ("PennyLane", "https://pennylane.ai/",
            "Quantum machine learning library", "🤖", 4),
            ("Quantum Inspire", "https://www.quantum-inspire.com/",
            "QuTech's quantum computing platform", "💡", 3),
        ]

        for title, url, description, icon, rating in tools:
            tool_container = tk.Frame(tools_row, bg=palette['background_3'])  # Changed from #1a1a1a to #2a2a2a
            tool_container.pack(side=tk.LEFT, fill=tk.Y, padx=10)
            self.create_enhanced_resource_card_horizontal(tool_container, title, url, description, icon, rating)

        # Enable mouse wheel scrolling on the canvas
        def on_mousewheel(event):
            canvas.xview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind("<MouseWheel>", on_mousewheel)
        # For Linux
        canvas.bind("<Button-4>", lambda e: canvas.xview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.xview_scroll(1, "units"))

    def create_enhanced_resource_card_horizontal(self, parent, title, url, description, icon, rating):
        """Create enhanced resource cards with horizontal layout and hover effects"""
        card_frame = tk.Frame(parent, bg=palette['background_3'], relief=tk.FLAT, bd=0, width=250, height=300)
        card_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=8)
        card_frame.pack_propagate(False)  # Maintain fixed size

        # Glow frame
        glow_frame = tk.Frame(card_frame, bg=palette['glow_frame_color'], height=2)
        glow_frame.pack(fill=tk.X)
        glow_frame.pack_forget()

        # Content frame
        content_frame = tk.Frame(card_frame, bg=palette['background_3'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Header with icon
        header_frame = tk.Frame(content_frame, bg=palette['background_3'])
        header_frame.pack(fill=tk.X, pady=(0, 10))

        # Icon - centered and larger
        icon_label = tk.Label(header_frame, text=icon,
                            font=('Arial', 28), bg=palette['background_3'])
        icon_label.pack()

        # Title - centered with wrapping
        title_label = tk.Label(header_frame, text=title,
                            font=('Arial', 12, 'bold'),
                            fg=palette['enhanced_title_color'], bg=palette['background_3'],
                            cursor='hand2', wraplength=220, justify=tk.CENTER)
        title_label.pack(pady=(5, 0))
        title_label.bind("<Button-1>", lambda e: self.open_url(url))

        # Rating stars - centered
        stars = "⭐" * rating + "☆" * (5 - rating)
        rating_label = tk.Label(header_frame, text=stars,
                            font=('Arial', 10),
                            fg=palette['rating_label_color'], bg=palette['background_3'])
        rating_label.pack(pady=(5, 0))

        # Description - centered with wrapping
        desc_label = tk.Label(content_frame, text=description,
                            font=('Arial', 10),
                            fg=palette['enhanced_description_color'], bg=palette['background_3'],
                            wraplength=220, justify=tk.CENTER)
        desc_label.pack(pady=(10, 15))

        # Try it button - centered
        try_btn = tk.Button(content_frame, text="Try It →",
                        bg=palette['try_it_button_background'], fg=palette['background_black'],
                        font=('Arial', 10, 'bold'),
                        padx=20, pady=8,
                        cursor='hand2',
                        command=lambda: self.open_url(url))
        try_btn.pack()

        # Hover effects
        def on_enter(event):
            card_frame.configure(bg=palette['background_4'])
            content_frame.configure(bg=palette['background_4'])
            header_frame.configure(bg=palette['background_4'])
            for widget in [icon_label, title_label, rating_label, desc_label]:
                widget.configure(bg=palette['background_4'])
            glow_frame.pack(fill=tk.X, before=content_frame)

        def on_leave(event):
            card_frame.configure(bg=palette['background_3'])
            content_frame.configure(bg=palette['background_3'])
            header_frame.configure(bg=palette['background_3'])
            for widget in [icon_label, title_label, rating_label, desc_label]:
                widget.configure(bg=palette['background_3'])
            glow_frame.pack_forget()

        card_frame.bind("<Enter>", on_enter)
        card_frame.bind("<Leave>", on_leave)

        # Bind hover to all child widgets
        for widget in [content_frame, header_frame, icon_label, title_label, rating_label, desc_label]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

    def create_separator_horizontal(self, parent):
        """Create a horizontal separator for horizontal layout"""
        separator_frame = tk.Frame(parent, bg=palette['background_3'])  # Changed from #1a1a1a to #2a2a2a
        separator_frame.pack(fill=tk.X, pady=30)

        # Gradient-like separator
        colors = [palette['gradient_separator_1'], palette['gradient_separator_2'], palette['gradient_separator_3']]
        for i, color in enumerate(colors):
            line = tk.Frame(separator_frame, bg=color, height=2)
            line.pack(fill=tk.X, pady=1)

    def create_section_header_horizontal(self, parent, title, color):
        """Create an enhanced section header for horizontal layout"""
        header_frame = tk.Frame(parent, bg=palette['background_3'])  # Changed from #1a1a1a to #2a2a2a
        header_frame.pack(fill=tk.X, pady=(20, 15))

        # Title with underline effect
        title_label = tk.Label(header_frame, text=title,
                            font=('Arial', 18, 'bold'),
                            fg=color, bg=palette['background_3'])  # Changed from #1a1a1a to #2a2a2a
        title_label.pack()

        # Underline
        underline = tk.Frame(header_frame, bg=color, height=2)
        underline.pack(fill=tk.X, pady=(5, 0))

    def create_section_header(self, parent, title, color):
        """Create an enhanced section header"""
        header_frame = tk.Frame(parent, bg=palette['background'])
        header_frame.pack(fill=tk.X, pady=(20, 15))

        # Title with underline effect
        title_label = tk.Label(header_frame, text=title,
                              font=('Arial', 18, 'bold'),
                              fg=color, bg=palette['background'])
        title_label.pack(anchor=tk.W)

        # Underline
        underline = tk.Frame(header_frame, bg=color, height=2)
        underline.pack(fill=tk.X, pady=(5, 0))

    def create_enhanced_resource_card(self, parent, title, url, description, icon, rating):
        """Create enhanced resource cards with ratings and hover effects"""
        card_frame = tk.Frame(parent, bg=palette['background_3'], relief=tk.FLAT, bd=0)
        card_frame.pack(fill=tk.X, pady=8)

        # Glow frame
        glow_frame = tk.Frame(card_frame, bg=palette['glow_frame_color'], height=2)
        glow_frame.pack(fill=tk.X)
        glow_frame.pack_forget()

        # Content frame
        content_frame = tk.Frame(card_frame, bg=palette['background_3'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Header
        header_frame = tk.Frame(content_frame, bg=palette['background_3'])
        header_frame.pack(fill=tk.X, pady=(0, 8))

        # Icon
        icon_label = tk.Label(header_frame, text=icon,
                             font=('Arial', 20), bg=palette['background_3'])
        icon_label.pack(side=tk.LEFT, padx=(0, 15))

        # Title and rating
        title_frame = tk.Frame(header_frame, bg=palette['background_3'])
        title_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        title_label = tk.Label(title_frame, text=title,
                              font=('Arial', 14, 'bold'),
                              fg=palette['enhanced_title_color'], bg=palette['background_3'],
                              cursor='hand2')
        title_label.pack(anchor=tk.W)
        title_label.bind("<Button-1>", lambda e: self.open_url(url))

        # Rating stars
        stars = "⭐" * rating + "☆" * (5 - rating)
        rating_label = tk.Label(title_frame, text=f"Rating: {stars}",
                               font=('Arial', 10),
                               fg=palette['rating_label_color'], bg=palette['background_3'])
        rating_label.pack(anchor=tk.W)

        # Try it button
        try_btn = tk.Button(header_frame, text="Try It →",
                           bg=palette['try_it_button_background'], fg=palette['background_black'],
                           font=('Arial', 10, 'bold'),
                           padx=15, pady=5,
                           cursor='hand2',
                           command=lambda: self.open_url(url))
        try_btn.pack(side=tk.RIGHT)

        # Description
        desc_label = tk.Label(content_frame, text=description,
                             font=('Arial', 11),
                             fg=palette['enhanced_description_color'], bg=palette['background_3'])
        desc_label.pack(anchor=tk.W)

        # Hover effects
        def on_enter(event):
            card_frame.configure(bg=palette['background_4'])
            content_frame.configure(bg=palette['background_4'])
            header_frame.configure(bg=palette['background_4'])
            title_frame.configure(bg=palette['background_4'])
            for widget in [icon_label, title_label, rating_label, desc_label]:
                widget.configure(bg=palette['background_4'])
            glow_frame.pack(fill=tk.X, before=content_frame)

        def on_leave(event):
            card_frame.configure(bg=palette['background_3'])
            content_frame.configure(bg=palette['background_3'])
            header_frame.configure(bg=palette['background_3'])
            title_frame.configure(bg=palette['background_3'])
            for widget in [icon_label, title_label, rating_label, desc_label]:
                widget.configure(bg=palette['background_3'])
            glow_frame.pack_forget()

        card_frame.bind("<Enter>", on_enter)
        card_frame.bind("<Leave>", on_leave)

    def create_separator(self, parent):
        """Create an animated separator"""
        separator_frame = tk.Frame(parent, bg=palette['background'])
        separator_frame.pack(fill=tk.X, pady=25)

        # Gradient-like separator
        colors = [palette['gradient_separator_1'], palette['gradient_separator_2'], palette['gradient_separator_3']]
        for i, color in enumerate(colors):
            line = tk.Frame(separator_frame, bg=color, height=1)
            line.pack(fill=tk.X, pady=1)

    def create_enhanced_footer(self, parent):
        """Create enhanced footer with gradient buttons"""
        footer_frame = tk.Frame(parent, bg=palette['background_3'])
        footer_frame.pack(fill=tk.X, 
                        padx=int(self.screen_width * 0.02), 
                        pady=(int(self.screen_height * 0.02), int(self.screen_height * 0.02)))

        # Create a centered button container
        button_container = tk.Frame(footer_frame, bg=palette['background_3'])
        button_container.pack(expand=True)

        # Button font size relative to screen
        button_font_size = max(12, int(self.screen_width * 0.01))
        button_padx = int(self.screen_width * 0.025)
        button_pady = int(self.screen_height * 0.012)

        # Back to Main Screen button with enhanced styling
        back_btn = tk.Button(button_container, text="🏠 Back to Main Screen",
                            command=self.back_to_menu,
                            font=('Arial', button_font_size, 'bold'),
                            bg=palette['main_menu_button_background'], fg=palette['background_black'],
                            padx=button_padx, pady=button_pady,
                            cursor='hand2',
                            relief=tk.FLAT,
                            borderwidth=0,
                            width=int(self.screen_width * 0.015))
        back_btn.pack(side=tk.LEFT, padx=int(self.screen_width * 0.008))

        # Close button with enhanced styling
        close_btn = tk.Button(button_container, text="❌ Close Application",
                            command=self.close_window,
                            font=('Arial', button_font_size, 'bold'),
                            bg=palette['close_button_background'], fg=palette['close_button_text_color'],
                            padx=button_padx, pady=button_pady,
                            cursor='hand2',
                            relief=tk.FLAT,
                            borderwidth=0,
                            width=int(self.screen_width * 0.015))
        close_btn.pack(side=tk.LEFT, padx=int(self.screen_width * 0.008))

        # Add enhanced hover effects to back button
        def on_back_enter(event):
            back_btn.configure(bg=palette['main_menu_button_hover_background'], fg=palette['background_black'])
        def on_back_leave(event):
            back_btn.configure(bg=palette['main_menu_button_background'], fg=palette['background_black'])

        back_btn.bind("<Enter>", on_back_enter)
        back_btn.bind("<Leave>", on_back_leave)

        # Add enhanced hover effects to close button
        def on_close_enter(event):
            close_btn.configure(bg=palette['close_button_hover_background'], fg=palette['close_button_text_color'])
        def on_close_leave(event):
            close_btn.configure(bg=palette['close_button_background'], fg=palette['close_button_text_color'])

        close_btn.bind("<Enter>", on_close_enter)
        close_btn.bind("<Leave>", on_close_leave)

        # Add a separator line above the buttons with relative sizing
        separator = tk.Frame(footer_frame, bg=palette['separator_line_color'], height=2)
        separator.pack(fill=tk.X, pady=(0, int(self.screen_height * 0.012)))

    def animate_circuit(self):
        """Animate the quantum circuit with subtle effects"""
        if not self.animation_running:
            return

        try:
            # Only redraw occasionally for subtle animation
            # You could add subtle effects here instead of full redraw
            # For now, let's make it less frequent
            pass  # Remove the redraw to stop flickering

            # Schedule next animation frame (longer interval)
            self.animation_id = self.root.after(10000, self.animate_circuit)  # Every 10 seconds instead of 3
        except tk.TclError:
            # Widget might be destroyed, stop animation
            self.animation_running = False

    def animate_subtitle(self):
        """Animate subtitle with pulsing effect"""
        if not self.animation_running or not hasattr(self, 'subtitle_label'):
            return

        try:
            if self.subtitle_label.winfo_exists():
                current_color = self.subtitle_label.cget('fg')
                new_color = '#00ff88' if current_color == '#4ecdc4' else '#4ecdc4'
                self.subtitle_label.configure(fg=new_color)

                # Schedule next animation frame
                self.root.after(2000, self.animate_subtitle)
        except (tk.TclError, AttributeError):
            # Widget might be destroyed or not exist, ignore
            pass

    def open_url(self, url):
        """Open URL in default browser"""
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"Error opening URL: {e}")

    def back_to_menu(self):
        """Go back to the main screen/menu"""
        self.animation_running = False

        # Cancel any pending animations
        if hasattr(self, 'animation_id') and self.animation_id:
            try:
                self.root.after_cancel(self.animation_id)
            except:
                pass

        self.root.destroy()
        try:
            # Try to import and launch the main menu
            from game_mode_selection import GameModeSelection
            selection_window = GameModeSelection()
            selection_window.run()
        except ImportError:
            try:
                # Alternative: try to import main menu
                import main_menu
                main_menu.main()
            except ImportError:
                try:
                    # Another alternative: try to run the main application
                    import main
                    main.main()
                except ImportError:
                    print("Could not find main menu module. Please run the main application.")
                    # Optionally create a simple menu selection
                    self.create_simple_menu_selection()
        except Exception as e:
            print(f"Error returning to main screen: {e}")
            # Fallback to simple menu
            self.create_simple_menu_selection()

    def create_simple_menu_selection(self):
        """Create a simple menu selection as fallback"""
        menu_root = tk.Tk()
        menu_root.title("Infinity Qubit - Main Menu")
        menu_root.geometry("400x300")
        menu_root.configure(bg=palette['background'])

        # Center the window
        menu_root.update_idletasks()
        x = (menu_root.winfo_screenwidth() - 400) // 2
        y = (menu_root.winfo_screenheight() - 300) // 2
        menu_root.geometry(f"400x300+{x}+{y}")

        # Title
        title_label = tk.Label(menu_root, text="🚀 Infinity Qubit",
                            font=('Arial', 24, 'bold'),
                            fg=palette['title_color'], bg=palette['background'])
        title_label.pack(pady=30)

        # Subtitle
        subtitle_label = tk.Label(menu_root, text="Main Menu",
                                font=('Arial', 16),
                                fg=palette['subtitle_color'], bg=palette['background'])
        subtitle_label.pack(pady=10)

        # Menu options
        button_frame = tk.Frame(menu_root, bg=palette['background'])
        button_frame.pack(expand=True)

        # Learn Hub button
        learn_btn = tk.Button(button_frame, text="📚 Learn Hub",
                            command=lambda: self.reopen_learn_hub(menu_root),
                            font=('Arial', 12, 'bold'),
                            bg=palette['learn_button_background'], fg=palette['background_black'],
                            padx=20, pady=10,
                            cursor='hand2', width=15)
        learn_btn.pack(pady=5)

        # Placeholder for other modes
        placeholder_label = tk.Label(button_frame, text="Other game modes coming soon...",
                                    font=('Arial', 10, 'italic'),
                                    fg=palette['placeholder_text_color'], bg=palette['background'])
        placeholder_label.pack(pady=20)

        # Close button
        close_btn = tk.Button(button_frame, text="❌ Exit",
                            command=menu_root.destroy,
                            font=('Arial', 12, 'bold'),
                            bg=palette['close_button_background'], fg=palette['close_button_text_color'],
                            padx=20, pady=10,
                            cursor='hand2', width=15)
        close_btn.pack(pady=5)

        menu_root.mainloop()

    def reopen_learn_hub(self, menu_root):
        """Reopen the Learn Hub"""
        menu_root.destroy()
        new_root = tk.Tk()
        LearnHub(new_root)
        new_root.mainloop()

    def close_window(self):
        """Close the learn hub window"""
        self.animation_running = False

        # Cancel any pending animations
        if hasattr(self, 'animation_id') and self.animation_id:
            try:
                self.root.after_cancel(self.animation_id)
            except:
                pass

        self.root.destroy()

def main():
    """For testing the learn hub independently"""
    root = tk.Tk()
    app = LearnHub(root)
    root.mainloop()

if __name__ == "__main__":
    main()