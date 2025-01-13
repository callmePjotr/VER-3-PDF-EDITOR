import cv2
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# image = cv2.imread('C:/UNI/1_Master/UMA/APL_UMA/PDF_EDITOR/tabellenkoepfe/Frank_modell_eval_page_4_roi_1_header.png')
image = cv2.imread('C:/UNI/1_Master/UMA/APL_UMA/PDF_EDITOR/tabelleninhalte/Frank_modell_eval_page_4_roi_1_content.png')

# Graustufen
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Zeilen mit Morphologie finden
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 5))  # 1 breit, 5 hoch
dilated = cv2.dilate(gray, kernel, iterations=1)

# Konturen finden (entsprechen Zeilen)
contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Jede Zeile extrahieren
for contour in contours:
    x, y, w, h = cv2.boundingRect(contour)
    roi = image[y:y+h, x:x+w]

    # Text mit Tesseract lesen
    text = pytesseract.image_to_string(roi, config='--psm 6')
    print(text)
