import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
from utils.logger import Logger


class GameTrainerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GameTrainer")
        self.logger = Logger()

        # Button Panel
        btn_frame = tk.Frame(root)
        btn_frame.pack(padx=10, pady=10)

        self.start_btn = tk.Button(btn_frame, text="Start", width=12, command=self.on_start)
        self.stop_btn = tk.Button(btn_frame, text="Stop", width=12, command=self.on_stop)
        self.pause_btn = tk.Button(btn_frame, text="Pause", width=12, command=self.on_pause)
        self.load_btn = tk.Button(btn_frame, text="Load Routine", width=12, command=self.on_load)
        self.config_btn = tk.Button(btn_frame, text="Configure", width=12, command=self.on_configure)
        self.contact_btn = tk.Button(btn_frame, text="Contact", width=12, command=self.on_contact)
        self.logs_btn = tk.Button(btn_frame, text="Logs", width=12, command=self.toggle_logs)

        buttons = [self.start_btn, self.stop_btn, self.pause_btn, self.load_btn,
                   self.config_btn, self.contact_btn, self.logs_btn]

        for btn in buttons:
            btn.pack(pady=2)

        # Log Display (hidden by default)
        self.log_window = ScrolledText(root, height=10, state="disabled")
        self.log_visible = False

    def on_start(self):
        self.logger.log("Bot started.")

    def on_stop(self):
        self.logger.log("Bot stopped.")

    def on_pause(self):
        self.logger.log("Bot paused.")

    def on_load(self):
        file = filedialog.askopenfilename(title="Load Routine")
        if file:
            self.logger.log(f"Loaded routine: {file}")

    def on_configure(self):
        messagebox.showinfo("Configure", "Configuration window not implemented yet.")
        self.logger.log("Opened configuration window.")

    def on_contact(self):
        messagebox.showinfo("Contact", "Reach me on Discord: yourtag#1234")
        self.logger.log("Displayed contact information.")

    def toggle_logs(self):
        if self.log_visible:
            self.log_window.pack_forget()
        else:
            self.log_window.pack(fill="both", expand=True)
        self.log_visible = not self.log_visible

    def update_log_display(self, msg):
        self.log_window.config(state="normal")
        self.log_window.insert(tk.END, msg + "\n")
        self.log_window.yview(tk.END)
        self.log_window.config(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    gui = GameTrainerGUI(root)
    gui.logger.set_gui_logger(gui.update_log_display)
    root.mainloop()
