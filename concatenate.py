import csv

# Dateipfade
content_file = 'Frank_modell_eval_page_4_roi_1_content.txt'
header_file = 'Frank_modell_eval_page_4_roi_1_header.txt'
sides_file = 'Frank_modell_eval_page_4_roi_1_sides.txt'
output_csv = 'output_table.csv'

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
    num_cols = len(header_rows)  # Annahme: alle Zeilen in header_blocks haben dieselbe Anzahl an Spalten

    # Inhalte aufteilen und in Zellen einfügen
    content_values = [item for block in split_lines_into_cells(content_blocks) for item in block]

    # Debugging: Ausgabe der Maße
    print(f"Header-Spalten: {num_cols}, Seitenzeilen: {num_rows}, Inhalte: {len(content_values)}")

    if len(content_values) != num_rows * num_cols:
        raise ValueError("Die Anzahl der Inhalte stimmt nicht mit den Tabellenmaßen überein.")

    # Tabelle erstellen
    table = [[""] * (num_cols + 1) for _ in range(num_rows + 1)]

    # Kopfzeilen in die Tabelle einfügen
    for col_index, header in enumerate(header_rows):
        table[0][col_index + 1] = " ".join(header)

    # Seitenbeschriftungen in die Tabelle einfügen
    for row_index, side in enumerate(side_rows):
        table[row_index + 1][0] = " ".join(side)  # Alle Zeilen der Beschriftung zusammenfügen

    # Inhalte spaltenweise in die Tabelle einfügen
    content_index = 0
    for col in range(1, num_cols + 1):  # Spaltenweise durchlaufen
        for row in range(1, num_rows + 1):  # Zeilenweise innerhalb der Spalte
            table[row][col] = content_values[content_index]
            content_index += 1

    return table


"""
- das ist die Version für das Parsing Zeilenweise
- die obige Funktion erzeugt aus dem Frank Paper eine richtige Tabelle
- dq ist das Parsing aufgrund der fehlenden Linien spaltenweise




def create_table(header_blocks, side_blocks, content_blocks):

header_rows = split_lines_into_cells(header_blocks)
side_rows = split_lines_into_cells(side_blocks)

# Dimensionen der Tabelle bestimmen
num_rows = len(side_rows)
num_cols = len(header_rows)  # Annahme: alle Zeilen in header_blocks haben dieselbe Anzahl an Spalten

# Inhalte aufteilen und in Zellen einfügen
content_values = [item for block in split_lines_into_cells(content_blocks) for item in block]

# Debugging: Ausgabe der Maße
print(f"Header-Spalten: {num_cols}, Seitenzeilen: {num_rows}, Inhalte: {len(content_values)}")

if len(content_values) != num_rows * num_cols:
    raise ValueError("Die Anzahl der Inhalte stimmt nicht mit den Tabellenmaßen überein.")

# Tabelle erstellen
table = [[""] * (num_cols + 1) for _ in range(num_rows + 1)]

# Kopfzeilen in die Tabelle einfügen
for col_index, header in enumerate(header_rows):
    table[0][col_index + 1] = " ".join(header)

# Seitenbeschriftungen in die Tabelle einfügen
for row_index, side in enumerate(side_rows):
    table[row_index + 1][0] = " ".join(side)  # Alle Zeilen der Beschriftung zusammenfügen

# Inhalte in die Tabelle einfügen
content_index = 0
for row in range(1, num_rows + 1):
    for col in range(1, num_cols + 1):
        table[row][col] = content_values[content_index]
        content_index += 1

return table




"""


def write_csv(file_path, table):
    """
    Schreibt die Tabelle in eine CSV-Datei.
    """
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(table)

if __name__ == '__main__':
    # Blöcke aus Dateien lesen
    header_blocks = read_blocks(header_file)
    side_blocks = read_blocks(sides_file)
    content_blocks = read_blocks(content_file)

    # Tabelle erstellen
    table = create_table(header_blocks, side_blocks, content_blocks)

    # Tabelle in CSV schreiben
    write_csv(output_csv, table)

    print(f"Tabelle erfolgreich in {output_csv} gespeichert.")
