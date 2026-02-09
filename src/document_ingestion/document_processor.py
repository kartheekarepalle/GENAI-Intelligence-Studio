"""Document processing module for loading and splitting documents."""

import json
import csv
import logging
from typing import List, Union
from pathlib import Path

from langchain_community.document_loaders import (
    WebBaseLoader,
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader,
    CSVLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DocumentProcessor:
    """Handles document loading and processing."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    # ---------- loaders ----------

    def load_from_url(self, url: str) -> List[Document]:
        loader = WebBaseLoader(url)
        return loader.load()

    def load_from_pdf(self, file_path: Union[str, Path]) -> List[Document]:
        """
        Load PDF documents with multiple fallback strategies.
        Tries: PyPDFLoader → pypdf → pdfplumber → PyMuPDF → Tesseract OCR → Image extraction
        """
        file_path = Path(file_path)
        logger.info(f"🔍 Attempting to load PDF: {file_path.name}")
        
        # Strategy 1: PyPDFLoader
        try:
            logger.info("  Strategy 1: Trying PyPDFLoader...")
            loader = PyPDFLoader(str(file_path))
            docs = loader.load()
            valid_docs = [d for d in docs if d.page_content.strip()]
            
            if valid_docs:
                logger.info(f"  ✅ PyPDFLoader SUCCESS: {len(valid_docs)} pages extracted")
                for d in valid_docs:
                    d.metadata.setdefault("source", str(file_path))
                return valid_docs
        except Exception as e:
            logger.warning(f"  ❌ PyPDFLoader failed: {e}")
        
        # Strategy 2: pypdf direct extraction
        try:
            logger.info("  Strategy 2: Trying pypdf directly...")
            from pypdf import PdfReader
            reader = PdfReader(str(file_path))
            docs = []
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and text.strip():
                    doc = Document(
                        page_content=text,
                        metadata={"source": str(file_path), "page": page_num + 1}
                    )
                    docs.append(doc)
            
            if docs:
                logger.info(f"  ✅ pypdf SUCCESS: {len(docs)} pages extracted")
                return docs
        except Exception as e:
            logger.warning(f"  ❌ pypdf failed: {e}")
        
        # Strategy 3: pdfplumber (very robust for text extraction)
        try:
            logger.info("  Strategy 3: Trying pdfplumber...")
            import pdfplumber
            docs = []
            with pdfplumber.open(str(file_path)) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text and text.strip():
                        doc = Document(
                            page_content=text,
                            metadata={"source": str(file_path), "page": page_num + 1}
                        )
                        docs.append(doc)
            
            if docs:
                logger.info(f"  ✅ pdfplumber SUCCESS: {len(docs)} pages extracted")
                return docs
        except Exception as e:
            logger.warning(f"  ❌ pdfplumber failed: {e}")
        
        # Strategy 4: PyMuPDF (fitz) - very powerful
        try:
            logger.info("  Strategy 4: Trying PyMuPDF (fitz)...")
            import fitz
            docs = []
            pdf_doc = fitz.open(str(file_path))
            for page_num in range(len(pdf_doc)):
                page = pdf_doc[page_num]
                text = page.get_text()
                if text and text.strip():
                    doc = Document(
                        page_content=text,
                        metadata={"source": str(file_path), "page": page_num + 1}
                    )
                    docs.append(doc)
            
            if docs:
                logger.info(f"  ✅ PyMuPDF SUCCESS: {len(docs)} pages extracted")
                return docs
        except Exception as e:
            logger.warning(f"  ❌ PyMuPDF failed: {e}")
        
        # Strategy 5: EasyOCR for scanned PDFs (Pure Python, no external dependencies)
        try:
            logger.info("  Strategy 5: Trying EasyOCR (Python-based OCR)...")
            import fitz
            from PIL import Image
            import io
            
            # Try to import EasyOCR
            try:
                import easyocr
            except ImportError:
                logger.warning("  ⚠️  EasyOCR not installed")
                raise ImportError("EasyOCR not available")
            
            # Initialize reader (downloads model on first use)
            logger.info("     Initializing OCR engine (first time may take 1-2 min)...")
            reader = easyocr.Reader(['en'], gpu=False)
            
            docs = []
            pdf_doc = fitz.open(str(file_path))
            
            for page_num in range(min(len(pdf_doc), 10)):  # Limit to first 10 pages for speed
                page = pdf_doc[page_num]
                
                # Convert page to image
                pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))  # 1.5x zoom
                img_data = pix.tobytes("ppm")
                img = Image.open(io.BytesIO(img_data))
                
                # Convert PIL Image to numpy array for EasyOCR
                import numpy as np
                img_array = np.array(img)
                
                # Extract text using EasyOCR
                results = reader.readtext(img_array)
                text = '\n'.join([result[1] for result in results])
                
                if text and text.strip() and len(text.strip()) > 20:
                    doc = Document(
                        page_content=text,
                        metadata={"source": str(file_path), "page": page_num + 1, "extraction": "easyocr"}
                    )
                    docs.append(doc)
            
            if docs:
                logger.info(f"  ✅ EasyOCR SUCCESS: {len(docs)} pages extracted")
                return docs
        except Exception as e:
            logger.warning(f"  ⚠️  EasyOCR not available: {e}")
        
        # Strategy 6: LAST RESORT - Extract any available metadata and image count
        try:
            logger.info("  Strategy 6: Last resort - Extracting metadata and structure...")
            import fitz
            
            pdf_doc = fitz.open(str(file_path))
            num_pages = len(pdf_doc)
            
            # Get metadata
            metadata = pdf_doc.metadata or {}
            metadata_text = f"PDF Metadata:\n"
            metadata_text += f"- Pages: {num_pages}\n"
            if metadata.get('title'):
                metadata_text += f"- Title: {metadata['title']}\n"
            if metadata.get('author'):
                metadata_text += f"- Author: {metadata['author']}\n"
            if metadata.get('subject'):
                metadata_text += f"- Subject: {metadata['subject']}\n"
            
            # Try to extract any text or structural info from each page
            page_contents = []
            for page_num in range(min(num_pages, 5)):  # Process first 5 pages
                page = pdf_doc[page_num]
                
                # Try to get blocks (text, image, etc.)
                blocks = page.get_text("blocks")
                page_text = f"Page {page_num + 1}:\n"
                
                for block in blocks:
                    if isinstance(block, tuple) and len(block) > 4:
                        text = block[4]
                        if text and text.strip():
                            page_text += text + "\n"
                
                if page_text.strip() and page_text != f"Page {page_num + 1}:\n":
                    page_contents.append(page_text)
            
            # Combine content
            if page_contents:
                full_content = metadata_text + "\n" + "\n".join(page_contents)
                doc = Document(
                    page_content=full_content,
                    metadata={"source": str(file_path), "extraction_method": "metadata+blocks"}
                )
                logger.info(f"  ✅ Metadata extraction SUCCESS: {len(full_content)} chars")
                return [doc]
            
            if metadata_text.strip():
                doc = Document(
                    page_content=metadata_text + f"\n(PDF contains {num_pages} pages)",
                    metadata={"source": str(file_path), "extraction_method": "metadata_only"}
                )
                logger.warning(f"  ⚠️ Only metadata available: {len(metadata_text)} chars")
                return [doc]
        
        except Exception as e:
            logger.warning(f"  ❌ Metadata extraction failed: {e}")
        
        # All strategies failed
        error_msg = f"❌ CRITICAL: Could not extract text from PDF {file_path.name} using any method"
        logger.error(error_msg)
        raise ValueError(error_msg)

    def load_from_txt(self, file_path: Union[str, Path]) -> List[Document]:
        loader = TextLoader(str(file_path), encoding="utf-8")
        docs = loader.load()
        for d in docs:
            d.metadata.setdefault("source", str(file_path))
        return docs

    def load_from_docx(self, file_path: Union[str, Path]) -> List[Document]:
        """Load Microsoft Word documents."""
        loader = Docx2txtLoader(str(file_path))
        docs = loader.load()
        for d in docs:
            d.metadata.setdefault("source", str(file_path))
            d.metadata["file_type"] = "docx"
        return docs

    def load_from_csv(self, file_path: Union[str, Path]) -> List[Document]:
        """Load CSV files."""
        loader = CSVLoader(str(file_path), encoding="utf-8")
        docs = loader.load()
        for d in docs:
            d.metadata.setdefault("source", str(file_path))
            d.metadata["file_type"] = "csv"
        return docs

    def load_from_json(self, file_path: Union[str, Path]) -> List[Document]:
        """Load JSON files."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert JSON to text representation
        if isinstance(data, list):
            content = "\n\n".join([json.dumps(item, indent=2) for item in data])
        else:
            content = json.dumps(data, indent=2)
        
        doc = Document(
            page_content=content,
            metadata={"source": str(file_path), "file_type": "json"}
        )
        return [doc]

    def load_from_markdown(self, file_path: Union[str, Path]) -> List[Document]:
        """Load Markdown files."""
        loader = UnstructuredMarkdownLoader(str(file_path))
        docs = loader.load()
        for d in docs:
            d.metadata.setdefault("source", str(file_path))
            d.metadata["file_type"] = "markdown"
        return docs

    def load_from_html(self, file_path: Union[str, Path]) -> List[Document]:
        """Load HTML files."""
        loader = UnstructuredHTMLLoader(str(file_path))
        docs = loader.load()
        for d in docs:
            d.metadata.setdefault("source", str(file_path))
            d.metadata["file_type"] = "html"
        return docs

    def load_from_python(self, file_path: Union[str, Path]) -> List[Document]:
        """Load Python source files."""
        loader = TextLoader(str(file_path), encoding="utf-8")
        docs = loader.load()
        for d in docs:
            d.metadata.setdefault("source", str(file_path))
            d.metadata["file_type"] = "python"
        return docs

    def load_documents(self, sources: List[Union[str, Path]]) -> List[Document]:
        """Load documents from URLs, PDFs, TXT, DOCX, CSV, JSON, MD, HTML, or Python files."""
        docs: List[Document] = []
        
        # Supported extensions mapping
        extension_loaders = {
            ".pdf": self.load_from_pdf,
            ".txt": self.load_from_txt,
            ".docx": self.load_from_docx,
            ".doc": self.load_from_docx,
            ".csv": self.load_from_csv,
            ".json": self.load_from_json,
            ".md": self.load_from_markdown,
            ".markdown": self.load_from_markdown,
            ".html": self.load_from_html,
            ".htm": self.load_from_html,
            ".py": self.load_from_python,
        }
        
        for src in sources:
            try:
                src_str = str(src)
                if src_str.startswith("http://") or src_str.startswith("https://"):
                    logger.info(f"Loading from URL: {src_str}")
                    docs.extend(self.load_from_url(src_str))
                    continue

                path = Path(src_str)
                suffix = path.suffix.lower()
                
                if suffix in extension_loaders:
                    loaded = extension_loaders[suffix](path)
                    docs.extend(loaded)
                else:
                    raise ValueError(
                        f"Unsupported source type: {src_str}. "
                        f"Supported: URL, .pdf, .txt, .docx, .csv, .json, .md, .html, .py"
                    )
            except Exception as e:
                logger.error(f"Error processing {src}: {str(e)}")
                raise
        
        return docs

    # ---------- splitter ----------

    def split_documents(self, documents: List[Document]) -> List[Document]:
        return self.splitter.split_documents(documents)

    # ---------- end-to-end ----------

    def process_sources(self, sources: List[Union[str, Path]]) -> List[Document]:
        """Process documents from sources and return split documents."""
        logger.info(f"\n{'='*60}")
        logger.info(f"📚 PROCESSING {len(sources)} SOURCE(S)")
        logger.info(f"{'='*60}")
        
        docs = []
        
        for idx, src in enumerate(sources, 1):
            src_path = Path(src)
            logger.info(f"\n[{idx}/{len(sources)}] Processing: {src_path.name} ({src_path.stat().st_size / 1024 / 1024:.2f} MB)")
            
            try:
                loaded = self.load_documents([src])
                logger.info(f"  -> Loaded {len(loaded)} documents")
                docs.extend(loaded)
            except ValueError as e:
                # If a PDF can't be extracted, create a placeholder
                if str(src_path).lower().endswith('.pdf'):
                    logger.warning(f"  -> PDF extraction failed, creating placeholder...")
                    placeholder = Document(
                        page_content=f"[Unable to extract text from PDF: {src_path.name}]\n\nPlease ensure the PDF is:\n- Not encrypted\n- Contains readable text or images\n- Not corrupted\n\nFile size: {src_path.stat().st_size / 1024 / 1024:.2f} MB",
                        metadata={"source": str(src_path), "type": "placeholder", "note": "extraction_failed"}
                    )
                    docs.append(placeholder)
                else:
                    raise
            except Exception as e:
                logger.error(f"  -> ERROR: {e}")
                raise
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 TOTAL DOCUMENTS LOADED: {len(docs)}")
        logger.info(f"{'='*60}")
        
        if not docs:
            error = "❌ No documents could be loaded from any source"
            logger.error(error)
            raise ValueError(error)
        
        # Filter out empty documents (but keep placeholder docs)
        non_empty_docs = []
        for d in docs:
            content = d.page_content.strip()
            if content and len(content) > 10:  # Need at least 10 characters
                non_empty_docs.append(d)
            elif d.metadata.get("type") == "placeholder":  # Keep placeholders
                non_empty_docs.append(d)
        
        docs = non_empty_docs
        logger.info(f"After filtering empty: {len(docs)} documents")
        
        if not docs:
            error = "❌ All documents are empty after filtering"
            logger.error(error)
            raise ValueError(error)
        
        # Split documents into chunks
        logger.info(f"Splitting documents into chunks (size={self.chunk_size}, overlap={self.chunk_overlap})...")
        split_docs = self.split_documents(docs)
        logger.info(f"✅ Total chunks created: {len(split_docs)}")
        
        logger.info(f"{'='*60}\n")
        return split_docs
