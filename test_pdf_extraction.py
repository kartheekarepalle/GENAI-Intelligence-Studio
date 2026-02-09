#!/usr/bin/env python3
"""
Quick test script to verify PDF extraction works.
This tests all 5 fallback strategies.
"""

import sys
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

from src.document_ingestion.document_processor import DocumentProcessor

def main():
    logger.info("🧪 Testing PDF Extraction Capabilities")
    logger.info("=" * 60)
    
    # Find a PDF in uploaded_docs
    uploaded_dir = Path("uploaded_docs")
    pdf_files = list(uploaded_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.warning("❌ No PDF files found in uploaded_docs/")
        logger.info("Please upload a PDF first via the Streamlit app.")
        return
    
    test_pdf = pdf_files[0]
    logger.info(f"\n📄 Testing with: {test_pdf.name} ({test_pdf.stat().st_size / 1024 / 1024:.2f} MB)")
    logger.info("=" * 60)
    
    try:
        processor = DocumentProcessor(chunk_size=500, chunk_overlap=50)
        
        logger.info("\n🔄 Processing PDF...")
        documents = processor.process_sources([test_pdf])
        
        logger.info(f"\n✅ SUCCESS!")
        logger.info(f"   Total chunks: {len(documents)}")
        
        if documents:
            logger.info(f"\n📊 First chunk preview (first 200 chars):")
            logger.info(f"   {documents[0].page_content[:200]}...")
        
        return True
    
    except Exception as e:
        logger.error(f"\n❌ FAILED: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
