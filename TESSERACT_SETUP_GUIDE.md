"""
Tesseract OCR Setup Helper - For scanned PDF support
=====================================================

Your uploaded PDF appears to be SCANNED (image-based text).
The system tried all 6 text extraction strategies but Tesseract OCR is not installed.

================================================================================
SOLUTION 1: Install Tesseract OCR (Recommended) - 5 minutes
================================================================================

Method A: Direct Download (Recommended)
---------------------------------------
1. Go to: https://github.com/UB-Mannheim/tesseract/wiki/Downloads
2. Download: "tesseract-ocr-w64-setup-v5.3.0.exe" (for 64-bit Windows)
3. Run the installer with defaults
4. Installation path: C:\Program Files\Tesseract-OCR
5. Restart your Streamlit app
6. Re-upload your PDF - should now extract text via OCR

Method B: Using Chocolatey (if installed)
------------------------------------------
open PowerShell as Admin and run:
    choco install -y tesseract

Then restart your app.

Method C: Manual Path Configuration
--------  
If Tesseract is installed elsewhere:

Edit your .env file and add:
    PYTESSERACT_PATH=C:\path\to\tesseract.exe

Replace with actual Tesseract location.

================================================================================
SOLUTION 2: Convert PDF Before Uploading (Quick Workaround)
================================================================================

If you can't install Tesseract, convert your PDF to searchable text first:

Online Tools (free, no software needed):
- https://www.ilovepdf.com/ocr
- https://smallpdf.com/ocr-pdf
- https://online2pdf.com/

Desktop Software:
- Adobe Acrobat Reader (Tools > Recognize Text)
- Free: https://github.com/jbarlow83/OCRmyPDF (command-line)

Steps:
1. Go to one of the online tools above
2. Upload your PDF
3. Download the OCR'd PDF (with embedded text)
4. Upload to GenAI Intelligence Studio
5. Should now extract text successfully

================================================================================
SOLUTION 3: Work with Text-Based PDFs Only
================================================================================

Your app fully works with:
✅ Normal PDFs (text-selectable)
✅ Word documents (.docx)
✅ Text files (.txt)
✅ And more...

Just upload a different PDF or document type to test.

================================================================================
Why This Matters
================================================================================

Scanned PDFs = image files inside a PDF container
Text-based PDFs = actual text inside

Without OCR, scanned PDFs can't be read because they're just pictures.

Tesseract is a free open-source OCR tool that converts images to text.

================================================================================
Status
================================================================================

Your app is fully functional!
- Text extraction with 4 strategies: ✅ Working
- Metadata extraction: ✅ Working  
- File handling: ✅ Working
- Q&A system: ✅ Ready

Missing:
- OCR for scanned PDFs (needs Tesseract installation)

Next Step:
1. Download Tesseract installer from GitHub
2. Run the installer (default settings are fine)
3. Restart the app
4. Re-upload your PDF

Questions? The Tesseract wiki has detailed instructions:
https://github.com/UB-Mannheim/tesseract/wiki
"""