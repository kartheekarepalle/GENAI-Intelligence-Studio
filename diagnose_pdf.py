"""
Diagnostic script to analyze PDF files and identify what's preventing text extraction.
"""

import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def diagnose_pdf(file_path):
    """Comprehensive PDF diagnosis."""
    file_path = Path(file_path)
    
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return False
    
    file_size = file_path.stat().st_size
    logger.info(f"\n{'='*60}")
    logger.info(f"DIAGNOSING: {file_path.name}")
    logger.info(f"Size: {file_size / 1024 / 1024:.2f} MB")
    logger.info(f"{'='*60}\n")
    
    # Test 1: Basic file integrity
    logger.info("[1/8] Testing file integrity...")
    try:
        with open(file_path, 'rb') as f:
            header = f.read(4)
            if header.startswith(b'%PDF'):
                logger.info("  -> Valid PDF header found")
            else:
                logger.warning(f"  -> Unusual header: {header}")
    except Exception as e:
        logger.error(f"  -> Cannot read file: {e}")
        return False
    
    # Test 2: PyPDFLoader
    logger.info("\n[2/8] Testing PyPDFLoader...")
    try:
        from langchain_community.document_loaders import PyPDFLoader
        loader = PyPDFLoader(str(file_path))
        docs = loader.load()
        logger.info(f"  -> Returned {len(docs)} pages")
        if docs:
            total_chars = sum(len(d.page_content) for d in docs)
            logger.info(f"  -> Total characters: {total_chars}")
            if total_chars == 0:
                logger.warning("  -> All pages are empty!")
        else:
            logger.warning("  -> No documents returned")
    except Exception as e:
        logger.error(f"  -> Failed: {e}")
    
    # Test 3: pypdf
    logger.info("\n[3/8] Testing pypdf...")
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(file_path))
        logger.info(f"  -> PDF has {len(reader.pages)} pages")
        
        if reader.is_encrypted:
            logger.warning("  -> PDF IS ENCRYPTED!")
            
        # Try to get text from first page
        if reader.pages:
            first_page_text = reader.pages[0].extract_text()
            if first_page_text:
                logger.info(f"  -> First page has text ({len(first_page_text)} chars)")
                logger.info(f"  -> Preview: {first_page_text[:100]}")
            else:
                logger.warning("  -> First page has NO TEXT")
    except Exception as e:
        logger.error(f"  -> Failed: {e}")
    
    # Test 4: pdfplumber
    logger.info("\n[4/8] Testing pdfplumber...")
    try:
        import pdfplumber
        with pdfplumber.open(str(file_path)) as pdf:
            logger.info(f"  -> PDF has {len(pdf.pages)} pages")
            
            if pdf.pages:
                first_page = pdf.pages[0]
                text = first_page.extract_text()
                if text:
                    logger.info(f"  -> First page has text ({len(text)} chars)")
                    logger.info(f"  -> Preview: {text[:100]}")
                else:
                    logger.warning("  -> First page has NO TEXT")
                
                # Check for tables
                tables = first_page.extract_tables()
                if tables:
                    logger.info(f"  -> Found {len(tables)} tables on first page")
    except Exception as e:
        logger.error(f"  -> Failed: {e}")
    
    # Test 5: PyMuPDF (fitz)
    logger.info("\n[5/8] Testing PyMuPDF (fitz)...")
    try:
        import fitz
        pdf_doc = fitz.open(str(file_path))
        logger.info(f"  -> PDF has {len(pdf_doc)} pages")
        
        if len(pdf_doc) > 0:
            page = pdf_doc[0]
            text = page.get_text()
            if text:
                logger.info(f"  -> First page has text ({len(text)} chars)")
                logger.info(f"  -> Preview: {text[:100]}")
            else:
                logger.warning("  -> First page has NO TEXT")
    except Exception as e:
        logger.error(f"  -> Failed: {e}")
    
    # Test 6: Check for images (scanned PDF)
    logger.info("\n[6/8] Checking for images (scanned PDF detection)...")
    try:
        import fitz
        pdf_doc = fitz.open(str(file_path))
        
        total_images = 0
        total_text = 0
        
        for page_num in range(min(3, len(pdf_doc))):  # Check first 3 pages
            page = pdf_doc[page_num]
            text = page.get_text()
            total_text += len(text)
            
            image_list = page.get_images()
            total_images += len(image_list)
        
        logger.info(f"  -> First 3 pages: {total_images} images, {total_text} text chars")
        
        if total_images > 0 and total_text < 100:
            logger.warning("  -> This appears to be a SCANNED PDF (images, no text)")
            logger.info("  -> OCR extraction will be needed")
    except Exception as e:
        logger.error(f"  -> Failed: {e}")
    
    # Test 7: Try converting to images and OCR sample (first page only)
    logger.info("\n[7/8] Testing OCR with Tesseract...")
    try:
        import fitz
        from PIL import Image
        import pytesseract
        import io
        
        pdf_doc = fitz.open(str(file_path))
        if len(pdf_doc) > 0:
            page = pdf_doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            
            text = pytesseract.image_to_string(img)
            if text and text.strip():
                logger.info(f"  -> OCR extracted {len(text)} characters from first page")
                logger.info(f"  -> Preview: {text[:100]}")
            else:
                logger.warning("  -> OCR returned empty/whitespace")
    except Exception as e:
        logger.error(f"  -> Failed: {e}")
    
    # Test 8: File format check
    logger.info("\n[8/8] Detailed file analysis...")
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
            
        # Check for common patterns
        if b'FlateDecode' in content:
            logger.info("  -> Contains FlateDecode (compressed)")
        if b'Encrypt' in content:
            logger.warning("  -> PDF contains Encrypt entry (may be encrypted)")
        if b'XObject' in content:
            logger.info("  -> Contains XObject (images/forms)")
        
        # Check for text streams
        if b'BT' in content and b'ET' in content:
            logger.info("  -> Contains text streams (BT...ET)")
        else:
            logger.warning("  -> No standard text streams found")
    except Exception as e:
        logger.error(f"  -> Failed: {e}")
    
    logger.info(f"\n{'='*60}\n")
    return True

def main():
    uploaded_dir = Path("uploaded_docs")
    pdf_files = list(uploaded_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.error("No PDF files found in uploaded_docs/")
        return False
    
    # Diagnose all PDFs
    for pdf_file in pdf_files:
        diagnose_pdf(pdf_file)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
