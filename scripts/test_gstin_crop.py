import sys
sys.path.insert(0, ".")
import cv2
import pytesseract
import numpy as np
import re
from kyc.ocr import deskew_image
from kyc.registry import validate_gstin_format, lookup_gstin

img = cv2.imread('data/kyc_documents/K10_gst_certificate.png')
deskewed = deskew_image(img)
h, w = deskewed.shape[:2]

data = pytesseract.image_to_data(deskewed, output_type=pytesseract.Output.DICT)
for i in range(len(data['text'])):
    word = data['text'][i].strip()
    if 'GSTIN' in word.upper():
        gx = data['left'][i]
        gy = data['top'][i]
        gw = data['width'][i]
        gh = data['height'][i]
        print(f"Found GSTIN: x={gx}, y={gy}, w={gw}, h={gh}")
        
        # Region to the right
        crop_x1 = max(0, gx + gw - 5)
        crop_y1 = max(0, gy - int(gh * 0.5))
        crop_x2 = min(w, gx + gw + int(gw * 8))
        crop_y2 = min(h, gy + int(gh * 1.5))
        
        cropped = deskewed[crop_y1:crop_y2, crop_x1:crop_x2]
        cv2.imwrite('k10_gst_crop.png', cropped)
        
        # Upscale 3-4x
        for scale in [3.0, 3.5, 4.0]:
            scaled = cv2.resize(cropped, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            gray = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY) if len(scaled.shape) == 3 else scaled
            cfg = '--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            txt = pytesseract.image_to_string(gray, config=cfg).strip()
            print(f"Scale {scale} raw: {txt}")
            
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            txt_th = pytesseract.image_to_string(thresh, config=cfg).strip()
            print(f"Scale {scale} otsu: {txt_th}")
