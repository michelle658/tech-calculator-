import ast
import json
import math
import tkinter as tk
from tkinter import messagebox


HISTORY_FILE = "calculator_history.json"

SAFE_NAMES = {
    "pi": math.pi,
    "e": math.e,
}

THEMES = {
    "dark": {
        "window_bg": "#000000",
        "panel_bg": "#000000",
        "surface_bg": "#111111",
        "display_bg": "#000000",
        "display_fg": "#ffffff",
        "text_main": "#ffffff",
        "text_muted": "#d0d0d0",
        "border": "#ffffff",
        "button_number_bg": "#111111",
        "button_number_fg": "#ffffff",
        "button_operator_bg": "#ffffff",
        "button_operator_fg": "#000000",
        "button_scientific_bg": "#222222",
        "button_scientific_fg": "#ffffff",
        "button_action_bg": "#000000",
        "button_action_fg": "#ffffff",
        "button_hover_bg": "#ffffff",
        "button_hover_fg": "#000000",
        "history_bg": "#111111",
        "history_fg": "#ffffff",
        "history_select_bg": "#ffffff",
        "history_select_fg": "#000000",
        "status_bg": "#000000",
        "status_fg": "#ffffff",
    },
    "light": {
        "window_bg": "#ffffff",
        "panel_bg": "#ffffff",
        "surface_bg": "#f2f2f2",
        "display_bg": "#ffffff",
        "display_fg": "#000000",
        "text_main": "#000000",
        "text_muted": "#333333",
        "border": "#000000",
        "button_number_bg": "#ffffff",
        "button_number_fg": "#000000",
        "button_operator_bg": "#000000",
        "button_operator_fg": "#ffffff",
        "button_scientific_bg": "#e6e6e6",
        "button_scientific_fg": "#000000",
        "button_action_bg": "#ffffff",
        "button_action_fg": "#000000",
        "button_hover_bg": "#000000",
        "button_hover_fg": "#ffffff",
        "history_bg": "#ffffff",
        "history_fg": "#000000",
        "history_select_bg": "#000000",
        "history_select_fg": "#ffffff",
        "status_bg": "#ffffff",
        "status_fg": "#000000",
    },
}


class CalculationError(Exception):
    # Represent user-friendly calculator errors.
    pass


def load_history():
    # Load saved calculations from a JSON file.
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            if isinstance(data, list):
                return data
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []
    return []


def save_history(history):
    # Save calculations so they remain available next time.
    with open(HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(history, file, indent=2)


def format_number(number):
    # Display whole numbers without an unnecessary .0.
    if number == int(number):
        return str(int(number))
    return str(number)


def evaluate_expression(expression, angle_mode):
    # Safely evaluate a math expression using Python's AST module.
    try:
        parsed_expression = ast.parse(expression, mode="eval")
    except SyntaxError as error:
        raise CalculationError("Please enter a valid calculation.") from error

    return evaluate_node(parsed_expression.body, angle_mode)


def evaluate_function(function_name, value, angle_mode):
    # Process supported scientific functions in one place.
    if function_name == "sqrt":
        return math.sqrt(value)
    if function_name == "sin":
        if angle_mode == "DEG":
            value = math.radians(value)
        return math.sin(value)
    if function_name == "cos":
        if angle_mode == "DEG":
            value = math.radians(value)
        return math.cos(value)
    if function_name == "tan":
        if angle_mode == "DEG":
            value = math.radians(value)
        return math.tan(value)
    if function_name == "log":
        return math.log10(value)
    if function_name == "ln":
        return math.log(value)
    if function_name == "abs":
        return abs(value)
    if function_name == "fact":
        if value < 0 or value != int(value):
            raise CalculationError("Factorial only works with whole numbers 0 or greater.")
        return math.factorial(int(value))
    raise CalculationError("That function is not available here.")


def evaluate_node(node, angle_mode):
    # Recursively process only the safe math nodes we support.
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)

    if isinstance(node, ast.Name):
        if node.id in SAFE_NAMES:
            return float(SAFE_NAMES[node.id])
        raise CalculationError("That item is not supported in this calculator.")

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise CalculationError("That function call is not supported.")

        if len(node.args) != 1:
            raise CalculationError("Scientific functions need one number.")

        function_name = node.func.id
        value = evaluate_node(node.args[0], angle_mode)

        try:
            return float(evaluate_function(function_name, value, angle_mode))
        except ValueError as error:
            raise CalculationError("That value is outside the allowed math range.") from error

    if isinstance(node, ast.UnaryOp):
        value = evaluate_node(node.operand, angle_mode)
        if isinstance(node.op, ast.UAdd):
            return value
        if isinstance(node.op, ast.USub):
            return -value
        raise CalculationError("That symbol is not supported.")

    if isinstance(node, ast.BinOp):
        left = evaluate_node(node.left, angle_mode)
        right = evaluate_node(node.right, angle_mode)

        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            if right == 0:
                raise CalculationError("Division by zero is not allowed.")
            return left / right
        if isinstance(node.op, ast.Mod):
            if right == 0:
                raise CalculationError("Modulus by zero is not allowed.")
            return left % right
        if isinstance(node.op, ast.Pow):
            return left ** right

        raise CalculationError("That operation is not supported.")

    raise CalculationError("Please enter a valid calculation.")


