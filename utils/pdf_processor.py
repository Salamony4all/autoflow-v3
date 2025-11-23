import os
import cv2
import numpy as np
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import json

class PDFProcessor:
    """Process PDF files to detect, crop, and stitch tables"""
    
    def __init__(self):
        self.table_keywords = ['sn', 'qty', 'image', 'description', 'unit', 'unit rate', 'total', 'sl.no', 'item', 'amount', 'price']
    
    def preprocess_pdf(self, pdf_path, session_id):
        """
        Preprocess PDF to detect and stitch tables
        Returns: dict with stitched table image and metadata
        """
        # Convert PDF to images
        images = convert_from_path(pdf_path, dpi=300)
        
        output_dir = os.path.join('outputs', session_id, 'preprocessing')
        os.makedirs(output_dir, exist_ok=True)
        
        all_tables = []
        table_header = None
        
        for page_num, image in enumerate(images):
            # Convert PIL image to OpenCV format
            img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Detect tables in the page
            tables = self.detect_tables(img_cv, page_num)
            
            for table in tables:
                # Extract table region
                x, y, w, h = table['bbox']
                table_img = img_cv[y:y+h, x:x+w]
                
                # Check if this is a header row
                if table_header is None and self.is_table_header(table_img):
                    table_header = table_img
                    table['is_header'] = True
                else:
                    table['is_header'] = False
                
                table['image'] = table_img
                all_tables.append(table)
        
        # Stitch tables together
        stitched_image = self.stitch_tables(all_tables, table_header)
        
        # Save stitched image
        stitched_path = os.path.join(output_dir, 'stitched_table.jpg')
        cv2.imwrite(stitched_path, stitched_image)
        
        # Save individual cropped tables as thumbnails
        thumbnails = []
        for idx, table in enumerate(all_tables):
            if not table.get('is_header', False):
                thumb_path = os.path.join(output_dir, f'table_page_{table["page"]}_part_{idx}.jpg')
                cv2.imwrite(thumb_path, table['image'])
                thumbnails.append({
                    'page': table['page'],
                    'index': idx,
                    'path': thumb_path,
                    'bbox': table['bbox']
                })
        
        return {
            'stitched_image': stitched_path,
            'thumbnails': thumbnails,
            'total_tables': len(all_tables),
            'has_header': table_header is not None
        }
    
    def detect_tables(self, image, page_num):
        """
        Detect table boundaries in an image
        Returns: list of table bounding boxes
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        
        # Detect horizontal and vertical lines
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        
        horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
        vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
        
        # Combine lines
        table_mask = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0)
        
        # Find contours
        contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        tables = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by size (ignore small contours)
            if w > 100 and h > 50:
                # Expand bbox slightly to capture borders
                padding = 10
                x = max(0, x - padding)
                y = max(0, y - padding)
                w = min(image.shape[1] - x, w + 2*padding)
                h = min(image.shape[0] - y, h + 2*padding)
                
                tables.append({
                    'bbox': (x, y, w, h),
                    'page': page_num,
                    'area': w * h
                })
        
        # Sort by y-coordinate (top to bottom)
        tables.sort(key=lambda t: t['bbox'][1])
        
        # If no structured tables detected, try OCR-based detection
        if len(tables) == 0:
            tables = self.detect_borderless_tables(image, page_num)
        
        return tables
    
    def detect_borderless_tables(self, image, page_num):
        """
        Detect borderless tables using OCR and text alignment
        """
        # Use pytesseract to get bounding boxes
        try:
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Find rows with table keywords
            table_regions = []
            for i, text in enumerate(data['text']):
                if text.lower().strip() in self.table_keywords:
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    table_regions.append((x, y, w, h))
            
            if table_regions:
                # Find bounding box encompassing all table regions
                min_x = min(r[0] for r in table_regions)
                min_y = min(r[1] for r in table_regions)
                max_x = max(r[0] + r[2] for r in table_regions)
                max_y = max(r[1] + r[3] for r in table_regions)
                
                # Expand to capture full table
                padding = 50
                x = max(0, min_x - padding)
                y = max(0, min_y - padding)
                w = min(image.shape[1] - x, max_x - min_x + 2*padding)
                h = min(image.shape[0] - y, max_y - min_y + 2*padding)
                
                return [{
                    'bbox': (x, y, w, h),
                    'page': page_num,
                    'area': w * h,
                    'borderless': True
                }]
        except Exception as e:
            print(f"OCR detection error: {e}")
        
        return []
    
    def is_table_header(self, table_img):
        """
        Check if table image contains header keywords
        """
        try:
            text = pytesseract.image_to_string(table_img).lower()
            keyword_count = sum(1 for keyword in self.table_keywords if keyword in text)
            return keyword_count >= 3
        except:
            return False
    
    def stitch_tables(self, tables, header):
        """
        Stitch multiple table images into one continuous table
        """
        if not tables:
            return None
        
        # Separate header from body tables
        body_tables = [t for t in tables if not t.get('is_header', False)]
        
        if not body_tables:
            return tables[0]['image'] if tables else None
        
        # Find maximum width
        max_width = max(t['image'].shape[1] for t in body_tables)
        if header is not None:
            max_width = max(max_width, header.shape[1])
        
        # Calculate total height
        total_height = 0
        if header is not None:
            total_height += header.shape[0]
        
        for table in body_tables:
            total_height += table['image'].shape[0]
        
        # Create canvas
        stitched = np.ones((total_height, max_width, 3), dtype=np.uint8) * 255
        
        # Place header
        current_y = 0
        if header is not None:
            h, w = header.shape[:2]
            stitched[current_y:current_y+h, 0:w] = header
            current_y += h
        
        # Place body tables
        for table in body_tables:
            img = table['image']
            h, w = img.shape[:2]
            stitched[current_y:current_y+h, 0:w] = img
            current_y += h
        
        return stitched
    
    def crop_table_precisely(self, image, bbox):
        """
        Crop table with precise boundaries
        """
        x, y, w, h = bbox
        
        # Crop the region
        cropped = image[y:y+h, x:x+w]
        
        # Remove extra white space
        gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)
        
        # Find content boundaries
        coords = cv2.findNonZero(thresh)
        if coords is not None:
            x2, y2, w2, h2 = cv2.boundingRect(coords)
            cropped = cropped[y2:y2+h2, x2:x2+w2]
        
        return cropped
