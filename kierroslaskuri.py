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

    # Load card names from a file
    def load_card_names(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            for line in lines:
                # print(f"Read line: {line.strip()}")
                if line.startswith("CardID:"):
                    parts = line.split(", Name:")
                    if len(parts) == 2:
                        card_id = parts[0].replace("CardID:", "").strip()
                        card_name = parts[1].strip()[:40]  # Trim name to 40 characters
                        self.card_names[card_id] = card_name
                        self.card_content[card_id] = (card_name, 0, 0)
                        # print(f"Added card: {card_id} - {card_name}")
                    else:
                        # print(f"Skipping invalid line in cardName.txt: {line}")
                        pass
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
            # print(f"File modified: {filepath} at {modified_time}")
            if filepath not in self.file_data:
                self.file_data[filepath] = {
                    'content': '',
                    'latest_values': {},
                    'last_read_line': 0
                }
            with open(filepath, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                self.file_data[filepath]['content'] = lines
                self.update_counters(filepath, lines)

    def update_counters(self, filepath, lines):
        if filepath in self.file_data:
            content = self.file_data[filepath]['content']
            latest_values = self.file_data[filepath]['latest_values']
            last_read_line = self.file_data[filepath]['last_read_line']

            for line in lines[last_read_line:]:
                values = line.split(';')
                if len(values) >= 8:
                    code_number = values[2].strip()
                    card_id = values[1].strip()
                    punch_time = values[7].strip()
                    if code_number == self.code_number:
                        if card_id in latest_values:
                            latest_values[card_id] += 1
                        else:
                            latest_values[card_id] = 1

                        lap_counter = (latest_values[card_id] - 1) % self.stage_divider + 1
                        stage_counter = (latest_values[card_id] - 1) // self.stage_divider + 1

                        self.card_content[card_id] = (self.card_names.get(card_id, card_id), stage_counter, lap_counter)
                        # print(f"{self.card_names.get(card_id, card_id)} - {stage_counter} - {lap_counter}")

            self.file_data[filepath]['last_read_line'] = len(lines)

            self.app.update_content_text(self.card_content)

    def reset_counters(self):
        self.file_data = {}
        self.card_content = {}
        if self.last_modified_filepath:
            with open(self.last_modified_filepath, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                self.file_data[self.last_modified_filepath] = {
                    'content': lines,
                    'latest_values': {},
                    'last_read_line': 0
                }
                self.update_counters(self.last_modified_filepath, lines)

class AppWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Kierroslaskuri")
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

    def update_content_text(self, card_content):
        existing_items = {self.tree.item(item, "values")[0]: item for item in self.tree.get_children()}
        for card_id, (name, stage, lap) in card_content.items():
            if name in existing_items:
                item_id = existing_items[name]
                current_values = self.tree.item(item_id, "values")
                if current_values != (name, stage, lap):
                    tags = ('font', 'yellow_bg')
                    if lap == self.handler.stage_divider:
                        tags = ('font', 'yellow_bg', 'bold')
                    self.tree.item(item_id, values=(name, stage, lap), tags=tags)
                    print(f"Updated row: {item_id}")
                    self.after(5000, lambda item_id=item_id: self.tree.item(item_id, tags=('font',)))
            else:
                tags = ('font',)
                if lap == self.handler.stage_divider:
                    tags = ('font', 'yellow_bg', 'bold')
                item_id = self.tree.insert("", "end", values=(name, stage, lap), tags=tags)
                print(f"Added row: {item_id}")
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
        
        # Filter the card content based on the input codes
        filtered_content = {card_id: line for card_id, line in self.handler.card_content.items() if any(code in line for code in filter_codes)}
        
        # Update the content text with the filtered content
        self.update_content_text(filtered_content)

        # Update the code number based on the filter input
        if filter_codes:
            self.handler.code_number = filter_codes[0]
            # print(f"Updated code number to: {self.handler.code_number}")
            # Recalculate counters with the new code number
            if self.handler.last_modified_filepath:
                self.handler.update_counters(self.handler.last_modified_filepath, self.file_data[self.handler.last_modified_filepath]['content'])

    def set_divider(self):
        # Get the divider input from the entry box
        divider_input = self.divider_entry.get()
        
        # Update the stage divider
        try:
            self.handler.stage_divider = int(divider_input)
            # print(f"Updated stage divider to: {self.handler.stage_divider}")
            # Reset counters and read the file from the beginning
            self.handler.reset_counters()
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

    def stop_observer(self):
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()

    def on_closing(self):
        self.stop_observer()
        self.destroy()

app = AppWindow()
app.mainloop()
