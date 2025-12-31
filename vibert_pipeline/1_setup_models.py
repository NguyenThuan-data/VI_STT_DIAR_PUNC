import os
import shutil
import subprocess
import sys
import zipfile
import urllib.request
from huggingface_hub import snapshot_download

def install_dependencies():
    """Install required packages"""
    print("Installing dependencies...")
    packages = [
        "transformers", "torch", "sentencepiece", "huggingface_hub",
        "gradio", "requests", "ffmpeg-python", "groq"
    ]
    
    for package in packages:
        # On Linux/Docker, we trust requirements.txt, but this is a safe fallback
        try:
            subprocess.run([
                "pip", "install", "-q", package
            ], check=True)
        except subprocess.CalledProcessError:
            print(f"⚠ Warning: Could not install {package}, assuming it is already installed.")
    
    print("✓ Dependencies check complete.")

def install_ffmpeg():
    """Install FFmpeg automatically (Windows Only)"""
    print("\nChecking FFmpeg...")
    
    # 1. Check if already installed globally or locally
    if os.path.exists("ffmpeg.exe") or shutil.which("ffmpeg"):
        print("✓ FFmpeg is already installed.")
        return

    print("FFmpeg not found. Installing automatically...")

    try:
        if os.name == 'nt': # WINDOWS
            print("   -> Downloading FFmpeg for Windows (approx. 30MB)...")
            url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
            zip_path = "ffmpeg_temp.zip"
            
            # Download
            urllib.request.urlretrieve(url, zip_path)
            
            # Extract only ffmpeg.exe
            print("   -> Extracting ffmpeg.exe...")
            with zipfile.ZipFile(zip_path, 'r') as z:
                # Find the path inside the zip (it changes with versions)
                ffmpeg_bin = next(name for name in z.namelist() if name.endswith("bin/ffmpeg.exe"))
                
                # Extract specifically that file to current folder
                with z.open(ffmpeg_bin) as source, open("ffmpeg.exe", "wb") as target:
                    shutil.copyfileobj(source, target)
            
            # Cleanup
            os.remove(zip_path)
            print("✓ FFmpeg installed locally (ffmpeg.exe).")

        else: # LINUX / MAC
            # We SKIP this in Docker because Dockerfile handles it safely
            print("⚠ Linux detected: Skipping manual FFmpeg install (Relying on System/Docker).")

    except Exception as e:
        print(f"⚠ Automatic FFmpeg installation failed: {e}")
        print("Please download it manually from https://ffmpeg.org/download.html")

def download_vibert_model():
    """Download Vibert-capu model files"""
    print("\nDownloading dragonSwing/vibert-capu scripts...")
    
    download_path = snapshot_download(
        repo_id="dragonSwing/vibert-capu",
        ignore_patterns=["*.bin", "*.safetensors", "*.pth"],
        local_dir="./vibert_cache"
    )
    
    print(f"✓ Model downloaded to: {download_path}")
    return download_path

def copy_critical_files(download_path):
    """Move critical files to working directory"""
    print("\nCopying critical files...")
    
    files_to_copy = [
        "gec_model.py", "utils.py", "modeling_seq2labels.py", 
        "configuration_seq2labels.py", "vocabulary.py", "verb-form-vocab.txt"
    ]
    
    for filename in files_to_copy:
        src = os.path.join(download_path, filename)
        dst = os.path.join(os.getcwd(), filename)
        
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"  ✓ Copied {filename}")
        else:
            print(f"  ⚠ Warning: {filename} not found")

def patch_model_files():
    """Apply code patches to fix bugs"""
    print("\nApplying code patches...")
    
    # Patch 1: modeling_seq2labels.py
    p1 = "modeling_seq2labels.py"
    if os.path.exists(p1):
        with open(p1, "r", encoding="utf-8") as f:
            code = f.read()
        
        if "@dataclass" not in code:
            code = "from dataclasses import dataclass\n" + code.replace(
                "class Seq2LabelsOutput(ModelOutput):", 
                "@dataclass\nclass Seq2LabelsOutput(ModelOutput):"
            )
        
        if "mean_resizing=False" not in code:
            code = code.replace(
                "self.bert.resize_token_embeddings(vocab_size + 1)",
                "self.bert.resize_token_embeddings(vocab_size + 1, mean_resizing=False)"
            )
        
        with open(p1, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"  ✓ Patched {p1}")
    
    # Patch 2: gec_model.py
    p2 = "gec_model.py"
    if os.path.exists(p2):
        with open(p2, "r", encoding="utf-8") as f:
            code = f.read()
        
        # Fix regex string escape warning
        if "f'\{x}'" in code:
            code = code.replace("f'\{x}'", "f'\\\\{x}'")
            
        with open(p2, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"  ✓ Patched {p2}")

def load_vibert_model():
    """Test loading the Vibert model"""
    print("\nTesting Model Load...")
    
    try:
        from gec_model import GecBERTModel
    except ImportError:
        # If imports fail, try adding current dir to path
        sys.path.append(os.getcwd())
        try:
            from gec_model import GecBERTModel
        except ImportError:
            raise ImportError("Failed to load gec_model.py. Setup incomplete.")
    
    download_path = "./vibert_cache"
    vocab_path = os.path.join(download_path, "vocabulary")
    
    if not os.path.exists(vocab_path):
        vocab_path = os.path.join(os.getcwd(), "vocabulary")
    
    model = GecBERTModel(
        vocab_path=vocab_path,
        model_paths="dragonSwing/vibert-capu",
        split_chunk=True,
        device='cpu' # Just testing load, CPU is fine
    )
    
    print("✓ Vibert-capu loaded successfully!")
    return model

def main():
    """Main setup routine"""
    print("="*60)
    print("MEDICAL ASR - AUTO SETUP")
    print("="*60)
    
    try:
        install_dependencies()
        
        # --- FIXED: Only run FFmpeg install if NOT on Linux ---
        if sys.platform != "linux":
            install_ffmpeg()
        else:
            print("Skipping manual FFmpeg install (Handled by Docker)")
        # ------------------------------------------------------

        download_path = download_vibert_model()
        copy_critical_files(download_path)
        patch_model_files()
        
        # Test load
        load_vibert_model()
        
        print("\n" + "="*60)
        print("✓ SETUP COMPLETE!")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()