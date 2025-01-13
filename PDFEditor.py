import fitz  # PyMuPDF
import PIL.Image, PIL.ImageTk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from Annotation import AnnotationTool
import cv2
import pytesseract
import os

class PDFROIEditor:
    def __init__(self, master):
        self.master = master
        self.master.title("PDF ROI Editor")

        # High-DPI-Unterstützung aktivieren
        self.master.call('tk', 'scaling', 2.0)  # Skalierung für 1440p

        # Vollbild-Modus für große Monitore
        self.master.state('zoomed')

        # Layout-Frame für bessere Kontrolle
        self.main_frame = tk.Frame(master)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # PDF-Laden Button
        self.load_button = tk.Button(self.main_frame, text="PDF laden", command=self.load_pdf)
        self.load_button.pack(pady=10)

        # Seitennavigation
        self.page_frame = tk.Frame(self.main_frame)
        self.page_frame.pack(pady=10)

        self.prev_button = tk.Button(self.page_frame, text="Vorherige Seite", command=self.prev_page)
        self.prev_button.pack(side=tk.LEFT, padx=10)

        self.page_label = tk.Label(self.page_frame, text="Seite: 0/0")
        self.page_label.pack(side=tk.LEFT, padx=10)

        self.next_button = tk.Button(self.page_frame, text="Nächste Seite", command=self.next_page)
        self.next_button.pack(side=tk.LEFT, padx=10)

        # Canvas-Container für maximale Bildnutzung
        self.canvas_frame = tk.Frame(self.main_frame)
        self.canvas_frame.pack(expand=True, fill=tk.BOTH)

        # Canvas für PDF-Anzeige mit dynamischer Größe
        self.canvas = tk.Canvas(self.canvas_frame, bg='lightgray')
        self.canvas.pack(expand=True, fill=tk.BOTH)

        # ROI-Markierungsmodus
        self.roi_mode = False
        self.page_rois = {}  # Speichert ROIs pro Seite
        self.current_roi = None

        # ROI-Buttons
        self.roi_frame = tk.Frame(self.main_frame)
        self.roi_frame.pack(pady=10)

        self.start_roi_button = tk.Button(self.roi_frame, text="ROI Markierung starten", command=self.start_roi_mode)
        self.start_roi_button.pack(side=tk.LEFT, padx=10)

        self.clear_rois_button = tk.Button(self.roi_frame, text="ROIs der aktuellen Seite löschen",
                                           command=self.clear_page_rois)
        self.clear_rois_button.pack(side=tk.LEFT, padx=10)

        self.clear_all_rois_button = tk.Button(self.roi_frame, text="Alle ROIs löschen", command=self.clear_all_rois)
        self.clear_all_rois_button.pack(side=tk.LEFT, padx=10)

        self.save_rois_button = tk.Button(self.roi_frame, text="Save ROI", command=self.save_rois)
        self.save_rois_button.pack(side=tk.LEFT, padx=10)


        # --- Button für Bilder annotieren ---
        self.start_image_annotation = tk.Button(self.roi_frame, text="Bilder annotieren", command=self.image_annotation)
        self.start_image_annotation.pack(side=tk.LEFT, padx=10)

        # --- Button für Textextraktion ---
        self.start_image_annotation = tk.Button(self.roi_frame, text="Text extrahieren", command=self.extractText)
        self.start_image_annotation.pack(side=tk.LEFT, padx=10)


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
            #self.scale_factor = img_resized.width / pix.width
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

    def resize_image_max(self, img, canvas_width, canvas_height):
        # Berechnung des Skalierungsfaktors für maximale Bildgröße
        width_ratio = canvas_width / img.width
        height_ratio = canvas_height / img.height

        # Wähle den kleineren Skalierungsfaktor
        scale_factor = min(width_ratio, height_ratio)
        print(scale_factor)

        # Neue Größe berechnen
        new_width = int(img.width * scale_factor)
        new_height = int(img.height * scale_factor)

        # Bild skalieren
        img_resized = img.resize((new_width, new_height), PIL.Image.LANCZOS)
        return img_resized, scale_factor

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

        """
        save_dir = filedialog.askdirectory()
        if not save_dir:
            return  # Abbruch, wenn kein Verzeichnis gewählt wurde
        """

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
                y1 = int(min(roi[1], roi[3]) / self.scale_factor) - (x_offset*0.05)
                x2 = int(max(roi[0], roi[2]) / self.scale_factor) - (x_offset*0.2)
                y2 = int(max(roi[1], roi[3]) / self.scale_factor) - (x_offset*0.15)


                """
                # irgendwie wird hier die Skalierung anders berechnet
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
                x_offset = (canvas_width - self.current_image.width()) // 2
                y_offset = (canvas_height - self.current_image.height()) // 2

                scaled_temp_roi = [
                    int(self.current_roi[0] * self.scale_factor) + x_offset,
                    int(self.current_roi[1] * self.scale_factor) + y_offset,
                    int(self.current_roi[2] * self.scale_factor) + x_offset,
                    int(self.current_roi[3] * self.scale_factor) + y_offset
                ]
                """



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

                save_dir = "C:/UNI/1_Master/UMA/APL_UMA/ROI_Exports"

                # Speichern des ROI-Bildes
                roi_filename = os.path.join(save_dir, f"{self.pdf_name}_page_{page_number + 1}_roi_{idx + 1}.png")
                cropped_img.save(roi_filename, "PNG")

                """
                --- IDEE ---
                - vielleicht startet man hier dann einen zweiten Durchlauf
                - man würde noch mal die markierten ROIs als .png bekommen
                - dann würde man manuell den Tabellenkopf bzw. die Beschriftung der Zeilen und Spalten markieren
                - da Tessercat Textblöcke auseinander halten kann
                - so könnte dann eine Tabelle mit NxN Spalten initialisiert werden
                - für jeden erkannten Textblock gibt es dann eine Zeile oder Spalte
                - im zweiten Annotationsschritt würde man also effektiv noch mal zwei ROIs markieren
                - eventuell noch eine Dritte für den Content
                - dann einen automatischen Parser der den Content dann in die richtigen Spalten/Zeilen einordnet
                - dann das ganze noch in ein passendes Format bringen
                - das könnten zum Beispiel ein .csv sein
                
                - bevor man jedoch die Daten in einem CSV speichert, sollte der Nutzer die Möglichkeit haben die Daten zu kontrollieren
                - 11 wird bei manchen Schriftarten als AA erkannt
                - oder >=/<= werden nur als =, < oder > erkannt
                """

    # --- oben wird mit einem button einfach ganz Stump ein weiteres Python File gestartet ---
    # effektiv starten wir mit dem Knopf die Annotation.py
    # dann können wir die eben gespeicherten Bilder einfach selber weiter annotieren
    def image_annotation(self):
        annotation_window = tk.Toplevel(self.roi_frame)
        AnnotationTool(annotation_window)  # AnnotationTool im neuen Fenster starten

    # --- folgende Funktion dient der Extraktion der Texte aus den Bildern ---
    # ich schlage folgende Vorgehensweise vor:
    # pro Tabelle gibt es drei Bilder
    # mann könnte in Betracht ziehen, die Bilder nach der Erkennung wieder zu löschen
    # das Orginalbild würde man behalten
    # die drei Bilder aus den Ordnern (seitenbeschriftung, tabellenkoepfe und tabelleninhalte) wären dann zu löschen
    # wir legen mit dem gleichen Namensschema Textdateien an
    # darin steht dann der aus den Bildern extrahierte Text
    # dann würde man die Texte in einer einzelnen Datei zusammenführen
    # auf diese neuen Textdateien lässt man dann eine Parser laufen, der die Inhalte interpretiert
    def extractText(self):
        # Pfad zu Tesseract OCR
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

        # Ordnerpfad mit Bildern
        safe_dir = r'C:/UNI/1_Master/UMA/APL_UMA/PDF_EDITOR/'

        paths = [
            r'C:/UNI/1_Master/UMA/APL_UMA/PDF_EDITOR/tabelleninhalte',
            r'C:/UNI/1_Master/UMA/APL_UMA/PDF_EDITOR/seitenbeschriftungen',
            r'C:/UNI/1_Master/UMA/APL_UMA/PDF_EDITOR/tabellenkoepfe'
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


    # --- Nachbearbeitung der Texte ---
    """
    - tatsächlich kann es bei horizontalen Texten wie es bei den Köpfen der Tabellen der Fall ist Probleme geben
    - gibt es keine Strukturelemente oder Texte die Aufschluss über Zusammenhang einzelner Textblöcke geben,
      kann es der Fall sein, dass sich die Parsing-Reihenfolge der OCR ändert von vertikal auf horizontal 
    - das zieht das Problem nach sich, dass der Text zwar erkannt wird, aber in der falschen Reihenfolge
    - dann macht der text natürlich keinen Sinn mehr
    - mein Lösungsvorschlag wäre ein weiterer Zwischenschritt:
    - man würde die Texte präsentiert bekommen und die Möglichkeit haben, diese anzupassen
    
    - denkbar wäre eine Split-Ansicht
    - das zugeschnittene Bild wird dann angezeigt
    - daneben oder darunter der erkannte Text
    - bevor sozusagen gespeichert wird, kann dieser nochmals angepasst werden
    """
    # --- Implementierung davon folgt hier ---
    # --- über die Naviagation müsste man sich Gedanken machen ---
    # eventuell Kobination von Annotation und Annotation_with_text.py
    # wir brauchen eine Option "Texte überprüfen" sodass man eventuell das main-Fenster refreshed anstatt dann mehrere Fenster geöffnet zu habem

    # --- dafür gibt es den VER-2-PDF-EDITOR ---
    # --- bessere Navigation ---
    """
    - das bisher größte Problem ist, dass wir drei Skripte haben, die bereits unsere Aufgabe erfüllen
    - jedoch ist die Navigation und Verwendung nicht gerade nutzerfreundlich
    - wir öffnen und schließen mehrere Fenster
    mit self.current_frame.pack_forget() können wir sozusagne das aktuelle Fenster überschreiben
    - Ziel ist eine nutzerfreundliche Anwendung
    - hierfür hat VER-2 eine Sidebar, mit der man zwischen den drei Hauptfunktionen navigieren soll
    - Tabellenextraktion, Aufspalten der Tabellen + Extraktion der Texte, Überprüfung/Bearbeitung der Texte
    """

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFROIEditor(root)
    root.mainloop()