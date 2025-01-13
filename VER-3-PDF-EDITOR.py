from PIL import Image, ImageTk
import fitz  # PyMuPDF
import PIL.Image, PIL.ImageTk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import pytesseract
import os

global_base_dir = "C:/UNI/1_Master/UMA/APL_UMA/VER-3-PDF-EDITOR/"
tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hauptmenü mit Sidebar")
        self.geometry("800x600")  # Fenstergröße

        # Hauptlayout mit `grid`
        self.grid_rowconfigure(0, weight=1)  # Zeilen sollen den gesamten Platz einnehmen
        self.grid_columnconfigure(0, weight=0)  # Sidebar hat festen Platz
        self.grid_columnconfigure(1, weight=1)  # Der rechte Bereich nutzt den gesamten verbleibenden Platz

        # Sidebar erstellen (linker Bereich)
        self.sidebar = tk.Frame(self, bg="gray", width=200)
        self.sidebar.grid(row=0, column=0, sticky="ns")  # Links fixiert

        # Buttons für die Sidebar
        buttons = [
            ("PDF-EDITOR", self.show_program1),
            ("Tabellen splitten", self.show_program2),
            ("Texte kontrollieren", self.show_program3)
        ]
        for text, command in buttons:
            button = tk.Button(self.sidebar, text=text, command=command, bg="lightgray")
            button.pack(fill="x", pady=5)

        # Platz für Programminhalte (rechter Bereich)
        self.content_frame = tk.Frame(self, bg="white")
        self.content_frame.grid(row=0, column=1, sticky="nsew")  # Rechte Seite füllt Platz aus

        # Konfigurieren des Frames, damit er den gesamten Platz nutzt
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Frames für Programme initialisieren
        self.frames = {
            "program1": Program1(self.content_frame, self),
            "program2": Program2(self.content_frame, self),
            "program3": Program3(self.content_frame, self)
        }

        # Start mit dem ersten Programm
        self.show_program1()

    def show_program1(self):
        self._show_frame("program1")

    def show_program2(self):
        self._show_frame("program2")

    def show_program3(self):
        self._show_frame("program3")

    def _show_frame(self, name):
        for frame in self.frames.values():
            frame.grid_forget()  # Versteckt alle Frames
        self.frames[name].grid(row=0, column=0, sticky="nsew")  # Zeigt den gewünschten Frame


