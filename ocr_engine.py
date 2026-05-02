import pytesseract
from PIL import ImageGrab
import re
import logging
import os
import sys

class OCREngine:
    def __init__(self, tesseract_path):
        # Check if running as a PyInstaller bundle
        if getattr(sys, 'frozen', False):
            # _MEIPASS points to the bundled directory
            bundled_path = os.path.join(sys._MEIPASS, 'Tesseract-OCR', 'tesseract.exe')
            if os.path.exists(bundled_path):
                pytesseract.pytesseract.tesseract_cmd = bundled_path
                # We must also tell Tesseract where its tessdata folder is
                tessdata_dir = os.path.join(sys._MEIPASS, 'Tesseract-OCR', 'tessdata')
                os.environ['TESSDATA_PREFIX'] = tessdata_dir
                return
                
        # Fallback to configured path for local development
        if tesseract_path and os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        else:
            logging.warning("Tesseract path not found. OCR may fail.")

    def extract_word_at(self, x, y):
        """
        Captures a small box around the (x, y) coordinates and extracts the text.
        """
        # Box dimensions: 240 width, 80 height (centered horizontally, mostly above cursor)
        # x, y is the click position
        box_width = 240
        box_height = 80
        
        left = max(0, x - box_width // 2)
        top = max(0, y - box_height // 2)
        right = left + box_width
        bottom = top + box_height
        
        try:
            # Capture the screen region
            image = ImageGrab.grab(bbox=(left, top, right, bottom))
            
            # Optional: convert to grayscale to improve OCR slightly
            image = image.convert('L')
            
            # Run OCR to get data with bounding boxes
            data = pytesseract.image_to_data(image, config='--psm 11', output_type=pytesseract.Output.DICT)
            
            best_word = None
            min_dist = float('inf')
            
            # The click was exactly at the center of the captured image box
            center_x = box_width // 2
            center_y = box_height // 2
            
            for i in range(len(data['text'])):
                word = data['text'][i].strip()
                # Clean punctuation, keep only letters
                word = re.sub(r'[^A-Za-z]', '', word)
                
                # Filter out single stray characters except 'a' and 'i'
                if len(word) > 1 or word.lower() in ('a', 'i'):
                    # Center of the bounding box for this word
                    word_x = data['left'][i] + data['width'][i] / 2
                    word_y = data['top'][i] + data['height'][i] / 2
                    
                    # Distance squared from click point
                    dist = (word_x - center_x)**2 + (word_y - center_y)**2
                    
                    if dist < min_dist:
                        min_dist = dist
                        best_word = word
                        
            return best_word
            
        except Exception as e:
            logging.error(f"OCR Error: {e}")
            return None
