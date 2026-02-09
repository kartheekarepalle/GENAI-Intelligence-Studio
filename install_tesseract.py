"""
Automated Tesseract OCR Installer for Windows
This script downloads and installs Tesseract OCR automatically.
"""

import sys
import subprocess
import os
from pathlib import Path
import time

def download_tesseract():
    """Download Tesseract installer using urllib from multiple mirrors."""
    print("[*] Downloading Tesseract OCR v5.3.0 (~95 MB)...")
    print("    This may take 1-2 minutes...")
    
    # Try multiple mirrors
    mirrors = [
        "https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.0/tesseract-ocr-w64-setup-v5.3.0.exe",
        "https://sourceforge.net/projects/tesseract-ocr-alt/files/tesseract-ocr-setup-v5.3.0.exe/download",
    ]
    
    installer_path = Path(os.environ['TEMP']) / "tesseract-setup.exe"
    
    for url in mirrors:
        try:
            print(f"[*] Trying: {url.split('/')[2]}")
            import urllib.request
            urllib.request.urlretrieve(url, installer_path, reporthook=None)
            
            if installer_path.exists():
                size_mb = installer_path.stat().st_size / (1024 * 1024)
                print(f"[OK] Downloaded {size_mb:.1f} MB")
                return installer_path
        except Exception as e:
            print(f"    ❌ Failed: {type(e).__name__}")
            continue
    
    print("[ERROR] All download mirrors failed")
    return None

def install_tesseract(installer_path):
    """Run Tesseract installer silently."""
    print("\n[*] Running Tesseract installer...")
    print("    Installation location: C:\\Program Files\\Tesseract-OCR")
    
    try:
        # Run installer silently
        subprocess.run(
            [str(installer_path), "/S", "/D=C:\\Program Files\\Tesseract-OCR"],
            check=False,
            timeout=300
        )
        
        # Wait for installation to complete
        print("[*] Waiting for installation to complete...")
        for i in range(60):  # Wait up to 60 seconds
            if Path("C:\\Program Files\\Tesseract-OCR\\tesseract.exe").exists():
                print(f"[OK] Installation complete!")
                return True
            time.sleep(1)
            if i % 10 == 0 and i > 0:
                print(f"    Still installing... ({i}s)")
        
        # Final check
        if Path("C:\\Program Files\\Tesseract-OCR\\tesseract.exe").exists():
            return True
        else:
            print("[WARNING] Installation may still be in progress, checking one more time...")
            time.sleep(10)
            return Path("C:\\Program Files\\Tesseract-OCR\\tesseract.exe").exists()
            
    except Exception as e:
        print(f"[ERROR] Installation failed: {e}")
        return False

def verify_tesseract():
    """Verify Tesseract installation."""
    tesseract_path = Path("C:\\Program Files\\Tesseract-OCR\\tesseract.exe")
    
    print("\n[*] Verifying Tesseract installation...")
    
    if not tesseract_path.exists():
        print(f"[ERROR] Tesseract not found at {tesseract_path}")
        print("[INFO] Checking alternative locations...")
        
        alt_paths = [
            Path("C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe"),
            Path(os.environ.get('ProgramFiles', '')) / "Tesseract-OCR\\tesseract.exe",
        ]
        
        for path in alt_paths:
            if path.exists():
                print(f"[OK] Found at: {path}")
                return path
        
        return None
    
    try:
        result = subprocess.run(
            [str(tesseract_path), "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print(f"[OK] Tesseract is working!")
            print(f"[OK] Version: {result.stdout.split()[1]}")
            return tesseract_path
        else:
            print(f"[ERROR] Tesseract not working: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        return None

def main():
    print("="*60)
    print("Tesseract OCR Automated Installer")
    print("="*60)
    
    # Step 1: Download
    installer = download_tesseract()
    if not installer:
        print("\n[ERROR] Failed to download Tesseract")
        print("[INFO] Please download manually from:")
        print("       https://github.com/UB-Mannheim/tesseract/wiki")
        return False
    
    # Step 2: Install
    if not install_tesseract(installer):
        print("\n[ERROR] Installation may have failed")
        print("[INFO] Check if installer is still running...")
        return False
    
    # Step 3: Verify
    tesseract_path = verify_tesseract()
    
    if tesseract_path:
        print("\n" + "="*60)
        print("[SUCCESS] Tesseract OCR installed successfully!")
        print("="*60)
        print(f"\nLocation: {tesseract_path}")
        print("\nYou can now:")
        print("1. Restart your Streamlit app")
        print("2. Re-upload your PDF")
        print("3. Scanned PDFs will be extracted via OCR")
        return True
    else:
        print("\n[ERROR] Tesseract installation verification failed")
        print("[INFO] Try installing manually:")
        print("       https://github.com/UB-Mannheim/tesseract/wiki/Downloads")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
