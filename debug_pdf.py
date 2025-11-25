
import os
from pypdf import PdfReader

file_path = "Transcrip_Of_Record.pdf"

if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
else:
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        print(f"Total length: {len(text)}")
        print("-" * 20)
        print(text[:5000]) # Print first 5000 chars
        print("-" * 20)
    except Exception as e:
        print(f"Error reading PDF: {e}")
