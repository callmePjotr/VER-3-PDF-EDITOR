import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import shutil


class AnnotationTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Tabellen-Annotations-Tool")

        # Zustandsvariablen
        self.current_image_path = None
        self.image_files = []
        self.current_image_index = 0
        self.annotation_mode = "header"  # header, sides, content
        self.selection_start = None
        self.selection_end = None
        self.original_image = None
        self.scale_factor = 1.0

        # Verzeichnisse für die verschiedenen Annotationstypen
        self.output_dirs = {
            "header": "tabellenkoepfe",
            "sides": "seitenbeschriftungen",
            "content": "tabelleninhalte"
        }

        # Vollbild-Modus
        self.root.state('zoomed')  # Für Windows
        # self.root.attributes('-zoomed', True)  # Für Linux

        self.setup_ui()

    def setup_ui(self):
        # Hauptframe
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Kontrollbereich
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(self.control_frame, text="Ordner öffnen", command=self.load_directory).pack(side=tk.LEFT, padx=5)

        # Modus-Anzeige
        self.mode_label = ttk.Label(self.control_frame, text="Aktueller Modus: Tabellenköpfe")
        self.mode_label.pack(side=tk.LEFT, padx=20)

        # Canvas für das Bild
        self.canvas_frame = ttk.Frame(self.main_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, bg='gray')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Event-Bindings
        self.canvas.bind("<ButtonPress-1>", self.start_selection)
        self.canvas.bind("<B1-Motion>", self.update_selection)
        self.canvas.bind("<ButtonRelease-1>", self.end_selection)
        self.canvas.bind("<Configure>", self.on_resize)

        # Erstelle Ausgabeordner
        for dir_name in self.output_dirs.values():
            os.makedirs(dir_name, exist_ok=True)

    def load_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.image_files = [f for f in os.listdir(directory)
                                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp'))]
            self.image_files = [os.path.join(directory, f) for f in self.image_files]
            if self.image_files:
                self.current_image_index = 0
                self.load_current_image()
            else:
                messagebox.showwarning("Warnung", "Keine Bilder im ausgewählten Ordner gefunden!")

    def on_resize(self, event):
        if self.current_image_path:
            self.load_current_image()

    def load_current_image(self):
        if 0 <= self.current_image_index < len(self.image_files):
            self.current_image_path = self.image_files[self.current_image_index]
            self.original_image = Image.open(self.current_image_path)

            # Berechne Skalierungsfaktor
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            if canvas_width > 1 and canvas_height > 1:  # Verhindere Division durch Null
                img_width, img_height = self.original_image.size
                width_ratio = canvas_width / img_width
                height_ratio = canvas_height / img_height
                self.scale_factor = min(width_ratio, height_ratio)

                # Skaliere das Bild
                new_width = int(img_width * self.scale_factor)
                new_height = int(img_height * self.scale_factor)

                resized_image = self.original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                self.tk_image = ImageTk.PhotoImage(resized_image)

                # Zentriere das Bild auf dem Canvas
                x_offset = (canvas_width - new_width) // 2
                y_offset = (canvas_height - new_height) // 2

                self.canvas.delete("all")
                self.canvas.create_image(x_offset, y_offset, anchor="nw", image=self.tk_image)

    def start_selection(self, event):
        self.selection_start = (event.x, event.y)
        self.canvas.delete("selection")

    def update_selection(self, event):
        if self.selection_start:
            self.canvas.delete("selection")
            self.canvas.create_rectangle(
                self.selection_start[0], self.selection_start[1],
                event.x, event.y,
                outline="red", tags="selection"
            )

    def end_selection(self, event):
        if self.selection_start:
            self.selection_end = (event.x, event.y)
            self.save_selection()

            # Zum nächsten Modus oder Bild wechseln
            if self.annotation_mode == "header":
                self.annotation_mode = "sides"
                self.mode_label.config(text="Aktueller Modus: Seitenbeschriftungen")
            elif self.annotation_mode == "sides":
                self.annotation_mode = "content"
                self.mode_label.config(text="Aktueller Modus: Tabelleninhalt")
            elif self.annotation_mode == "content":
                self.annotation_mode = "header"
                self.mode_label.config(text="Aktueller Modus: Tabellenköpfe")
                self.next_image()

    def save_selection(self):
        if self.selection_start and self.selection_end and self.current_image_path:
            # Koordinaten im skalierten Bild
            x1, y1 = self.selection_start
            x2, y2 = self.selection_end

            # Koordinaten zurück auf Originalbildgröße skalieren
            canvas_width = self.canvas.winfo_width()
            img_width = self.original_image.size[0]

            # Offset berücksichtigen
            x_offset = (canvas_width - self.tk_image.width()) // 2
            y_offset = (self.canvas.winfo_height() - self.tk_image.height()) // 2

            # Koordinaten korrigieren
            x1 = (x1 - x_offset) / self.scale_factor
            y1 = (y1 - y_offset) / self.scale_factor
            x2 = (x2 - x_offset) / self.scale_factor
            y2 = (y2 - y_offset) / self.scale_factor

            # Koordinaten normalisieren
            left, top = min(x1, x2), min(y1, y2)
            right, bottom = max(x1, x2), max(y1, y2)

            # Bereich aus Originalbild ausschneiden
            cropped = self.original_image.crop((left, top, right, bottom))

            # Dateiname generieren
            base_name = os.path.splitext(os.path.basename(self.current_image_path))[0]
            output_filename = f"{base_name}_{self.annotation_mode}.png"
            output_path = os.path.join(self.output_dirs[self.annotation_mode], output_filename)

            # Speichern
            cropped.save(output_path, "PNG")

    def next_image(self):
        if self.current_image_index < len(self.image_files) - 1:
            self.current_image_index += 1
            self.load_current_image()
        else:
            messagebox.showinfo("Fertig", "Alle Bilder wurden bearbeitet!")


if __name__ == "__main__":
    root = tk.Tk()
    app = AnnotationTool(root)
    root.mainloop()