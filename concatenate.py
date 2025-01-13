import os
import csv

global_base_dir = "C:/UNI/1_Master/UMA/APL_UMA/VER-3-PDF-EDITOR/"
# Ordnerpfade
dir_content = global_base_dir + 'tabelleninhalte'
dir_header = global_base_dir + 'tabellenkoepfe'
dir_sides = global_base_dir + 'seitenbeschriftungen'
output_dir = 'output_csv_files'

# Sicherstellen, dass der Ausgabeordner existiert
os.makedirs(output_dir, exist_ok=True)


def normalize_file_name(file_name):
    """
    Extrahiert den Basisnamen aus dem Dateinamen ohne Suffix und Dateiendung.
    Beispiel: 'Frank_modell_eval_page_4_roi_1_content.txt' -> 'frank_modell_eval_page_4_roi_1'
    """
    # Entferne die Dateiendung (.txt oder .png)
    name_without_ext = os.path.splitext(file_name)[0]

    # Entferne die bekannten Suffixe
    for suffix in ['_content', '_header', '_sides']:
        if name_without_ext.endswith(suffix):
            return name_without_ext[:-len(suffix)].lower()

    return None


def read_blocks(file_path):
    """
    Liest Blöcke von Text aus einer Datei. Blöcke sind durch leere Zeilen getrennt.
    """
    with open(file_path, 'r') as f:
        data = f.read()
    blocks = [block.strip() for block in data.split('\n\n') if block.strip()]
    return blocks


def split_lines_into_cells(blocks):
    """
    Teilt jeden Block in Zeilen auf, sodass jede Zeile eine Zelle repräsentiert.
    """
    return [block.splitlines() for block in blocks]


def create_table(header_blocks, side_blocks, content_blocks):
    """
    Erstellt die Tabelle basierend auf Kopfzeilen, Seitenbeschriftungen und Inhalten.
    """
    header_rows = split_lines_into_cells(header_blocks)
    side_rows = split_lines_into_cells(side_blocks)

    # Dimensionen der Tabelle bestimmen
    num_rows = len(side_rows)
    num_cols = len(header_rows)

    # Inhalte aufteilen und in Zellen einfügen
    content_values = [item for block in split_lines_into_cells(content_blocks) for item in block]

    if len(content_values) != num_rows * num_cols:
        raise ValueError("Die Anzahl der Inhalte stimmt nicht mit den Tabellenmaßen überein.")

    # Tabelle erstellen
    table = [[""] * (num_cols + 1) for _ in range(num_rows + 1)]

    # Kopfzeilen in die Tabelle einfügen
    for col_index, header in enumerate(header_rows):
        table[0][col_index + 1] = " ".join(header)

    # Seitenbeschriftungen in die Tabelle einfügen
    for row_index, side in enumerate(side_rows):
        table[row_index + 1][0] = " ".join(side)

    # Inhalte spaltenweise in die Tabelle einfügen
    content_index = 0
    for col in range(1, num_cols + 1):
        for row in range(1, num_rows + 1):
            table[row][col] = content_values[content_index]
            content_index += 1

    return table


def write_csv(file_path, table):
    """
    Schreibt die Tabelle in eine CSV-Datei.
    """
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(table)


def process_files():
    """
    Findet und verarbeitet alle passenden Dateien in den Ordnern.
    """
    # Nur .txt Dateien verarbeiten und Basisnamen extrahieren
    content_files = {normalize_file_name(f): os.path.join(dir_content, f)
                     for f in os.listdir(dir_content)
                     if f.endswith(".txt")}

    header_files = {normalize_file_name(f): os.path.join(dir_header, f)
                    for f in os.listdir(dir_header)
                    if f.endswith(".txt")}

    sides_files = {normalize_file_name(f): os.path.join(dir_sides, f)
                   for f in os.listdir(dir_sides)
                   if f.endswith(".txt")}

    # Debug-Ausgaben
    print("Normalisierte Seitenbeschriftungen:", sides_files)
    print("Normalisierte Tabellenköpfe:", header_files)
    print("Normalisierte Tabelleninhalte:", content_files)

    # Gemeinsame Basisnamen finden (ohne None-Werte)
    content_files = {k: v for k, v in content_files.items() if k is not None}
    header_files = {k: v for k, v in header_files.items() if k is not None}
    sides_files = {k: v for k, v in sides_files.items() if k is not None}

    common_files = set(content_files.keys()) & set(header_files.keys()) & set(sides_files.keys())
    print("Gemeinsame Dateien:", common_files)

    # Verarbeitung der gemeinsamen Dateien
    for base_name in common_files:
        try:
            header_blocks = read_blocks(header_files[base_name])
            side_blocks = read_blocks(sides_files[base_name])
            content_blocks = read_blocks(content_files[base_name])

            table = create_table(header_blocks, side_blocks, content_blocks)

            output_csv = os.path.join(output_dir, f"{base_name}.csv")
            write_csv(output_csv, table)

            print(f"Tabelle für {base_name} erfolgreich in {output_csv} gespeichert.")

        except Exception as e:
            print(f"Fehler beim Verarbeiten von {base_name}: {e}")


if __name__ == '__main__':
    process_files()