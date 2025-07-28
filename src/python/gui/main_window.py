import tkinter as tk
from tkinter import ttk, filedialog

class GameTrainerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Game Trainer")
        self.root.geometry("800x500")
        self.is_bot_running = False
        self.setup_gui()

    def setup_gui(self):
        # Create main frame with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Script selection frame
        script_frame = ttk.Frame(main_frame)
        script_frame.pack(fill=tk.X, pady=(0, 20))

        script_label = ttk.Label(script_frame, text="Select Script:")
        script_label.pack(side=tk.LEFT, padx=(0, 10))

        self.script_var = tk.StringVar()
        self.script_combo = ttk.Combobox(script_frame, textvariable=self.script_var)
        self.script_combo['values'] = ('Script 1', 'Script 2', 'Script 3')  # Add your script options here
        self.script_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        browse_btn = ttk.Button(script_frame, text="Browse...", command=self.browse_script)
        browse_btn.pack(side=tk.RIGHT)

        # Buttons
        self.start_stop_btn = ttk.Button(main_frame, text="Start Bot", command=self.toggle_bot)
        self.start_stop_btn.pack(fill=tk.X, pady=(0, 10))

        configure_btn = ttk.Button(main_frame, text="Configure", command=self.configure)
        configure_btn.pack(fill=tk.X, pady=(0, 10))

        help_btn = ttk.Button(main_frame, text="Help", command=self.show_help)
        help_btn.pack(fill=tk.X, pady=(0, 10))

        contact_btn = ttk.Button(main_frame, text="Contact", command=self.show_contact)
        contact_btn.pack(fill=tk.X, pady=(0, 10))

    def browse_script(self):
        filename = filedialog.askopenfilename(
            title="Select Script",
            filetypes=(("Python files", "*.py"), ("All files", "*.*"))
        )
        if filename:
            self.script_var.set(filename)

    def toggle_bot(self):
        self.is_bot_running = not self.is_bot_running
        if self.is_bot_running:
            self.start_stop_btn.configure(text="Stop Bot")
            # Add your bot start logic here
        else:
            self.start_stop_btn.configure(text="Start Bot")
            # Add your bot stop logic here

    def bot_loop(self):
        while self.is_bot_running:
            try:
                # Example bot logic using C functions
                if self.script_var.get() == "Script 1":
                    health = read_memory(0x12345678)  # Example address
                    if health < 100:
                        write_memory(0x12345678, 100)

                    jittered_mouse_move(100, 100)
                    send_key(0x41)  # 'A' key
                time.sleep(0.1)  # Prevent CPU overuse
            except Exception as e:
                print(f"Error in bot loop: {e}")
                self.stop_bot()

    def toggle_bot(self):
        self.is_bot_running = not self.is_bot_running
        if self.is_bot_running:
            self.start_stop_btn.configure(text="Stop Bot")
            self.bot_thread = threading.Thread(target=self.bot_loop, daemon=True)
            self.bot_thread.start()
        else:
            self.stop_bot()

    def stop_bot(self):
        self.is_bot_running = False
        if self.bot_thread:
            self.bot_thread.join(timeout=1.0)
        self.start_stop_btn.configure(text="Start Bot")


    def configure(self):
        # Add configuration window logic here
        pass

    def show_help(self):
        # Add help window logic here
        pass

    def show_contact(self):
        # Add contact window logic here
        pass

    def run(self):
        self.root.mainloop()

def main():
    app = GameTrainerGUI()
    app.run()

if __name__ == "__main__":
    main()