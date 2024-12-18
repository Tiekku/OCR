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
        self.code_number = "31"  # Default code number
        self.stage_divider = 3  # Default stage divider
        self.last_modified_filepath = None  # Store the last modified file path
        self.last_read_line = 0  # Store the last read line number
        self.card_name_filepath = None  # Store the card name file path
        self.first_time = True  # Flag to check if it's the first time the file was changed

    # Load card names from a file
    def load_card_names(self, filepath):
        self.card_name_filepath = filepath
        with open(filepath, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            for line in lines:
                if line.startswith("CardID:"):
                    parts = line.split(", Name:")
                    if len(parts) == 2:
                        card_id = parts[0].replace("CardID:", "").strip()
                        card_name = parts[1].strip()[:40]  # Trim name to 40 characters
                        self.card_names[card_id] = card_name
                        self.card_content[card_id] = (card_name, 0, 0)
        self.update_counters_from_card_names()
        self.app.update_content_text(self.card_content)

    def update_counters_from_card_names(self):
        for card_id in self.card_names:
            self.card_content[card_id] = (self.card_names[card_id], 0, 0)

    def on_modified(self, event):
        if not event.is_directory:
            filepath = event.src_path
            self.last_modified_filepath = filepath  # Store the last modified file path
            modified_time = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
            if filepath not in self.file_data:
                self.file_data[filepath] = {
                    'content': [],
                    'latest_values': {},
                    'last_read_line': 0
                }
            with open(filepath, 'r', encoding='utf-8') as file:
                # Read only new lines
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(self.file_data[filepath]['last_read_line'], os.SEEK_SET)
                lines = file.readlines()
                self.file_data[filepath]['content'].extend(lines)
                self.file_data[filepath]['last_read_line'] = file_size
                if self.first_time:
                    self.update_counters(filepath, lines, reset=True)
                    self.first_time = False
                else:
                    self.update_counters(filepath, lines, reset=False)

    def update_counters(self, filepath, lines, reset=False):
        if filepath in self.file_data:
            content = self.file_data[filepath]['content']
            latest_values = self.file_data[filepath]['latest_values']
            if reset:
                latest_values.clear()
                self.update_counters_from_card_names()
            last_read_line = 0 if reset else self.file_data[filepath]['last_read_line']
            updated_card_ids = set()

            for line in lines:
                print(f"Reading line: {line.strip()}")
                values = line.split(';')
                if len(values) >= 8:
                    code_number = values[2].strip()
                    card_id = values[1].strip()
                    punch_time = values[7].strip()
                    if code_number == self.code_number:
                        if card_id not in self.card_names:
                            card_name = f"Unknown {card_id}"
                            self.add_new_card(card_id, card_name)
                        if card_id in latest_values:
                            latest_values[card_id] += 1
                        else:
                            latest_values[card_id] = 1

                        lap_counter = (latest_values[card_id] - 1) % self.stage_divider + 1
                        stage_counter = (latest_values[card_id] - 1) // self.stage_divider + 1

                        if self.card_content.get(card_id) != (self.card_names.get(card_id, card_id), stage_counter, lap_counter):
                            self.card_content[card_id] = (self.card_names.get(card_id, card_id), stage_counter, lap_counter)
                            updated_card_ids.add(card_id)
                            print(f"Updated card: {card_id}, Stage: {stage_counter}, Lap: {lap_counter}")

            self.app.update_content_text(self.card_content, updated_card_ids)

    def reset_counters(self):
        self.file_data = {}
        self.card_content = {}
        self.last_read_line = 0
        self.first_time = True  # Reset the flag to ensure full update on next file change
        if self.last_modified_filepath:
            with open(self.last_modified_filepath, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                self.file_data[self.last_modified_filepath] = {
                    'content': lines,
                    'latest_values': {},
                    'last_read_line': 0
                }
                self.update_counters(self.last_modified_filepath, lines, reset=True)

    def add_new_card(self, card_id, card_name):
        self.card_names[card_id] = card_name
        self.card_content[card_id] = (card_name, 0, 0)
        if self.card_name_filepath:
            with open(self.card_name_filepath, "a+", encoding='utf-8') as file:
                file.seek(0, os.SEEK_END)
                if file.tell() > 0:
                    file.seek(file.tell() - 1, os.SEEK_SET)
                    if file.read(1) != '\n':
                        file.write("\n")
                file.write(f"CardID:{card_id}, Name:{card_name}\n")

class AppWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Kierroslaskuri-2024_11_22:18:30")
        self.geometry("800x600")

        self.style = ttk.Style(self)
        self.style.configure("Treeview", rowheight=25)  # Set default row height

        self.tree = ttk.Treeview(self, columns=("Name", "Stage", "Lap"), show='headings')
        self.tree.heading("Name", text="Name")
        self.tree.heading("Stage", text="Stage")
        self.tree.heading("Lap", text="Lap")
        self.tree.column("Name", width=300)
        self.tree.column("Stage", width=50, anchor='center')
        self.tree.column("Lap", width=50, anchor='center')
        self.tree.pack(expand=True, fill=tk.BOTH)

        self.create_font_buttons()

        self.handler = MyHandler(self)
        self.observer = Observer()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Bind keyboard shortcuts for increasing and decreasing font size
        self.bind_all("<Alt-plus>", lambda event: self.increase_font_size())
        self.bind_all("<Alt-minus>", lambda event: self.decrease_font_size())

        # Set default font size
        self.default_font_size = 12
        self.tree.tag_configure('font', font=('TkDefaultFont', self.default_font_size))

    def create_font_buttons(self):
        button_frame = ttk.Frame(self)
        button_frame.pack(side=tk.RIGHT, fill=tk.Y)

        filter_label = ttk.Label(button_frame, text="Filter CN:")
        filter_label.grid(row=0, column=0, padx=5, pady=5)

        self.filter_entry = tk.Entry(button_frame)
        self.filter_entry.grid(row=0, column=1, padx=5, pady=5)
        self.filter_entry.insert(0, "31")  # Set default value to 31

        filter_button = ttk.Button(button_frame, text="Apply Filter", command=self.apply_filter)
        filter_button.grid(row=0, column=2, padx=5, pady=5)

        divider_label = ttk.Label(button_frame, text="Stage Divider:")
        divider_label.grid(row=1, column=0, padx=5, pady=5)

        self.divider_entry = tk.Entry(button_frame)
        self.divider_entry.grid(row=1, column=1, padx=5, pady=5)
        self.divider_entry.insert(0, "3")  # Set default value to 3

        divider_button = ttk.Button(button_frame, text="Set Divider", command=self.set_divider)
        divider_button.grid(row=1, column=2, padx=5, pady=5)

        plus_button = ttk.Button(button_frame, text="+", command=self.increase_font_size)
        plus_button.grid(row=2, column=0, padx=5, pady=5)

        minus_button = ttk.Button(button_frame, text="-", command=self.decrease_font_size)
        minus_button.grid(row=2, column=1, padx=5, pady=5)

        folder_button = ttk.Button(button_frame, text="Select Folder", command=self.start_observer)
        folder_button.grid(row=2, column=2, padx=5, pady=5)

    def increase_font_size(self):
        self.default_font_size += 1
        self.tree.tag_configure('font', font=('TkDefaultFont', self.default_font_size))
        self.style.configure("Treeview", rowheight=self.default_font_size + 12)  # Adjust row height
        self.update_content_text(self.handler.card_content)

    def decrease_font_size(self):
        self.default_font_size = max(8, self.default_font_size - 1)
        self.tree.tag_configure('font', font=('TkDefaultFont', self.default_font_size))
        self.style.configure("Treeview", rowheight=self.default_font_size + 12)  # Adjust row height
        self.update_content_text(self.handler.card_content)

    def set_default_font(self):
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(size=20, weight="bold")
        self.tree.tag_configure('font', font=default_font.actual())
        self.style.configure("Treeview", rowheight=default_font.actual()['size'] + 12)  # Adjust row height

    def update_content_text(self, card_content, updated_card_ids=None):
        existing_items = {self.tree.item(item, "values")[0]: item for item in self.tree.get_children()}
        updated_card_ids = updated_card_ids or set(card_content.keys())
        for card_id, (name, stage, lap) in card_content.items():
            if card_id in updated_card_ids:
                if name in existing_items:
                    item_id = existing_items[name]
                    current_values = self.tree.item(item_id, "values")
                    if current_values != (name, stage, lap):
                        tags = ('font', 'yellow_bg')
                        if lap == self.handler.stage_divider:
                            tags = ('font', 'yellow_bg', 'bold')
                        self.tree.item(item_id, values=(name, stage, lap), tags=tags)
                        #print(f"Updated row: {item_id}, Name: {name}, Stage: {stage}, Lap: {lap}")
                        self.after(5000, lambda item_id=item_id: self.tree.item(item_id, tags=('font',)))
                else:
                    tags = ('font',)
                    if lap == self.handler.stage_divider:
                        tags = ('font', 'yellow_bg', 'bold')
                    item_id = self.tree.insert("", "end", values=(name, stage, lap), tags=tags)
                    print(f"Added row: {item_id}, Name: {name}, Stage: {stage}, Lap: {lap}")
                    self.after(5000, lambda item_id=item_id: self.tree.item(item_id, tags=('font',)))
        self.tree.tag_configure('red', foreground='red')
        self.tree.tag_configure('yellow_bg', background='yellow')
        self.tree.tag_configure('bold', font=('TkDefaultFont', self.default_font_size, 'bold'))
        print("Updated content text in the window.")

    def apply_filter(self):
        # Get the filter input from the entry box
        filter_input = self.filter_entry.get()
        
        # Split the input into individual codes
        filter_codes = filter_input.split(',')
        
        # Update the code number based on the filter input
        if filter_codes:
            self.handler.code_number = filter_codes[0]
            # Reset counters and read the file from the beginning
            self.handler.reset_counters()
            self.handler.load_card_names(self.handler.card_name_filepath)
            self.handler.update_counters(self.handler.last_modified_filepath, self.handler.file_data[self.handler.last_modified_filepath]['content'], reset=True)

    def set_divider(self):
        # Get the divider input from the entry box
        divider_input = self.divider_entry.get()
        
        # Update the stage divider
        try:
            self.handler.stage_divider = int(divider_input)
            # Reset counters and read the file from the beginning
            self.handler.reset_counters()
            self.handler.load_card_names(self.handler.card_name_filepath)
            self.handler.update_counters(self.handler.last_modified_filepath, self.handler.file_data[self.handler.last_modified_filepath]['content'], reset=True)
        except ValueError:
            print("Invalid stage divider value")

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
            self.handler.reset_counters()  # Reset counters and read the file from the beginning

    def stop_observer(self):
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()

    def on_closing(self):
        self.stop_observer()
        self.destroy()

app = AppWindow()
app.mainloop()