class CalculatorApp:
    # Build a clean calculator window that works well on wide and narrow screens.
    def __init__(self, root):
        self.root = root
        self.root.title("Tech Calculator")
        self.root.geometry("1160x740")
        self.root.minsize(420, 640)

        self.current_expression = ""
        self.previous_result = None
        self.history = load_history()
        self.current_mode = "scientific"
        self.angle_mode = "DEG"
        self.memory_value = None
        self.theme_name = "dark"
        self.theme = THEMES[self.theme_name]
        self.is_compact_layout = None
        self.all_buttons = []

        self.create_menu()
        self.create_layout()
        self.update_history_list()
        self.bind_shortcuts()
        self.apply_theme()
        self.set_mode(self.current_mode)
        self.update_layout_mode()
        self.set_status("Ready. Tap or type to start calculating.")

    def create_menu(self):
        # Add a simple menu bar for common app actions.
        menu_bar = tk.Menu(self.root)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Copy Result", command=self.copy_result)
        file_menu.add_command(label="Clear History", command=self.clear_history)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.destroy)
        menu_bar.add_cascade(label="File", menu=file_menu)

        view_menu = tk.Menu(menu_bar, tearoff=0)
        view_menu.add_command(label="Standard Mode", command=lambda: self.set_mode("standard"))
        view_menu.add_command(label="Scientific Mode", command=lambda: self.set_mode("scientific"))
        view_menu.add_separator()
        view_menu.add_command(label="Toggle Theme", command=self.toggle_theme)
        menu_bar.add_cascade(label="View", menu=view_menu)

        tools_menu = tk.Menu(menu_bar, tearoff=0)
        tools_menu.add_command(label="Degrees", command=lambda: self.set_angle_mode("DEG"))
        tools_menu.add_command(label="Radians", command=lambda: self.set_angle_mode("RAD"))
        menu_bar.add_cascade(label="Tools", menu=tools_menu)

        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="Help", command=self.show_help)
        help_menu.add_command(label="About", command=self.show_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menu_bar)

    def create_layout(self):
        # Build the main frames and widgets for the app.
        self.main_frame = tk.Frame(self.root, padx=16, pady=16)
        self.main_frame.pack(fill="both", expand=True)

        self.calculator_frame = tk.Frame(self.main_frame)
        self.history_frame = tk.Frame(self.main_frame, padx=12, pady=12, highlightthickness=1)

        self.header_frame = tk.Frame(self.calculator_frame)
        self.header_frame.pack(fill="x", padx=12, pady=(12, 8))

        self.title_label = tk.Label(
            self.header_frame,
            text="Tech Calculator",
            font=("Consolas", 22, "bold"),
        )
        self.title_label.pack(side="left")

        top_action_frame = tk.Frame(self.header_frame)
        top_action_frame.pack(side="right")
        self.theme_button = tk.Button(
            top_action_frame,
            text="Theme",
            font=("Consolas", 11, "bold"),
            bd=0,
            relief="flat",
            command=self.toggle_theme,
        )
        self.theme_button.pack(side="left", padx=(0, 8))
        self.register_button(self.theme_button, "action")

        self.about_button = tk.Button(
            top_action_frame,
            text="About",
            font=("Consolas", 11, "bold"),
            bd=0,
            relief="flat",
            command=self.show_about,
        )
        self.about_button.pack(side="left")
        self.register_button(self.about_button, "action")

        self.mode_frame = tk.Frame(self.calculator_frame)
        self.mode_frame.pack(fill="x", padx=12, pady=(0, 8))

        self.standard_mode_button = tk.Button(
            self.mode_frame,
            text="Standard",
            font=("Consolas", 11, "bold"),
            bd=0,
            relief="flat",
            command=lambda: self.set_mode("standard"),
        )
        self.standard_mode_button.pack(side="left")
        self.register_button(self.standard_mode_button, "action")

        self.scientific_mode_button = tk.Button(
            self.mode_frame,
            text="Scientific",
            font=("Consolas", 11, "bold"),
            bd=0,
            relief="flat",
            command=lambda: self.set_mode("scientific"),
        )
        self.scientific_mode_button.pack(side="left", padx=(8, 0))
        self.register_button(self.scientific_mode_button, "action")

        self.info_label = tk.Label(
            self.calculator_frame,
            text="Scientific mode is on. Advanced tools are ready.",
            font=("Segoe UI", 10),
        )
        self.info_label.pack(anchor="w", pady=(0, 6), padx=12)

        self.mode_label = tk.Label(
            self.calculator_frame,
            text="Mode: Scientific | Theme: Dark | Angle: DEG",
            font=("Consolas", 10),
        )
        self.mode_label.pack(anchor="w", pady=(0, 10), padx=12)

        self.display_var = tk.StringVar()

        self.display_frame = tk.Frame(self.calculator_frame, padx=12, pady=12, highlightthickness=1)
        self.display_frame.pack(fill="x", padx=12, pady=(0, 10))

        display_header = tk.Frame(self.display_frame)
        display_header.pack(fill="x", pady=(0, 4))

        self.expression_label = tk.Label(
            display_header,
            text="Expression / Result",
            anchor="w",
            font=("Consolas", 11),
        )
        self.expression_label.pack(side="left")

        self.memory_label = tk.Label(
            display_header,
            text="Memory: Empty",
            anchor="e",
            font=("Consolas", 11),
        )
        self.memory_label.pack(side="right")

        self.display = tk.Entry(
            self.display_frame,
            textvariable=self.display_var,
            font=("Consolas", 28, "bold"),
            justify="right",
            bd=0,
            relief="flat",
        )
        self.display.pack(fill="x", ipady=14)
        self.display.focus_set()

        display_action_frame = tk.Frame(self.calculator_frame)
        display_action_frame.pack(fill="x", padx=12, pady=(0, 12))

        self.copy_button = tk.Button(
            display_action_frame,
            text="Copy Result",
            font=("Consolas", 11, "bold"),
            bd=0,
            relief="flat",
            command=self.copy_result,
        )
        self.copy_button.pack(side="left")
        self.register_button(self.copy_button, "action")

        self.reuse_button = tk.Button(
            display_action_frame,
            text="Reuse Selected",
            font=("Consolas", 11, "bold"),
            bd=0,
            relief="flat",
            command=self.show_selected_history,
        )
        self.reuse_button.pack(side="left", padx=(8, 0))
        self.register_button(self.reuse_button, "action")

        self.content_frame = tk.Frame(self.calculator_frame)
        self.content_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.scientific_frame = tk.Frame(self.content_frame, padx=8, pady=8, highlightthickness=1)

        scientific_header = tk.Frame(self.scientific_frame)
        scientific_header.pack(fill="x", padx=6, pady=(2, 10))

        self.scientific_title = tk.Label(
            scientific_header,
            text="Scientific Tools",
            font=("Consolas", 14, "bold"),
        )
        self.scientific_title.pack(side="left")

        self.angle_toggle_button = tk.Button(
            scientific_header,
            text="Angle: DEG",
            font=("Consolas", 10, "bold"),
            bd=0,
            relief="flat",
            command=self.toggle_angle_mode,
        )
        self.angle_toggle_button.pack(side="right")
        self.register_button(self.angle_toggle_button, "scientific")

        self.scientific_button_frame = tk.Frame(self.scientific_frame)
        self.scientific_button_frame.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        sci_buttons = [
            ["sqrt(", "sin(", "cos("],
            ["tan(", "log(", "ln("],
            ["pi", "e", "abs("],
            ["fact(", "^2", "1/x"],
        ]

        for row_index, row in enumerate(sci_buttons):
            self.scientific_button_frame.grid_rowconfigure(row_index, weight=1)
            for col_index, value in enumerate(row):
                self.scientific_button_frame.grid_columnconfigure(col_index, weight=1)
                button = tk.Button(
                    self.scientific_button_frame,
                    text=value,
                    font=("Consolas", 11, "bold"),
                    bd=0,
                    relief="flat",
                    command=lambda item=value: self.on_button_click(item),
                )
                self.register_button(button, "scientific")
                button.grid(
                    row=row_index,
                    column=col_index,
                    sticky="nsew",
                    padx=4,
                    pady=4,
                    ipady=10,
                )

        self.standard_frame = tk.Frame(self.content_frame)

        self.memory_frame = tk.Frame(self.standard_frame)
        self.memory_frame.pack(fill="x", pady=(0, 10))

        memory_buttons = ["MC", "MR", "M+", "M-"]
        for index, value in enumerate(memory_buttons):
            self.memory_frame.grid_columnconfigure(index, weight=1)
            button = tk.Button(
                self.memory_frame,
                text=value,
                font=("Consolas", 11, "bold"),
                bd=0,
                relief="flat",
                command=lambda item=value: self.on_button_click(item),
            )
            self.register_button(button, "action")
            button.grid(
                row=0,
                column=index,
                sticky="nsew",
                padx=4,
                pady=4,
                ipady=10,
            )

        self.button_frame = tk.Frame(self.standard_frame)
        self.button_frame.pack(fill="both", expand=True)

        buttons = [
            ["C", "Del", "Ans", "/"],
            ["7", "8", "9", "x"],
            ["4", "5", "6", "-"],
            ["1", "2", "3", "+"],
            ["0", ".", "%", "^"],
            ["(", ")", "=", "History"],
        ]

        for row_index, row in enumerate(buttons):
            self.button_frame.grid_rowconfigure(row_index, weight=1)
            for col_index, value in enumerate(row):
                self.button_frame.grid_columnconfigure(col_index, weight=1)
                button = tk.Button(
                    self.button_frame,
                    text=value,
                    font=("Consolas", 13, "bold"),
                    bd=0,
                    relief="flat",
                    command=lambda item=value: self.on_button_click(item),
                )
                self.register_button(button, self.get_button_role(value))
                button.grid(
                    row=row_index,
                    column=col_index,
                    sticky="nsew",
                    padx=4,
                    pady=4,
                    ipady=14,
                )
        self.history_title = tk.Label(
            self.history_frame,
            text="History",
            font=("Consolas", 16, "bold"),
        )
        self.history_title.pack(anchor="w")

        self.history_hint = tk.Label(
            self.history_frame,
            text="Double-click an item to load its result.",
            font=("Segoe UI", 9),
        )
        self.history_hint.pack(anchor="w", pady=(4, 8))

        self.history_listbox = tk.Listbox(
            self.history_frame,
            width=28,
            height=16,
            font=("Consolas", 10),
            bd=0,
            relief="flat",
        )
        self.history_listbox.pack(pady=(10, 10), fill="both", expand=True)
        self.history_listbox.bind("<Double-Button-1>", lambda event: self.show_selected_history())

        history_action_frame = tk.Frame(self.history_frame)
        history_action_frame.pack(fill="x")

        self.copy_history_button = tk.Button(
            history_action_frame,
            text="Copy Selected",
            font=("Consolas", 11, "bold"),
            bd=0,
            relief="flat",
            command=self.copy_selected_history,
        )
        self.copy_history_button.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.register_button(self.copy_history_button, "action")

        self.delete_history_button = tk.Button(
            history_action_frame,
            text="Delete Selected",
            font=("Consolas", 11, "bold"),
            bd=0,
            relief="flat",
            command=self.delete_selected_history,
        )
        self.delete_history_button.pack(side="left", fill="x", expand=True, padx=4)
        self.register_button(self.delete_history_button, "action")

        self.clear_history_button = tk.Button(
            history_action_frame,
            text="Clear History",
            font=("Consolas", 11, "bold"),
            bd=0,
            relief="flat",
            command=self.clear_history,
        )
        self.clear_history_button.pack(side="left", fill="x", expand=True, padx=(4, 0))
        self.register_button(self.clear_history_button, "action")

        self.status_var = tk.StringVar()
        self.status_label = tk.Label(
            self.root,
            textvariable=self.status_var,
            anchor="w",
            font=("Consolas", 10),
            padx=12,
            pady=6,
        )
        self.status_label.pack(fill="x", side="bottom")

    def get_button_role(self, value):
        # Group buttons so each type can share styling.
        if value in ["+", "-", "x", "/", "%", "^", "="]:
            return "operator"
        if value in ["C", "Del", "Ans", "History", "MC", "MR", "M+", "M-"]:
            return "action"
        return "number"

    def register_button(self, button, role):
        # Track buttons so hover and theme styling stay in sync.
        button.button_role = role
        self.all_buttons.append(button)
        button.bind("<Enter>", self.on_button_hover_enter)
        button.bind("<Leave>", self.on_button_hover_leave)

    def get_button_colors(self, role):
        # Return the colors for a given button type.
        if role == "operator":
            return self.theme["button_operator_bg"], self.theme["button_operator_fg"]
        if role == "scientific":
            return self.theme["button_scientific_bg"], self.theme["button_scientific_fg"]
        if role == "action":
            return self.theme["button_action_bg"], self.theme["button_action_fg"]
        return self.theme["button_number_bg"], self.theme["button_number_fg"]

    def style_button(self, button):
        # Apply the current theme to one button.
        bg_color, fg_color = self.get_button_colors(button.button_role)
        button.configure(
            bg=bg_color,
            fg=fg_color,
            activebackground=self.theme["button_hover_bg"],
            activeforeground=self.theme["button_hover_fg"],
            highlightbackground=self.theme["border"],
            highlightcolor=self.theme["border"],
            highlightthickness=1,
            cursor="hand2",
        )

    def on_button_hover_enter(self, event):
        # Create a lightweight hover effect.
        event.widget.configure(
            bg=self.theme["button_hover_bg"],
            fg=self.theme["button_hover_fg"],
        )

    def on_button_hover_leave(self, event):
        # Restore the standard button colors.
        self.style_button(event.widget)

    def set_status(self, message):
        # Show a short message at the bottom of the app.
        self.status_var.set(message)

    def update_memory_label(self):
        # Show the current memory state.
        if self.memory_value is None:
            self.memory_label.config(text="Memory: Empty")
        else:
            self.memory_label.config(text=f"Memory: {format_number(self.memory_value)}")

    def apply_theme(self):
        # Repaint the whole app with the selected black/white theme.
        self.theme = THEMES[self.theme_name]
        theme_label = self.theme_name.title()

        self.root.configure(bg=self.theme["window_bg"])
        self.main_frame.configure(bg=self.theme["window_bg"])
        self.calculator_frame.configure(bg=self.theme["panel_bg"])
        self.history_frame.configure(
            bg=self.theme["surface_bg"],
            highlightbackground=self.theme["border"],
        )
        self.header_frame.configure(bg=self.theme["panel_bg"])
        self.mode_frame.configure(bg=self.theme["panel_bg"])
        self.title_label.configure(bg=self.theme["panel_bg"], fg=self.theme["text_main"])
        self.info_label.configure(bg=self.theme["panel_bg"], fg=self.theme["text_muted"])
        self.mode_label.configure(
            bg=self.theme["panel_bg"],
            fg=self.theme["text_muted"],
            text=(
                f"Mode: {self.current_mode.title()} | "
                f"Theme: {theme_label} | Angle: {self.angle_mode}"
            ),
        )
        self.display_frame.configure(
            bg=self.theme["surface_bg"],
            highlightbackground=self.theme["border"],
        )
        self.expression_label.configure(bg=self.theme["surface_bg"], fg=self.theme["text_muted"])
        self.memory_label.configure(bg=self.theme["surface_bg"], fg=self.theme["text_muted"])
        self.display.configure(
            bg=self.theme["display_bg"],
            fg=self.theme["display_fg"],
            insertbackground=self.theme["display_fg"],
        )
        self.content_frame.configure(bg=self.theme["panel_bg"])
        self.standard_frame.configure(bg=self.theme["panel_bg"])
        self.memory_frame.configure(bg=self.theme["panel_bg"])
        self.button_frame.configure(bg=self.theme["panel_bg"])
        self.scientific_frame.configure(
            bg=self.theme["surface_bg"],
            highlightbackground=self.theme["border"],
        )
        self.scientific_title.configure(bg=self.theme["surface_bg"], fg=self.theme["text_main"])
        self.scientific_button_frame.configure(bg=self.theme["surface_bg"])
        self.history_title.configure(bg=self.theme["surface_bg"], fg=self.theme["text_main"])
        self.history_hint.configure(bg=self.theme["surface_bg"], fg=self.theme["text_muted"])
        self.history_listbox.configure(
            bg=self.theme["history_bg"],
            fg=self.theme["history_fg"],
            selectbackground=self.theme["history_select_bg"],
            selectforeground=self.theme["history_select_fg"],
            highlightbackground=self.theme["border"],
            highlightcolor=self.theme["border"],
            highlightthickness=1,
        )
        self.status_label.configure(bg=self.theme["status_bg"], fg=self.theme["status_fg"])

        for button in self.all_buttons:
            self.style_button(button)

        self.theme_button.configure(text=f"Theme: {theme_label}")
        self.angle_toggle_button.configure(text=f"Angle: {self.angle_mode}")
        self.update_memory_label()
        self.highlight_mode_buttons()

    def highlight_mode_buttons(self):
        # Make the active mode button stand out clearly.
        active_bg = self.theme["button_hover_bg"]
        active_fg = self.theme["button_hover_fg"]
        inactive_bg, inactive_fg = self.get_button_colors("action")

        if self.current_mode == "standard":
            self.standard_mode_button.configure(bg=active_bg, fg=active_fg)
            self.scientific_mode_button.configure(bg=inactive_bg, fg=inactive_fg)
        else:
            self.standard_mode_button.configure(bg=inactive_bg, fg=inactive_fg)
            self.scientific_mode_button.configure(bg=active_bg, fg=active_fg)

    def bind_shortcuts(self):
        # Let the user control the calculator with the keyboard.
        self.root.bind("<Return>", lambda event: self.calculate_result())
        self.root.bind("<KP_Enter>", lambda event: self.calculate_result())
        self.root.bind("<BackSpace>", lambda event: self.on_button_click("Del"))
        self.root.bind("<Delete>", lambda event: self.on_button_click("C"))
        self.root.bind("<Escape>", lambda event: self.on_button_click("C"))
        self.root.bind("<Control-h>", lambda event: self.show_selected_history())
        self.root.bind("<Control-H>", lambda event: self.show_selected_history())
        self.root.bind("<Control-l>", lambda event: self.clear_history())
        self.root.bind("<Control-L>", lambda event: self.clear_history())
        self.root.bind("<Control-c>", lambda event: self.copy_result())
        self.root.bind("<Control-C>", lambda event: self.copy_result())
        self.root.bind("<F1>", lambda event: self.show_help())
        self.root.bind("<F2>", lambda event: self.switch_modes())
        self.root.bind("<F3>", lambda event: self.toggle_theme())
        self.root.bind("<F4>", lambda event: self.toggle_angle_mode())
        self.root.bind("<Configure>", self.on_window_resize)
        self.root.bind("<Key>", self.handle_keypress)

    def handle_keypress(self, event):
        # Accept only the keys that make sense for this calculator.
        allowed_keys = "0123456789+-*/%.()"

        if event.keysym in ["Return", "KP_Enter", "BackSpace", "Delete", "Escape"]:
            return

        if event.state & 0x4:
            return

        if event.char in allowed_keys:
            self.current_expression += event.char
            self.display_var.set(self.current_expression)
            self.set_status(f"Typing: {self.current_expression}")
    def on_window_resize(self, event):
        # Switch between wide and compact layouts based on width.
        if event.widget is self.root:
            self.update_layout_mode()

    def update_layout_mode(self):
        # Rearrange the frames so the app works better on small windows too.
        compact = self.root.winfo_width() < 860
        if compact == self.is_compact_layout:
            return

        self.is_compact_layout = compact
        self.calculator_frame.pack_forget()
        self.history_frame.pack_forget()
        self.standard_frame.pack_forget()
        self.scientific_frame.pack_forget()

        if compact:
            self.calculator_frame.pack(fill="both", expand=True)
            self.history_frame.pack(fill="x", pady=(12, 0))
        else:
            self.calculator_frame.pack(side="left", fill="both", expand=True, padx=(0, 12))
            self.history_frame.pack(side="right", fill="y")

        self.refresh_mode_layout()

    def refresh_mode_layout(self):
        # Show the correct calculator panels for the selected mode.
        self.standard_frame.pack_forget()
        self.scientific_frame.pack_forget()

        if self.current_mode == "standard":
            self.standard_frame.pack(fill="both", expand=True)
        else:
            if self.is_compact_layout:
                self.scientific_frame.pack(fill="x", pady=(0, 10))
                self.standard_frame.pack(fill="both", expand=True)
            else:
                self.scientific_frame.pack(side="left", fill="y", padx=(0, 10))
                self.standard_frame.pack(side="left", fill="both", expand=True)

    def set_mode(self, mode_name):
        # Switch between standard and scientific layouts.
        self.current_mode = mode_name
        if mode_name == "scientific":
            self.info_label.config(text="Scientific mode is on. Advanced tools are ready.")
            self.set_status("Scientific mode enabled.")
        else:
            self.info_label.config(text="Standard mode is on. The layout stays cleaner and simpler.")
            self.set_status("Standard mode enabled.")
        self.apply_theme()
        self.refresh_mode_layout()

    def switch_modes(self):
        # Toggle quickly between the two main modes.
        if self.current_mode == "standard":
            self.set_mode("scientific")
        else:
            self.set_mode("standard")

    def set_angle_mode(self, angle_mode):
        # Set the angle mode used by trig functions.
        self.angle_mode = angle_mode
        self.apply_theme()
        self.set_status(f"Angle mode set to {angle_mode}.")

    def toggle_angle_mode(self):
        # Switch between degree and radian mode.
        if self.angle_mode == "DEG":
            self.set_angle_mode("RAD")
        else:
            self.set_angle_mode("DEG")

    def on_button_click(self, value):
        # Decide what happens when the user clicks a button.
        if value == "C":
            self.current_expression = ""
            self.display_var.set("")
            self.set_status("Cleared the current expression.")
        elif value == "Del":
            self.current_expression = self.current_expression[:-1]
            self.display_var.set(self.current_expression)
            self.set_status("Removed the last character.")
        elif value == "Ans":
            if self.previous_result is None:
                messagebox.showinfo("Nothing To Reuse", "There is no previous result yet. Try a calculation first.")
                self.set_status("No previous result is available yet.")
            else:
                answer_text = format_number(self.previous_result)
                self.current_expression += answer_text
                self.display_var.set(self.current_expression)
                self.set_status(f"Inserted previous result: {answer_text}")
        elif value == "=":
            self.calculate_result()
        elif value == "History":
            self.show_selected_history()
        elif value == "MC":
            self.memory_value = None
            self.update_memory_label()
            self.set_status("Memory cleared.")
        elif value == "MR":
            if self.memory_value is None:
                messagebox.showinfo("Memory Empty", "There is no stored memory value yet.")
                self.set_status("Memory is empty.")
            else:
                memory_text = format_number(self.memory_value)
                self.current_expression += memory_text
                self.display_var.set(self.current_expression)
                self.set_status(f"Inserted memory value: {memory_text}")
        elif value == "M+":
            self.add_to_memory()
        elif value == "M-":
            self.subtract_from_memory()
        elif value == "^2":
            self.current_expression += "**2"
            self.display_var.set(self.current_expression)
            self.set_status(f"Typing: {self.current_expression}")
        elif value == "1/x":
            self.current_expression += "1/("
            self.display_var.set(self.current_expression)
            self.set_status(f"Typing: {self.current_expression}")
        elif value == "x":
            self.current_expression += "*"
            self.display_var.set(self.current_expression)
            self.set_status(f"Typing: {self.current_expression}")
        elif value == "^":
            self.current_expression += "**"
            self.display_var.set(self.current_expression)
            self.set_status(f"Typing: {self.current_expression}")
        else:
            self.current_expression += value
            self.display_var.set(self.current_expression)
            self.set_status(f"Typing: {self.current_expression}")

    def add_to_memory(self):
        # Add the current display value to memory.
        value = self.read_display_value()
        if value is None:
            return
        if self.memory_value is None:
            self.memory_value = value
        else:
            self.memory_value += value
        self.update_memory_label()
        self.set_status(f"Added {format_number(value)} to memory.")

    def subtract_from_memory(self):
        # Subtract the current display value from memory.
        value = self.read_display_value()
        if value is None:
            return
        if self.memory_value is None:
            self.memory_value = -value
        else:
            self.memory_value -= value
        self.update_memory_label()
        self.set_status(f"Subtracted {format_number(value)} from memory.")

    def read_display_value(self):
        # Convert the display text into a number when memory buttons need it.
        display_text = self.display_var.get().strip()
        if display_text == "":
            messagebox.showinfo("Nothing To Store", "Enter or calculate a value before using memory buttons.")
            self.set_status("Use a value before using memory.")
            return None

        try:
            return evaluate_expression(display_text, self.angle_mode)
        except CalculationError:
            try:
                return float(display_text)
            except ValueError:
                messagebox.showinfo("Need A Number", "The display needs a valid number before memory can use it.")
                self.set_status("The display is not ready for memory.")
                return None

    def calculate_result(self):
        # Safely evaluate the current expression and show the result.
        expression = self.current_expression.strip()

        if expression == "":
            messagebox.showinfo("Start With An Expression", "Type or tap a calculation before pressing equals.")
            self.set_status("Enter an expression before pressing =.")
            return

        try:
            result = evaluate_expression(expression, self.angle_mode)
        except CalculationError as error:
            messagebox.showerror("Calculation Problem", f"I couldn't calculate that.\n\n{error}")
            self.set_status(f"Error: {error}")
            return

        self.previous_result = result
        result_text = format_number(result)
        calculation_line = f"{expression} = {result_text}"

        self.history.append(calculation_line)
        save_history(self.history)
        self.update_history_list()

        self.current_expression = result_text
        self.display_var.set(result_text)
        self.set_status(f"Result ready: {result_text}")

    def update_history_list(self):
        # Refresh the visible history list after changes.
        self.history_listbox.delete(0, tk.END)
        if not self.history:
            self.history_listbox.insert(tk.END, "No history yet.")
        else:
            for item in self.history:
                self.history_listbox.insert(tk.END, item)
            self.history_listbox.see(tk.END)
    def clear_history(self):
        # Remove all saved history after confirmation.
        if not self.history:
            messagebox.showinfo("History Is Already Empty", "There are no saved calculations to remove.")
            self.set_status("History is already empty.")
            return

        should_clear = messagebox.askyesno(
            "Clear History",
            "Do you want to remove all saved calculations from history?",
        )

        if should_clear:
            self.history.clear()
            save_history(self.history)
            self.update_history_list()
            self.set_status("History cleared.")
        else:
            self.set_status("History clear canceled.")

    def delete_selected_history(self):
        # Remove one selected history item.
        selected_items = self.history_listbox.curselection()
        if not selected_items or not self.history:
            messagebox.showinfo("Select History First", "Choose a saved history item before deleting.")
            self.set_status("Select a history item before deleting.")
            return

        index = selected_items[0]
        if self.history_listbox.get(index) == "No history yet.":
            return

        del self.history[index]
        save_history(self.history)
        self.update_history_list()
        self.set_status("Selected history item deleted.")

    def show_selected_history(self):
        # Copy a selected history result back into the display.
        selected_items = self.history_listbox.curselection()

        if not selected_items:
            messagebox.showinfo("History", "Select a history item first, then try again.")
            self.set_status("Select a history item first.")
            return

        selected_line = self.history_listbox.get(selected_items[0])
        if selected_line == "No history yet.":
            self.set_status("There is no saved history to reuse.")
            return

        if "=" in selected_line:
            result_text = selected_line.split("=")[-1].strip()
            self.current_expression = result_text
            self.display_var.set(result_text)
            self.set_status(f"Loaded from history: {result_text}")

    def show_help(self):
        # Explain the main controls and scientific functions.
        help_text = (
            "Keyboard shortcuts:\n"
            "Enter = calculate\n"
            "Backspace = delete\n"
            "Delete or Esc = clear\n"
            "F1 = help\n"
            "F2 = switch standard/scientific mode\n"
            "F3 = toggle theme\n"
            "F4 = toggle DEG/RAD\n"
            "Ctrl+C = copy result\n\n"
            "Scientific tools:\n"
            "sqrt(x), sin(x), cos(x), tan(x)\n"
            "log(x), ln(x), abs(x), fact(x)\n"
            "pi, e, x^2, 1/x\n\n"
            "Memory tools:\n"
            "MC, MR, M+, M-"
        )
        messagebox.showinfo("Help", help_text)
        self.set_status("Help opened.")

    def toggle_theme(self):
        # Switch between dark and light monochrome themes.
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        self.apply_theme()
        self.set_status(f"{self.theme_name.title()} theme enabled.")

    def copy_result(self):
        # Copy the current result or expression to the clipboard.
        result_text = self.display_var.get().strip()
        if not result_text:
            messagebox.showinfo("Nothing To Copy", "There is no result to copy yet.")
            self.set_status("There is no result to copy.")
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(result_text)
        self.set_status("Current result copied to clipboard.")

    def copy_selected_history(self):
        # Copy the selected history item to the clipboard.
        selected_items = self.history_listbox.curselection()
        if not selected_items:
            messagebox.showinfo("Select History First", "Choose a history entry before copying.")
            self.set_status("Select a history item before copying.")
            return

        selected_text = self.history_listbox.get(selected_items[0])
        if selected_text == "No history yet.":
            self.set_status("There is no saved history to copy.")
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(selected_text)
        self.set_status("Selected history item copied to clipboard.")

    def show_about(self):
        # Display a short summary about the app.
        about_text = (
            "Tech Calculator\n\n"
            "A lightweight Tkinter calculator with:\n"
            "- standard and scientific modes\n"
            "- memory controls and saved history\n"
            "- safe expression evaluation\n"
            "- degree and radian trig support\n"
            "- keyboard shortcuts and monochrome themes"
        )
        messagebox.showinfo("About", about_text)
        self.set_status("About dialog opened.")


def main():
    # Start the tkinter application.
    root = tk.Tk()
    CalculatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
