#!/usr/bin/env python3
"""
Sandbox Mode for Infinity Qubit
Allows users to experiment with quantum circuits in a freeform manner.
"""

import os
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import re
import sys
import json
import pygame
import datetime
import numpy as np
import tkinter as tk
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit
from tkinter import ttk, messagebox
from qiskit.quantum_info import Statevector
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from qiskit.visualization import plot_bloch_multivector, plot_state_qsphere

from q_utils import get_colors_from_file, extract_color_palette

sys.path.append('..')
from run import PROJECT_ROOT, get_resource_path

# Get color palette
color_file_path = get_resource_path('config/color_palette.json')
palette = extract_color_palette(get_colors_from_file(color_file_path), 'sandbox_mode')


class SandboxMode:
    SAVE_DIR = os.path.expanduser("resources/saves/infinity_qubit_sandbox_saves")


    def __init__(self, root):
        self.root = root
        self.root.title("Quantum Sandbox Mode")

        # Set fullscreen mode
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Make window fullscreen without title bar
        self.root.overrideredirect(True)
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        self.root.configure(bg=palette['background'])
        self.root.resizable(False, False)  # Fixed size window

        # Store dimensions (use full screen)
        self.window_width = screen_width
        self.window_height = screen_height

        # Bind Escape key to exit
        self.root.bind('<Escape>', self.exit_fullscreen)
        self.root.bind('<F11>', self.toggle_fullscreen)

        # Initialize sound system (optional - can reuse from main)
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.sound_enabled = True

            # Load sound files (same as tutorial)
            self.sounds = {}
            try:
                # Gate sounds
                self.sounds['gate_place'] = pygame.mixer.Sound(get_resource_path("resources/sounds/add_gate.wav"))
                self.sounds['success'] = pygame.mixer.Sound(get_resource_path("resources/sounds/correct.wav"))
                self.sounds['error'] = pygame.mixer.Sound(get_resource_path("resources/sounds/wrong.wav"))
                self.sounds['click'] = pygame.mixer.Sound(get_resource_path("resources/sounds/click.wav"))
                self.sounds['clear'] = pygame.mixer.Sound(get_resource_path("resources/sounds/clear.wav"))

                # Set volumes
                for sound in self.sounds.values():
                    sound.set_volume(0.5)

            except (pygame.error, FileNotFoundError) as e:
                print(f"Could not load sound files: {e}")
                # Fallback to programmatic sounds
                self.sounds = {}

        except:
            self.sound_enabled = False
            self.sounds = {}

        # Get screen dimensions for relative sizing
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Sandbox state
        self.num_qubits = 1
        self.placed_gates = []
        self.initial_state = "|0⟩"
        self.available_gates = ["H", "X", "Y", "Z", "S", "T", "CNOT", "CZ", "Toffoli"]
        self.selected_qubit = 0  # Track currently selected qubit for single-qubit gates

        # Setup UI
        self.setup_ui()
        self.update_circuit_display()


    def save_circuit(self):
        """Save the current circuit configuration with timestamp."""
        if not os.path.exists(self.SAVE_DIR):
            os.makedirs(self.SAVE_DIR)

        # Create timestamp-based filename
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(self.SAVE_DIR, f"circuit_{self.num_qubits}qubits_{timestamp}.json")

        data = {
            "num_qubits": self.num_qubits,
            "placed_gates": self.placed_gates,
            "initial_state": self.initial_state
        }

        try:
            with open(filename, "w") as f:
                json.dump(data, f)
            self.play_sound('click')
            self.show_custom_dialog("Success", f"Circuit saved!", "success")
        except Exception as e:
            self.play_sound('error', self.play_error_sound_fallback)
            self.show_custom_dialog("Error", f"Could not save circuit: {e}", "error")


    def load_circuit(self):
        """Show a touch-friendly list of saved circuits."""
        if not os.path.exists(self.SAVE_DIR):
            self.play_sound('error', self.play_error_sound_fallback)
            self.show_custom_dialog("No Saves", "No saved circuits found.", "info")
            return

        files = [f for f in os.listdir(self.SAVE_DIR) if f.endswith(".json")]
        if not files:
            self.play_sound('error', self.play_error_sound_fallback)
            self.show_custom_dialog("No Saves", "No saved circuits found.", "info")
            return

        # Play click sound
        self.play_sound('click')

        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Load Circuit")
        dialog.configure(bg=palette['background'])

        # Make dialog fullscreen-compatible and always on top
        dialog.overrideredirect(True)
        dialog.attributes('-topmost', True)

        # Calculate size (70% of screen)
        dialog_width = int(self.screen_width * 0.7)
        dialog_height = int(self.screen_height * 0.8)
        x = (self.screen_width - dialog_width) // 2
        y = (self.screen_height - dialog_height) // 2
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

        dialog.transient(self.root)

        # Ensure dialog is visible BEFORE grab_set
        dialog.lift()
        dialog.update_idletasks()  # Make sure dialog is rendered
        dialog.deiconify()  # Ensure it's visible

        # NOW set grab and focus after dialog is fully visible
        dialog.grab_set()
        dialog.focus_force()

        # Border frame
        border_frame = tk.Frame(dialog, bg=palette['main_menu_button_text_color'], bd=2, relief=tk.RAISED)
        border_frame.pack(fill=tk.BOTH, expand=True)

        # Main frame
        main_frame = tk.Frame(border_frame, bg=palette['background_3'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Title bar
        title_bar = tk.Frame(main_frame, bg=palette['background_4'], height=40)
        title_bar.pack(fill=tk.X)
        title_bar.pack_propagate(False)

        # Title
        title_label = tk.Label(title_bar, text="Load Saved Circuit",
                            font=('Arial', 14, 'bold'),
                            fg=palette['title_color'], bg=palette['background_4'])
        title_label.pack(side=tk.LEFT, padx=15, pady=5)

        # Close button
        close_btn = tk.Button(title_bar, text="",
                            command=dialog.destroy,
                            font=('Arial', 16, 'bold'),
                            bg=palette['background_4'],
                            fg=palette['title_color'],
                            bd=0, padx=15, pady=5)
        close_btn.pack(side=tk.RIGHT)

        # Scrollable frame for circuit buttons
        canvas = tk.Canvas(main_frame, bg=palette['background_3'], highlightthickness=0)
        scrollbar = tk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=palette['background_3'])

        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack scrollbar and canvas
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create window in canvas for scrollable frame
        canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW,
                            width=dialog_width - 50)  # Adjust width to fit dialog

        # Sort files by timestamp (newest first)
        files.sort(reverse=True)

        def do_load(filename):
            try:
                with open(os.path.join(self.SAVE_DIR, filename), "r") as f:
                    data = json.load(f)
                self.num_qubits = data.get("num_qubits", 1)
                self.placed_gates = data.get("placed_gates", [])
                self.initial_state = data.get("initial_state", "|0⟩")
                
                # Update the state variable instead of qubit_var
                self.state_var.set(self.initial_state)
                
                # Update the qubit display
                self.update_qubit_display()
                
                # Update the qubit selection dropdowns
                self.update_qubit_selections()
                
                # Update the circuit display
                self.update_circuit_display()
                
                dialog.destroy()
                
                # Show success message
                self.show_custom_dialog("Success", f"Circuit loaded successfully!\n{self.num_qubits} qubits, {len(self.placed_gates)} gates", "success")
                
            except Exception as e:
                self.show_custom_dialog("Error", f"Could not load circuit: {e}", "error")
                dialog.destroy()

        # Create touch-friendly buttons for each save file
        for filename in files:
            match = re.match(r"circuit_(\d+)qubits_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.json", filename)
            if match:
                qubits, timestamp = match.groups()
                datetime_obj = datetime.datetime.strptime(timestamp, "%Y-%m-%d_%H-%M-%S")
                friendly_date = datetime_obj.strftime("%b %d, %Y %I:%M %p")
                btn_frame = tk.Frame(scrollable_frame, bg=palette['background_4'],
                                relief=tk.RAISED, bd=2)
                btn_frame.pack(fill=tk.X, padx=10, pady=5)

                load_btn = tk.Button(btn_frame,
                                text=f"{qubits} Qubits Circuit\n{friendly_date}",
                                command=lambda f=filename: do_load(f),
                                font=('Arial', 12),
                                bg=palette['background_4'],
                                fg=palette['title_color'],
                                justify=tk.LEFT,
                                padx=20, pady=15,
                                cursor='hand2')
                load_btn.pack(fill=tk.X)

                def on_enter(e):
                    e.widget.configure(bg=palette['button_hover_background'])
                def on_leave(e):
                    e.widget.configure(bg=palette['background_4'])

                load_btn.bind("<Enter>", on_enter)
                load_btn.bind("<Leave>", on_leave)

        # Update scroll region
        scrollable_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

        # Make title bar draggable
        def start_move(event):
            dialog.x = event.x
            dialog.y = event.y

        def on_move(event):
            deltax = event.x - dialog.x
            deltay = event.y - dialog.y
            x = dialog.winfo_x() + deltax
            y = dialog.winfo_y() + deltay
            dialog.geometry(f"+{x}+{y}")

        title_bar.bind("<Button-1>", start_move)
        title_bar.bind("<B1-Motion>", on_move)

        # Mouse wheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind_all("<MouseWheel>", on_mousewheel)

        # Bind Escape to close
        dialog.bind('<Escape>', lambda e: dialog.destroy())


    def exit_fullscreen(self, event=None):
        """Exit fullscreen mode"""
        self.root.overrideredirect(False)
        self.root.state('normal')
        self.root.geometry("1200x800")


    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode"""
        # Toggle between windowed and fullscreen mode
        if self.root.attributes('-fullscreen'):
            # Exit fullscreen
            self.root.attributes('-fullscreen', False)
            # Reset to optimal window size and center
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            target_width = int(screen_width * 0.85)
            target_height = int(screen_height * 0.85)
            x = (screen_width - target_width) // 2
            y = (screen_height - target_height) // 2
            self.root.geometry(f"{target_width}x{target_height}+{x}+{y}")
        else:
            # Enter fullscreen
            self.root.attributes('-fullscreen', True)


    def play_sound(self, sound_name, fallback_func=None):
        """Play a sound file or fallback to programmatic sound"""
        if not self.sound_enabled:
            return

        try:
            if sound_name in self.sounds:
                self.sounds[sound_name].play()
            elif fallback_func:
                fallback_func()
        except Exception as e:
            print(f"Sound error: {e}")
            if fallback_func:
                fallback_func()


    def play_gate_sound_fallback(self):
        """Fallback sound for gate placement"""
        try:
            frequency = 440
            duration = 0.15
            sample_rate = 22050
            frames = int(duration * sample_rate)

            t = np.linspace(0, duration, frames)
            wave = np.sin(2 * np.pi * frequency * t)
            envelope = np.exp(-t * 5)
            wave = wave * envelope

            wave = (wave * 16383).astype(np.int16)
            stereo_wave = np.array([wave, wave]).T

            sound = pygame.sndarray.make_sound(stereo_wave)
            sound.set_volume(0.4)
            sound.play()
        except:
            pass


    def play_success_sound_fallback(self):
        """Fallback sound for success"""
        try:
            frequencies = [440, 523, 659, 784]
            duration = 0.15
            sample_rate = 22050
            frames = int(duration * sample_rate)

            total_frames = frames * len(frequencies)
            full_wave = np.zeros(total_frames)

            for i, freq in enumerate(frequencies):
                t = np.linspace(0, duration, frames)
                wave = np.sin(2 * np.pi * freq * t)
                envelope = np.exp(-t * 4)
                wave = wave * envelope

                start_idx = i * frames
                end_idx = start_idx + frames
                full_wave[start_idx:end_idx] = wave

            full_wave = (full_wave * 16383).astype(np.int16)
            stereo_wave = np.array([full_wave, full_wave]).T

            sound = pygame.sndarray.make_sound(stereo_wave)
            sound.set_volume(0.6)
            sound.play()
        except:
            pass


    def play_error_sound_fallback(self):
        """Fallback sound for errors"""
        try:
            frequency = 150
            duration = 0.2
            sample_rate = 22050
            frames = int(duration * sample_rate)

            t = np.linspace(0, duration, frames)
            wave1 = np.sin(2 * np.pi * frequency * t)
            wave2 = np.sin(2 * np.pi * (frequency * 1.1) * t)
            wave = (wave1 + wave2) / 2

            envelope = np.exp(-t * 8)
            wave = wave * envelope

            wave = (wave * 16383).astype(np.int16)
            stereo_wave = np.array([wave, wave]).T

            sound = pygame.sndarray.make_sound(stereo_wave)
            sound.set_volume(0.5)
            sound.play()
        except:
            pass


    def play_clear_sound_fallback(self):
        """Fallback sound for clearing"""
        try:
            start_freq = 800
            duration = 0.3
            sample_rate = 22050
            frames = int(duration * sample_rate)

            t = np.linspace(0, duration, frames)
            freq_sweep = start_freq * np.exp(-t * 5)
            wave = np.sin(2 * np.pi * freq_sweep * t)

            envelope = np.exp(-t * 2)
            wave = wave * envelope

            wave = (wave * 16383).astype(np.int16)
            stereo_wave = np.array([wave, wave]).T

            sound = pygame.sndarray.make_sound(stereo_wave)
            sound.set_volume(0.4)
            sound.play()
        except:
            pass


    def create_canvas_dialog_button(self, parent, text, command, bg_color, text_color,
                               width=120, height=40, font_size=12, font_weight='bold'):
        """Create a canvas-based button for dialogs and popup windows"""
        # Create canvas for the button
        canvas = tk.Canvas(parent, width=width, height=height,
                        highlightthickness=0, bd=0,
                        bg=parent['bg'] if hasattr(parent, 'cget') and parent.cget('bg') else palette['background_2'])

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


    def setup_ui(self):
        """Setup the sandbox UI with enhanced styling matching learn hub"""
        # Main container with gradient-like effect
        main_frame = tk.Frame(self.root, bg=palette['background_2'])
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Add subtle top border with relative height
        top_border = tk.Frame(main_frame, bg=palette['top_border_color'], height=int(self.screen_height * 0.003))
        top_border.pack(fill=tk.X)

        # Content frame
        content_frame = tk.Frame(main_frame, bg=palette['background_3'])
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Create simplified header (no animation)
        self.create_simple_header(content_frame)

        # Main content container with relative padding
        main_container = tk.Frame(content_frame, bg=palette['background_3'])
        main_container.pack(fill=tk.BOTH, expand=True,
                        padx=int(self.screen_width * 0.02),
                        pady=(0, int(self.screen_height * 0.02)))

        # Control panel
        self.setup_control_panel(main_container)

        # Circuit display area
        self.setup_circuit_area(main_container)


    def create_simple_header(self, parent):
        """Create a simple header without animation to save space"""
        header_frame = tk.Frame(parent, bg=palette['background_3'])
        header_frame.pack(fill=tk.X,
                        padx=int(self.screen_width * 0.02),
                        pady=(int(self.screen_height * 0.015), int(self.screen_height * 0.01)))

        # Add a top navigation bar with title and menu button
        nav_frame = tk.Frame(header_frame, bg=palette['background_3'])
        nav_frame.pack(fill=tk.X)

        # Title on the left with relative font size
        title_font_size = max(16, int(self.screen_width * 0.015))
        title_label = tk.Label(nav_frame, text="️ Quantum Circuit Sandbox",
                            font=('Arial', title_font_size, 'bold'),
                            fg=palette['title_color'], bg=palette['background_3'])
        title_label.pack(side=tk.LEFT)

        # Subtitle below title with relative font size
        subtitle_font_size = max(10, int(self.screen_width * 0.008))
        subtitle_label = tk.Label(nav_frame,
                                text="Build and simulate quantum circuits in real-time",
                                font=('Arial', subtitle_font_size, 'italic'),
                                fg=palette['subtitle_color'], bg=palette['background_3'])
        subtitle_label.pack(side=tk.LEFT, padx=(int(self.screen_width * 0.008), 0))

        # Back to Main Menu button - top right with relative sizing
        button_font_size = max(9, int(self.screen_width * 0.007))
        # Canvas-based main menu button for better color control on macOS
        button_font_size = max(10, int(self.screen_width * 0.008))
        button_width = max(120, int(self.screen_width * 0.08))
        button_height = max(35, int(self.screen_height * 0.03))

        main_menu_canvas = tk.Canvas(nav_frame,
                                   width=button_width,
                                   height=button_height,
                                   bg=palette['sandbox_mode_button_color'],
                                   highlightthickness=0,
                                   bd=0)
        main_menu_canvas.pack(side=tk.RIGHT)

        # Draw button background
        main_menu_canvas.create_rectangle(2, 2, button_width-2, button_height-2,
                                        fill=palette['sandbox_mode_button_color'],
                                        outline=palette['sandbox_mode_button_color'], width=1,
                                        tags="menu_bg")

        # Add text to button
        main_menu_canvas.create_text(button_width//2, button_height//2,
                                   text=" Main Menu",
                                   font=('Arial', button_font_size, 'bold'),
                                   fill=palette['sandbox_mode_button_text_color'],
                                   tags="menu_text")

        # Bind click events
        def on_menu_click(event):
            self.return_to_main_menu()

        def on_menu_enter(event):
            main_menu_canvas.itemconfig("menu_bg", fill=palette['sandbox_mode_button_hover_color'])
            main_menu_canvas.itemconfig("menu_text", fill=palette['sandbox_mode_button_text_color'])
            main_menu_canvas.configure(cursor="hand2")

        def on_menu_leave(event):
            main_menu_canvas.itemconfig("menu_bg", fill=palette['sandbox_mode_button_color'])
            main_menu_canvas.itemconfig("menu_text", fill=palette['sandbox_mode_button_text_color'])
            main_menu_canvas.configure(cursor="")

        main_menu_canvas.bind("<Button-1>", on_menu_click)
        main_menu_canvas.bind("<Enter>", on_menu_enter)
        main_menu_canvas.bind("<Leave>", on_menu_leave)


    def return_to_main_menu(self):
        """Return to the main menu with confirmation dialog"""
        self.play_sound('click')

        # Create custom confirmation dialog without decorations
        dialog = tk.Toplevel(self.root)
        dialog.title("Return to Main Menu")
        dialog.overrideredirect(True)
        dialog.configure(bg=palette['background'])
        dialog.transient(self.root)

        # Make dialog bigger for touch screens
        dialog_width = 900
        dialog_height = 400  # Reduced height since no save section needed
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - dialog_width) // 2
        y = (screen_height - dialog_height) // 2

        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

        # Ensure dialog is visible
        dialog.lift()
        dialog.attributes("-topmost", True)
        dialog.update_idletasks()
        dialog.deiconify()
        dialog.grab_set()
        dialog.focus_set()

        result = [None]

        # Main container with border
        main_frame = tk.Frame(dialog, bg=palette['background_2'], relief=tk.RAISED, bd=3)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Title
        title_label = tk.Label(main_frame, text="Return to Main Menu",
                            font=('Arial', 20, 'bold'),
                            fg=palette['title_color'], bg=palette['background_2'])
        title_label.pack(pady=(20, 15))

        # Message
        message_label = tk.Label(main_frame,
                            text="Are you sure you want to return to the main menu?\nYour current circuit will be lost unless saved.",
                            font=('Arial', 16),
                            fg=palette['subtitle_color'], bg=palette['background_2'],
                            justify=tk.CENTER)
        message_label.pack(pady=20)

        # Button frame
        button_frame = tk.Frame(main_frame, bg=palette['background_2'])
        button_frame.pack(pady=(20, 10))

        def confirm_return():
            result[0] = True
            dialog.destroy()

        def cancel_return():
            result[0] = False
            dialog.destroy()

        # FIXED: Buttons with correct parameters
        yes_canvas = self.create_canvas_dialog_button(
            button_frame, "✓ Yes, Return", confirm_return,
            palette.get('return_to_gamemode_button_background', '#ff6b6b'),
            palette.get('return_to_gamemode_button_text_color', '#ffffff'),
            width=270, height=90, font_size=24
        )
        yes_canvas.pack(side=tk.LEFT, padx=30)

        no_canvas = self.create_canvas_dialog_button(
            button_frame, "✗ No, Stay", cancel_return,
            palette.get('close_gamemode_button_background', '#00cc66'),
            palette.get('close_gamemode_button_text_color', '#ffffff'),
            width=270, height=90, font_size=24
        )
        no_canvas.pack(side=tk.LEFT, padx=30)

        # Handle ESC key to cancel
        dialog.bind('<Escape>', lambda e: cancel_return())

        # Wait for dialog to close and get result
        dialog.wait_window()

        # Process result
        if result[0]:
            try:
                from game_mode_selection import GameModeSelection
                selection_window = GameModeSelection()
                selection_window.root.update()
                selection_window.root.lift()
                selection_window.root.focus_force()
                self.root.destroy()
                selection_window.run()
            except ImportError as e:
                print(f"Error importing game mode selection: {e}")
                self.root.destroy()
            except Exception as e:
                print(f"Error returning to main menu: {e}")
                self.root.destroy()


    def setup_control_panel(self, parent):
        """Setup the control panel with enhanced styling"""
        control_frame = tk.Frame(parent, bg=palette['background_3'], relief=tk.RAISED, bd=2)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        # Enhanced title with relative font size
        title_font_size = max(14, int(self.screen_width * 0.012))
        control_title = tk.Label(control_frame, text="️ Circuit Configuration",
                                font=('Arial', title_font_size, 'bold'),
                                fg=palette['circuit_title_text_color'], bg=palette['background_3'])
        control_title.pack(pady=(10, 15))

        # Main controls container with fixed height
        controls_container = tk.Frame(control_frame, bg=palette['background_3'], height=120)
        controls_container.pack(fill=tk.X, padx=20, pady=(0, 15))
        controls_container.pack_propagate(False)  # Prevent height from expanding

        # Create left and right sections directly in controls_container
        left_frame = tk.Frame(controls_container, bg=palette['background_4'], relief=tk.RAISED, bd=1)
        left_frame.place(relx=0.35, rely=0.5, relwidth=0.2, relheight=0.9, anchor='center')

        right_frame = tk.Frame(controls_container, bg=palette['background_4'], relief=tk.RAISED, bd=1)
        right_frame.place(relx=0.65, rely=0.5, relwidth=0.2, relheight=0.9, anchor='center')

        # Setup qubit controls in left frame
        self.setup_qubit_controls(left_frame)

        # Setup state controls in right frame
        self.setup_state_controls(right_frame)


    def setup_qubit_controls(self, parent):
        """Setup qubit number controls with proper height using place"""
        label_font_size = max(11, int(self.screen_width * 0.009))
        
        # Title with relative positioning
        title_label = tk.Label(parent, text="Number of Qubits",
                              font=('Arial', label_font_size, 'bold'),
                              fg=palette['qubit_number_title_color'], bg=palette['background_4'])
        title_label.place(relx=0.5, rely=0.15, anchor='center')

        # Counter container with relative positioning
        counter_container = tk.Frame(parent, bg=palette['background_4'])
        counter_container.place(relx=0.5, rely=0.65, relwidth=0.9, relheight=0.5, anchor='center')

        # Decrement button frame
        decrement_frame = tk.Frame(counter_container, bg=palette['background_4'])
        decrement_frame.place(relx=0.15, rely=0.5, relwidth=0.3, relheight=0.8, anchor='center')

        decrement_canvas = tk.Canvas(decrement_frame, bg=palette['background'], 
                                   highlightthickness=0, bd=0)
        decrement_canvas.place(relx=0.5, rely=0.5, relwidth=0.7, relheight=0.9, anchor='center')

        # Draw decrement button
        def draw_decrement_button():
            decrement_canvas.delete("all")
            decrement_canvas.update_idletasks()
            width = decrement_canvas.winfo_width()
            height = decrement_canvas.winfo_height()
            if width > 1 and height > 1:
                decrement_canvas.create_rectangle(2, 2, width-2, height-2,
                                                fill=palette['background'], 
                                                outline=palette['qubit_spinbox_color'], width=2, tags="bg")
                font_size = max(10, int(min(width, height) * 0.4))
                decrement_canvas.create_text(width//2, height//2, text="−",
                                           font=('Arial', font_size, 'bold'), 
                                           fill=palette['qubit_spinbox_color'], tags="text")

        decrement_canvas.bind('<Configure>', lambda e: draw_decrement_button())
        decrement_canvas.after(10, draw_decrement_button)

        # Display frame
        display_frame = tk.Frame(counter_container, bg=palette['background_4'])
        display_frame.place(relx=0.5, rely=0.5, relwidth=0.4, relheight=0.8, anchor='center')

        self.qubit_display_label = tk.Label(display_frame, 
                                          text=str(self.num_qubits),
                                          font=('Arial', 16, 'bold'),
                                          fg=palette['qubit_spinbox_color'], 
                                          bg=palette['background_4'],
                                          relief=tk.SUNKEN, bd=2)
        self.qubit_display_label.place(relx=0.5, rely=0.5, relwidth=0.8, relheight=0.8, anchor='center')

        # Increment button frame
        increment_frame = tk.Frame(counter_container, bg=palette['background_4'])
        increment_frame.place(relx=0.85, rely=0.5, relwidth=0.3, relheight=0.8, anchor='center')

        increment_canvas = tk.Canvas(increment_frame, bg=palette['background'], 
                                   highlightthickness=0, bd=0)
        increment_canvas.place(relx=0.5, rely=0.5, relwidth=0.7, relheight=0.9, anchor='center')

        # Draw increment button
        def draw_increment_button():
            increment_canvas.delete("all")
            increment_canvas.update_idletasks()
            width = increment_canvas.winfo_width()
            height = increment_canvas.winfo_height()
            if width > 1 and height > 1:
                increment_canvas.create_rectangle(2, 2, width-2, height-2,
                                                fill=palette['background'], 
                                                outline=palette['qubit_spinbox_color'], width=2, tags="bg")
                font_size = max(10, int(min(width, height) * 0.4))
                increment_canvas.create_text(width//2, height//2, text="+",
                                           font=('Arial', font_size, 'bold'), 
                                           fill=palette['qubit_spinbox_color'], tags="text")

        increment_canvas.bind('<Configure>', lambda e: draw_increment_button())
        increment_canvas.after(10, draw_increment_button)

        # Button click handlers
        def decrement_qubits(event):
            if self.num_qubits > 1:
                self.num_qubits -= 1
                self.update_qubit_display()
                self.on_qubit_change_touch()
                self.play_sound('click')

        def increment_qubits(event):
            if self.num_qubits < 4:
                self.num_qubits += 1
                self.update_qubit_display()
                self.on_qubit_change_touch()
                self.play_sound('click')

        # Bind click events and hover effects
        decrement_canvas.bind("<Button-1>", decrement_qubits)
        increment_canvas.bind("<Button-1>", increment_qubits)

        # Hover effects for decrement button
        def dec_on_enter(event):
            decrement_canvas.itemconfig("bg", fill=palette['button_hover_background'])
            decrement_canvas.itemconfig("text", fill=palette['button_hover_text_color'])
            decrement_canvas.configure(cursor='hand2')

        def dec_on_leave(event):
            decrement_canvas.itemconfig("bg", fill=palette['background'])
            decrement_canvas.itemconfig("text", fill=palette['qubit_spinbox_color'])
            decrement_canvas.configure(cursor='')

        decrement_canvas.bind("<Enter>", dec_on_enter)
        decrement_canvas.bind("<Leave>", dec_on_leave)

        # Hover effects for increment button
        def inc_on_enter(event):
            increment_canvas.itemconfig("bg", fill=palette['button_hover_background'])
            increment_canvas.itemconfig("text", fill=palette['button_hover_text_color'])
            increment_canvas.configure(cursor='hand2')

        def inc_on_leave(event):
            increment_canvas.itemconfig("bg", fill=palette['background'])
            increment_canvas.itemconfig("text", fill=palette['qubit_spinbox_color'])
            increment_canvas.configure(cursor='')

        increment_canvas.bind("<Enter>", inc_on_enter)
        increment_canvas.bind("<Leave>", inc_on_leave)



    def setup_state_controls(self, parent):
        """Setup initial state controls with a single button showing current state"""

        # Initialize state variable
        self.state_var = tk.StringVar(value="|0⟩")

        # Single state button that shows current state and opens dialog when clicked
        state_button_canvas = tk.Canvas(parent, bg=palette['background_4'], 
                                      highlightthickness=2, highlightcolor=palette['combobox_color'],
                                      bd=0, relief=tk.SUNKEN)
        state_button_canvas.place(relx=0.5, rely=0.5, relwidth=0.8, relheight=0.6, anchor='center')

        def draw_state_button():
            state_button_canvas.delete("all")
            state_button_canvas.update_idletasks()
            width = state_button_canvas.winfo_width()
            height = state_button_canvas.winfo_height()
            if width > 1 and height > 1:
                # Draw current state text
                font_size = max(14, int(min(width, height) * 0.3))
                current_state = self.state_var.get()
                state_button_canvas.create_text(width//2, height//2, text=current_state,
                                              font=('Arial', font_size, 'bold'), 
                                              fill=palette['combobox_color'], tags="text")

        # Update button display when state changes
        def update_state_display(*args):
            draw_state_button()
        
        self.state_var.trace('w', update_state_display)

        state_button_canvas.bind('<Configure>', lambda e: draw_state_button())
        state_button_canvas.after(100, draw_state_button)

        # Click handler for state selection
        def open_state_dialog(event):
            self.show_state_selection_dialog()

        state_button_canvas.bind("<Button-1>", open_state_dialog)

        # Hover effects
        def state_on_enter(event):
            state_button_canvas.configure(bg=palette['button_hover_background'])
            state_button_canvas.itemconfig("text", fill=palette['button_hover_text_color'])
            state_button_canvas.configure(cursor='hand2')

        def state_on_leave(event):
            state_button_canvas.configure(bg=palette['background_4'])
            state_button_canvas.itemconfig("text", fill=palette['combobox_color'])
            state_button_canvas.configure(cursor='')

        state_button_canvas.bind("<Enter>", state_on_enter)
        state_button_canvas.bind("<Leave>", state_on_leave)


    def show_state_selection_dialog(self):
        """Show a touch-friendly state selection dialog with grid layout"""
        self.play_sound('click')

        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Initial State")
        dialog.configure(bg=palette['background'])

        # Make dialog fullscreen-compatible and always on top
        dialog.overrideredirect(True)
        dialog.attributes('-topmost', True)

        # Calculate responsive size using geometry instead of place
        dialog_width = int(self.screen_width * 0.6)
        dialog_height = int(self.screen_height * 0.7)
        x = (self.screen_width - dialog_width) // 2
        y = (self.screen_height - dialog_height) // 2
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

        dialog.transient(self.root)
        dialog.transient(self.root)
        try:
            dialog.grab_set()
            dialog.focus_force()
        except tk.TclError:
            # Window not ready yet, try again after a short delay
            self.root.after(50, lambda: dialog.grab_set() if dialog.winfo_exists() else None)
            dialog.focus_force()

        # Border frame
        border_frame = tk.Frame(dialog, bg=palette['main_menu_button_text_color'], bd=2, relief=tk.RAISED)
        border_frame.pack(fill=tk.BOTH, expand=True)

        # Main frame
        main_frame = tk.Frame(border_frame, bg=palette['background_3'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Title bar
        title_bar = tk.Frame(main_frame, bg=palette['background_4'], height=50)
        title_bar.pack(fill=tk.X)
        title_bar.pack_propagate(False)

        # Title
        title_label = tk.Label(title_bar, text="🎯 Select Initial Quantum State",
                            font=('Arial', 14, 'bold'),
                            fg=palette['title_color'], bg=palette['background_4'])
        title_label.pack(side=tk.LEFT, padx=15, pady=15)

        # Close button
        close_canvas = tk.Canvas(title_bar, bg=palette['background_4'], highlightthickness=0, bd=0, width=40, height=30)
        close_canvas.pack(side=tk.RIGHT, padx=15, pady=10)

        def draw_close_button():
            close_canvas.delete("all")
            close_canvas.create_rectangle(2, 2, 38, 28,
                                        fill=palette['background_4'], 
                                        outline=palette['title_color'], width=1, tags="bg")
            close_canvas.create_text(20, 15, text="✕",
                                   font=('Arial', 12, 'bold'), 
                                   fill=palette['title_color'], tags="text")

        draw_close_button()
        close_canvas.bind("<Button-1>", lambda e: dialog.destroy())

        # Hover effects for close button
        def close_on_enter(event):
            close_canvas.itemconfig("bg", fill=palette['button_hover_background'])
            close_canvas.itemconfig("text", fill=palette['button_hover_text_color'])
            close_canvas.configure(cursor='hand2')

        def close_on_leave(event):
            close_canvas.itemconfig("bg", fill=palette['background_4'])
            close_canvas.itemconfig("text", fill=palette['title_color'])
            close_canvas.configure(cursor='')

        close_canvas.bind("<Enter>", close_on_enter)
        close_canvas.bind("<Leave>", close_on_leave)

        # Content area
        content_frame = tk.Frame(main_frame, bg=palette['background_3'])
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Get available states based on number of qubits
        states = self.get_available_states()

        # Create grid of state buttons
        self.create_state_grid(content_frame, states, dialog)

        # Make title bar draggable
        def start_move(event):
            dialog.x = event.x_root - dialog.winfo_x()
            dialog.y = event.y_root - dialog.winfo_y()

        def on_move(event):
            x = event.x_root - dialog.x
            y = event.y_root - dialog.y
            dialog.geometry(f"+{x}+{y}")

        title_bar.bind("<Button-1>", start_move)
        title_bar.bind("<B1-Motion>", on_move)
        title_label.bind("<Button-1>", start_move)
        title_label.bind("<B1-Motion>", on_move)

        # Bind Escape to close
        dialog.bind('<Escape>', lambda e: dialog.destroy())


    def get_available_states(self):
        """Get available initial states based on number of qubits"""
        if self.num_qubits == 1:
            return ["|0⟩", "|1⟩", "|+⟩", "|-⟩"]
        elif self.num_qubits == 2:
            return ["|00⟩", "|01⟩", "|10⟩", "|11⟩", "|++⟩", "|--⟩", "|+-⟩", "|−+⟩"]
        elif self.num_qubits == 3:
            return ["|000⟩", "|001⟩", "|010⟩", "|011⟩", "|100⟩", "|101⟩", "|110⟩", "|111⟩"]
        elif self.num_qubits == 4:
            return ["|0000⟩", "|0001⟩", "|0010⟩", "|0011⟩", "|0100⟩", "|0101⟩", "|0110⟩", "|0111⟩",
                   "|1000⟩", "|1001⟩", "|1010⟩", "|1011⟩", "|1100⟩", "|1101⟩", "|1110⟩", "|1111⟩"]
        else:
            return ["|" + "0" * self.num_qubits + "⟩"]


    def create_state_grid(self, parent, states, dialog):
        """Create a responsive grid of state selection buttons"""
        # Calculate grid dimensions
        total_states = len(states)
        if total_states <= 4:
            cols = 2
            rows = 2
        elif total_states <= 8:
            cols = 4
            rows = 2
        elif total_states <= 16:
            cols = 4
            rows = 4
        else:
            cols = 6
            rows = (total_states + cols - 1) // cols

        # Create scrollable area if needed
        if total_states > 16:
            canvas = tk.Canvas(parent, bg=palette['background_3'], highlightthickness=0)
            scrollbar = tk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg=palette['background_3'])

            canvas.configure(yscrollcommand=scrollbar.set)
            scrollbar.place(relx=0.98, rely=0.05, relwidth=0.02, relheight=0.9)
            canvas.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=0.9)

            canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
            grid_parent = scrollable_frame
        else:
            grid_parent = parent

        # Create grid of buttons
        for i, state in enumerate(states):
            row = i // cols
            col = i % cols

            # Calculate button position using relative coordinates
            button_relx = (col + 0.5) / cols
            button_rely = (row + 0.5) / rows
            button_relwidth = 0.8 / cols
            button_relheight = 0.8 / rows

            # Create button frame
            btn_frame = tk.Frame(grid_parent, bg=palette['background_4'], relief=tk.RAISED, bd=2)
            if total_states <= 16:
                btn_frame.place(relx=button_relx, rely=button_rely, 
                               relwidth=button_relwidth, relheight=button_relheight, anchor='center')
            else:
                # For scrollable grid, use pack
                btn_frame.pack(side=tk.LEFT if col == 0 else None, 
                              fill=tk.BOTH, expand=True, padx=5, pady=5)

            # Create canvas button
            btn_canvas = tk.Canvas(btn_frame, bg=palette['background'], highlightthickness=0, bd=0)
            btn_canvas.place(relx=0.1, rely=0.1, relwidth=0.8, relheight=0.8)

            # State description
            state_desc = self.get_state_description(state)
            
            def draw_state_button(event=None, canvas=btn_canvas, state_text=state, desc=state_desc):
                canvas.delete("all")
                canvas.update_idletasks()
                width = canvas.winfo_width()
                height = canvas.winfo_height()
                if width > 1 and height > 1:
                    canvas.create_rectangle(2, 2, width-2, height-2,
                                          fill=palette['background'], 
                                          outline=palette['combobox_color'], width=2, tags="bg")
                    
                    # State text
                    state_font_size = max(8, int(min(width, height) * 0.2))
                    canvas.create_text(width//2, height//3, text=state_text,
                                     font=('Arial', state_font_size, 'bold'), 
                                     fill=palette['combobox_color'], tags="state_text")
                    
                    # Description text
                    desc_font_size = max(6, int(min(width, height) * 0.12))
                    canvas.create_text(width//2, 2*height//3, text=desc,
                                     font=('Arial', desc_font_size), 
                                     fill=palette['subtitle_color'], tags="desc_text")

            btn_canvas.bind('<Configure>', draw_state_button)
            btn_canvas.after(10, draw_state_button)

            # Click handler
            def create_state_handler(selected_state):
                def on_state_select(event):
                    self.state_var.set(selected_state)
                    self.initial_state = selected_state
                    self.on_state_change()
                    self.play_sound('click')
                    dialog.destroy()
                return on_state_select

            btn_canvas.bind("<Button-1>", create_state_handler(state))

            # Hover effects
            def create_hover_handlers(canvas, state_text, desc):
                def on_enter(event):
                    canvas.itemconfig("bg", fill=palette['button_hover_background'])
                    canvas.itemconfig("state_text", fill=palette['button_hover_text_color'])
                    canvas.itemconfig("desc_text", fill=palette['button_hover_text_color'])
                    canvas.configure(cursor='hand2')

                def on_leave(event):
                    canvas.itemconfig("bg", fill=palette['background'])
                    canvas.itemconfig("state_text", fill=palette['combobox_color'])
                    canvas.itemconfig("desc_text", fill=palette['subtitle_color'])
                    canvas.configure(cursor='')

                return on_enter, on_leave

            on_enter, on_leave = create_hover_handlers(btn_canvas, state, state_desc)
            btn_canvas.bind("<Enter>", on_enter)
            btn_canvas.bind("<Leave>", on_leave)

        # Update scroll region for scrollable grids
        if total_states > 16:
            scrollable_frame.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))


    def get_state_description(self, state):
        """Get a descriptive name for the quantum state"""
        descriptions = {
            "|0⟩": "Ground",
            "|1⟩": "Excited", 
            "|+⟩": "Plus",
            "|-⟩": "Minus",
            "|00⟩": "00",
            "|01⟩": "01", 
            "|10⟩": "10",
            "|11⟩": "11",
            "|++⟩": "Plus-Plus",
            "|--⟩": "Minus-Minus",
            "|+-⟩": "Plus-Minus",
            "|−+⟩": "Minus-Plus"
        }
        
        # For longer states, just return the binary part
        if state.startswith("|") and state.endswith("⟩"):
            binary_part = state[1:-1]
            if binary_part in descriptions.values():
                return descriptions.get(state, binary_part)
            return binary_part
        
        return descriptions.get(state, "Custom")


    def update_qubit_display(self):
        """Update the qubit counter display"""
        if hasattr(self, 'qubit_display_label'):
            self.qubit_display_label.configure(text=str(self.num_qubits))




    def setup_circuit_area(self, parent):
        """Setup the circuit visualization area with enhanced styling"""
        circuit_frame = tk.Frame(parent, bg=palette['background_3'], relief=tk.RAISED, bd=2)
        circuit_frame.pack(fill=tk.X, pady=(0, int(self.screen_height * 0.015)))

        # Enhanced title with icon and relative font size
        title_font_size = max(12, int(self.screen_width * 0.01))
        circuit_title = tk.Label(circuit_frame, text=" Quantum Circuit Designer",
                                font=('Arial', title_font_size, 'bold'),
                                fg=palette['circuit_designer_title_color'], bg=palette['background_3'])
        circuit_title.pack(pady=(int(self.screen_height * 0.01), int(self.screen_height * 0.008)))

        # Circuit canvas with enhanced styling and relative sizing
        canvas_container = tk.Frame(circuit_frame, bg=palette['background'], relief=tk.SUNKEN, bd=3)
        canvas_container.pack(padx=int(self.screen_width * 0.02),
                            pady=(0, int(self.screen_height * 0.01)))

        # Use relative canvas dimensions
        canvas_width = int(self.screen_width * 0.85)
        canvas_height = int(self.screen_height * 0.25)

        self.circuit_canvas = tk.Canvas(canvas_container, width=canvas_width, height=canvas_height,
                                    bg=palette['background_2'], highlightthickness=0)
        self.circuit_canvas.pack(padx=int(self.screen_width * 0.005),
                                pady=int(self.screen_height * 0.005))

        self.canvas_width = canvas_width
        self.canvas_height = canvas_height

        # Create bottom section with gate palette and controls
        self.setup_bottom_section(parent)


    def on_qubit_change_touch(self):
        """Handle change in number of qubits for touch interface"""
        self.placed_gates = []  # Clear gates when changing qubit count
        
        # Reset selected qubit if it's out of range
        if self.selected_qubit >= self.num_qubits:
            self.selected_qubit = 0

        # Update available initial states based on qubit count
        states = self.get_available_states()
        self.state_var.set(states[0])
        self.initial_state = states[0]

        # Update the qubit selection dropdowns
        self.update_qubit_selections()

        # Refresh multi-qubit gate controls to show/hide gates based on new qubit count
        self.refresh_multi_gate_controls()

        self.update_circuit_display()

    def refresh_multi_gate_controls(self):
        """Refresh the multi-qubit gate controls when the number of qubits changes"""
        if hasattr(self, 'multi_frame'):
            # Clear existing widgets in the multi-qubit frame
            for widget in self.multi_frame.winfo_children():
                widget.destroy()
            
            # Recreate the multi-qubit gate controls
            self.setup_multi_gate_controls(self.multi_frame)



    def setup_bottom_section(self, parent):
        """Setup the bottom section with gate palette on left, controls in middle, and results on right"""
        bottom_frame = tk.Frame(parent, bg=palette['background_3'])
        bottom_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Left side - Gate Palette (35% width instead of expanding)
        gate_frame = tk.Frame(bottom_frame, bg=palette['background_3'], relief=tk.RAISED, bd=2)
        gate_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        gate_frame.configure(width=int(self.screen_width * 0.35))  # Fixed width
        gate_frame.pack_propagate(False)  # Maintain fixed width

        # # Gate palette title
        # title_label = tk.Label(gate_frame, text=" Gate Palette",
        #         font=('Arial', 14, 'bold'), fg=palette['gate_palette_title_color'], bg=palette['background_3'])
        # title_label.place(relx=0.5, rely=0.08, anchor='center')

        # Create button selection area
        button_frame = tk.Frame(gate_frame, bg=palette['background_3'])
        button_frame.place(relx=0.1, rely=0.05, relwidth=0.8, relheight=0.12)

        # Initialize current view state
        self.current_gate_view = "single"

        # Single-qubit gates button
        self.single_btn_canvas = tk.Canvas(button_frame, bg=palette['background_4'], 
                                         highlightthickness=1, highlightcolor=palette['combobox_color'])
        self.single_btn_canvas.place(relx=0, rely=0, relwidth=0.48, relheight=1)

        # Multi-qubit gates button  
        self.multi_btn_canvas = tk.Canvas(button_frame, bg=palette['background'], 
                                        highlightthickness=1, highlightcolor=palette['combobox_color'])
        self.multi_btn_canvas.place(relx=0.52, rely=0, relwidth=0.48, relheight=1)

        # Create content area for gate controls
        content_area = tk.Frame(gate_frame, bg=palette['background_3'])
        content_area.place(relx=0.05, rely=0.20, relwidth=0.9, relheight=0.8)

        # Single-qubit gates frame
        self.single_frame = tk.Frame(content_area, bg=palette['background_3'])
        self.single_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.setup_single_gate_controls(self.single_frame)

        # Multi-qubit gates frame (initially hidden)
        self.multi_frame = tk.Frame(content_area, bg=palette['background_3'])
        self.setup_multi_gate_controls(self.multi_frame)

        # Button drawing and click functions
        def draw_single_button():
            self.single_btn_canvas.delete("all")
            self.single_btn_canvas.update_idletasks()
            width = self.single_btn_canvas.winfo_width()
            height = self.single_btn_canvas.winfo_height()
            if width > 1 and height > 1:
                font_size = max(8, int(min(width, height) * 0.25))
                color = palette['combobox_color'] if self.current_gate_view == "single" else palette['subtitle_color']
                self.single_btn_canvas.create_text(width//2, height//2, text="Single-Qubit",
                                                 font=('Arial', font_size, 'bold'), 
                                                 fill=color, tags="text")

        def draw_multi_button():
            self.multi_btn_canvas.delete("all")
            self.multi_btn_canvas.update_idletasks()
            width = self.multi_btn_canvas.winfo_width()
            height = self.multi_btn_canvas.winfo_height()
            if width > 1 and height > 1:
                font_size = max(8, int(min(width, height) * 0.25))
                color = palette['combobox_color'] if self.current_gate_view == "multi" else palette['subtitle_color']
                self.multi_btn_canvas.create_text(width//2, height//2, text="Multi-Qubit",
                                                font=('Arial', font_size, 'bold'), 
                                                fill=color, tags="text")

        def switch_to_single():
            if self.current_gate_view != "single":
                self.current_gate_view = "single"
                self.single_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
                self.multi_frame.place_forget()
                self.single_btn_canvas.configure(bg=palette['background_4'])
                self.multi_btn_canvas.configure(bg=palette['background'])
                draw_single_button()
                draw_multi_button()
                self.play_sound('click')

        def switch_to_multi():
            if self.current_gate_view != "multi":
                self.current_gate_view = "multi"
                self.multi_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
                self.single_frame.place_forget()
                self.multi_btn_canvas.configure(bg=palette['background_4'])
                self.single_btn_canvas.configure(bg=palette['background'])
                draw_single_button()
                draw_multi_button()
                self.play_sound('click')

        # Bind events
        self.single_btn_canvas.bind('<Configure>', lambda e: draw_single_button())
        self.multi_btn_canvas.bind('<Configure>', lambda e: draw_multi_button())
        self.single_btn_canvas.bind("<Button-1>", lambda e: switch_to_single())
        self.multi_btn_canvas.bind("<Button-1>", lambda e: switch_to_multi())

        # Hover effects
        def single_on_enter(event):
            if self.current_gate_view != "single":
                self.single_btn_canvas.configure(cursor='hand2')

        def single_on_leave(event):
            self.single_btn_canvas.configure(cursor='')

        def multi_on_enter(event):
            if self.current_gate_view != "multi":
                self.multi_btn_canvas.configure(cursor='hand2')

        def multi_on_leave(event):
            self.multi_btn_canvas.configure(cursor='')

        self.single_btn_canvas.bind("<Enter>", single_on_enter)
        self.single_btn_canvas.bind("<Leave>", single_on_leave)
        self.multi_btn_canvas.bind("<Enter>", multi_on_enter)
        self.multi_btn_canvas.bind("<Leave>", multi_on_leave)

        # Initialize buttons after a short delay to ensure proper sizing
        self.single_btn_canvas.after(100, draw_single_button)
        self.multi_btn_canvas.after(100, draw_multi_button)

        # Middle section - Circuit Controls (30% width with fixed size)
        controls_frame = tk.Frame(bottom_frame, bg=palette['background_3'], relief=tk.RAISED, bd=2)
        controls_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        controls_frame.configure(width=int(self.screen_width * 0.25))  # Fixed width
        controls_frame.pack_propagate(False)  # Maintain fixed width

        # Action buttons in middle section
        self.setup_action_buttons(controls_frame)

        # Right side - Quantum State Analysis (35% width instead of expanding)
        results_frame = tk.Frame(bottom_frame, bg=palette['background_3'], relief=tk.RAISED, bd=2)
        results_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        results_frame.configure(width=int(self.screen_width * 0.35))  # Fixed width
        results_frame.pack_propagate(False)  # Maintain fixed width

        # Results area in right section
        self.setup_results_area(results_frame)



    def setup_action_buttons(self, parent):
        """Setup action buttons with enhanced styling in middle section using place layout"""
        # Title for action section
        action_title = tk.Label(parent, text="Circuit Controls",
                            font=('Arial', 14, 'bold'), fg=palette['circuit_title_text_color'], bg=palette['background_3'])
        action_title.place(relx=0.5, rely=0.05, anchor='center')

        # Create buttons container - remove fixed width/height, use relative sizing only
        action_frame = tk.Frame(parent, bg=palette['background_3'])
        action_frame.place(relx=0.05, rely=0.15, relwidth=0.9, relheight=0.85)

        # Create enhanced buttons with hover effects - arranged in rows
        buttons_data = [
            ("Run Circuit", self.run_circuit, palette['run_button_background'], palette['background_black']),
            ("Clear Circuit", self.clear_circuit, palette['clear_button_background'], palette['clear_button_text_color']),
            ("Save Circuit", self.save_circuit, palette['save_image_background'], palette['background_black']),
            ("Load Circuit", self.load_circuit, palette['refresh_button_background'], palette['background_black']),
            ("3D Visualizer", self.open_3d_visualizer, palette['visualizer_button_background'], palette['visualizer_button_text_color']),
            ("Undo Last", self.undo_gate, palette['undo_button_background'], palette['background_black'])
        ]

        # Button layout positions: [row, column, colspan]
        button_positions = [
            (0, 0, 2),  # Run Circuit - full width
            (1, 0, 2),  # 3D Visualizer - full width
            (2, 0, 1),  # Clear Circuit - left half
            (2, 1, 1),  # Undo Last - right half
            (3, 0, 1),  # Save Circuit - left half
            (3, 1, 1)   # Load Circuit - right half
        ]

        # Create buttons using place layout
        for i, (text, command, bg_color, fg_color) in enumerate(buttons_data):
            row, col, colspan = button_positions[i]
            
            # Calculate position and size based on row/column
            if colspan == 2:  # Full width buttons
                relx = 0.5
                relwidth = 0.9
            else:  # Half width buttons
                relx = 0.25 if col == 0 else 0.75
                relwidth = 0.4
            
            rely = 0.1 + (row * 0.23)  # Start at 10% with 23% spacing between rows
            relheight = 0.2  # Button height

            # Create canvas-based button directly
            btn_canvas = tk.Canvas(action_frame, bg=bg_color, highlightthickness=0, relief=tk.FLAT, bd=0)
            btn_canvas.place(relx=relx, rely=rely, relwidth=relwidth, relheight=relheight, anchor='center')

            # Create button rectangle and text with responsive font size
            def draw_button(event=None, canvas=btn_canvas, color=bg_color, button_text=text, text_color=fg_color):
                canvas.delete("all")
                canvas.update_idletasks()
                width = canvas.winfo_width()
                height = canvas.winfo_height()
                if width > 1 and height > 1:
                    rect_id = canvas.create_rectangle(2, 2, width-2, height-2,
                                                    fill=color, outline=color, width=0, tags="bg")
                    
                    # Calculate responsive font size based on button dimensions
                    # Use the smaller dimension to ensure text fits
                    min_dimension = min(width, height)
                    # Scale font size between 8 and 16 based on button size
                    font_size = max(8, min(16, int(min_dimension * 0.3)))
                    
                    text_id = canvas.create_text(width//2, height//2, text=button_text,
                                            font=('Arial', font_size, 'bold'), fill=text_color, tags="text")
                    # Store IDs for hover effects
                    canvas.rect_id = rect_id
                    canvas.text_id = text_id

            btn_canvas.bind('<Configure>', draw_button)
            btn_canvas.after(10, draw_button)

            # Add click handler with proper closure
            def create_click_handler(cmd):
                return lambda event: cmd()

            btn_canvas.bind("<Button-1>", create_click_handler(command))
            btn_canvas.configure(cursor='hand2')

            # Add hover effects for canvas
            def create_hover_functions(canvas, orig_color, orig_fg):
                def on_enter(event):
                    if hasattr(canvas, 'rect_id') and hasattr(canvas, 'text_id'):
                        canvas.itemconfig(canvas.rect_id, fill=palette['button_hover_background'])
                        canvas.itemconfig(canvas.text_id, fill=palette['button_hover_text_color'])

                def on_leave(event):
                    if hasattr(canvas, 'rect_id') and hasattr(canvas, 'text_id'):
                        canvas.itemconfig(canvas.rect_id, fill=orig_color)
                        canvas.itemconfig(canvas.text_id, fill=orig_fg)

                return on_enter, on_leave

            on_enter, on_leave = create_hover_functions(btn_canvas, bg_color, fg_color)
            btn_canvas.bind("<Enter>", on_enter)
            btn_canvas.bind("<Leave>", on_leave)


    def open_3d_visualizer(self):
        """Open the 3D quantum state visualizer window"""
        try:
            # Check if there are any gates to visualize
            if not self.placed_gates:
                self.show_custom_dialog("3D Visualizer", "Add some gates to your circuit first to see the 3D visualization!", "info")
                self.play_sound('error', self.play_error_sound_fallback)
                return

            # Play sound for button click
            self.play_sound('click')

            # Create the quantum circuit
            qc = QuantumCircuit(self.num_qubits)
            self.set_initial_state(qc)

            # Apply gates
            for gate, qubits in self.placed_gates:
                try:
                    if gate == 'H' and len(qubits) == 1:
                        qc.h(qubits[0])
                    elif gate == 'X' and len(qubits) == 1:
                        qc.x(qubits[0])
                    elif gate == 'Y' and len(qubits) == 1:
                        qc.y(qubits[0])
                    elif gate == 'Z' and len(qubits) == 1:
                        qc.z(qubits[0])
                    elif gate == 'S' and len(qubits) == 1:
                        qc.s(qubits[0])
                    elif gate == 'T' and len(qubits) == 1:
                        qc.t(qubits[0])
                    elif gate == 'CNOT' and len(qubits) == 2:
                        qc.cx(qubits[0], qubits[1])
                    elif gate == 'CZ' and len(qubits) == 2:
                        qc.cz(qubits[0], qubits[1])
                    elif gate == 'Toffoli' and len(qubits) == 3:
                        qc.ccx(qubits[0], qubits[1], qubits[2])
                except Exception as gate_error:
                    print(f"Error applying gate {gate}: {str(gate_error)}")

            # Get the final state
            final_state = Statevector(qc)

            # Create and show the 3D visualization window
            self.show_3d_visualization(final_state)

        except ImportError as ie:
            self.show_custom_dialog("Import Error",
                f"Missing required packages for 3D visualization.\n\n"
                f"Please install: pip install matplotlib\n"
                f"Error: {str(ie)}", "error")
            self.play_sound('error', self.play_error_sound_fallback)
        except Exception as e:
            self.show_custom_dialog("3D Visualizer Error",
                f"Error creating 3D visualization:\n{str(e)}", "error")
            self.play_sound('error', self.play_error_sound_fallback)


    def show_custom_dialog(self, title, message, dialog_type="info"):
        """Show a custom dialog with the same background as the main window"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.configure(bg=palette['background'])

        # Make dialog fullscreen-compatible and always on top
        dialog.overrideredirect(True)
        dialog.attributes('-topmost', True)

        # Calculate relative sizing
        dialog_width = int(self.screen_width * 0.35)
        dialog_height = int(self.screen_height * 0.35)
        x = (self.screen_width - dialog_width) // 2
        y = (self.screen_height - dialog_height) // 2
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

        # Make dialog modal - AFTER positioning and visibility
        dialog.transient(self.root)

        # Ensure dialog is visible BEFORE grab_set
        dialog.lift()
        dialog.update_idletasks()
        dialog.deiconify()
        dialog.grab_set()
        dialog.focus_force()

        # Add border frame
        border_frame = tk.Frame(dialog, bg=palette.get('main_menu_button_text_color', '#2c1f12'), bd=2, relief=tk.RAISED)
        border_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Main frame inside border
        main_frame = tk.Frame(border_frame, bg=palette['background_3'], relief=tk.FLAT, bd=0)
        main_frame.place(relx=0.005, rely=0.005, relwidth=0.99, relheight=0.99)

        # Add title bar
        title_bar = tk.Frame(main_frame, bg=palette['background_4'])
        title_bar.place(relx=0, rely=0, relwidth=1, relheight=0.15)

        # FIXED: Close button with correct parameters
        close_btn = self.create_canvas_dialog_button(
            title_bar, "✕", dialog.destroy,
            palette['background_4'], palette['title_color'],
            width=25, height=20, font_size=12
        )
        close_btn.place(relx=0.92, rely=0.2, relwidth=0.06, relheight=0.6)

        # Content area
        content_frame = tk.Frame(main_frame, bg=palette['background_3'])
        content_frame.place(relx=0.05, rely=0.2, relwidth=0.9, relheight=0.75)

        # Icon and title together
        header_font_size = max(12, int(self.screen_width * 0.02))
        header_label = tk.Label(content_frame, text=f"{title}",
                            font=('Arial', header_font_size, 'bold'),
                            fg=palette['title_color'], bg=palette['background_3'])
        header_label.place(relx=0, rely=0.1, relwidth=1, relheight=0.2)

        # Message
        message_font_size = max(10, int(self.screen_width * 0.012))
        message_label = tk.Label(content_frame, text=message,
                                font=('Arial', message_font_size),
                                fg=palette['subtitle_color'], bg=palette['background_3'],
                                wraplength=int(dialog_width * 0.8), justify=tk.CENTER)
        message_label.place(relx=0, rely=0.35, relwidth=1, relheight=0.3)

        # Button frame
        button_frame = tk.Frame(content_frame, bg=palette['background_3'])
        button_frame.place(relx=0, rely=0.75, relwidth=1, relheight=0.2)

        # OK button with correct parameters
        ok_button = self.create_canvas_dialog_button(
            button_frame, "OK", dialog.destroy,
            palette['close_button_background'], palette.get('main_menu_button_text_color', '#2c1f12'),
            width=80, height=30, font_size=max(8, int(self.screen_width * 0.007))
        )
        ok_button.place(relx=0.35, rely=0.2, relwidth=0.3, relheight=0.7)

        # Make title bar draggable
        def start_move(event):
            dialog.x = event.x
            dialog.y = event.y

        def on_move(event):
            deltax = event.x - dialog.x
            deltay = event.y - dialog.y
            x = dialog.winfo_x() + deltax
            y = dialog.winfo_y() + deltay
            dialog.geometry(f"+{x}+{y}")

        title_bar.bind("<Button-1>", start_move)
        title_bar.bind("<B1-Motion>", on_move)

        # Bind keys
        dialog.bind('<Return>', lambda e: dialog.destroy())
        dialog.bind('<Escape>', lambda e: dialog.destroy())

        # Wait for dialog to close
        dialog.wait_window()


    def show_3d_visualization(self, state_vector):
        """Show the 3D quantum state visualization in a new window"""
        try:
            # Create a new window for the 3D visualization
            viz_window = tk.Toplevel(self.root)
            viz_window.title(" 3D Quantum State Visualizer")
            viz_window.configure(bg=palette['background'])

            # Make visualization window fullscreen-compatible and always on top
            viz_window.overrideredirect(True)
            viz_window.attributes('-topmost', True)

            # Set window size and center it with relative sizing
            window_width = int(self.screen_width * 0.7)
            window_height = int(self.screen_height * 0.8)
            x = (self.screen_width - window_width) // 2
            y = (self.screen_height - window_height) // 2
            viz_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

            # Make window modal and force focus - AFTER positioning
            viz_window.transient(self.root)

            # Ensure window is visible BEFORE grab_set
            viz_window.lift()
            viz_window.update_idletasks()  # Make sure window is rendered
            viz_window.deiconify()  # Ensure it's visible

            # NOW set grab and focus after window is fully visible
            viz_window.grab_set()
            viz_window.focus_force()

            # Add border since overrideredirect removes window decorations
            border_frame = tk.Frame(viz_window, bg=palette['main_menu_button_text_color'], bd=2, relief=tk.RAISED)
            border_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

            # Main container inside border
            main_container = tk.Frame(border_frame, bg=palette['background'], relief=tk.FLAT, bd=0)
            main_container.place(relx=0.01, rely=0.01, relwidth=0.98, relheight=0.98)

            # Custom title bar since we removed window decorations - RESPONSIVE
            title_bar = tk.Frame(main_container, bg=palette['background_4'])
            title_bar.place(relx=0, rely=0, relwidth=1, relheight=0.08)

            # Title in title bar with relative font size
            title_font_size = max(12, int(self.screen_width * 0.01))
            title_bar_label = tk.Label(title_bar, text="3D Quantum State Visualizer",
                                    font=('Arial', title_font_size, 'bold'),
                                    fg=palette['3D_visualizer_title_color'], bg=palette['background_4'])
            title_bar_label.place(relx=0.02, rely=0.5, anchor='w')

            # Close button in title bar using canvas for macOS compatibility
            close_btn_font_size = max(10, int(self.screen_width * 0.008))
            close_btn_canvas = tk.Canvas(title_bar, bg=palette['background_4'], highlightthickness=0, bd=0)
            close_btn_canvas.place(relx=0.92, rely=0.5, relwidth=0.06, relheight=0.6, anchor='center')

            def draw_title_close_button():
                close_btn_canvas.delete("all")
                close_btn_canvas.update_idletasks()
                width = close_btn_canvas.winfo_width()
                height = close_btn_canvas.winfo_height()
                if width > 1 and height > 1:
                    close_btn_canvas.create_rectangle(2, 2, width-2, height-2,
                                                    fill=palette['background_4'], 
                                                    outline=palette['title_color'], width=1, tags="bg")
                    close_btn_canvas.create_text(width//2, height//2, text="✕",
                                            font=('Arial', int(min(width, height) * 0.4), 'bold'), 
                                            fill=palette['title_color'], tags="text")

            close_btn_canvas.bind('<Configure>', lambda e: draw_title_close_button())
            close_btn_canvas.after(10, draw_title_close_button)
            close_btn_canvas.bind("<Button-1>", lambda e: viz_window.destroy())

            # Info panel with RESPONSIVE positioning
            info_frame = tk.Frame(main_container, bg=palette['background_3'], relief=tk.RAISED, bd=1)
            info_frame.place(relx=0.02, rely=0.09, relwidth=0.96, relheight=0.06)

            info_font_size = max(10, int(self.screen_width * 0.008))
            info_text = tk.Label(info_frame,
                text=f"Circuit: {self.num_qubits} qubits, {len(self.placed_gates)} gates | "
                    f"Gates: {[gate for gate, _ in self.placed_gates]}",
                font=('Arial', info_font_size), fg=palette['info_panel_text_color'], bg=palette['background_3'])
            info_text.place(relx=0.5, rely=0.5, anchor='center')

            # State information panel - BOTTOM POSITIONED RESPONSIVELY
            state_info_frame = tk.Frame(main_container, bg=palette['background_3'], relief=tk.RAISED, bd=1)
            state_info_frame.place(relx=0.02, rely=0.88, relwidth=0.96, relheight=0.06)

            # Calculate and display state information
            state_data = state_vector.data
            entangled = self.is_state_entangled(state_vector) if self.num_qubits > 1 else False

            info_text = f"🔬 State Analysis: "
            if entangled:
                info_text += "Entangled state detected! "
            else:
                info_text += "Separable state. "

            # Count significant amplitudes
            significant_states = sum(1 for amp in state_data if abs(amp) > 0.001)
            info_text += f"Active basis states: {significant_states}/{2**self.num_qubits}"

            state_font_size = max(10, int(self.screen_width * 0.008))
            state_label = tk.Label(state_info_frame, text=info_text,
                                font=('Arial', state_font_size),
                                fg='#ffffff', bg=palette['background_3'])
            state_label.place(relx=0.5, rely=0.5, anchor='center')

            # Control buttons - BOTTOM POSITIONED RESPONSIVELY
            controls_frame = tk.Frame(main_container, bg=palette['background_3'])
            controls_frame.place(relx=0.02, rely=0.795, relwidth=0.96, relheight=0.08)

            # Button styling with relative font sizes
            button_font_size = max(10, int(self.screen_width * 0.008))

            # Visualization container - TAKES UP REMAINING SPACE RESPONSIVELY
            viz_container = tk.Frame(main_container, bg=palette['background'], relief=tk.SUNKEN, bd=3)
            viz_container.place(relx=0.02, rely=0.16, relwidth=0.96, relheight=0.63)

            # Create matplotlib figure with dark theme
            plt.style.use('dark_background')

            # Choose visualization based on number of qubits
            if self.num_qubits == 1:
                try:
                    fig = plot_bloch_multivector(state_vector)
                    fig.suptitle('Single Qubit Bloch Sphere Visualization',
                            fontsize=max(14, int(self.screen_width * 0.012)),
                            color=palette['sphere_visualization_color'], fontweight='bold')
                except Exception as bloch_error:
                    print(f"Bloch sphere error: {bloch_error}")
                    fig = plot_state_qsphere(state_vector)
                    fig.suptitle('Single Qubit Q-Sphere Visualization',
                            fontsize=max(14, int(self.screen_width * 0.012)),
                            color=palette['sphere_visualization_color'], fontweight='bold')
            else:
                fig = plot_state_qsphere(state_vector)
                fig.suptitle(f'{self.num_qubits}-Qubit Q-Sphere Visualization',
                        fontsize=max(14, int(self.screen_width * 0.012)),
                        color=palette['sphere_visualization_color'], fontweight='bold')

            # Customize the plot appearance
            fig.patch.set_facecolor(palette['background'])

            # Make sure all axes have dark background
            for ax in fig.get_axes():
                ax.set_facecolor(palette['background'])
                ax.tick_params(colors='white')
                ax.xaxis.label.set_color('white')
                ax.yaxis.label.set_color('white')
                if hasattr(ax, 'zaxis'):
                    ax.zaxis.label.set_color('white')

            # Embed the matplotlib figure in tkinter - RESPONSIVE
            canvas = FigureCanvasTkAgg(fig, viz_container)
            canvas.draw()
            canvas.get_tk_widget().place(relx=0.01, rely=0.01, relwidth=0.98, relheight=0.98)

            # Make title bar draggable
            def start_move(event):
                viz_window.x = event.x
                viz_window.y = event.y

            def on_move(event):
                deltax = event.x - viz_window.x
                deltay = event.y - viz_window.y
                x = viz_window.winfo_x() + deltax
                y = viz_window.winfo_y() + deltay
                viz_window.geometry(f"+{x}+{y}")

            title_bar.bind("<Button-1>", start_move)
            title_bar.bind("<B1-Motion>", on_move)
            title_bar_label.bind("<Button-1>", start_move)
            title_bar_label.bind("<B1-Motion>", on_move)

            # Bind Escape key to close
            viz_window.bind('<Escape>', lambda e: viz_window.destroy())

            # Play success sound
            self.play_sound('success', self.play_success_sound_fallback)

        except Exception as e:
            self.show_custom_dialog("Visualization Error", f"Error creating 3D visualization:\n{str(e)}", "error")
            self.play_sound('error', self.play_error_sound_fallback)
            print(f"Full visualization error: {e}")
            import traceback
            traceback.print_exc()



    def is_state_entangled(self, state_vector):
        """Simple check for entanglement (for educational purposes)"""
        try:
            if self.num_qubits != 2:
                return False  # Simple check only for 2 qubits

            # For a 2-qubit state to be separable, it should be expressible as |a⟩⊗|b⟩
            # This is a simplified check
            state_data = state_vector.data

            # Check if the state can be written as a product state
            # |00⟩ + |11⟩ (Bell state) would be entangled
            # |00⟩ or |01⟩ or |10⟩ or |11⟩ would be separable

            # Count non-zero amplitudes
            non_zero_count = sum(1 for amp in state_data if abs(amp) > 0.001)

            # If more than one basis state has significant amplitude, might be entangled
            # This is a very simplified check
            return non_zero_count > 1 and not (abs(state_data[0]) > 0.99 or abs(state_data[1]) > 0.99 or
                                             abs(state_data[2]) > 0.99 or abs(state_data[3]) > 0.99)
        except:
            return False


    def setup_results_area(self, parent):
        """Setup the results display area on the right side"""
        # Enhanced title with responsive font size
        title_font_size = max(14, int(self.screen_width * 0.012))
        results_title = tk.Label(parent, text="Quantum State Analysis",
                                font=('Arial', title_font_size, 'bold'), fg=palette['state_analysis_title_color'], bg=palette['background_3'])
        results_title.pack(pady=(10, 15))

        # Results container with styling
        results_container = tk.Frame(parent, bg=palette['background'], relief=tk.SUNKEN, bd=3)
        results_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Enhanced results text with scrollbar
        text_frame = tk.Frame(results_container, bg=palette['background'])
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Calculate responsive font size for results text
        results_font_size = max(10, int(self.screen_width * 0.008))  # Increased from 9
        
        self.results_text = tk.Text(text_frame, width=40,  # Fixed width for right panel
                                font=('Consolas', results_font_size), bg=palette['background_2'], fg=palette['results_text_color'],
                                relief=tk.FLAT, bd=0, insertbackground=palette['results_background'],
                                selectbackground=palette['results_select_background'], selectforeground=palette['background_black'],
                                wrap=tk.WORD)

        # Add scrollbar with responsive width
        scrollbar_width = max(15, int(self.screen_width * 0.01))
        scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.results_text.yview,
                                bg=palette['background_4'], troughcolor=palette['background'], 
                                activebackground=palette['scrollbar_active_background'],
                                width=scrollbar_width)
        self.results_text.configure(yscrollcommand=scrollbar.set)

        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Initial message with responsive formatting
        welcome_font_size = max(12, int(self.screen_width * 0.009))
        instruction_font_size = max(10, int(self.screen_width * 0.008))
        
        # Configure text tags for different font sizes
        self.results_text.tag_configure("welcome", font=('Consolas', welcome_font_size, 'bold'))
        self.results_text.tag_configure("instruction", font=('Consolas', instruction_font_size))
        self.results_text.tag_configure("normal", font=('Consolas', results_font_size))

        # Insert initial message with tags
        self.results_text.insert(tk.END, "Welcome to Quantum Circuit Sandbox!\n\n", "welcome")
        self.results_text.insert(tk.END, "Build your circuit and click 'Run Circuit' to see the results.\n\n", "instruction")
        self.results_text.insert(tk.END, "Instructions:\n", "instruction")
        self.results_text.insert(tk.END, "1. Select gates from the palette\n", "normal")
        self.results_text.insert(tk.END, "2. Configure qubits and initial states\n", "normal")
        self.results_text.insert(tk.END, "3. Run your circuit to see quantum state analysis\n", "normal")
        self.results_text.configure(state=tk.DISABLED)



    def setup_single_gate_controls(self, parent):
        """Setup single-qubit gate controls with canvas-based buttons and responsive design"""
        # Create a frame that works with ttk parent
        container = tk.Frame(parent)
        container.configure(bg=palette['background_3'])
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Gate buttons section title
        title_font_size = max(10, int(self.screen_width * 0.009))
        gates_title = tk.Label(container, text="Single-Qubit Gates:",
                            font=('Arial', title_font_size, 'bold'),
                            fg=palette['single_qubit_gates_title_color'], bg=palette['background_3'])
        gates_title.place(relx=0.5, rely=0.1, anchor='center')

        # Gate data
        gate_colors = {
            'H': palette['H_color'], 'X': palette['X_color'], 'Y': palette['Y_color'],
            'Z': palette['Z_color'], 'S': palette['S_color'], 'T': palette['T_color']
        }

        gate_descriptions = {
            'H': 'Hadamard',
            'X': 'Pauli-X',
            'Y': 'Pauli-Y',
            'Z': 'Pauli-Z',
            'S': 'S Gate',
            'T': 'T Gate'
        }

        single_gates = ['H', 'X', 'Y', 'Z', 'S', 'T']

        # Calculate relative font sizes
        button_font_size = max(10, int(self.screen_width * 0.009))
        desc_font_size = max(7, int(self.screen_width * 0.0055))

        # Create 2x3 grid with relative positioning
        button_positions = [
            # Row 1: H, X, Y
            (0.15, 0.35), (0.5, 0.35), (0.85, 0.35),
            # Row 2: Z, S, T
            (0.15, 0.75), (0.5, 0.75), (0.85, 0.75)
        ]

        for i, gate in enumerate(single_gates):
            color = gate_colors.get(gate, '#ffffff')
            description = gate_descriptions.get(gate, '')
            relx, rely = button_positions[i]

            # Create button container with relative positioning
            btn_container = tk.Frame(container, bg=palette['background_4'], relief=tk.RAISED, bd=1)
            btn_container.place(relx=relx, rely=rely, relwidth=0.25, relheight=0.3, anchor='center')

            # Canvas button with relative dimensions
            btn_canvas = tk.Canvas(btn_container, highlightthickness=0, bd=0, bg=color)
            btn_canvas.place(relx=0.5, rely=0.4, relwidth=0.8, relheight=0.7, anchor='center')

            # Create button background and text
            def draw_button(event=None, canvas=btn_canvas, gate_color=color, gate_text=gate):
                canvas.delete("all")
                width = canvas.winfo_width()
                height = canvas.winfo_height()
                if width > 1 and height > 1:  # Only draw if we have valid dimensions
                    canvas.create_rectangle(0, 0, width, height, fill=gate_color, outline=gate_color, tags="bg")
                    canvas.create_text(width//2, height//2, text=gate_text,
                                    font=('Arial', button_font_size, 'bold'),
                                    fill=palette['background_black'], tags="text")

            # Bind configure event to redraw when size changes
            btn_canvas.bind('<Configure>', draw_button)
            # Initial draw after the widget is mapped
            btn_canvas.after(10, draw_button)

            # Click handler
            def on_button_click(event, g=gate):
                self.add_single_gate(g)

            # Hover effects
            def on_enter(event, canvas=btn_canvas, gate_color=color):
                canvas.delete("bg")
                width = canvas.winfo_width()
                height = canvas.winfo_height()
                if width > 1 and height > 1:
                    canvas.create_rectangle(0, 0, width, height, fill=palette['button_hover_background'], outline=palette['button_hover_background'], tags="bg")
                canvas.configure(cursor='hand2')
                canvas.tag_lower("bg")

            def on_leave(event, canvas=btn_canvas, gate_color=color):
                canvas.delete("bg")
                width = canvas.winfo_width()
                height = canvas.winfo_height()
                if width > 1 and height > 1:
                    canvas.create_rectangle(0, 0, width, height, fill=gate_color, outline=gate_color, tags="bg")
                canvas.configure(cursor='')
                canvas.tag_lower("bg")

            # Bind events
            btn_canvas.bind("<Button-1>", on_button_click)
            btn_canvas.bind("<Enter>", on_enter)
            btn_canvas.bind("<Leave>", on_leave)

            # Description label with relative positioning
            desc_label = tk.Label(btn_container, text=description,
                                font=('Arial', desc_font_size),
                                fg=palette['gate_description_color'], bg=palette['background_4'])
            desc_label.place(relx=0.5, rely=0.87, anchor='center')


    def setup_multi_gate_controls(self, parent):
        """Setup multi-qubit gate controls with canvas-based buttons similar to single-qubit gates"""
        # Create a frame that works with ttk parent
        container = tk.Frame(parent)
        container.configure(bg=palette['background_3'])
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Gate buttons section title
        title_font_size = max(10, int(self.screen_width * 0.009))
        gates_title = tk.Label(container, text="Multi-Qubit Gates:",
                            font=('Arial', title_font_size, 'bold'),
                            fg=palette['multi_qubit_gates_title_color'], bg=palette['background_3'])
        gates_title.place(relx=0.5, rely=0.1, anchor='center')

        # Gate data
        gate_colors = {
            'CNOT': palette['CNOT_color'], 
            'CZ': palette['CZ_gate_title_color'], 
            'Toffoli': palette['Toffoli_color']
        }

        gate_descriptions = {
            'CNOT': 'Controlled-X',
            'CZ': 'Controlled-Z',
            'Toffoli': 'CCNOT Gate'
        }

        # Define which gates to show based on number of qubits
        multi_gates = []
        if self.num_qubits >= 2:
            multi_gates.extend(['CNOT', 'CZ'])
        if self.num_qubits >= 3:
            multi_gates.append('Toffoli')

        if not multi_gates:
            # Show message if no multi-qubit gates available
            no_gates_label = tk.Label(container, text="Add more qubits to enable multi-qubit gates",
                                    font=('Arial', max(9, int(self.screen_width * 0.007))),
                                    fg=palette['subtitle_color'], bg=palette['background_3'])
            no_gates_label.place(relx=0.5, rely=0.5, anchor='center')
            return

        # Calculate relative font sizes
        button_font_size = max(10, int(self.screen_width * 0.009))
        desc_font_size = max(7, int(self.screen_width * 0.0055))

        # Create responsive grid layout
        if len(multi_gates) == 1:
            button_positions = [(0.5, 0.5)]
        elif len(multi_gates) == 2:
            button_positions = [(0.3, 0.5), (0.7, 0.5)]
        else:  # 3 gates
            button_positions = [(0.2, 0.5), (0.5, 0.5), (0.8, 0.5)]

        for i, gate in enumerate(multi_gates):
            color = gate_colors.get(gate, '#ffffff')
            description = gate_descriptions.get(gate, '')
            relx, rely = button_positions[i]

            # Create button container with relative positioning
            btn_container = tk.Frame(container, bg=palette['background_4'], relief=tk.RAISED, bd=1)
            btn_container.place(relx=relx, rely=rely, relwidth=0.25, relheight=0.4, anchor='center')

            # Canvas button with relative dimensions
            btn_canvas = tk.Canvas(btn_container, highlightthickness=0, bd=0, bg=color)
            btn_canvas.place(relx=0.5, rely=0.4, relwidth=0.8, relheight=0.7, anchor='center')

            # Create button background and text
            def draw_button(event=None, canvas=btn_canvas, gate_color=color, gate_text=gate):
                canvas.delete("all")
                width = canvas.winfo_width()
                height = canvas.winfo_height()
                if width > 1 and height > 1:  # Only draw if we have valid dimensions
                    canvas.create_rectangle(0, 0, width, height, fill=gate_color, outline=gate_color, tags="bg")
                    # Adjust font size for multi-qubit gate names
                    font_size = max(8, int(min(width, height) * 0.15))
                    canvas.create_text(width//2, height//2, text=gate_text,
                                    font=('Arial', font_size, 'bold'),
                                    fill=palette['background_black'], tags="text")

            # Bind configure event to redraw when size changes
            btn_canvas.bind('<Configure>', draw_button)
            # Initial draw after the widget is mapped
            btn_canvas.after(10, draw_button)

            # Click handler
            def on_button_click(event, g=gate):
                self.add_multi_qubit_gate(g)

            # Hover effects
            def on_enter(event, canvas=btn_canvas, gate_color=color):
                canvas.delete("bg")
                width = canvas.winfo_width()
                height = canvas.winfo_height()
                if width > 1 and height > 1:
                    canvas.create_rectangle(0, 0, width, height, fill=palette['button_hover_background'], outline=palette['button_hover_background'], tags="bg")
                canvas.configure(cursor='hand2')
                canvas.tag_lower("bg")

            def on_leave(event, canvas=btn_canvas, gate_color=color):
                canvas.delete("bg")
                width = canvas.winfo_width()
                height = canvas.winfo_height()
                if width > 1 and height > 1:
                    canvas.create_rectangle(0, 0, width, height, fill=gate_color, outline=gate_color, tags="bg")
                canvas.configure(cursor='')
                canvas.tag_lower("bg")

            # Bind events
            btn_canvas.bind("<Button-1>", on_button_click)
            btn_canvas.bind("<Enter>", on_enter)
            btn_canvas.bind("<Leave>", on_leave)

            # Description label with relative positioning
            desc_label = tk.Label(btn_container, text=description,
                                font=('Arial', desc_font_size),
                                fg=palette['gate_description_color'], bg=palette['background_4'])
            desc_label.place(relx=0.5, rely=0.87, anchor='center')

    def add_single_gate(self, gate):
        """Add a single-qubit gate to the selected qubit"""
        # Place gate on the currently selected qubit (no dialog needed)
        self.placed_gates.append((gate, [self.selected_qubit]))
        self.update_circuit_display()
        self.play_sound('gate_place', self.play_gate_sound_fallback)

    def add_multi_qubit_gate(self, gate):
        """Add a multi-qubit gate with appropriate qubit selection dialogs"""
        # Check if enough qubits are available
        required_qubits = 2 if gate in ['CNOT', 'CZ'] else 3
        
        if self.num_qubits < required_qubits:
            self.show_custom_dialog("Warning", 
                                  f"{gate} gate requires at least {required_qubits} qubits", 
                                  "warning")
            self.play_sound('error', self.play_error_sound_fallback)
            return
        
        # Show appropriate qubit selection dialogs based on gate type
        if gate in ['CNOT', 'CZ']:
            self.show_two_qubit_gate_dialog(gate)
        elif gate == 'Toffoli':
            self.show_three_qubit_gate_dialog(gate)

    def show_two_qubit_gate_dialog(self, gate):
        """Show dialog sequence for selecting two qubits (control and target)"""
        self.selected_qubits = []
        self.current_gate = gate
        
        # First dialog: Select control qubit
        self.show_qubit_selection_dialog_multi(
            gate, 
            "Control", 
            f"Select the control qubit for the {gate} gate:",
            self.on_control_qubit_selected
        )

    def show_three_qubit_gate_dialog(self, gate):
        """Show dialog sequence for selecting three qubits (control1, control2, target)"""
        self.selected_qubits = []
        self.current_gate = gate
        
        # First dialog: Select first control qubit
        self.show_qubit_selection_dialog_multi(
            gate,
            "Control 1",
            f"Select the first control qubit for the {gate} gate:",
            self.on_first_control_qubit_selected
        )

    def show_qubit_selection_dialog_multi(self, gate, selection_type, instruction_text, callback):
        """Show a qubit selection dialog for multi-qubit gates"""
        self.play_sound('click')

        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title(f"{gate} Gate - {selection_type}")
        dialog.configure(bg=palette['background'])

        # Make dialog fullscreen-compatible and always on top
        dialog.overrideredirect(True)
        dialog.attributes('-topmost', True)

        # Calculate responsive size
        dialog_width = int(self.screen_width * 0.4)
        dialog_height = int(self.screen_height * 0.5)
        x = (self.screen_width - dialog_width) // 2
        y = (self.screen_height - dialog_height) // 2
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

        dialog.transient(self.root)
        try:
            dialog.grab_set()
            dialog.focus_force()
        except tk.TclError:
            self.root.after(50, lambda: dialog.grab_set() if dialog.winfo_exists() else None)
            dialog.focus_force()

        # Border frame
        border_frame = tk.Frame(dialog, bg=palette['main_menu_button_text_color'], bd=2, relief=tk.RAISED)
        border_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Main frame
        main_frame = tk.Frame(border_frame, bg=palette['background_3'])
        main_frame.place(relx=0.01, rely=0.01, relwidth=0.98, relheight=0.98)

        # Title bar
        title_bar = tk.Frame(main_frame, bg=palette['background_4'])
        title_bar.place(relx=0, rely=0, relwidth=1, relheight=0.15)

        # Title
        title_font_size = max(12, int(self.screen_width * 0.01))
        title_label = tk.Label(title_bar, text=f"🎯 {gate} Gate - {selection_type}",
                            font=('Arial', title_font_size, 'bold'),
                            fg=palette['title_color'], bg=palette['background_4'])
        title_label.place(relx=0.05, rely=0.5, anchor='w')

        # Close button
        close_canvas = tk.Canvas(title_bar, bg=palette['background_4'], highlightthickness=0, bd=0)
        close_canvas.place(relx=0.9, rely=0.5, relwidth=0.08, relheight=0.6, anchor='center')

        def draw_close_button():
            close_canvas.delete("all")
            close_canvas.update_idletasks()
            width = close_canvas.winfo_width()
            height = close_canvas.winfo_height()
            if width > 1 and height > 1:
                close_canvas.create_rectangle(2, 2, width-2, height-2,
                                            fill=palette['background_4'], 
                                            outline=palette['title_color'], width=1, tags="bg")
                close_canvas.create_text(width//2, height//2, text="✕",
                                    font=('Arial', int(min(width, height) * 0.4), 'bold'), 
                                    fill=palette['title_color'], tags="text")

        close_canvas.bind('<Configure>', lambda e: draw_close_button())
        close_canvas.after(10, draw_close_button)
        close_canvas.bind("<Button-1>", lambda e: dialog.destroy())

        # Hover effects for close button
        def close_on_enter(event):
            close_canvas.itemconfig("bg", fill=palette['button_hover_background'])
            close_canvas.itemconfig("text", fill=palette['button_hover_text_color'])
            close_canvas.configure(cursor='hand2')

        def close_on_leave(event):
            close_canvas.itemconfig("bg", fill=palette['background_4'])
            close_canvas.itemconfig("text", fill=palette['title_color'])
            close_canvas.configure(cursor='')

        close_canvas.bind("<Enter>", close_on_enter)
        close_canvas.bind("<Leave>", close_on_leave)

        # Content area
        content_frame = tk.Frame(main_frame, bg=palette['background_3'])
        content_frame.place(relx=0, rely=0.15, relwidth=1, relheight=0.85)

        # Create grid of qubit buttons for multi-qubit gate placement
        self.create_multi_qubit_selection_grid(content_frame, dialog, gate, instruction_text, callback)

        # Make title bar draggable
        def start_move(event):
            dialog.x = event.x_root - dialog.winfo_x()
            dialog.y = event.y_root - dialog.winfo_y()

        def on_move(event):
            x = event.x_root - dialog.x
            y = event.y_root - dialog.y
            dialog.geometry(f"+{x}+{y}")

        title_bar.bind("<Button-1>", start_move)
        title_bar.bind("<B1-Motion>", on_move)
        title_label.bind("<Button-1>", start_move)
        title_label.bind("<B1-Motion>", on_move)

        # Bind Escape to close
        dialog.bind('<Escape>', lambda e: dialog.destroy())

    def create_multi_qubit_selection_grid(self, parent, dialog, gate, instruction_text, callback):
        """Create a responsive grid of qubit selection buttons for multi-qubit gate placement"""
        # Calculate grid dimensions based on number of qubits
        if self.num_qubits <= 2:
            cols = 2
            rows = 1
        elif self.num_qubits <= 4:
            cols = 2
            rows = 2
        else:
            cols = 3
            rows = (self.num_qubits + cols - 1) // cols

        # Create instruction label
        instruction_font = max(10, int(self.screen_width * 0.008))
        instruction_label = tk.Label(parent, text=instruction_text,
                                font=('Arial', instruction_font),
                                fg=palette['subtitle_color'], bg=palette['background_3'])
        instruction_label.place(relx=0.5, rely=0.1, anchor='center')

        # Create grid of buttons
        button_font_size = max(12, int(self.screen_width * 0.01))
        
        for qubit in range(self.num_qubits):
            row = qubit // cols
            col = qubit % cols

            # Calculate button position using relative coordinates
            button_relx = (col + 0.5) / cols
            button_rely = 0.3 + (row + 0.5) / rows * 0.6
            button_relwidth = 0.8 / cols
            button_relheight = min(0.4 / rows, 0.15)

            # Disable already selected qubits
            is_disabled = hasattr(self, 'selected_qubits') and qubit in self.selected_qubits

            # Create button frame
            btn_frame = tk.Frame(parent, bg=palette['background_4'], relief=tk.RAISED, bd=2)
            btn_frame.place(relx=button_relx, rely=button_rely, 
                        relwidth=button_relwidth, relheight=button_relheight, anchor='center')

            # Create canvas button
            btn_canvas = tk.Canvas(btn_frame, bg=palette['background'], highlightthickness=0, bd=0)
            btn_canvas.place(relx=0.1, rely=0.1, relwidth=0.8, relheight=0.8)

            def draw_qubit_button(event=None, canvas=btn_canvas, qubit_num=qubit, disabled=is_disabled):
                canvas.delete("all")
                canvas.update_idletasks()
                width = canvas.winfo_width()
                height = canvas.winfo_height()
                if width > 1 and height > 1:
                    if disabled:
                        bg_color = palette['background_2']
                        text_color = palette['gate_description_color']
                    else:
                        bg_color = palette['background']
                        text_color = palette['combobox_color']
                    
                    canvas.create_rectangle(2, 2, width-2, height-2,
                                        fill=bg_color, 
                                        outline=palette['combobox_color'], width=2, tags="bg")
                    
                    # Qubit text
                    qubit_font_size = max(10, int(min(width, height) * 0.3))
                    canvas.create_text(width//2, height//2, text=f"q{qubit_num}",
                                    font=('Arial', qubit_font_size, 'bold'), 
                                    fill=text_color, tags="text")

            btn_canvas.bind('<Configure>', draw_qubit_button)
            btn_canvas.after(10, draw_qubit_button)

            if not is_disabled:
                # Click handler
                def create_qubit_handler(selected_qubit):
                    def on_qubit_select(event):
                        callback(selected_qubit, dialog)
                    return on_qubit_select

                btn_canvas.bind("<Button-1>", create_qubit_handler(qubit))

                # Hover effects
                def create_hover_handlers(canvas, qubit_num):
                    def on_enter(event):
                        canvas.itemconfig("bg", fill=palette['button_hover_background'])
                        canvas.itemconfig("text", fill=palette['button_hover_text_color'])
                        canvas.configure(cursor='hand2')

                    def on_leave(event):
                        canvas.itemconfig("bg", fill=palette['background'])
                        canvas.itemconfig("text", fill=palette['combobox_color'])
                        canvas.configure(cursor='')

                    return on_enter, on_leave

                on_enter, on_leave = create_hover_handlers(btn_canvas, qubit)
                btn_canvas.bind("<Enter>", on_enter)
                btn_canvas.bind("<Leave>", on_leave)

    def on_control_qubit_selected(self, qubit, dialog):
        """Handle control qubit selection for two-qubit gates"""
        self.selected_qubits.append(qubit)
        self.play_sound('click')
        dialog.destroy()
        
        # Show second dialog for target qubit
        self.show_qubit_selection_dialog_multi(
            self.current_gate,
            "Target",
            f"Select the target qubit for the {self.current_gate} gate:",
            self.on_target_qubit_selected
        )

    def on_target_qubit_selected(self, qubit, dialog):
        """Handle target qubit selection for two-qubit gates"""
        self.selected_qubits.append(qubit)
        self.play_sound('click')
        dialog.destroy()
        
        # Validate selection and place gate
        self.validate_and_place_two_qubit_gate()

    def on_first_control_qubit_selected(self, qubit, dialog):
        """Handle first control qubit selection for three-qubit gates"""
        self.selected_qubits.append(qubit)
        self.play_sound('click')
        dialog.destroy()
        
        # Show second dialog for second control qubit
        self.show_qubit_selection_dialog_multi(
            self.current_gate,
            "Control 2",
            f"Select the second control qubit for the {self.current_gate} gate:",
            self.on_second_control_qubit_selected
        )

    def on_second_control_qubit_selected(self, qubit, dialog):
        """Handle second control qubit selection for three-qubit gates"""
        self.selected_qubits.append(qubit)
        self.play_sound('click')
        dialog.destroy()
        
        # Show third dialog for target qubit
        self.show_qubit_selection_dialog_multi(
            self.current_gate,
            "Target",
            f"Select the target qubit for the {self.current_gate} gate:",
            self.on_three_qubit_target_selected
        )

    def on_three_qubit_target_selected(self, qubit, dialog):
        """Handle target qubit selection for three-qubit gates"""
        self.selected_qubits.append(qubit)
        self.play_sound('click')
        dialog.destroy()
        
        # Validate selection and place gate
        self.validate_and_place_three_qubit_gate()

    def validate_and_place_two_qubit_gate(self):
        """Validate two-qubit gate selection and place the gate"""
        control, target = self.selected_qubits
        
        # Check if qubits are different
        if control == target:
            self.show_custom_dialog("Invalid Selection", 
                                  "Control and target qubits must be different", 
                                  "warning")
            self.play_sound('error', self.play_error_sound_fallback)
            return
        
        # Check if qubits are valid
        if control >= self.num_qubits or target >= self.num_qubits:
            self.show_custom_dialog("Invalid Selection", 
                                  "Invalid qubit selection", 
                                  "warning")
            self.play_sound('error', self.play_error_sound_fallback)
            return
        
        # Place the gate
        self.placed_gates.append((self.current_gate, [control, target]))
        self.update_circuit_display()
        self.play_sound('gate_place', self.play_gate_sound_fallback)

    def validate_and_place_three_qubit_gate(self):
        """Validate three-qubit gate selection and place the gate"""
        c1, c2, target = self.selected_qubits
        
        # Check if all qubits are different
        if len(set([c1, c2, target])) != 3:
            self.show_custom_dialog("Invalid Selection", 
                                  "All three qubits must be different", 
                                  "warning")
            self.play_sound('error', self.play_error_sound_fallback)
            return
        
        # Check if qubits are valid
        if c1 >= self.num_qubits or c2 >= self.num_qubits or target >= self.num_qubits:
            self.show_custom_dialog("Invalid Selection", 
                                  "Invalid qubit selection", 
                                  "warning")
            self.play_sound('error', self.play_error_sound_fallback)
            return
        
        # Place the gate
        self.placed_gates.append((self.current_gate, [c1, c2, target]))
        self.update_circuit_display()
        self.play_sound('gate_place', self.play_gate_sound_fallback)


    def add_gate(self, gate):
        """Add a gate to the circuit"""
        # For multi-qubit gates, we need to specify which qubits
        if gate in ['CNOT', 'CZ'] and self.num_qubits < 2:
            messagebox.showwarning("Warning", f"{gate} gate requires at least 2 qubits")
            return
        elif gate == 'Toffoli' and self.num_qubits < 3:
            messagebox.showwarning("Warning", "Toffoli gate requires at least 3 qubits")
            return

        # For simplicity, apply multi-qubit gates to consecutive qubits
        if gate in ['CNOT', 'CZ']:
            self.placed_gates.append((gate, [0, 1]))
        elif gate == 'Toffoli':
            self.placed_gates.append((gate, [0, 1, 2]))
        else:
            # Single qubit gate - apply to currently selected qubit
            self.placed_gates.append((gate, [self.selected_qubit]))

        self.update_circuit_display()

        # Play sound if available
        if self.sound_enabled:
            try:
                # Create a simple beep for gate placement
                frequency = 440
                duration = 0.1
                sample_rate = 22050
                frames = int(duration * sample_rate)
                arr = np.sin(2 * np.pi * frequency * np.linspace(0, duration, frames))
                arr = (arr * 16383).astype(np.int16)
                sound = pygame.sndarray.make_sound(arr)
                sound.set_volume(0.3)
                sound.play()
            except:
                pass


    def clear_circuit(self):
        """Clear all gates from the circuit"""
        self.placed_gates = []
        self.update_circuit_display()

        # Clear and update results
        self.results_text.configure(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, " Circuit cleared. Ready for new gates.\n")
        self.results_text.insert(tk.END, "Add gates using the Gate Palette and click 'Run Circuit' to see results.\n")
        self.results_text.configure(state=tk.DISABLED)

        self.play_sound('clear', self.play_clear_sound_fallback)


    def undo_gate(self):
        """Remove the last placed gate"""
        if self.placed_gates:
            removed_gate = self.placed_gates.pop()
            self.update_circuit_display()

            # Update results
            self.results_text.configure(state=tk.NORMAL)
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"↶ Undid last gate: {removed_gate[0]}\n")
            self.results_text.insert(tk.END, f"Gates remaining: {len(self.placed_gates)}\n")
            self.results_text.configure(state=tk.DISABLED)

            self.play_sound('click')
        else:
            # No gates to undo
            self.results_text.configure(state=tk.NORMAL)
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, " No gates to undo.\n")
            self.results_text.configure(state=tk.DISABLED)
            self.play_sound('error', self.play_error_sound_fallback)


    def on_qubit_change(self):
        """Handle change in number of qubits"""
        self.num_qubits = self.qubit_var.get()
        self.placed_gates = []  # Clear gates when changing qubit count
        
        # Reset selected qubit if it's out of range
        if self.selected_qubit >= self.num_qubits:
            self.selected_qubit = 0

        # Update available initial states based on qubit count
        if self.num_qubits == 1:
            states = ["|0⟩", "|1⟩", "|+⟩", "|-⟩"]
        elif self.num_qubits == 2:
            states = ["|00⟩", "|01⟩", "|10⟩", "|11⟩", "|++⟩"]
        elif self.num_qubits == 3:
            states = ["|000⟩", "|001⟩", "|010⟩", "|011⟩", "|100⟩", "|101⟩", "|110⟩", "|111⟩"]
        elif self.num_qubits == 4:
            states = ["|0000⟩", "|0001⟩", "|0010⟩", "|0011⟩", "|0100⟩", "|0101⟩", "|0110⟩", "|0111⟩",
                "|1000⟩", "|1001⟩", "|1010⟩", "|1011⟩", "|1100⟩", "|1101⟩", "|1110⟩", "|1111⟩"]
        else:
            states = ["|" + "0" * self.num_qubits + "⟩"]

        self.update_state_combobox(states)
        self.state_var.set(states[0])
        self.initial_state = states[0]

        # Update the qubit selection dropdowns
        self.update_qubit_selections()

        self.update_circuit_display()


    def update_qubit_selections(self):
        """Update all qubit selection dropdowns when number of qubits cf there are any remaining issues or missing pieces in the multi-qubit selection syshanges"""
        # Note: Since we now use dialog-based selection for multi-qubit gates,
        # this method no longer needs to update multi-qubit gate controls
        pass


    def update_state_combobox(self, states):
        """Update the state combobox with new values"""
        # Find and update the combobox
        # This is a bit tricky since we need to access the widget
        # Let's store a reference to the combobox in setup_control_panel
        if hasattr(self, 'state_combo'):
            self.state_combo['values'] = states


    def on_state_change(self, event=None):
        """Handle change in initial state"""
        self.initial_state = self.state_var.get()
        self.update_circuit_display()


    def update_circuit_display(self):
        """Update the circuit visualization with enhanced graphics"""
        self.circuit_canvas.delete("all")

        if self.num_qubits == 0:
            return

        # Enhanced circuit drawing parameters
        wire_start = 80  # Increased from 60 to make room for arrow
        wire_end = self.canvas_width - 60
        qubit_spacing = max(40, self.canvas_height // (self.num_qubits + 2))

        # Draw enhanced background grid
        for i in range(0, self.canvas_width, 50):
            self.circuit_canvas.create_line(i, 0, i, self.canvas_height,
                                          fill=palette['background'], width=1)

        # Draw enhanced qubit wires with colors (greyed out if not selected)
        wire_colors = [palette['quantum_wire_1'], palette['quantum_wire_2'], palette['quantum_wire_3'], palette['quantum_wire_4']]

        for qubit in range(self.num_qubits):
            y_pos = (qubit + 1) * qubit_spacing + 20
            color = wire_colors[qubit % len(wire_colors)]
            
            # Grey out non-selected wires
            is_selected = (qubit == self.selected_qubit)
            if not is_selected:
                # Make wire greyed out
                color = '#888888'  # Grey color
                alpha = 0.5
            else:
                alpha = 1.0

            # Draw wire with gradient effect (multiple lines for thickness)
            for thickness in [6, 4, 2]:
                line_alpha = (0.3 + (thickness / 6) * 0.7) * alpha
                self.circuit_canvas.create_line(wire_start, y_pos, wire_end, y_pos,
                                              fill=color, width=thickness)

            # Enhanced qubit label with larger clickable background
            label_width = 45  # Increased from 30 for easier clicking
            label_height = 18  # Increased from 12 for easier clicking
            
            label_bg_color = palette['level_button_color'] if is_selected else palette['background_4']
            label_text_color = palette['level_button_text_color'] if is_selected else '#ffffff'
            
            label_bg = self.circuit_canvas.create_rectangle(wire_start - label_width, y_pos - label_height,
                                                          wire_start - 5, y_pos + label_height,
                                                          fill=label_bg_color, outline=color, width=2,
                                                          tags=f"qubit_label_{qubit}")

            label_text = self.circuit_canvas.create_text(wire_start - 22, y_pos,
                                          text=f"q{qubit}", fill=label_text_color,
                                          font=('Arial', 12, 'bold'),
                                          tags=f"qubit_label_{qubit}")
            
            # Make qubit label clickable
            self.circuit_canvas.tag_bind(f"qubit_label_{qubit}", "<Button-1>", 
                                        lambda e, q=qubit: self.select_qubit(q))
            self.circuit_canvas.tag_bind(f"qubit_label_{qubit}", "<Enter>", 
                                        lambda e: self.circuit_canvas.configure(cursor='hand2'))
            self.circuit_canvas.tag_bind(f"qubit_label_{qubit}", "<Leave>", 
                                        lambda e: self.circuit_canvas.configure(cursor=''))

        # Draw arrow pointing to selected qubit
        selected_y_pos = (self.selected_qubit + 1) * qubit_spacing + 20
        arrow_x = wire_start - 55
        # Draw arrow pointing to the right
        self.circuit_canvas.create_polygon(
            arrow_x, selected_y_pos,
            arrow_x - 10, selected_y_pos - 8,
            arrow_x - 10, selected_y_pos + 8,
            fill=palette.get('level_button_text_color', '#ffb86b'),
            outline=palette.get('level_button_color', '#ffb86b')
        )

        # Draw enhanced gates
        self.draw_enhanced_gates(wire_start, qubit_spacing)

        # Update status labels if they exist
        if hasattr(self, 'gates_count_label'):
            self.gates_count_label.configure(text=f"Gates: {len(self.placed_gates)}")
        if hasattr(self, 'qubits_info_label'):
            self.qubits_info_label.configure(text=f"Qubits: {self.num_qubits}")


    def select_qubit(self, qubit):
        """Select a qubit for single-qubit gate placement"""
        if 0 <= qubit < self.num_qubits:
            self.selected_qubit = qubit
            self.update_circuit_display()
            self.play_sound('click')


    def draw_enhanced_gates(self, wire_start, qubit_spacing):
        """Draw gates with enhanced 3D styling"""
        gate_x_start = wire_start + 100
        gate_spacing = 100

        gate_colors = {
            'H': palette['H_color'], 'X': palette['X_color'], 'Y': palette['Y_color'],
            'Z': palette['Z_color'], 'S': palette['S_color'], 'T': palette['T_color'],
            'CNOT': palette['CNOT_color'], 'CZ': palette['CZ_color'], 'Toffoli': palette['Toffoli_color']
        }

        for i, (gate, qubits) in enumerate(self.placed_gates):
            x = gate_x_start + i * gate_spacing
            color = gate_colors.get(gate, '#ffffff')

            if len(qubits) == 1:
                # Enhanced single qubit gate
                qubit = qubits[0]
                if qubit < self.num_qubits:
                    y_pos = (qubit + 1) * qubit_spacing + 20

                    # 3D shadow effect
                    self.circuit_canvas.create_rectangle(x - 22, y_pos - 17,
                                                        x + 22, y_pos + 17,
                                                        fill=palette['background_black'], outline='')

                    # Main gate with gradient effect
                    self.circuit_canvas.create_rectangle(x - 20, y_pos - 15,
                                                        x + 20, y_pos + 15,
                                                        fill=color, outline='#ffffff', width=2)

                    # Inner highlight
                    self.circuit_canvas.create_rectangle(x - 18, y_pos - 13,
                                                        x + 18, y_pos + 13,
                                                        fill='', outline='#ffffff', width=1)

                    # Gate symbol with shadow
                    self.circuit_canvas.create_text(x + 1, y_pos + 1, text=gate,
                                                   fill=palette['background_black'], font=('Arial', 11, 'bold'))
                    self.circuit_canvas.create_text(x, y_pos, text=gate,
                                                   fill=palette['background_black'], font=('Arial', 12, 'bold'))

            elif len(qubits) == 2 and gate in ['CNOT', 'CZ']:
                # Enhanced two-qubit gate
                control_qubit, target_qubit = qubits
                if control_qubit < self.num_qubits and target_qubit < self.num_qubits:
                    control_y = (control_qubit + 1) * qubit_spacing + 20
                    target_y = (target_qubit + 1) * qubit_spacing + 20

                    # Enhanced control dot with 3D effect
                    self.circuit_canvas.create_oval(x - 10, control_y - 10,
                                                   x + 10, control_y + 10,
                                                   fill=palette['background_black'], outline='')
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
                                                       fill=palette['background_black'], outline='')
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
                                                       fill=palette['background_black'], outline='')
                        self.circuit_canvas.create_oval(x - 8, target_y - 8,
                                                       x + 8, target_y + 8,
                                                       fill='#ffffff', outline='#cccccc', width=2)

            elif len(qubits) == 3 and gate == 'Toffoli':
                # Enhanced three-qubit Toffoli gate
                control1_qubit, control2_qubit, target_qubit = qubits
                if (control1_qubit < self.num_qubits and control2_qubit < self.num_qubits and 
                    target_qubit < self.num_qubits):
                    
                    control1_y = (control1_qubit + 1) * qubit_spacing + 20
                    control2_y = (control2_qubit + 1) * qubit_spacing + 20
                    target_y = (target_qubit + 1) * qubit_spacing + 20
                    
                    # Find the min and max y positions for the connection line
                    min_y = min(control1_y, control2_y, target_y)
                    max_y = max(control1_y, control2_y, target_y)
                    
                    # Enhanced connection line spanning all qubits
                    self.circuit_canvas.create_line(x, min_y, x, max_y,
                                                   fill='#ffffff', width=4)
                    self.circuit_canvas.create_line(x, min_y, x, max_y,
                                                   fill=color, width=2)
                    
                    # Enhanced control dots with 3D effect
                    for control_y in [control1_y, control2_y]:
                        self.circuit_canvas.create_oval(x - 10, control_y - 10,
                                                       x + 10, control_y + 10,
                                                       fill=palette['background_black'], outline='')
                        self.circuit_canvas.create_oval(x - 8, control_y - 8,
                                                       x + 8, control_y + 8,
                                                       fill='#ffffff', outline='#cccccc', width=2)
                    
                    # Enhanced Toffoli target (same as CNOT target)
                    self.circuit_canvas.create_oval(x - 17, target_y - 17,
                                                   x + 17, target_y + 17,
                                                   fill=palette['background_black'], outline='')
                    self.circuit_canvas.create_oval(x - 15, target_y - 15,
                                                   x + 15, target_y + 15,
                                                   fill='', outline='#ffffff', width=3)
                    
                    # X symbol for target
                    self.circuit_canvas.create_line(x - 8, target_y - 8,
                                                   x + 8, target_y + 8,
                                                   fill='#ffffff', width=3)
                    self.circuit_canvas.create_line(x - 8, target_y + 8,
                                                   x + 8, target_y - 8,
                                                   fill='#ffffff', width=3)

    def run_circuit(self):
        """Execute the quantum circuit and display results"""
        try:
            # Clear previous results first
            self.results_text.configure(state=tk.NORMAL)
            self.results_text.delete(1.0, tk.END)

            # Check if there are any gates to run
            if not self.placed_gates:
                self.results_text.insert(tk.END, "No gates placed. Add some gates to your circuit first.\n")
                self.results_text.configure(state=tk.DISABLED)
                return

            # Display current circuit info
            self.results_text.insert(tk.END, f" Running Quantum Circuit...\n")
            self.results_text.insert(tk.END, f"Qubits: {self.num_qubits}\n")
            self.results_text.insert(tk.END, f"Initial State: {self.initial_state}\n")
            self.results_text.insert(tk.END, f"Gates: {[gate for gate, _ in self.placed_gates]}\n")
            self.results_text.insert(tk.END, "-" * 50 + "\n\n")
            self.results_text.update()

            # Create quantum circuit
            qc = QuantumCircuit(self.num_qubits)

            # Set initial state
            self.set_initial_state(qc)

            # Apply gates
            for gate, qubits in self.placed_gates:
                try:
                    if gate == 'H' and len(qubits) == 1:
                        qc.h(qubits[0])
                    elif gate == 'X' and len(qubits) == 1:
                        qc.x(qubits[0])
                    elif gate == 'Y' and len(qubits) == 1:
                        qc.y(qubits[0])
                    elif gate == 'Z' and len(qubits) == 1:
                        qc.z(qubits[0])
                    elif gate == 'S' and len(qubits) == 1:
                        qc.s(qubits[0])
                    elif gate == 'T' and len(qubits) == 1:
                        qc.t(qubits[0])
                    elif gate == 'CNOT' and len(qubits) == 2:
                        qc.cx(qubits[0], qubits[1])
                    elif gate == 'CZ' and len(qubits) == 2:
                        qc.cz(qubits[0], qubits[1])
                    elif gate == 'Toffoli' and len(qubits) == 3:
                        qc.ccx(qubits[0], qubits[1], qubits[2])
                    else:
                        self.results_text.insert(tk.END, f"Warning: Unknown gate {gate} with qubits {qubits}\n")
                except Exception as gate_error:
                    self.results_text.insert(tk.END, f"Error applying gate {gate}: {str(gate_error)}\n")

            # Get final state
            final_state = Statevector(qc)

            # Display results
            self.display_results(final_state)

            # Play success sound after results are displayed
            self.play_sound('success', self.play_success_sound_fallback)

        except ImportError as ie:
            self.results_text.insert(tk.END, f"Import Error: {str(ie)}\n")
            self.results_text.insert(tk.END, "Make sure Qiskit is installed: pip install qiskit\n")
            self.play_sound('error', self.play_error_sound_fallback)
        except Exception as e:
            self.results_text.insert(tk.END, f"Error executing circuit: {str(e)}\n")
            self.results_text.insert(tk.END, f"Error type: {type(e).__name__}\n")
            import traceback
            self.results_text.insert(tk.END, f"Traceback:\n{traceback.format_exc()}\n")
            self.play_sound('error', self.play_error_sound_fallback)
        finally:
            self.results_text.configure(state=tk.DISABLED)


    def set_initial_state(self, qc):
        """Set the initial state of the quantum circuit"""
        state = self.initial_state

        if state == "|1⟩" and self.num_qubits >= 1:
            qc.x(0)
        elif state == "|+⟩" and self.num_qubits >= 1:
            qc.h(0)
        elif state == "|-⟩" and self.num_qubits >= 1:
            qc.x(0)
            qc.h(0)
        elif state == "|01⟩" and self.num_qubits >= 2:
            qc.x(1)
        elif state == "|10⟩" and self.num_qubits >= 2:
            qc.x(0)
        elif state == "|11⟩" and self.num_qubits >= 2:
            qc.x(0)
            qc.x(1)
        elif state == "|++⟩" and self.num_qubits >= 2:
            qc.h(0)
            qc.h(1)
        else:
            # Handle arbitrary binary states like |0000⟩, |0001⟩, etc.
            # Extract the binary string from the ket notation
            if state.startswith("|") and state.endswith("⟩"):
                binary_str = state[1:-1]  # Remove |⟩ brackets

                # Apply X gates for each '1' in the binary string
                for i, bit in enumerate(reversed(binary_str)):
                    if bit == '1' and i < self.num_qubits:
                        qc.x(i)


    def display_results(self, state_vector):
        """Display the quantum state results"""
        try:
            # Circuit summary
            self.results_text.insert(tk.END, f" Circuit Executed Successfully!\n\n")

            # State vector
            self.results_text.insert(tk.END, " Final State Vector:\n")
            state_data = state_vector.data

            for i, amplitude in enumerate(state_data):
                if abs(amplitude) > 0.001:  # Only show significant amplitudes
                    basis_state = format(i, f'0{self.num_qubits}b')
                    prob = abs(amplitude) ** 2
                    # Format complex numbers nicely
                    if isinstance(amplitude, complex):
                        real_part = amplitude.real
                        imag_part = amplitude.imag
                        if abs(imag_part) < 0.001:
                            amp_str = f"{real_part:.4f}"
                        else:
                            amp_str = f"{real_part:.4f} + {imag_part:.4f}i"
                    else:
                        amp_str = f"{amplitude:.4f}"

                    self.results_text.insert(tk.END,
                        f"|{basis_state}⟩: {amp_str} (prob: {prob:.1%})\n")

            self.results_text.insert(tk.END, "\n")

            # Measurement probabilities summary
            self.results_text.insert(tk.END, " Measurement Probabilities:\n")
            total_prob = 0
            for i, amplitude in enumerate(state_data):
                prob = abs(amplitude) ** 2
                if prob > 0.001:
                    basis_state = format(i, f'0{self.num_qubits}b')
                    self.results_text.insert(tk.END, f"|{basis_state}⟩: {prob:.1%}\n")
                    total_prob += prob

            self.results_text.insert(tk.END, f"\nTotal probability: {total_prob:.1%}\n")

        except Exception as e:
            self.results_text.insert(tk.END, f"Error displaying results: {str(e)}\n")


def main():
    """For testing the sandbox independently"""
    root = tk.Tk()
    app = SandboxMode(root)
    root.mainloop()


if __name__ == "__main__":
    main()
