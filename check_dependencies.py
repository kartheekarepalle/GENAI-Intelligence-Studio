"""
Verification script to ensure all dependencies are installed correctly.
"""

import sys
import importlib

def check_import(module_name, display_name=None):
    """Check if a module can be imported."""
    if display_name is None:
        display_name = module_name
    
    try:
        importlib.import_module(module_name)
        print(f"[OK] {display_name}")
        return True
    except ImportError as e:
        print(f"[FAIL] {display_name}")
        print(f"   Error: {e}")
        return False

def main():
    print("\n===== Checking Dependencies =====\n")
    
    critical_modules = [
        ("streamlit", "Streamlit"),
        ("langchain", "LangChain"),
        ("langchain_core", "LangChain Core"),
        ("langchain_community", "LangChain Community"),
        ("langchain_groq", "LangChain Groq"),
        ("faiss", "FAISS"),
        ("sentence_transformers", "Sentence Transformers"),
        ("langgraph", "LangGraph"),
    ]
    
    pdf_modules = [
        ("pypdf", "pypdf"),
        ("pdfplumber", "pdfplumber"),
        ("fitz", "PyMuPDF (fitz)"),
        ("pytesseract", "pytesseract (OCR)"),
        ("PIL", "Pillow (PIL)"),
    ]
    
    other_modules = [
        ("requests", "Requests"),
        ("beautifulsoup4", "BeautifulSoup4"),
        ("dotenv", "python-dotenv"),
        ("groq", "Groq"),
    ]
    
    print("Core Dependencies:")
    core_ok = all(check_import(*m) for m in critical_modules)
    
    print("\nPDF Processing Dependencies:")
    pdf_ok = all(check_import(*m) for m in pdf_modules)
    
    print("\nOther Dependencies:")
    other_ok = all(check_import(*m) for m in other_modules)
    
    print("\n===== Summary =====")
    if core_ok and pdf_ok and other_ok:
        print("[OK] All dependencies are installed!\n")
        return True
    else:
        print("[WARNING] Some dependencies may be missing.")
        print("Run: pip install -r requirements.txt\n")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
