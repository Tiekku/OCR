import os
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import tkinter.font as tkfont
from datetime import datetime

# class for handling file system events
class MyHandler(FileSystemEventHandler):
    def __init__(self, app):
        self.app = app
        self.file_data = {}
        self.card_names = {}
        self.card_content = {}

    # Load card names from a file
    def load_card_names(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            for line in lines:
                print(f"Read line: {line.strip()}")
                if line.startswith("CardID:"):
                    parts = line.split(", Name:")
                    if len(parts) == 2:
                        card_id = parts[0].replace("CardID:", "").strip()
                        card_name = parts[1].strip()
                        self.card_names[card_id] = card_name
                        self.card_content[card_id] = f"{card_name} | Stage 0 - Lap 0 | Time: N/A"
                        print(f"Added card: {card_id} - {card_name}")
                    else:
                        print(f"Skipping invalid line in cardName.txt: {line}")
        self.app.update_content_text(self.card_content.values())

    def on_modified(self, event):
        if not event.is_directory:
            filepath = event.src_path
            modified_time = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
            print(f"File modified: {filepath} at {modified_time}")
            if filepath not in self.file_data:
                self.file_data[filepath] = {
                    'content': '',
                    'latest_values': {}
                }
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
                self.file_data[filepath]['content'] = content
            self.update_counters(filepath)

    def update_counters(self, filepath):
        if filepath in self.file_data:
            content = self.file_data[filepath]['content']
            lines = content.split('\n')
            latest_values = self.file_data[filepath]['latest_values']
            new_latest_values = {}

            for line in lines:
                values = line.split(';')
                if len(values) >= 8:
                    code_number = values[2].strip()
                    card_id = values[1].strip()
                    punch_time = values[7].strip()
                    if code_number == '31':
                        if card_id in new_latest_values:
                            new_latest_values[card_id] += 1
                        else:
                            new_latest_values[card_id] = 1

                        lap_counter = new_latest_values[card_id] % 3
                        stage_counter = new_latest_values[card_id] // 3
                        counter_text = f"Stage {stage_counter} - Lap {lap_counter}"

                        self.card_content[card_id] = f"{self.card_names.get(card_id, card_id)} | {counter_text} | Time: {punch_time}"
                        print(f"Updated card content: {self.card_content[card_id]}")

            for card_id in list(latest_values.keys()):
                if card_id not in [values[1].strip() if len(values) >= 8 else "" for values in lines]:
                    del latest_values[card_id]

            latest_values.update(new_latest_values)

            self.app.update_content_text(self.card_content.values())

class AppWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Kierroslaskuri")
        self.geometry("800x600")

        self.content_text = tk.Text(self)
        self.content_text.pack(expand=True, fill=tk.BOTH)
        self.set_default_font()

        self.create_font_buttons()

        self.handler = MyHandler(self)
        self.observer = Observer()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_font_buttons(self):
        button_frame = ttk.Frame(self)
        button_frame.pack(side=tk.RIGHT, fill=tk.Y)

        filter_label = ttk.Label(button_frame, text="Filter CN:")
        filter_label.grid(row=0, column=0, padx=5, pady=5)

        self.filter_entry = tk.Entry(button_frame)
        self.filter_entry.grid(row=0, column=1, padx=5, pady=5)

        filter_button = ttk.Button(button_frame, text="Apply Filter", command=self.apply_filter)
        filter_button.grid(row=0, column=2, padx=5, pady=5)

        plus_button = ttk.Button(button_frame, text="+", command=self.increase_font_size)
        plus_button.grid(row=1, column=0, padx=5, pady=5)

        minus_button = ttk.Button(button_frame, text="-", command=self.decrease_font_size)
        minus_button.grid(row=1, column=1, padx=5, pady=5)

        folder_button = ttk.Button(button_frame, text="Select Folder", command=self.start_observer)
        folder_button.grid(row=1, column=2, padx=5, pady=5)

    def increase_font_size(self):
        current_font = tkfont.Font(font=self.content_text['font'])
        new_font_size = current_font.actual()['size'] + 1
        self.content_text.configure(font=(current_font.actual()['family'], new_font_size))

    def decrease_font_size(self):
        current_font = tkfont.Font(font=self.content_text['font'])
        new_font_size = max(8, current_font.actual()['size'] - 1)
        self.content_text.configure(font=(current_font.actual()['family'], new_font_size))

    def set_default_font(self):
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(size=20, weight="bold")
        self.content_text.configure(font=default_font.actual())

    def update_content_text(self, content):
        self.content_text.delete(1.0, tk.END)
        for line in content:
            self.content_text.insert(tk.END, line + '\n')
        print("Updated content text in the window.")

    def apply_filter(self):
        # Get the filter input from the entry box
        filter_input = self.filter_entry.get()
        
        # Split the input into individual codes
        filter_codes = filter_input.split(',')
        
        # Filter the card content based on the input codes
        filtered_content = [line for line in self.handler.card_content.values() if any(code in line for code in filter_codes)]
        
        # Update the content text with the filtered content
        self.update_content_text(filtered_content)

    def start_observer(self):
        directory = filedialog.askdirectory()
        if directory:
            filename = "cardName.txt"
            filepath = os.path.join(directory, filename)
            if not os.path.exists(filepath):
                return
            self.observer.schedule(self.handler, directory, recursive=True)
            self.observer.start()
            self.handler.load_card_names(filepath)

    def stop_observer(self):
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()

    def on_closing(self):
        self.stop_observer()
        self.destroy()

app = AppWindow()
app.mainloop()
