#!/usr/bin/env python3
"""
Learn Hub for Infinity Qubit
Educational resources and quantum computing concepts hub.
"""

import sys
import webbrowser
import tkinter as tk
from tkinter import ttk, scrolledtext
import os

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from run import PROJECT_ROOT, get_resource_path
from q_utils import get_colors_from_file, extract_color_palette

color_file_path = get_resource_path('config/color_palette.json')
palette = extract_color_palette(get_colors_from_file(color_file_path), 'learn_hub')


class LearnHub:
    def __init__(self, root):
        self.root = root
        self.root.title("Infinity Qubit - Learn Hub")

        # Set fullscreen mode
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Enable fullscreen
        self.root.overrideredirect(True)
        self.root.geometry(f"{screen_width}x{screen_height}")
        self.root.configure(bg=palette['background_2'])
        self.root.resizable(False, False)  # Fixed size window

        # Store dimensions for relative sizing (use full screen)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.window_width = screen_width
        self.window_height = screen_height
        
        # Animation tracking
        self.animation_id = None
        self.animation_ids = []  # Track all animation IDs
        self.animation_running = False
        
        # Scrolling variables
        self.scroll_start_y = 0
        self.last_y = 0
        self.is_scrolling = False
        self.scroll_indicator = None

        # Bind Escape key to exit
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
        
        # Apply extra-wide scrollbar styling
        self.style_scrollbars()


    def style_scrollbars(self):
        """Apply extra-wide scrollbar styling for better touch interaction"""
        style = ttk.Style()
        
        # Configure both standard scrollbar and our custom vertical scrollbar
        for scrollbar_style in ["TScrollbar", "Vertical.TScrollbar"]:
            style.configure(scrollbar_style, 
                          gripcount=0,
                          background=palette['subtitle_color'],
                          darkcolor=palette['background_4'], 
                          lightcolor=palette['background_3'],
                          troughcolor=palette['background_4'],
                          bordercolor=palette['background_4'],
                          arrowcolor=palette['title_color'],
                          arrowsize=40,
                          width=150)  # Extra wide scrollbar for tablet use
        
        # Apply the styling to map states as well
        style.map("TScrollbar",
                background=[("active", palette['background_4'])],
                arrowcolor=[("active", palette['title_color'])])
        
        style.map("Vertical.TScrollbar",
                background=[("active", palette['background_4'])],
                arrowcolor=[("active", palette['title_color'])])
        
        # Override any default scrollbar appearance
        self.root.option_add("*TScrollbar*width", 150)
        self.root.option_add("*Scrollbar*width", 150)


    def exit_fullscreen(self, event=None):
        """Exit the learn hub"""
        self.back_to_menu()


    def create_canvas_dialog_button(self, parent, text, command, width, height, bg_color, fg_color, padx=0, pady=0):
        """Create a canvas-based button for macOS compatibility"""
        # Create frame for proper packing
        btn_frame = tk.Frame(parent, bg=parent.cget('bg'))
        btn_frame.pack(padx=padx, pady=pady)

        # Create canvas for the button
        btn_canvas = tk.Canvas(btn_frame, width=width, height=height,
                              bg=bg_color, highlightthickness=0, relief=tk.FLAT, bd=0)
        btn_canvas.pack()

        # Create button rectangle and text
        rect_id = btn_canvas.create_rectangle(2, 2, width-2, height-2,
                                            fill=bg_color, outline=bg_color, width=0)
        text_id = btn_canvas.create_text(width//2, height//2, text=text,
                                       font=('Arial', 12, 'bold'), fill=fg_color)

        # Add click handler
        def on_click(event):
            command()

        # Add hover effects
        def on_enter(event):
            btn_canvas.itemconfig(rect_id, fill=palette['button_hover_background'])
            btn_canvas.itemconfig(text_id, fill=palette['button_hover_text_color'])

        def on_leave(event):
            btn_canvas.itemconfig(rect_id, fill=bg_color)
            btn_canvas.itemconfig(text_id, fill=fg_color)

        btn_canvas.bind("<Button-1>", on_click)
        btn_canvas.bind("<Enter>", on_enter)
        btn_canvas.bind("<Leave>", on_leave)
        btn_canvas.configure(cursor='hand2')

        return btn_canvas


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


    def start_animations(self):
        """Start background animations"""
        self.animation_running = True
        
        # Start circuit animation after UI is ready with a longer interval
        animation_id = self.root.after(500, self.animate_circuit)
        self.animation_id = str(animation_id)
        self.animation_ids.append(self.animation_id)
        
        # Start subtitle animation with lambda to avoid "invalid command name" error
        subtitle_anim_id = self.root.after(1000, lambda: self.animate_subtitle())
        self.animation_ids.append(str(subtitle_anim_id))


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

        # Create simplified header with internal padding
        self.create_animated_header(content_frame)

        # Create a container for the notebook spanning full width
        notebook_container = tk.Frame(content_frame, bg=palette['background_3'])
        notebook_container.pack(fill=tk.BOTH, expand=True,
                            padx=0,  # No horizontal padding for full width
                            pady=(0, int(self.screen_height * 0.02)))

        # Create notebook for tabs - full width
        self.notebook = ttk.Notebook(notebook_container)
        self.notebook.pack(expand=True, fill=tk.BOTH)

        # Apply enhanced styling
        self.style_notebook()
        
        # Dictionary to store scroll widgets for each tab
        self.tab_scrolling = {}
        
        # Create new tabs for expanded Learn Hub
        self.create_community_tab()
        self.create_news_tab()
        self.create_projects_tab()
        self.create_career_tab()
        self.create_resources_tab()
        
        # Force equal distribution of tabs after creation
        self.configure_equal_tab_distribution()
        
        # Bind tab change to handle scrolling
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)
        
        # Add a scroll indicator label to show users they can scroll
        self.scroll_indicator = tk.Label(
            content_frame, 
            text="↓ Drag to scroll content ↓",
            font=('Arial', 16, 'italic'),
            fg=palette['subtitle_color'],
            bg=palette['background_3']
        )
        self.scroll_indicator.place(relx=0.5, rely=0.95, anchor="center")
        
        # After 5 seconds, fade out the indicator
        self.root.after(5000, self.hide_scroll_indicator)
    
    def _hide_scroll_indicator_widget(self):
        """Hide the scroll indicator widget with a fade effect"""
        if hasattr(self, 'scroll_indicator_widget') and self.scroll_indicator_widget:
            try:
                self.scroll_indicator_widget.destroy()
            except:
                pass
            self.scroll_indicator_widget = None
            
    def hide_scroll_indicator(self):
        """Hide the scroll indicator after a delay"""
        if hasattr(self, 'scroll_indicator') and self.scroll_indicator.winfo_exists():
            self.scroll_indicator.destroy()
        
    def on_tab_change(self, event):
        """Handle tab changes to manage scrolling bindings"""
        # Remove any existing scroll indicator
        if hasattr(self, 'scroll_indicator_widget') and self.scroll_indicator_widget:
            try:
                self.scroll_indicator_widget.destroy()
            except:
                pass
            self.scroll_indicator_widget = None
            
        # Unbind all wheel and drag events first
        self.root.unbind_all("<MouseWheel>")
        self.root.unbind_all("<Button-4>")
        self.root.unbind_all("<Button-5>")
        
        # Reset scrolling state
        self.is_scrolling = False
        
        # Get current tab
        current_tab = self.notebook.index("current")
        tab_name = self.notebook.tab(current_tab, "text").strip()
        
        # If this tab has scroll widgets, bind them
        if tab_name in self.tab_scrolling:
            canvas = self.tab_scrolling[tab_name]
            
            # Bind mouse wheel for scrolling (Windows)
            def _on_mousewheel(event):
                # For Windows
                if hasattr(event, 'delta'):
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                # For Linux (event.num)
                elif event.num == 4:
                    canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    canvas.yview_scroll(1, "units")
                
            # Separate functions for Linux scrolling
            def _on_button4(event):
                canvas.yview_scroll(-1, "units")
                
            def _on_button5(event):
                canvas.yview_scroll(1, "units")
            
            # Bind drag scrolling events
            def _start_scroll(event):
                # Only start scrolling on left mouse button
                if event.num == 1:
                    # Remember the starting position
                    self.scroll_start_y = event.y
                    self.last_y = event.y
                    self.is_scrolling = True
                    
                    # Change cursor to indicate dragging is happening
                    canvas.config(cursor="fleur")
            
            def _do_scroll(event):
                # Only scroll if we're in scrolling mode
                if not self.is_scrolling:
                    return
                    
                # Calculate how far we've moved
                delta_y = self.last_y - event.y
                self.last_y = event.y
                
                if delta_y != 0:
                    # Scroll the canvas - adjust sensitivity as needed
                    # Lower denominator = more sensitive scrolling
                    scroll_amount = int(delta_y/1.5)  # More sensitive scrolling
                    if scroll_amount != 0:
                        canvas.yview_scroll(scroll_amount, "units")
            
            def _stop_scroll(event):
                # Reset scrolling state and cursor
                self.is_scrolling = False
                canvas.config(cursor="hand2")  # Reset to hand cursor
            
            # Handle mouse leaving canvas during drag
            def _on_leave(event):
                if self.is_scrolling:
                    self.is_scrolling = False
                    canvas.config(cursor="hand2")  # Reset to hand cursor
            
            # Bind wheel events - use platform-specific bindings
            # Windows/macOS wheel event
            self.root.bind_all("<MouseWheel>", _on_mousewheel)
            # Linux wheel events
            self.root.bind_all("<Button-4>", _on_button4)
            self.root.bind_all("<Button-5>", _on_button5)
            
            # Bind drag scrolling events directly to the canvas for better performance
            canvas.bind("<ButtonPress-1>", _start_scroll)
            canvas.bind("<B1-Motion>", _do_scroll)
            canvas.bind("<ButtonRelease-1>", _stop_scroll)
            canvas.bind("<Leave>", _on_leave)
            
            # Ensure the canvas has focus for events
            canvas.focus_set()

    def create_community_tab(self):
        """Community & Discussion tab: integrated information instead of external links"""
        community_frame = ttk.Frame(self.notebook)
        self.notebook.add(community_frame, text="Community")

        main_container = tk.Frame(community_frame, bg=palette['background_3'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

        # Centered title
        title_frame = tk.Frame(main_container, bg=palette['background_3'])
        title_frame.pack(fill=tk.X, pady=10)
        tk.Label(title_frame, text="Quantum Computing Communities", font=('Arial', 36, 'bold'), 
                 fg=palette['title_color'], bg=palette['background_3']).pack(pady=10, anchor="center")
        
        # Create a frame with scrollbar for better tablet usability
        outer_frame = tk.Frame(main_container, bg=palette['background_3'])
        outer_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a large scrollbar for tablet use
        scrollbar = ttk.Scrollbar(outer_frame, orient="vertical", style="Vertical.TScrollbar")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5, padx=(5, 0))
        
        # Create canvas with scrollbar
        canvas = tk.Canvas(outer_frame, bg=palette['background_3'], 
                         highlightthickness=0,
                         yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure the scrollbar to work with the canvas
        scrollbar.config(command=canvas.yview)
        
        # Create frame inside canvas to hold content
        content_frame = tk.Frame(canvas, bg=palette['background_3'])
        
        # Create window in canvas to display the content frame
        canvas_window = canvas.create_window((0, 0), window=content_frame, anchor="nw", tags="content_frame")
        
        # Configure canvas scrolling
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Keep the width of content_frame matched to canvas width
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())
            
        content_frame.bind("<Configure>", configure_scroll_region)
        
        # Ensure canvas is configurable by mouse wheel
        canvas.configure(yscrollincrement=20)  # Set scroll increment for smoother scrolling
        
        # Store canvas in dictionary for tab switching
        self.tab_scrolling["Community"] = canvas
        
        # Bind canvas resize to adjust content width
        def on_canvas_resize(event):
            canvas.itemconfig(canvas_window, width=event.width)
            
        canvas.bind("<Configure>", on_canvas_resize)
        
        # Community sections with information instead of links
        communities = [
            {
                "name": "Quantum Computing Stack Exchange",
                "description": "A community-driven question and answer site for quantum computing researchers, practitioners, and students.",
                "members": "25,000+ members",
                "topics": "Quantum algorithms, error correction, qubits, quantum gates"
            },
            {
                "name": "r/QuantumComputing",
                "description": "Reddit's quantum computing community for discussing advancements, research, and educational resources.",
                "members": "100,000+ members",
                "topics": "News, tutorials, quantum programming, theoretical discussions"
            },
            {
                "name": "IBM Quantum Community",
                "description": "IBM's dedicated quantum computing community connecting researchers, developers, and enthusiasts.",
                "members": "150,000+ members",
                "topics": "Qiskit, IBM Quantum systems, cloud-based quantum computing"
            },
            {
                "name": "Quantum Open Source Foundation",
                "description": "A community promoting development and standardization of open source quantum computing software.",
                "members": "5,000+ contributors",
                "topics": "Open source projects, hackathons, mentoring programs"
            }
        ]
        
        # Create community cards directly in the content frame
        for i, community in enumerate(communities):
            # Create card with visible border
            card = tk.Frame(content_frame, bg=palette['background_3'], bd=2, relief=tk.RAISED,
                          highlightbackground="#4ecdc4", highlightthickness=2)
            card.pack(fill=tk.X, pady=15, padx=20)
            
            # Card title
            tk.Label(card, text=community["name"], font=('Arial', 32, 'bold'), 
                    fg="#00ff88", bg=palette['background_3']).pack(anchor="center", pady=10)
            
            # Card description
            tk.Label(card, text=community["description"], font=('Arial', 22), 
                    fg=palette['subtitle_color'], bg=palette['background_3'], 
                    wraplength=900, justify=tk.CENTER).pack(anchor="center", pady=5)
            
            # Members info
            tk.Label(card, text=f"Members: {community['members']}", font=('Arial', 20), 
                    fg=palette['description_label_color'], bg=palette['background_3']).pack(anchor="center", pady=5)
            
            # Topics info
            tk.Label(card, text=f"Topics: {community['topics']}", font=('Arial', 20), 
                    fg=palette['description_label_color'], bg=palette['background_3'],
                    wraplength=900, justify=tk.CENTER).pack(anchor="center", pady=5)
            
            # Add separator except for last item
            if i < len(communities) - 1:
                ttk.Separator(content_frame, orient='horizontal').pack(fill=tk.X, padx=50, pady=10)

    def create_news_tab(self):
        """Latest News & Research tab: integrated information instead of external links"""
        news_frame = ttk.Frame(self.notebook)
        self.notebook.add(news_frame, text="News & Research")

        main_container = tk.Frame(news_frame, bg=palette['background_3'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

        # Centered title
        title_frame = tk.Frame(main_container, bg=palette['background_3'])
        title_frame.pack(fill=tk.X, pady=10)
        tk.Label(title_frame, text="Latest Quantum Computing News", font=('Arial', 36, 'bold'), 
                 fg=palette['title_color'], bg=palette['background_3']).pack(pady=10, anchor="center")
        
        # Create a frame with scrollbar for better tablet usability
        outer_frame = tk.Frame(main_container, bg=palette['background_3'])
        outer_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a large scrollbar for tablet use
        scrollbar = ttk.Scrollbar(outer_frame, orient="vertical", style="Vertical.TScrollbar")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5, padx=(5, 0))
        
        # Style the scrollbar to be bigger and more touch-friendly (style already created in community tab)
        scrollbar.configure(style="Vertical.TScrollbar")
        
        # Create canvas with scrollbar
        canvas = tk.Canvas(outer_frame, bg=palette['background_3'], 
                         highlightthickness=0,
                         yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure the scrollbar to work with the canvas
        scrollbar.config(command=canvas.yview)
        
        # Create frame inside canvas to hold content
        content_frame = tk.Frame(canvas, bg=palette['background_3'])
        
        # Create window in canvas to display the content frame
        canvas_window = canvas.create_window((0, 0), window=content_frame, anchor="nw", tags="content_frame")
        
        # Configure canvas scrolling
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Keep the width of content_frame matched to canvas width
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())
            
        content_frame.bind("<Configure>", configure_scroll_region)
        
        # Ensure canvas is configurable by mouse wheel
        canvas.configure(yscrollincrement=20)  # Set scroll increment for smoother scrolling
        
        # Store canvas in dictionary for tab switching
        self.tab_scrolling["News & Research"] = canvas
        
        # Bind canvas resize to adjust content width
        def on_canvas_resize(event):
            canvas.itemconfig(canvas_window, width=event.width)
            
        canvas.bind("<Configure>", on_canvas_resize)
        
        # News articles with images, dates, and content
        news = [
            {
                "title": "Quantum Computer Achieves 1000 Qubit Milestone",
                "date": "September 15, 2025",
                "source": "Quantum Magazine",
                "summary": "Scientists have successfully built and operated a quantum computer with 1000 qubits, marking a significant step toward practical quantum advantage. The system demonstrates unprecedented coherence times and error correction capabilities.",
                "category": "Hardware"
            },
            {
                "title": "New Quantum Algorithm Promises Breakthrough in Materials Science",
                "date": "September 10, 2025",
                "source": "Science Today",
                "summary": "Researchers have developed a novel quantum algorithm that can simulate complex molecular structures with exponentially less computational resources than classical methods. The algorithm is expected to accelerate discoveries in materials science and drug development.",
                "category": "Algorithms"
            },
            {
                "title": "Quantum Error Correction Reaches Record Fidelity",
                "date": "September 5, 2025",
                "source": "Quantum Research Journal",
                "summary": "A team of physicists has demonstrated quantum error correction with over 99% fidelity, addressing one of the major obstacles to building large-scale quantum computers. This breakthrough brings fault-tolerant quantum computing significantly closer to reality.",
                "category": "Error Correction"
            },
            {
                "title": "Quantum Internet Prototype Links Three Cities",
                "date": "August 28, 2025",
                "source": "Tech News Daily",
                "summary": "The world's first multi-node quantum internet has successfully linked three cities over 100km apart, enabling secure quantum communication protocols. The network uses quantum entanglement to achieve theoretically unhackable information transfer.",
                "category": "Quantum Communication"
            }
        ]
        
        # Container to center all news cards
        news_container = tk.Frame(content_frame, bg=palette['background_3'])
        news_container.pack(fill=tk.X, expand=True)
        
        for i, article in enumerate(news):
            # Frame to center the card
            article_container = tk.Frame(news_container, bg=palette['background_3'])
            article_container.pack(fill=tk.X, expand=True, pady=15, padx=10)
            
            # The news card with increased padding for touch friendliness
            frame = tk.Frame(article_container, bg=palette['background_3'], bd=2, relief=tk.RAISED)
            frame.pack(fill=tk.X, expand=True)
            
            # Header section with title and date - centered
            header = tk.Frame(frame, bg=palette['background_3'], padx=15, pady=15)
            header.pack(fill=tk.X)
            
            # Title centered
            tk.Label(header, text=article["title"], font=('Arial', 28, 'bold'), 
                    fg="#4ecdc4", bg=palette['background_3'], 
                    wraplength=900, justify=tk.CENTER).pack(anchor="center", pady=5)
            
            # Date centered
            tk.Label(header, text=article["date"], font=('Arial', 20, 'italic'), 
                    fg=palette['description_label_color'], bg=palette['background_3']).pack(anchor="center")
            
            # Source and category in separate sections with larger touch targets
            category_frame = tk.Frame(frame, bg=palette['background_3'], padx=15, pady=10)
            category_frame.pack(fill=tk.X)
            
            # Center-align the content
            category_inner = tk.Frame(category_frame, bg=palette['background_3'])
            category_inner.pack(anchor="center")
            
            # Category tag - larger and more prominent
            category_label = tk.Label(category_inner, text=article["category"], font=('Arial', 20, 'bold'), 
                                     fg="#FFFFFF", bg="#5151A2", padx=18, pady=8)
            category_label.pack(side=tk.LEFT, padx=10)
            
            # Source
            tk.Label(category_inner, text=f"Source: {article['source']}", font=('Arial', 20), 
                    fg=palette['description_label_color'], bg=palette['background_3'], padx=8, pady=8).pack(side=tk.LEFT)
            
            # Summary - centered text
            summary_frame = tk.Frame(frame, bg=palette['background_3'], padx=20, pady=15)
            summary_frame.pack(fill=tk.X)
            
            tk.Label(summary_frame, text=article["summary"], font=('Arial', 22), 
                    fg=palette['subtitle_color'], bg=palette['background_3'], 
                    wraplength=900, justify=tk.CENTER).pack(anchor="center")
            
            # Bottom padding for better touch
            tk.Frame(frame, height=10, bg=palette['background_3']).pack(fill=tk.X)
            
            # Separator except for last item
            if i < len(news) - 1:
                sep_frame = tk.Frame(news_container, bg=palette['background_3'])
                sep_frame.pack(fill=tk.X, expand=True)
                ttk.Separator(sep_frame, orient='horizontal').pack(fill=tk.X, padx=50, pady=10)

    def create_projects_tab(self):
        """Project Ideas & Challenges tab: integrated project information instead of just ideas"""
        projects_frame = ttk.Frame(self.notebook)
        self.notebook.add(projects_frame, text="Projects")

        main_container = tk.Frame(projects_frame, bg=palette['background_3'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

        # Centered title
        title_frame = tk.Frame(main_container, bg=palette['background_3'])
        title_frame.pack(fill=tk.X, pady=10)
        tk.Label(title_frame, text="Quantum Computing Projects & Challenges", font=('Arial', 36, 'bold'), 
                 fg=palette['title_color'], bg=palette['background_3']).pack(pady=10, anchor="center")
        
        # Create a frame with scrollbar for better tablet usability
        outer_frame = tk.Frame(main_container, bg=palette['background_3'])
        outer_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a large scrollbar for tablet use
        scrollbar = ttk.Scrollbar(outer_frame, orient="vertical")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Style the scrollbar to be bigger and more touch-friendly (style already created in community tab)
        scrollbar.configure(style="Vertical.TScrollbar")
        
        # Create canvas with scrollbar
        canvas = tk.Canvas(outer_frame, bg=palette['background_3'], 
                         highlightthickness=0,
                         yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure the scrollbar to work with the canvas
        scrollbar.config(command=canvas.yview)
        
        # Create frame inside canvas to hold content
        content_frame = tk.Frame(canvas, bg=palette['background_3'])
        
        # Create window in canvas to display the content frame
        canvas_window = canvas.create_window((0, 0), window=content_frame, anchor="nw", tags="content_frame")
        
        # Configure canvas scrolling
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Keep the width of content_frame matched to canvas width
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())
            
        content_frame.bind("<Configure>", configure_scroll_region)
        
        # Ensure canvas is configurable by mouse wheel
        canvas.configure(yscrollincrement=20)  # Set scroll increment for smoother scrolling
        
        # Store canvas in dictionary for tab switching
        self.tab_scrolling["Projects"] = canvas
        
        # Bind canvas resize to adjust content width
        def on_canvas_resize(event):
            canvas.itemconfig(canvas_window, width=event.width)
            
        canvas.bind("<Configure>", on_canvas_resize)
        
        # Project cards with detailed information
        projects = [
            {
                "title": "Quantum Random Number Generator",
                "difficulty": "Beginner",
                "time": "2-3 hours",
                "description": "Create a true random number generator using quantum superposition principles. This project introduces basic quantum gates and measurement.",
                "tools": "Qiskit, Python",
                "steps": [
                    "Create a quantum circuit with one qubit",
                    "Apply Hadamard gate to create superposition",
                    "Measure the qubit to get random 0 or 1",
                    "Repeat to generate longer random sequences"
                ]
            },
            {
                "title": "Quantum Teleportation Demo",
                "difficulty": "Intermediate",
                "time": "4-6 hours",
                "description": "Build a quantum teleportation circuit that transfers a quantum state from one qubit to another using entanglement and classical communication.",
                "tools": "Qiskit, Python, NumPy",
                "steps": [
                    "Create a circuit with three qubits",
                    "Prepare the state to teleport",
                    "Create Bell pair for entanglement",
                    "Perform Bell measurement",
                    "Apply correction operations",
                    "Verify teleported state"
                ]
            },
            {
                "title": "Grover's Search Algorithm Implementation",
                "difficulty": "Advanced",
                "time": "8-10 hours",
                "description": "Implement Grover's quantum search algorithm to find an item in an unsorted database with quadratic speedup compared to classical algorithms.",
                "tools": "Qiskit, Python, Linear Algebra knowledge",
                "steps": [
                    "Initialize qubits in superposition",
                    "Implement oracle function for the search target",
                    "Apply diffusion operator",
                    "Repeat amplitude amplification steps",
                    "Measure results and verify correctness",
                    "Compare with classical search complexity"
                ]
            },
            {
                "title": "Quantum Error Correction Code",
                "difficulty": "Expert",
                "time": "10-15 hours",
                "description": "Build a simple quantum error correction code to protect quantum information from bit-flip or phase-flip errors.",
                "tools": "Qiskit, Python, Error correction theory",
                "steps": [
                    "Implement the 3-qubit bit-flip code",
                    "Add controlled error channels",
                    "Perform syndrome measurement",
                    "Apply error correction",
                    "Compare results with and without correction",
                    "Extend to Shor's 9-qubit code (advanced)"
                ]
            }
        ]
        
        # Container to center all project cards
        projects_container = tk.Frame(content_frame, bg=palette['background_3'])
        projects_container.pack(fill=tk.X, expand=True)
        
        for i, project in enumerate(projects):
            # Difficulty colors for the card borders
            difficulty_colors = {
                "Beginner": "#4CAF50",
                "Intermediate": "#2196F3",
                "Advanced": "#FF9800",
                "Expert": "#F44336"
            }
            
            border_color = difficulty_colors.get(project["difficulty"], "#CCCCCC")
            
            # Frame to center each project card
            card_container = tk.Frame(projects_container, bg=palette['background_3'])
            card_container.pack(fill=tk.X, expand=True, pady=20, padx=20)
            
            # Project card with larger touch targets
            card = tk.Frame(card_container, bg=palette['background_3'], bd=3, 
                           highlightbackground=border_color, highlightthickness=3)
            card.pack(fill=tk.X, expand=True)
            
            # Header with title and difficulty badge - centered
            header = tk.Frame(card, bg=palette['background_3'], padx=20, pady=15)
            header.pack(fill=tk.X)
            
            # Title centered
            tk.Label(header, text=project["title"], font=('Arial', 28, 'bold'), 
                    fg=palette['enhanced_title_color'], bg=palette['background_3']).pack(anchor="center", pady=5)
            
            # Difficulty and time info - centered
            info_frame = tk.Frame(header, bg=palette['background_3'])
            info_frame.pack(anchor="center", pady=5)
            
            # Difficulty badge - larger for touch
            difficulty_label = tk.Label(info_frame, text=project["difficulty"], 
                                      font=('Arial', 20, 'bold'), 
                                      fg="white", bg=border_color, 
                                      padx=16, pady=8)
            difficulty_label.pack(side=tk.LEFT, padx=5)
            
            # Time estimate - larger for touch
            tk.Label(info_frame, text=f"Time: {project['time']}", 
                    font=('Arial', 18), 
                    fg=palette['description_label_color'], 
                    bg=palette['background_3'],
                    padx=8, pady=8).pack(side=tk.LEFT)
            
            # Description - centered
            desc_frame = tk.Frame(card, bg=palette['background_3'], padx=20, pady=10)
            desc_frame.pack(fill=tk.X)
            
            tk.Label(desc_frame, text=project["description"], 
                    font=('Arial', 20), 
                    fg=palette['subtitle_color'], bg=palette['background_3'], 
                    wraplength=900, justify=tk.CENTER).pack(anchor="center")
            
            # Tools section - centered
            tools_frame = tk.Frame(card, bg=palette['background_3'], padx=20, pady=10)
            tools_frame.pack(fill=tk.X)
            
            tools_container = tk.Frame(tools_frame, bg=palette['background_3'])
            tools_container.pack(anchor="center")
            
            tk.Label(tools_container, text="Tools:", 
                    font=('Arial', 20, 'bold'), 
                    fg=palette['subtitle_color'], bg=palette['background_3']).pack(side=tk.LEFT, padx=(0, 8))
            
            tk.Label(tools_container, text=project["tools"], 
                    font=('Arial', 20), 
                    fg=palette['description_label_color'], bg=palette['background_3']).pack(side=tk.LEFT)
            
            # Steps section - centered header with left-aligned steps for readability
            steps_frame = tk.Frame(card, bg=palette['background_3'], padx=20, pady=10)
            steps_frame.pack(fill=tk.X)
            
            tk.Label(steps_frame, text="Implementation Steps:", 
                    font=('Arial', 20, 'bold'), 
                    fg=palette['subtitle_color'], bg=palette['background_3']).pack(anchor="center", pady=5)
            
            # Create bulleted list of steps - centered frame with left-aligned text
            steps_list = tk.Frame(steps_frame, bg=palette['background_3'])
            steps_list.pack(anchor="center", pady=5)
            
            for j, step in enumerate(project["steps"]):
                step_frame = tk.Frame(steps_list, bg=palette['background_3'])
                step_frame.pack(fill=tk.X, anchor="w", pady=4)  # Increased padding for touch
                
                tk.Label(step_frame, text="•", 
                        font=('Arial', 20), 
                        fg=palette['subtitle_color'], bg=palette['background_3']).pack(side=tk.LEFT, padx=(0, 12))
                
                tk.Label(step_frame, text=step, 
                        font=('Arial', 20), 
                        fg=palette['subtitle_color'], bg=palette['background_3'], 
                        anchor="w").pack(side=tk.LEFT, fill=tk.X)
                        
            # Add bottom padding for touch
            tk.Frame(card, height=15, bg=palette['background_3']).pack(fill=tk.X)

    def create_career_tab(self):
        """Career & Learning Pathways tab: integrated information instead of external links"""
        career_frame = ttk.Frame(self.notebook)
        self.notebook.add(career_frame, text="Careers")

        main_container = tk.Frame(career_frame, bg=palette['background_3'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

        # Centered title
        title_frame = tk.Frame(main_container, bg=palette['background_3'])
        title_frame.pack(fill=tk.X, pady=10)
        tk.Label(title_frame, text="Quantum Computing Career Paths", font=('Arial', 36, 'bold'), 
                fg=palette['title_color'], bg=palette['background_3']).pack(pady=10, anchor="center")
        
        # Create a frame with scrollbar for better tablet usability
        outer_frame = tk.Frame(main_container, bg=palette['background_3'])
        outer_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a large scrollbar for tablet use
        scrollbar = ttk.Scrollbar(outer_frame, orient="vertical")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Style the scrollbar to be bigger and more touch-friendly (style already created in community tab)
        scrollbar.configure(style="Vertical.TScrollbar")
        
        # Create canvas with scrollbar
        canvas = tk.Canvas(outer_frame, bg=palette['background_3'], 
                         highlightthickness=0,
                         yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure the scrollbar to work with the canvas
        scrollbar.config(command=canvas.yview)
        
        # Create frame inside canvas to hold content
        content_frame = tk.Frame(canvas, bg=palette['background_3'])
        
        # Create window in canvas to display the content frame
        canvas_window = canvas.create_window((0, 0), window=content_frame, anchor="nw", tags="content_frame")
        
        # Configure canvas scrolling
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Keep the width of content_frame matched to canvas width
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())
            
        content_frame.bind("<Configure>", configure_scroll_region)
        
        # Ensure canvas is configurable by mouse wheel
        canvas.configure(yscrollincrement=20)  # Set scroll increment for smoother scrolling
        
        # Store canvas in dictionary for tab switching
        self.tab_scrolling["Careers"] = canvas
        
        # Bind canvas resize to adjust content width
        def on_canvas_resize(event):
            canvas.itemconfig(canvas_window, width=event.width)
            
        canvas.bind("<Configure>", on_canvas_resize)
        
        # Career paths with detailed information
        careers = [
            {
                "title": "Quantum Software Engineer",
                "education": "BS/MS in Computer Science, Physics, or related field",
                "skills": "Programming (Python, C++), Quantum algorithms, Linear algebra",
                "description": "Develop software for quantum computers, including circuit design, algorithm implementation, and quantum programming frameworks.",
                "companies": "IBM Quantum, Google Quantum AI, Microsoft Quantum, Rigetti, D-Wave",
                "salary_range": "$90,000 - $160,000",
                "growth": "High demand expected for the next decade as quantum computers become more commercially viable."
            },
            {
                "title": "Quantum Algorithm Researcher",
                "education": "PhD in Computer Science, Physics, or Mathematics",
                "skills": "Advanced mathematics, Algorithm design, Quantum theory",
                "description": "Research and develop new quantum algorithms that can provide advantages over classical computing methods for specific problem domains.",
                "companies": "Academic institutions, National laboratories, IBM Research, Google Research",
                "salary_range": "$110,000 - $180,000",
                "growth": "Steady growth as businesses seek quantum solutions to complex problems in optimization, simulation, and machine learning."
            },
            {
                "title": "Quantum Hardware Engineer",
                "education": "PhD in Physics, Electrical Engineering, or related field",
                "skills": "Quantum mechanics, Superconductivity, Electronic design, Cryogenics",
                "description": "Design and build the physical components of quantum computers, including qubits, control systems, and error correction mechanisms.",
                "companies": "IBM, Google, Intel, Rigetti, IonQ, Quantum Circuits Inc.",
                "salary_range": "$120,000 - $200,000",
                "growth": "Critical field with high demand as quantum hardware continues to evolve and scale up."
            },
            {
                "title": "Quantum Applications Specialist",
                "education": "MS/PhD in domain field (Chemistry, Finance, etc.) with quantum computing knowledge",
                "skills": "Domain expertise, Quantum algorithms, Optimization techniques",
                "description": "Apply quantum computing to solve industry-specific problems in fields like pharmaceuticals, materials science, finance, or logistics.",
                "companies": "JP Morgan Chase, Goldman Sachs, Merck, Airbus, ExxonMobil",
                "salary_range": "$100,000 - $170,000",
                "growth": "Rapidly expanding field as more industries adopt quantum computing for specialized applications."
            },
            {
                "title": "Quantum Education & Outreach",
                "education": "BS/MS in Physics, Computer Science, or Education with quantum knowledge",
                "skills": "Communication, Teaching, Quantum fundamentals, Content creation",
                "description": "Develop educational materials, teach courses, and create content to help others learn about quantum computing and its applications.",
                "companies": "Universities, Coding bootcamps, Qiskit Advocates program, Quantum education startups",
                "salary_range": "$60,000 - $120,000",
                "growth": "Growing demand as more educational institutions add quantum computing to their curriculum."
            }
        ]
        
        # Create career cards directly in the content frame
        for i, career in enumerate(careers):
            # Create card with visible border
            card = tk.Frame(content_frame, bg=palette['background_3'], bd=2, relief=tk.RAISED)
            card.pack(fill=tk.X, pady=15, padx=20)
            
            # Title with underline - centered
            title_frame = tk.Frame(card, bg=palette['background_3'], padx=15, pady=15)
            title_frame.pack(fill=tk.X)
            
            tk.Label(title_frame, text=career["title"], font=('Arial', 28, 'bold'), 
                    fg="#ffb86b", bg=palette['background_3']).pack(anchor="center")
            
            separator = ttk.Separator(card, orient='horizontal')
            separator.pack(fill=tk.X, padx=20, pady=5)
            
            # Content frame - centered layout
            content = tk.Frame(card, bg=palette['background_3'], padx=20, pady=10)
            content.pack(fill=tk.X)
            
            # Information sections centered but with content left-aligned for readability
            sections = [
                {"title": "Education:", "content": career["education"]},
                {"title": "Key Skills:", "content": career["skills"]},
                {"title": "Description:", "content": career["description"]},
                {"title": "Companies:", "content": career["companies"]},
                {"title": "Salary Range:", "content": career["salary_range"]},
                {"title": "Growth Outlook:", "content": career["growth"]}
            ]
            
            for section in sections:
                section_frame = tk.Frame(content, bg=palette['background_3'], pady=10)
                section_frame.pack(fill=tk.X, anchor="center")
                
                # Section title
                title_label = tk.Label(section_frame, text=section["title"], font=('Arial', 20, 'bold'), 
                        fg=palette['subtitle_color'], bg=palette['background_3'])
                title_label.pack(anchor="center", pady=(0, 6))
                
                # Content - larger font for better readability on touch screens
                content_label = tk.Label(section_frame, text=section["content"], font=('Arial', 18), 
                        fg=palette['description_label_color'], bg=palette['background_3'], 
                        wraplength=900, justify=tk.CENTER)
                content_label.pack(anchor="center")
            
            # Add bottom padding for touch
            tk.Frame(card, height=10, bg=palette['background_3']).pack(fill=tk.X)
            
            # Add separator except for last item
            if i < len(careers) - 1:
                ttk.Separator(content_frame, orient='horizontal').pack(fill=tk.X, padx=50, pady=10)
    def create_animated_header(self, parent):
        """Create a simplified header without animation canvas"""
        header_frame = tk.Frame(parent, bg=palette['background_3'])
        header_frame.pack(fill=tk.X,
                        padx=int(self.screen_width * 0.02),
                        pady=(int(self.screen_height * 0.02), int(self.screen_height * 0.015)))

        # Add a top navigation bar
        nav_frame = tk.Frame(header_frame, bg=palette['background_3'])
        nav_frame.pack(fill=tk.X, pady=(0, int(self.screen_height * 0.008)))

        # Back to Main Screen button - top right with relative sizing
        button_font_size = max(12, int(self.screen_width * 0.01))
        # Canvas-based main menu button for better color control on macOS
        button_width = max(180, int(self.screen_width * 0.12))
        button_height = max(50, int(self.screen_height * 0.045))

        back_main_canvas = tk.Canvas(nav_frame,
                               width=button_width,
                               height=button_height,
                               bg=palette['learn_hub_button_color'],
                               highlightthickness=0,
                               bd=0)

        back_main_canvas.pack(side=tk.RIGHT)

        # Draw button background with proper colors - larger for touch
        back_main_canvas.create_rectangle(2, 2, button_width-2, button_height-2,
                                        fill=palette['learn_hub_button_color'],
                                        outline="#2b3340", width=2,
                                        tags="menu_bg")

        # Add text to button with proper contrast - larger font
        back_main_canvas.create_text(button_width//2, button_height//2,
                                text=" Main Screen",
                                font=('Arial', button_font_size, 'bold'),
                                fill=palette['learn_hub_button_text_color'],
                                tags="menu_text")

        # Bind click events
        def on_menu_click(event):
            self.back_to_menu()

        # FIXED: Hover effects with proper colors
        def on_menu_enter(event):
            back_main_canvas.itemconfig("menu_bg", fill=palette['learn_hub_button_hover_color'])  # FIXED: Use hover color
            back_main_canvas.itemconfig("menu_text", fill=palette['learn_hub_button_text_color'])  # Keep text color consistent
            back_main_canvas.configure(cursor="hand2")

        def on_menu_leave(event):
            back_main_canvas.itemconfig("menu_bg", fill=palette['learn_hub_button_color'])  # FIXED: Back to normal color
            back_main_canvas.itemconfig("menu_text", fill=palette['learn_hub_button_text_color'])  # Keep text color consistent
            back_main_canvas.configure(cursor="")

        back_main_canvas.bind("<Button-1>", on_menu_click)
        back_main_canvas.bind("<Enter>", on_menu_enter)
        back_main_canvas.bind("<Leave>", on_menu_leave)

        # Title with shadow effect and relative font size
        title_frame = tk.Frame(header_frame, bg=palette['background_3'])
        title_frame.pack()

        # Shadow title with relative font size
        title_font_size = max(24, int(self.screen_width * 0.025))
        shadow_title = tk.Label(title_frame, text=" Quantum Computing Learn Hub",
                            font=('Arial', title_font_size, 'bold'),
                            fg='#003322', bg=palette['background_3'])
        shadow_title.place(x=3, y=3)

        # Main title with gradient-like effect
        main_title = tk.Label(title_frame, text=" Quantum Computing Learn Hub",
                            font=('Arial', title_font_size, 'bold'),
                            fg=palette['title_color'], bg=palette['background_3'])
        main_title.pack(pady=(0, int(self.screen_height * 0.008)))

        # Enhanced subtitle with pulsing effect and relative font size
        subtitle_font_size = max(12, int(self.screen_width * 0.01))
        self.subtitle_label = tk.Label(header_frame,
                                    text=" Explore quantum computing concepts and resources ",
                                    font=('Arial', subtitle_font_size, 'italic'),
                                    fg=palette['subtitle_color'], bg=palette['background_3'])
        self.subtitle_label.pack()


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





    def style_notebook(self):
        """Apply enhanced styling to the notebook for touch-friendly tabs"""
        style = ttk.Style()
        style.theme_use('clam')

        # Enhanced notebook styling with larger targets for touch screens - full width
        style.configure('TNotebook',
                    background=palette['background_3'],
                    borderwidth=0,
                    tabmargins=[0, 0, 0, 0])  # Remove margins to span full width

        # Larger padding for touch-friendly tabs - equal distribution
        style.configure('TNotebook.Tab',
                    background=palette['background_4'],
                    foreground='#ffffff',  # Default text color - white
                    padding=[10, 20],      # Reduced horizontal padding to fit equally
                    borderwidth=0,
                    font=('Arial', 18, 'bold'),  # Much larger font for better visibility
                    anchor='center')  # Center text in tabs

        # FIXED: Text colors for tab states
        style.map('TNotebook.Tab',
                background=[('selected', palette['background_3']),  # Selected tab background
                            ('active', palette['background_4'])],    # Hover background
                foreground=[('selected', '#ffb86b'),               # FIXED: Orange text when selected
                            ('active', '#ffffff'),                  # White text when hovering
                            ('!active', '#ffffff')])               # White text when not active

        # Style large tablet-friendly scrollbars
        style.configure("Vertical.TScrollbar", 
                        gripcount=0,
                        background=palette['subtitle_color'],
                        darkcolor=palette['background_4'], 
                        lightcolor=palette['background_3'],
                        troughcolor=palette['background_4'],
                        bordercolor=palette['background_4'],
                        arrowcolor='#ffffff',
                        arrowsize=100,
                        width=150)  # Extra wide scrollbar for tablet use

        style.configure('TFrame', background=palette['background_3'])

        # Center the tabs by configuring tab positioning
        style.configure('TNotebook', tabposition='n')

    def configure_equal_tab_distribution(self):
        """Configure tabs to be equally distributed across the full width"""
        # Update after the window is ready
        self.root.after(100, self._apply_equal_distribution)
    
    def _apply_equal_distribution(self):
        """Apply equal distribution styling to tabs"""
        try:
            # Get the number of tabs
            tab_count = self.notebook.index("end")
            if tab_count > 0:
                # Calculate equal width for each tab
                notebook_width = self.notebook.winfo_width()
                if notebook_width > 1:  # Make sure notebook is rendered
                    tab_width = notebook_width // tab_count
                    
                    # Apply uniform width to all tabs through styling
                    style = ttk.Style()
                    style.configure('TNotebook.Tab',
                        background=palette['background_4'],
                        foreground='#ffffff',
                        padding=[5, 20],  # Minimal horizontal padding
                        borderwidth=0,
                        font=('Arial', 18, 'bold'),
                        anchor='center',
                        width=tab_width)  # Set calculated width
                else:
                    # Retry if notebook not ready
                    self.root.after(100, self._apply_equal_distribution)
        except Exception:
            # Fallback - retry once more
            self.root.after(200, self._apply_equal_distribution)


    # Removed concepts tab



    # Removed gates tab


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
        stars = "" * difficulty + "" * (5 - difficulty)
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



    # Removed algorithms tab
    def create_coming_soon_tab(self):
        """Create a simple 'Coming Soon' tab for future features"""
        coming_frame = ttk.Frame(self.notebook)
        self.notebook.add(coming_frame, text=" Coming Soon")

        main_container = tk.Frame(coming_frame, bg=palette['background_3'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

        label = tk.Label(main_container,
                        text="More quantum learning features are coming soon!\nStay tuned for interactive tutorials, quizzes, and more.",
                        font=('Arial', 16, 'italic'),
                        fg=palette['subtitle_color'],
                        bg=palette['background_3'],
                        justify=tk.CENTER)
        label.pack(expand=True)


    def create_resources_tab(self):
        """Resources tab: integrated information instead of external links"""
        resources_frame = ttk.Frame(self.notebook)
        self.notebook.add(resources_frame, text="Resources")

        main_container = tk.Frame(resources_frame, bg=palette['background_3'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

        # Centered title
        title_frame = tk.Frame(main_container, bg=palette['background_3'])
        title_frame.pack(fill=tk.X, pady=10)
        tk.Label(title_frame, text="Quantum Computing Resources", font=('Arial', 36, 'bold'), 
                fg=palette['title_color'], bg=palette['background_3']).pack(pady=10, anchor="center")
        
        # Create a frame with scrollbar for better tablet usability
        outer_frame = tk.Frame(main_container, bg=palette['background_3'])
        outer_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a large scrollbar for tablet use
        scrollbar = ttk.Scrollbar(outer_frame, orient="vertical")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Style the scrollbar to be bigger and more touch-friendly (style already created in community tab)
        scrollbar.configure(style="Vertical.TScrollbar")
        
        # Create canvas with scrollbar
        canvas = tk.Canvas(outer_frame, bg=palette['background_3'], 
                         highlightthickness=0,
                         yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure the scrollbar to work with the canvas
        scrollbar.config(command=canvas.yview)
        
        # Create frame inside canvas to hold content
        content_frame = tk.Frame(canvas, bg=palette['background_3'])
        
        # Create window in canvas to display the content frame
        canvas_window = canvas.create_window((0, 0), window=content_frame, anchor="nw", tags="content_frame")
        
        # Configure canvas scrolling
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Keep the width of content_frame matched to canvas width
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())
            
        content_frame.bind("<Configure>", configure_scroll_region)
        
        # Ensure canvas is configurable by mouse wheel
        canvas.configure(yscrollincrement=20)  # Set scroll increment for smoother scrolling
        
        # Store canvas in dictionary for tab switching
        self.tab_scrolling["Resources"] = canvas
        
        # Bind canvas resize to adjust content width
        def on_canvas_resize(event):
            canvas.itemconfig(canvas_window, width=event.width)
            
        canvas.bind("<Configure>", on_canvas_resize)
        
        # Resource categories
        categories = [
            {
                "name": "Essential Books",
                "items": [
                    {
                        "title": "Quantum Computation and Quantum Information",
                        "authors": "Michael A. Nielsen and Isaac L. Chuang",
                        "description": "The definitive textbook in the field, often called 'Mike and Ike'. Covers quantum mechanics, quantum computation, quantum information theory, and quantum cryptography."
                    },
                    {
                        "title": "Quantum Computing: An Applied Approach",
                        "authors": "Jack D. Hidary",
                        "description": "A practical, application-focused introduction to quantum computing with real-world examples and programming exercises using Qiskit and other platforms."
                    },
                    {
                        "title": "Programming Quantum Computers",
                        "authors": "Eric R. Johnston, Nic Harrigan, and Mercedes Gimeno-Segovia",
                        "description": "A hands-on introduction to quantum computing that focuses on practical implementation with visual explanations and programming examples."
                    }
                ]
            },
            {
                "name": "Learning Concepts",
                "items": [
                    {
                        "title": "Quantum Superposition",
                        "description": "Quantum bits (qubits) can exist in multiple states simultaneously, unlike classical bits. This property allows quantum computers to process a vast amount of possibilities at once."
                    },
                    {
                        "title": "Quantum Entanglement",
                        "description": "When qubits become entangled, the state of one qubit is directly related to the state of another, regardless of the distance between them. Measuring one immediately determines the state of the other."
                    },
                    {
                        "title": "Quantum Gates",
                        "description": "Quantum gates are the building blocks of quantum circuits. Common gates include the Hadamard gate (creates superposition), Pauli-X gate (quantum NOT), and CNOT gate (creates entanglement between qubits)."
                    },
                    {
                        "title": "Quantum Algorithms",
                        "description": "Specialized algorithms that leverage quantum properties to solve certain problems more efficiently than classical computers. Examples include Shor's algorithm for factoring large numbers and Grover's algorithm for searching."
                    }
                ]
            },
            {
                "name": "Mathematics for Quantum Computing",
                "items": [
                    {
                        "title": "Linear Algebra",
                        "description": "Essential for understanding quantum states and operations. Key concepts include vectors, matrices, eigenvalues, eigenvectors, and tensor products."
                    },
                    {
                        "title": "Complex Numbers",
                        "description": "Quantum amplitudes are represented as complex numbers. Understanding complex arithmetic, polar form, and Euler's formula is important."
                    },
                    {
                        "title": "Probability Theory",
                        "description": "Quantum measurements are probabilistic. Concepts like probability distributions, expected values, and Born's rule are fundamental."
                    }
                ]
            }
        ]
        
        # Display each category and its items directly in the content frame
        for category_index, category in enumerate(categories):
            # Category header - centered
            category_frame = tk.Frame(content_frame, bg=palette['background_3'])
            category_frame.pack(fill=tk.X, pady=(25, 10))
            
            tk.Label(category_frame, text=category["name"], font=('Arial', 30, 'bold'), 
                    fg="#50fa7b", bg=palette['background_3']).pack(anchor="center", pady=8)
            
            # Items in this category
            for item_index, item in enumerate(category["items"]):
                # Item card with increased padding for touch
                item_frame = tk.Frame(content_frame, bg=palette['background_3'], bd=2, relief=tk.GROOVE)
                item_frame.pack(fill=tk.X, expand=True, padx=15, pady=10)
                
                # Title with authors if available - centered
                title_frame = tk.Frame(item_frame, bg=palette['background_3'], padx=15, pady=12)
                title_frame.pack(fill=tk.X)
                
                tk.Label(title_frame, text=item["title"], font=('Arial', 24, 'bold'), 
                        fg="#8be9fd", bg=palette['background_3']).pack(anchor="center", pady=(0, 8))
                
                if "authors" in item:
                    tk.Label(title_frame, text=f"By: {item['authors']}", font=('Arial', 18, 'italic'), 
                            fg=palette['subtitle_color'], bg=palette['background_3']).pack(anchor="center", pady=(0, 8))
                
                # Description - centered text with good readability
                desc_frame = tk.Frame(item_frame, bg=palette['background_3'], padx=24, pady=16)
                desc_frame.pack(fill=tk.X)
                
                tk.Label(desc_frame, text=item["description"], font=('Arial', 18), 
                        fg=palette['description_label_color'], bg=palette['background_3'], 
                        wraplength=900, justify=tk.CENTER).pack(anchor="center", pady=8)
            
            # Add separator between categories except for last one
            if category_index < len(categories) - 1:
                sep_frame = tk.Frame(content_frame, bg=palette['background_3'])
                sep_frame.pack(fill=tk.X, pady=10)
                ttk.Separator(sep_frame, orient='horizontal').pack(fill=tk.X, padx=50)
        
        # Additional learning tips section
        tips_container = tk.Frame(content_frame, bg=palette['background_3'])
        tips_container.pack(fill=tk.X, expand=True, pady=25)
        
        tips_frame = tk.Frame(tips_container, bg=palette['background_3'], bd=2, relief=tk.GROOVE)
        tips_frame.pack(fill=tk.X, expand=True, padx=15)
        
        # Title centered
        tips_title = tk.Frame(tips_frame, bg=palette['background_3'], padx=10, pady=15)
        tips_title.pack(fill=tk.X)
        
        tk.Label(tips_title, text="Learning Tips", font=('Arial', 30, 'bold'), 
                fg="#bd93f9", bg=palette['background_3']).pack(anchor="center")
        
        # Tips with larger touch targets
        tips = [
            "Start with the basics: Learn classical computing fundamentals before diving into quantum",
            "Practice with simulators: Use this application to experiment with quantum circuits",
            "Learn incrementally: Master one concept before moving to the next",
            "Apply your knowledge: Try to implement simple algorithms after learning them",
            "Join the community: Participate in quantum computing forums and discussions"
        ]
        
        # Container for tips
        tips_list = tk.Frame(tips_frame, bg=palette['background_3'], padx=24, pady=18)
        tips_list.pack(fill=tk.X)
        
        for tip in tips:
            tip_container = tk.Frame(tips_list, bg=palette['background_3'], pady=12)
            tip_container.pack(fill=tk.X)
            
            # Create a frame to center the tip content
            tip_content = tk.Frame(tip_container, bg=palette['background_3'])
            tip_content.pack(anchor="center")
            
            # Bullet point and tip text with larger font and padding for touch
            tk.Label(tip_content, text="•", font=('Arial', 24, 'bold'), 
                    fg=palette['description_label_color'], bg=palette['background_3']).pack(side=tk.LEFT, padx=(0, 16))
            
            tk.Label(tip_content, text=tip, font=('Arial', 20), 
                    fg=palette['description_label_color'], bg=palette['background_3'], 
                    wraplength=900, justify=tk.LEFT).pack(side=tk.LEFT, padx=8, pady=8)


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
        stars = "" * rating + "" * (5 - rating)
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
        try_canvas = tk.Canvas(content_frame, highlightthickness=0, bd=0, width=100, height=35)
        try_canvas.pack()

        # Draw try button
        try_canvas.create_rectangle(0, 0, 100, 35, fill=palette['try_it_button_background'], outline=palette['try_it_button_background'], tags="bg")
        try_canvas.create_text(50, 17, text="Try It →",
                             font=('Arial', 10, 'bold'),
                             fill=palette['background_black'], tags="text")

        def on_try_click(event):
            self.open_url(url)

        def on_try_enter(event):
            try_canvas.itemconfig("bg", fill=palette['close_button_hover_background'])
            try_canvas.configure(cursor='hand2')

        def on_try_leave(event):
            try_canvas.itemconfig("bg", fill=palette['try_it_button_background'])
            try_canvas.configure(cursor='')

        try_canvas.bind("<Button-1>", on_try_click)
        try_canvas.bind("<Enter>", on_try_enter)
        try_canvas.bind("<Leave>", on_try_leave)

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
        stars = "" * rating + "" * (5 - rating)
        rating_label = tk.Label(title_frame, text=f"Rating: {stars}",
                               font=('Arial', 10),
                               fg=palette['rating_label_color'], bg=palette['background_3'])
        rating_label.pack(anchor=tk.W)

        # Try it button
        try_canvas2 = tk.Canvas(header_frame, highlightthickness=0, bd=0, width=80, height=30)
        try_canvas2.pack(side=tk.RIGHT)

        # Draw try button
        try_canvas2.create_rectangle(0, 0, 80, 30, fill=palette['try_it_button_background'], outline=palette['try_it_button_background'], tags="bg")
        try_canvas2.create_text(40, 15, text="Try It →",
                              font=('Arial', 10, 'bold'),
                              fill=palette['background_black'], tags="text")

        def on_try2_click(event):
            self.open_url(url)

        def on_try2_enter(event):
            try_canvas2.itemconfig("bg", fill=palette['close_button_hover_background'])
            try_canvas2.configure(cursor='hand2')

        def on_try2_leave(event):
            try_canvas2.itemconfig("bg", fill=palette['try_it_button_background'])
            try_canvas2.configure(cursor='')

        try_canvas2.bind("<Button-1>", on_try2_click)
        try_canvas2.bind("<Enter>", on_try2_enter)
        try_canvas2.bind("<Leave>", on_try2_leave)

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
        if not self.animation_running or not hasattr(self, 'root') or not self.root.winfo_exists():
            return
        
        # Safe check to ensure the subtitle label exists and the window is still open
        try:
            if hasattr(self, 'subtitle_label') and self.subtitle_label.winfo_exists():
                current_color = self.subtitle_label.cget('fg')
                new_color = '#00ff88' if current_color == '#4ecdc4' else '#4ecdc4'
                self.subtitle_label.configure(fg=new_color)
                
                # Schedule next animation only if still running
                if self.animation_running:
                    # Use a named callback to avoid the "invalid command name" error
                    animation_id = self.root.after(2000, lambda: self.animate_subtitle())
                    self.animation_ids.append(str(animation_id))
            else:
                # If the subtitle label doesn't exist, stop trying to animate it
                self.animation_running = False
        except (tk.TclError, AttributeError, RuntimeError) as e:
            # Widget might be destroyed or not exist
            print(f"Animation error: {e}")
            self.animation_running = False


    def open_url(self, url):
        """Open URL in default browser"""
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"Error opening URL: {e}")


    def back_to_menu(self):
        """Go back to the main screen/menu"""
        # Stop all animations immediately
        self.animation_running = False

        # Cancel any pending animations
        if hasattr(self, 'animation_id') and self.animation_id:
            try:
                self.root.after_cancel(self.animation_id)
            except Exception:
                pass
                
        # Cancel all tracked animation IDs
        if hasattr(self, 'animation_ids'):
            for anim_id in self.animation_ids:
                try:
                    if isinstance(anim_id, str) and anim_id.isdigit():
                        self.root.after_cancel(int(anim_id))
                    else:
                        self.root.after_cancel(anim_id)
                except Exception:
                    pass

        try:
            # Create main menu FIRST
            from game_mode_selection import GameModeSelection
            selection_window = GameModeSelection()

            # Make sure new window is visible
            selection_window.root.update()
            selection_window.root.lift()
            selection_window.root.focus_force()

            # THEN destroy current window
            self.root.destroy()

            # Start the main menu mainloop
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
                    self.root.destroy()
        except Exception as e:
            print(f"Error returning to main screen: {e}")
            self.root.destroy()


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
        title_label = tk.Label(menu_root, text=" Infinity Qubit",
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
        # Learn button using canvas for macOS compatibility
        self.create_canvas_dialog_button(button_frame, " Learn Hub",
                                        lambda event=None: self.reopen_learn_hub(menu_root),
                                        200, 45, palette['learn_button_background'],
                                        palette['background_black'], pady=5)

        # Placeholder for other modes
        placeholder_label = tk.Label(button_frame, text="Other game modes coming soon...",
                                    font=('Arial', 10, 'italic'),
                                    fg=palette['placeholder_text_color'], bg=palette['background'])
        placeholder_label.pack(pady=20)

        # Close button using canvas for macOS compatibility
        self.create_canvas_dialog_button(button_frame, " Exit", menu_root.destroy,
                                        200, 45, palette['close_button_background'],
                                        palette['close_button_text_color'], pady=5)

        menu_root.mainloop()


    def reopen_learn_hub(self, menu_root):
        """Reopen the Learn Hub"""
        menu_root.destroy()
        new_root = tk.Tk()
        LearnHub(new_root)
        new_root.mainloop()


    def close_window(self):
        """Close the learn hub window"""
        # Stop all animations immediately
        self.animation_running = False

        # Cancel any pending animations
        if hasattr(self, 'animation_id') and self.animation_id:
            try:
                self.root.after_cancel(self.animation_id)
            except Exception:
                pass
                
        # Cancel all tracked animation IDs
        if hasattr(self, 'animation_ids'):
            for anim_id in self.animation_ids:
                try:
                    self.root.after_cancel(anim_id)
                except Exception:
                    pass
        
        # Clean destroy the window
        self.root.destroy()


def main():
    """For testing the learn hub independently"""
    root = tk.Tk()
    app = LearnHub(root)
    root.mainloop()


if __name__ == "__main__":
    main()
