import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import os


class TextCorrectionTool:
    def __init__(self, root):
        self.root = root
        self.root.title("OCR Text Korrektur Tool")

        # Zustandsvariablen
        self.base_directory = None
        self.current_mode = "header"
        self.image_text_pairs = []
        self.current_index = 0
        self.original_image = None
        self.scale_factor = 1.0

        # Verzeichnisse
        self.directories = {
            "header": "tabellenkoepfe",
            "sides": "seitenbeschriftungen",
            "content": "tabelleninhalte"
        }

        # Vollbild-Modus
        self.root.state('zoomed')

        self.setup_ui()

    def setup_ui(self):
        # Hauptframe
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Ordnerauswahl-Bereich
        self.folder_frame = ttk.Frame(self.main_frame)
        self.folder_frame.pack(fill=tk.X, pady=(0, 10))

        self.folder_label = ttk.Label(self.folder_frame, text="Kein Ordner ausgewählt")
        self.folder_label.pack(side=tk.LEFT, padx=5)

        ttk.Button(self.folder_frame, text="Ordner auswählen",
                   command=self.select_base_directory).pack(side=tk.LEFT, padx=5)

        # Status-Label für Ordnerauswahl
        self.folder_status = ttk.Label(self.folder_frame, text="")
        self.folder_status.pack(side=tk.LEFT, padx=20)

        # Kontrollbereich
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(fill=tk.X, pady=(0, 10))

        # Modus-Auswahl
        ttk.Label(self.control_frame, text="Modus:").pack(side=tk.LEFT, padx=5)
        self.mode_var = tk.StringVar(value="header")
        mode_menu = ttk.OptionMenu(self.control_frame, self.mode_var, "header",
                                   "header", "sides", "content",
                                   command=self.change_mode)
        mode_menu.pack(side=tk.LEFT, padx=5)

        # Navigation
        ttk.Button(self.control_frame, text="Vorheriges", command=self.prev_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.control_frame, text="Nächstes", command=self.next_item).pack(side=tk.LEFT, padx=5)

        # Fortschrittsanzeige
        self.progress_label = ttk.Label(self.control_frame, text="0/0")
        self.progress_label.pack(side=tk.LEFT, padx=20)

        # Bildbereich
        self.image_frame = ttk.Frame(self.main_frame)
        self.image_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.canvas = tk.Canvas(self.image_frame, bg='gray')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Textbereich
        self.text_frame = ttk.Frame(self.main_frame)
        self.text_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))

        ttk.Label(self.text_frame, text="Erkannter Text:").pack(anchor=tk.W)

        self.text_widget = tk.Text(self.text_frame, height=10, wrap=tk.WORD)
        self.text_widget.pack(fill=tk.BOTH, expand=True, pady=(5, 5))

        # Unterer Bereich mit Speichern-Button und Status
        self.bottom_frame = ttk.Frame(self.text_frame)
        self.bottom_frame.pack(fill=tk.X, pady=(5, 0))

        # Speicher-Button
        self.save_button = ttk.Button(self.bottom_frame, text="Änderungen speichern",
                                    command=self.save_changes)
        self.save_button.pack(side=tk.LEFT)

        # Status-Label für Speichervorgang
        self.status_label = ttk.Label(self.bottom_frame, text="")
        self.status_label.pack(side=tk.LEFT, padx=10)

        # Tastenkürzel für Speichern
        self.root.bind("<Control-s>", lambda event: self.save_changes())

        # Event-Binding für Canvas-Resize
        self.canvas.bind('<Configure>', self.on_canvas_resize)

    def show_status(self, message, label_widget, duration=3000):
        """Zeigt eine Statusmeldung für eine bestimmte Zeit an"""
        label_widget.config(text=message)
        self.root.after(duration, lambda: label_widget.config(text=""))

    def select_base_directory(self):
        directory = filedialog.askdirectory(title="Wählen Sie den Hauptordner")
        if directory:
            self.base_directory = directory
            self.folder_label.config(text=f"Ausgewählter Ordner: {os.path.basename(directory)}")
            self.load_current_directory()

    def on_canvas_resize(self, event=None):
        if self.original_image:
            self.display_image()

    def load_current_directory(self):
        if not self.base_directory:
            return

        mode = self.mode_var.get()
        directory = os.path.join(self.base_directory, self.directories[mode])

        if not os.path.exists(directory):
            self.show_status(f"Verzeichnis {directory} nicht gefunden!", self.folder_status)
            return

        self.image_text_pairs = []
        found_images = False
        missing_text_files = []

        for file in os.listdir(directory):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                found_images = True
                image_path = os.path.join(directory, file)
                text_path = os.path.join(directory, os.path.splitext(file)[0] + '.txt')

                if not os.path.exists(text_path):
                    missing_text_files.append(os.path.basename(text_path))
                    try:
                        with open(text_path, 'w', encoding='utf-8') as f:
                            f.write('')
                    except Exception as e:
                        self.show_status(f"Fehler beim Erstellen der Textdatei: {e}", self.folder_status)
                        continue

                self.image_text_pairs.append((image_path, text_path))

        if not found_images:
            self.show_status(f"Keine Bilder im Verzeichnis gefunden!", self.folder_status)
            return

        if missing_text_files:
            self.show_status(f"{len(missing_text_files)} neue Textdateien erstellt", self.folder_status)

        self.current_index = 0
        self.update_display()

    def change_mode(self, *args):
        self.load_current_directory()

    def update_display(self):
        if not self.image_text_pairs:
            self.canvas.delete("all")
            self.text_widget.delete('1.0', tk.END)
            self.progress_label.config(text="0/0")
            return

        self.progress_label.config(
            text=f"{self.current_index + 1}/{len(self.image_text_pairs)}")

        image_path, text_path = self.image_text_pairs[self.current_index]
        self.original_image = Image.open(image_path)
        self.display_image()

        try:
            with open(text_path, 'r', encoding='utf-8') as f:
                text = f.read()
            self.text_widget.delete('1.0', tk.END)
            self.text_widget.insert('1.0', text)
        except Exception as e:
            self.show_status(f"Fehler beim Lesen der Textdatei: {e}", self.status_label)

    def display_image(self):
        if self.original_image:
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            if canvas_width > 1 and canvas_height > 1:
                img_width, img_height = self.original_image.size
                width_ratio = canvas_width / img_width
                height_ratio = canvas_height / img_height
                self.scale_factor = min(width_ratio, height_ratio)

                new_width = int(img_width * self.scale_factor)
                new_height = int(img_height * self.scale_factor)

                resized_image = self.original_image.resize(
                    (new_width, new_height), Image.Resampling.LANCZOS)
                self.tk_image = ImageTk.PhotoImage(resized_image)

                x_offset = (canvas_width - new_width) // 2
                y_offset = (canvas_height - new_height) // 2

                self.canvas.delete("all")
                self.canvas.create_image(
                    x_offset, y_offset, anchor="nw", image=self.tk_image)

    def save_changes(self):
        if not self.image_text_pairs:
            return

        _, text_path = self.image_text_pairs[self.current_index]
        text = self.text_widget.get('1.0', tk.END.strip())

        try:
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(text)
            self.show_status("Änderungen gespeichert!", self.status_label)
        except Exception as e:
            self.show_status(f"Fehler beim Speichern: {e}", self.status_label)

    def next_item(self):
        if self.current_index < len(self.image_text_pairs) - 1:
            self.current_index += 1
            self.update_display()

    def prev_item(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.update_display()


if __name__ == "__main__":
    root = tk.Tk()
    app = TextCorrectionTool(root)
    root.mainloop()