class Program1(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Titel setzen
        label = tk.Label(self, text="PDF ROI Editor", font=("Arial", 18))
        label.pack(pady=10)

        # High-DPI-Unterstützung aktivieren
        self.controller.call('tk', 'scaling', 2.0)  # Skalierung für 1440p

        # Vollbild-Modus für große Monitore
        self.controller.state('zoomed')

        # Layout-Frame für bessere Kontrolle
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # PDF-Laden Button
        self.load_button = ttk.Button(self.main_frame, text="PDF laden", command=self.load_pdf)
        self.load_button.pack(pady=10)

        # Seitennavigation
        self.page_frame = ttk.Frame(self.main_frame)
        self.page_frame.pack(pady=10)

        self.prev_button = ttk.Button(self.page_frame, text="Vorherige Seite", command=self.prev_page)
        self.prev_button.pack(side=tk.LEFT, padx=10)

        self.page_label = ttk.Label(self.page_frame, text="Seite: 0/0")
        self.page_label.pack(side=tk.LEFT, padx=10)

        self.next_button = ttk.Button(self.page_frame, text="Nächste Seite", command=self.next_page)
        self.next_button.pack(side=tk.LEFT, padx=10)

        # Canvas-Container für maximale Bildnutzung
        self.canvas_frame = ttk.Frame(self.main_frame)
        self.canvas_frame.pack(expand=True, fill=tk.BOTH)

        # Canvas für PDF-Anzeige mit dynamischer Größe
        self.canvas = tk.Canvas(self.canvas_frame, bg='lightgray')
        self.canvas.pack(expand=True, fill=tk.BOTH)

        # ROI-Markierungsmodus
        self.roi_mode = False
        self.page_rois = {}  # Speichert ROIs pro Seite
        self.current_roi = None

        # ROI-Buttons
        self.roi_frame = ttk.Frame(self.main_frame)
        self.roi_frame.pack(pady=10)

        self.start_roi_button = ttk.Button(self.roi_frame, text="ROI Markierung starten",
                                           command=self.start_roi_mode)
        self.start_roi_button.pack(side=tk.LEFT, padx=10)

        self.clear_rois_button = ttk.Button(self.roi_frame, text="ROIs der aktuellen Seite löschen",
                                            command=self.clear_page_rois)
        self.clear_rois_button.pack(side=tk.LEFT, padx=10)

        self.clear_all_rois_button = ttk.Button(self.roi_frame, text="Alle ROIs löschen",
                                                command=self.clear_all_rois)
        self.clear_all_rois_button.pack(side=tk.LEFT, padx=10)

        self.save_rois_button = ttk.Button(self.roi_frame, text="Save ROI", command=self.save_rois)
        self.save_rois_button.pack(side=tk.LEFT, padx=10)

        # --- Button für Textextraktion ---
        self.start_text_extraction = ttk.Button(self.roi_frame, text="Text extrahieren",
                                                command=self.extractText)
        self.start_text_extraction.pack(side=tk.LEFT, padx=10)

        # Klassenvariablen
        self.pdf_document = None
        self.current_page_number = 0
        self.current_image = None
        self.scale_factor = 1.0

        # Canvas-Events für ROI-Markierung
        self.canvas.bind("<Configure>", self.resize_canvas)
        self.canvas.bind("<ButtonPress-1>", self.start_roi)
        self.canvas.bind("<B1-Motion>", self.draw_roi)
        self.canvas.bind("<ButtonRelease-1>", self.end_roi)

    def load_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF Dateien", "*.pdf")])
        if file_path:
            try:
                self.pdf_document = fitz.open(file_path)
                self.current_page_number = 0
                self.page_rois = {}  # Zurücksetzen der ROIs
                self.pdf_name = os.path.splitext(os.path.basename(file_path))[0]  # PDF-Name speichern
                self.display_page()
            except Exception as e:
                messagebox.showerror("Fehler", f"PDF konnte nicht geladen werden: {str(e)}")

    def resize_canvas(self, event):
        if self.pdf_document:
            self.display_page()

    def resize_image_max(self, img, canvas_width, canvas_height):
        # Berechnung des Skalierungsfaktors für maximale Bildgröße
        width_ratio = canvas_width / img.width
        height_ratio = canvas_height / img.height

        # Wähle den kleineren Skalierungsfaktor
        scale_factor = min(width_ratio, height_ratio)

        # Neue Größe berechnen
        new_width = int(img.width * scale_factor)
        new_height = int(img.height * scale_factor)

        # Bild skalieren
        img_resized = img.resize((new_width, new_height), PIL.Image.LANCZOS)
        return img_resized, scale_factor

    def display_page(self):
        if self.pdf_document:
            page = self.pdf_document[self.current_page_number]
            # Höhere Auflösung beim Rendern verwenden
            pix = page.get_pixmap(dpi=150)  # Erhöhte DPI für schärfere Darstellung
            img = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Dynamische Skalierung
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            # Bild möglichst groß skalieren, aber innerhalb des Canvas
            img_resized, scale_factor = self.resize_image_max(img, canvas_width, canvas_height)
            self.current_image = PIL.ImageTk.PhotoImage(img_resized)

            # Skalierungsfaktor berechnen
            self.scale_factor = scale_factor

            self.canvas.delete("all")
            # Zentrieren des Bildes
            x_offset = (canvas_width - img_resized.width) // 2
            y_offset = (canvas_height - img_resized.height) // 2

            self.canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=self.current_image)

            # ROIs der aktuellen Seite zeichnen
            current_page_rois = self.page_rois.get(self.current_page_number, [])
            for roi in current_page_rois:
                # ROI-Koordinaten skalieren und zentrieren
                scaled_roi = [
                    int(roi[0] * self.scale_factor) + x_offset,
                    int(roi[1] * self.scale_factor) + y_offset,
                    int(roi[2] * self.scale_factor) + x_offset,
                    int(roi[3] * self.scale_factor) + y_offset
                ]
                self.canvas.create_rectangle(
                    scaled_roi[0], scaled_roi[1],
                    scaled_roi[2], scaled_roi[3],
                    outline='red', width=2
                )

            # Seitenlabel aktualisieren
            self.page_label.config(text=f"Seite: {self.current_page_number + 1}/{len(self.pdf_document)}")

    def next_page(self):
        if self.pdf_document and self.current_page_number < len(self.pdf_document) - 1:
            self.current_page_number += 1
            self.display_page()

    def prev_page(self):
        if self.pdf_document and self.current_page_number > 0:
            self.current_page_number -= 1
            self.display_page()

    def start_roi_mode(self):
        self.roi_mode = not self.roi_mode
        if self.roi_mode:
            self.start_roi_button.config(text="ROI Markierung beenden")
        else:
            self.start_roi_button.config(text="ROI Markierung starten")

    def start_roi(self, event):
        if self.roi_mode:
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            x_offset = (canvas_width - self.current_image.width()) // 2
            y_offset = (canvas_height - self.current_image.height()) // 2

            # Koordinaten relativ zum Originalbild berechnen
            img_x = (event.x - x_offset) / self.scale_factor
            img_y = (event.y - y_offset) / self.scale_factor

            # Grenzen prüfen
            img_x = max(0, min(img_x, self.current_image.width() / self.scale_factor))
            img_y = max(0, min(img_y, self.current_image.height() / self.scale_factor))

            self.current_roi = [img_x, img_y, img_x, img_y]

    def draw_roi(self, event):
        if self.roi_mode and self.current_roi:
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            x_offset = (canvas_width - self.current_image.width()) // 2
            y_offset = (canvas_height - self.current_image.height()) // 2

            # Korrigiere Koordinaten relativ zum Bild
            img_x = (event.x - x_offset) / self.scale_factor
            img_y = (event.y - y_offset) / self.scale_factor

            self.current_roi[2] = img_x
            self.current_roi[3] = img_y

            # Temporäres ROI zeichnen
            self.canvas.delete("temp_roi")
            scaled_temp_roi = [
                int(self.current_roi[0] * self.scale_factor) + x_offset,
                int(self.current_roi[1] * self.scale_factor) + y_offset,
                int(self.current_roi[2] * self.scale_factor) + x_offset,
                int(self.current_roi[3] * self.scale_factor) + y_offset
            ]

            self.canvas.create_rectangle(
                scaled_temp_roi[0],
                scaled_temp_roi[1],
                scaled_temp_roi[2],
                scaled_temp_roi[3],
                outline='red',
                width=2,
                tags="temp_roi"
            )

    def end_roi(self, event):
        if self.roi_mode and self.current_roi:
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            x_offset = (canvas_width - self.current_image.width()) // 2
            y_offset = (canvas_height - self.current_image.height()) // 2

            # Korrigiere Koordinaten relativ zum Bild
            img_x = (event.x - x_offset) / self.scale_factor
            img_y = (event.y - y_offset) / self.scale_factor

            self.current_roi[2] = img_x
            self.current_roi[3] = img_y

            # ROI speichern
            if self.current_page_number not in self.page_rois:
                self.page_rois[self.current_page_number] = []

            self.page_rois[self.current_page_number].append(self.current_roi)
            self.current_roi = None

            # Anzeige aktualisieren
            self.display_page()

    def clear_page_rois(self):
        if self.current_page_number in self.page_rois:
            self.page_rois[self.current_page_number] = []
            self.display_page()

    def clear_all_rois(self):
        self.page_rois = {}
        self.display_page()

    def save_rois(self):
        if not self.page_rois:
            messagebox.showinfo("Info", "Keine ROIs zum Speichern vorhanden.")
            return

        for page_number, rois in self.page_rois.items():
            page = self.pdf_document[page_number]
            pix = page.get_pixmap(dpi=300)  # Rendern der Seite in hoher Auflösung
            img = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            for idx, roi in enumerate(rois):
                # Debugging
                print("\n--- ROI Debug Info ---")
                print(f"Original ROI: {roi}")
                print(f"Scale Factor: {self.scale_factor}")

                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
                x_offset = (canvas_width - self.current_image.width()) // 2
                y_offset = (canvas_height - self.current_image.height()) // 2

                # Koordinaten mit Skalierungsfaktor korrigieren

                # TESTE mit OFFSET
                x1 = int(min(roi[0], roi[2]) / self.scale_factor)
                y1 = int(min(roi[1], roi[3]) / self.scale_factor) - (x_offset * 0.05)
                x2 = int(max(roi[0], roi[2]) / self.scale_factor) - (x_offset * 0.2)
                y2 = int(max(roi[1], roi[3]) / self.scale_factor) - (x_offset * 0.15)

                # Sicherstellen, dass die Koordinaten innerhalb der Bildgrenzen bleiben
                x1 = max(0, min(x1, pix.width))
                y1 = max(0, min(y1, pix.height))
                x2 = max(0, min(x2, pix.width))
                y2 = max(0, min(y2, pix.height))

                print(f"Calculated Coordinates: [{x1}, {y1}, {x2}, {y2}]")
                print(f"Original Image Size: {pix.width}x{pix.height}")

                # Restlicher Code bleibt unverändert...

                # Debug-Ausgabe
                print(f"Original ROI: {roi}")
                print(f"Scale Factor: {self.scale_factor}")

                # Ausschneiden des ROI
                cropped_img = img.crop((x1, y1, x2, y2))
                # cropped_img = img.crop((scaled_temp_roi[0], scaled_temp_roi[1], scaled_temp_roi[2], scaled_temp_roi[3]))

                # Prüfen, ob das Bild leer ist
                if cropped_img.width <= 0 or cropped_img.height <= 0:
                    messagebox.showerror("Fehler", f"ROI auf Seite {page_number + 1} ist ungültig.")
                    continue

                #save_dir = "C:/UNI/1_Master/UMA/APL_UMA/ROI_Exports"
                save_dir = global_base_dir+"ROI_Exports"

                # Speichern des ROI-Bildes
                roi_filename = os.path.join(save_dir, f"{self.pdf_name}_page_{page_number + 1}_roi_{idx + 1}.png")
                cropped_img.save(roi_filename, "PNG")

    def extractText(self):
        # Pfad zu Tesseract OCR
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

        # Ordnerpfad mit Bildern
        safe_dir = global_base_dir

        # Pfade mit os.path.join verbinden
        paths = [
            os.path.join(global_base_dir, 'tabelleninhalte'),
            os.path.join(global_base_dir, 'seitenbeschriftungen'),
            os.path.join(global_base_dir, 'tabellenkoepfe')
        ]

        # Ordner, in dem die Ergebnisse gespeichert werden
        ergebnis_ordner = os.path.join(safe_dir, 'OCR_Ergebnisse')
        os.makedirs(ergebnis_ordner, exist_ok=True)  # Ordner erstellen, falls er nicht existiert

        # Alle Dateien in den angegebenen Pfaden durchlaufen
        for path in paths:
            for datei_name in os.listdir(path):
                if datei_name.lower().endswith('.png'):  # Nur PNG-Bilder verarbeiten
                    bild_pfad = os.path.join(path, datei_name)  # Korrektes Zusammenfügen des Pfads
                    print(f"Verarbeite Bild: {bild_pfad}")

                    # Bild laden
                    bild = cv2.imread(bild_pfad)

                    # OCR auf das Bild anwenden
                    text = pytesseract.image_to_string(bild, lang='eng')

                    # Ergebnisdatei erstellen
                    text_datei_name = os.path.splitext(datei_name)[0] + '.txt'  # Dateiname mit .txt-Endung
                    text_datei_pfad = os.path.join(path, text_datei_name)

                    # Text in Datei schreiben
                    with open(text_datei_pfad, 'w', encoding='utf-8') as text_datei:
                        text_datei.write(text)

                    print(f"Text gespeichert in: {text_datei_pfad}")
                    print("=" * 100)  # Trenner zwischen Ergebnissen


