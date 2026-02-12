"""Tkinter GUI interface for Chem Validator."""

# Standard library
import logging
import threading
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
from pathlib import Path

# Local
from src.validator import UnifiedChemicalValidator
from src.app_meta import APP_NAME, LICENSE, REPO_URL, __version__


class ValidatorGUI:
    """
    Tkinter-based GUI for chemical validation.

    Provides file picker, output folder selection, live log viewer,
    and runs validation in a background thread to avoid UI freezes.

    Attributes:
        root: Tkinter root window
        file_path: StringVar holding the selected input file path
        output_mode: StringVar for output location mode (current/auto/custom)
        is_validating: Whether a validation is currently in progress
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Chem Validator")
        self.root.geometry("800x600")

        # Variables
        self.file_path = tk.StringVar()
        self.output_mode = tk.StringVar(value="current")  # current, auto, custom
        self.custom_output_path = tk.StringVar()
        self.verbose_logging = tk.BooleanVar(value=False)
        self.output_format = tk.StringVar(value="both")
        self.is_validating = False

        self.setup_ui()

    def setup_ui(self):
        self._setup_menu()

        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- File Selection Section ---
        file_frame = ttk.LabelFrame(main_frame, text="Input File", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Entry(file_frame, textvariable=self.file_path, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(file_frame, text="Browse...", command=self.browse_file).pack(side=tk.RIGHT)

        # --- Output Selection Section ---
        output_frame = ttk.LabelFrame(main_frame, text="Output Location", padding="10")
        output_frame.pack(fill=tk.X, pady=(0, 10))

        # Radio buttons
        ttk.Radiobutton(output_frame, text="Same folder as input file",
                        variable=self.output_mode, value="current",
                        command=self.toggle_output_entry).pack(anchor=tk.W)

        ttk.Radiobutton(output_frame, text="Auto Subfolder (output/filename/)",
                        variable=self.output_mode, value="auto",
                        command=self.toggle_output_entry).pack(anchor=tk.W)

        custom_frame = ttk.Frame(output_frame)
        custom_frame.pack(fill=tk.X, anchor=tk.W)

        ttk.Radiobutton(custom_frame, text="Custom Folder:",
                        variable=self.output_mode, value="custom",
                        command=self.toggle_output_entry).pack(side=tk.LEFT)

        self.custom_entry = ttk.Entry(custom_frame, textvariable=self.custom_output_path)
        self.custom_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))

        self.custom_browse_btn = ttk.Button(custom_frame, text="Browse...", command=self.browse_output_folder)
        self.custom_browse_btn.pack(side=tk.RIGHT)

        self.toggle_output_entry() # Initial state

        # --- Actions Section ---
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(
            action_frame,
            text="Verbose logging",
            variable=self.verbose_logging,
        ).pack(side=tk.LEFT)

        ttk.Label(action_frame, text="Output:").pack(side=tk.LEFT, padx=(15, 5))
        ttk.Combobox(
            action_frame,
            textvariable=self.output_format,
            values=("both", "xlsx", "csv"),
            state="readonly",
            width=8,
        ).pack(side=tk.LEFT)

        self.run_btn = ttk.Button(action_frame, text="Start Validation", command=self.start_validation_thread)
        self.run_btn.pack(side=tk.RIGHT)

        # --- Log Section ---
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(log_frame, state='disabled', height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Status Bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _setup_menu(self) -> None:
        menubar = tk.Menu(self.root)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label=f"About {APP_NAME}...", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def show_about(self) -> None:
        about_text = (
            f"{APP_NAME} v{__version__}\n"
            f"License: {LICENSE}\n"
            f"Repo: {REPO_URL}"
        )
        messagebox.showinfo(f"About {APP_NAME}", about_text)

    def toggle_output_entry(self):
        if self.output_mode.get() == "custom":
            self.custom_entry.config(state='normal')
            self.custom_browse_btn.config(state='normal')
        else:
            self.custom_entry.config(state='disabled')
            self.custom_browse_btn.config(state='disabled')

    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select Input File",
            filetypes=[("Excel/CSV Files", "*.xlsx *.xls *.csv"), ("All Files", "*.*")]
        )
        if filename:
            self.file_path.set(filename)

    def browse_output_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.custom_output_path.set(folder)

    def log(self, message):
        """Append message to log widget (thread-safe)"""
        def _append():
            self.log_text.config(state='normal')
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state='disabled')

        self.root.after(0, _append)

    def update_status(self, message):
        """Update status bar (thread-safe)"""
        self.root.after(0, lambda: self.status_var.set(message))

    def start_validation_thread(self):
        if self.is_validating:
            return

        input_path = self.file_path.get()
        if not input_path:
            messagebox.showerror("Error", "Please select an input file.")
            return

        # Prepare output folder
        mode = self.output_mode.get()
        output_folder = None
        if mode == 'current':
            output_folder = str(Path(input_path).expanduser().resolve().parent)
        if mode == 'auto':
            output_folder = 'auto'
        elif mode == 'custom':
            output_folder = self.custom_output_path.get()
            if not output_folder:
                messagebox.showerror("Error", "Please select a custom output folder.")
                return

        verbose = bool(self.verbose_logging.get())
        output_format = str(self.output_format.get() or "both").strip().lower()

        self.is_validating = True
        self.run_btn.config(state='disabled')
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')

        threading.Thread(
            target=self.run_validation,
            args=(input_path, output_folder, verbose, output_format),
            daemon=True,
        ).start()

    def run_validation(self, input_path: str, output_folder: str | None, verbose: bool, output_format: str):
        """Run validation in background thread with GUI logging."""
        self.log("Starting validation...")
        self.update_status("Validating...")

        try:
            validator = UnifiedChemicalValidator(input_path, output_folder)

            # Custom logging handler to redirect logging.info to GUI
            class GuiHandler(logging.Handler):
                def __init__(self, callback):
                    super().__init__()
                    self.callback = callback
                def emit(self, record):
                    msg = self.format(record)
                    self.callback(msg)

            gui_handler = GuiHandler(self.log)
            gui_handler.setFormatter(logging.Formatter('%(message)s'))
            gui_handler.setLevel(logging.INFO)

            # Attach to root logger temporarily
            root_logger = logging.getLogger()
            old_level = root_logger.level
            root_logger.setLevel(logging.DEBUG if verbose else logging.INFO)
            root_logger.addHandler(gui_handler)
            gui_handler.setLevel(logging.DEBUG if verbose else logging.INFO)

            try:
                success = validator.validate_csv(progress_callback=self.update_status)

                if validator.fatal_error:
                    self.log(f"\nInput file problem: {validator.fatal_error}")
                    self.update_status("Error")
                    self.root.after(0, lambda: messagebox.showerror("Input file problem", validator.fatal_error))
                    return

                # Always save results — rejected rows still need to appear in output
                validator.save_results(output_format=output_format)

                if success:
                    self.log("\nValidation complete — all chemicals passed.")
                    self.update_status("Done")
                    self.root.after(0, lambda: messagebox.showinfo("Success", "Validation completed successfully!"))
                else:
                    self.log("\nValidation complete — some chemicals were rejected. See output file.")
                    self.update_status("Done (with rejections)")
                    self.root.after(0, lambda: messagebox.showwarning("Done", "Validation complete. Some chemicals were rejected. See output file."))
            finally:
                root_logger.removeHandler(gui_handler)
                root_logger.setLevel(old_level)

        except Exception as e:
            self.log(f"Error: {str(e)}")
            self.update_status("Error")
            self.root.after(0, lambda: messagebox.showerror("Error", f"An unexpected error occurred:\n{e}"))

        finally:
            self.is_validating = False
            self.root.after(0, lambda: self.run_btn.config(state='normal'))

def main():
    """Launch the Tkinter GUI."""
    root = tk.Tk()
    app = ValidatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
