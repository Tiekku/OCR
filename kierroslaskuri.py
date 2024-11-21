import os
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from watchdog.observers import Observer
from watchdog.events import FileSystemEvent, FileSystemEventHandler
import tkinter.font as tkfont


class MyHandler(FileSystemEventHandler):
    def __init__(self, app):
        self.app = app
        self.file_data = {}
        self.card_names = {}
        self.card_content = {}

    def load_card_names(self, filepath):
        self.card_names = {}

        with open(filepath, 'r', encoding='latin-1') as file:
            lines = file.readlines()

        for line in lines:
            line = line.strip()
            if line:
                parts = line.split(", Name: ")
                if len(parts) == 2:
                    card_id = parts[0].split("CardID: ")[1].strip()
                    name = parts[1].strip()
                    self.card_names[card_id] = name
                    self.card_content[card_id] = ""

    def on_modified(self, event):
        if isinstance(event, FileSystemEvent):
            filepath = event.src_path
            if filepath not in self.file_data:
                self.file_data[filepath] = {
                    'content': '',
                    'latest_values': {}
                }

            with open(filepath, 'r') as file:
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
                if len(values) >= 8:  # Check if line has enough values
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

                        # Update card content with current situation
                        self.card_content[card_id] = f"{self.card_names.get(card_id, {card_id})} | {counter_text} | Time: {punch_time}"

            # Remove old card IDs from latest_values
            for card_id in list(latest_values.keys()):
                if card_id not in [values[1].strip() if len(values) >= 8 else "" for values in lines]:
                    del latest_values[card_id]

            # Update latest_values with new_latest_values
            latest_values.update(new_latest_values)

            # Update the display with the current content of each card
            self.app.update_content_text(self.card_content.values())



class AppWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Modified File Content")
        self.protocol("WM_DELETE_WINDOW", self.stop_observer)
        self.protocol("WM_DELETE_WINDOW", self.close_window)

        self.content_frame = ttk.Frame(self)
        self.content_frame.grid(row=0, column=0, sticky="nsew")

        self.content_text = tk.Text(self.content_frame, wrap="word")
        self.content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bind the '+' key event to the increase_font_size method
        self.bind("<plus>", lambda event: self.increase_font_size())
        self.bind("<KP_Add>", lambda event: self.increase_font_size())

        # Bind the '-' key event to the decrease_font_size method
        self.bind("<minus>", lambda event: self.decrease_font_size())
        self.bind("<KP_Subtract>", lambda event: self.decrease_font_size())

        scrollbar = ttk.Scrollbar(self.content_frame, command=self.content_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.content_text.config(yscrollcommand=scrollbar.set)

        self.event_handler = MyHandler(self)

        self.start_observer()
        self.create_font_buttons()
        self.set_default_font()
        self.center_text()


    def close_window(self):
        self.stop_observer()
        super().destroy()

    def destroy(self):
        self.stop_observer()
        super().destroy()
        

    def center_text(self):
        tag = "center"
        self.content_text.tag_configure(tag, justify="center")
        start_line = 1.0
        end_line = float(self.content_text.index(tk.END).split(".")[0]) + 1.0
        self.content_text.tag_add(tag, start_line, end_line)

    def start_observer(self):
        directory = filedialog.askdirectory()
        if directory:
            filename = "cardName.txt"
            filepath = os.path.join(directory, filename)
            self.observer = Observer()
            self.observer.schedule(self.event_handler, directory, recursive=True)
            self.observer.start()

            self.event_handler.load_card_names(filepath)

    def stop_observer(self):
        if hasattr(self, 'observer'):
            self.observer.stop()
            self.observer.join()


    def update_content_text(self, card_content):
        # Clear the current content
        self.content_text.delete("1.0", tk.END)

        # Append the content of each card
        for content in card_content:
            if content.strip():  # Skip empty lines
                self.content_text.insert(tk.END, content + '\n')

        # Configure output formatting
        self.configure_output_formatting()

    def configure_output_formatting(self):
        # Configure tags for formatting
        self.content_text.tag_configure("name", lmargin1=10)
        self.content_text.tag_configure("counter", lmargin1=100)

        # Apply formatting to each line
        for i in range(1, int(self.content_text.index(tk.END).split('.')[0])+1):
            self.format_line(i)

    def format_line(self, line_number):
        line_start = f"{line_number}.0"
        line_end = f"{line_number+1}.0"

        # Apply formatting to the name column
        self.content_text.tag_add("name", line_start, line_end)

        # Apply formatting to the counter column
        self.content_text.tag_add("counter", f"{line_number}.40", line_end)



    def create_font_buttons(self):
        button_frame = ttk.Frame(self)
        button_frame.grid(row=0, column=1, sticky="nsew")

        # Create a label for the filter input
        filter_label = ttk.Label(button_frame, text="Filter CN:")
        filter_label.grid(row=0, column=0, sticky=tk.E, padx=5, pady=5)

        # Create a text input box for CN filtering
        self.filter_entry = tk.Entry(button_frame)
        self.filter_entry.grid(row=1, column=0, padx=5, pady=5)

        # Create a button to apply the filter
        filter_button = ttk.Button(button_frame, text="Apply Filter", command=self.apply_filter)
        filter_button.grid(row=2, column=0, padx=5, pady=5)

        # Create + button to increase font size
        plus_button = ttk.Button(button_frame, text="+", command=self.increase_font_size)
        plus_button.grid(row=3, column=0, padx=5, pady=5)

        # Create - button to decrease font size
        minus_button = ttk.Button(button_frame, text="-", command=self.decrease_font_size)
        minus_button.grid(row=4, column=0, padx=5, pady=5)

    def apply_filter(self):
        # Get the filter input from the entry box
        filter_input = self.filter_entry.get()
        
        # Split the input into individual codes
        filter_codes = [code.strip() for code in filter_input.split(',')]

        # Filter the lines based on the codes
        filtered_lines = []
        for line in self.content_text.get("1.0", tk.END).splitlines():
            values = line.split('|')
            if len(values) >= 2:
                card_id = values[0].strip()
                if card_id in filter_codes:
                    filtered_lines.append(line)

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


app = AppWindow()
app.mainloop()