class Program2(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Titel setzen
        label = tk.Label(self, text="Tabellen-Annotations-Tool", font=("Arial", 18))
        label.pack(pady=10)

        self.input_directory = global_base_dir+"ROI_Exports"

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
        self.controller.state('zoomed')

        self.setup_ui()

        # bilder laden
        self.load_directory()

    def setup_ui(self):
        # Hauptframe
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Kontrollbereich
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(self.control_frame, text="Ordner öffnen",
                  command=self.load_directory).pack(side=tk.LEFT, padx=5)

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
        if not os.path.exists(self.input_directory):
            messagebox.showerror("Fehler", f"Eingabeverzeichnis {self.input_directory} existiert nicht!")
            return

        self.image_files = [f for f in os.listdir(self.input_directory)
                            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp'))]
        self.image_files = [os.path.join(self.input_directory, f) for f in self.image_files]

        if self.image_files:
            self.current_image_index = 0
            self.load_current_image()
        else:
            messagebox.showwarning("Warnung", "Keine Bilder im Eingabeverzeichnis gefunden!")

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

                resized_image = self.original_image.resize((new_width, new_height),
                                                         Image.Resampling.LANCZOS)
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



class Program3(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Titel setzen
        label = tk.Label(self, text="OCR Text Korrektur Tool", font=("Arial", 18))
        label.pack(pady=10)

        # Zustandsvariablen
        # self.base_directory = "C:/UNI/1_Master/UMA/APL_UMA/VER-3-PDF-EDITOR"  # Statischer Pfad hier festgelegt
        self.base_directory = global_base_dir
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
        self.controller.state('zoomed')

        self.setup_ui()
        # Lade direkt die Daten nach der Initialisierung
        self.load_current_directory()

    def setup_ui(self):
        # Hauptframe
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Ordner-Info-Bereich (ohne Auswahlbutton)
        self.folder_frame = ttk.Frame(self.main_frame)
        self.folder_frame.pack(fill=tk.X, pady=(0, 10))

        self.folder_label = ttk.Label(self.folder_frame, text=f"Arbeitsverzeichnis: {self.base_directory}")
        self.folder_label.pack(side=tk.LEFT, padx=5)

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
        self.controller.bind("<Control-s>", lambda event: self.save_changes())

        # Event-Binding für Canvas-Resize
        self.canvas.bind('<Configure>', self.on_canvas_resize)

    def show_status(self, message, label_widget, duration=3000):
        """Zeigt eine Statusmeldung für eine bestimmte Zeit an"""
        label_widget.config(text=message)
        self.controller.after(duration, lambda: label_widget.config(text=""))

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
    app = MainApp()
    app.mainloop()
