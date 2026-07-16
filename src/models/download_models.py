import os
import sys
import urllib.request

MODELS = {
    "birefnet-general": {
        "url": "https://github.com/danielgatis/rembg/releases/download/v0.0.0/BiRefNet-general-epoch_244.onnx",
        "filename": "birefnet-general.onnx"
    },
    "birefnet-general-lite": {
        "url": "https://github.com/danielgatis/rembg/releases/download/v0.0.0/BiRefNet-general-bb_swin_v1_tiny-epoch_232.onnx",
        "filename": "birefnet-general-lite.onnx"
    },
    "isnet-general-use": {
        "url": "https://github.com/danielgatis/rembg/releases/download/v0.0.0/isnet-general-use.onnx",
        "filename": "isnet-general-use.onnx"
    },
    "u2net": {
        "url": "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx",
        "filename": "u2net.onnx"
    },
    "u2netp": {
        "url": "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx",
        "filename": "u2netp.onnx"
    },
    "vitmatte-small": {
        "url": "https://huggingface.co/Xenova/vitmatte-small-composition-1k/resolve/main/onnx/model.onnx",
        "filename": "vitmatte-small.onnx"
    }
}

def download_progress(block_num, block_size, total_size):
    """
    Console progress reporter helper.
    """
    if total_size <= 0:
        return
    downloaded = block_num * block_size
    percent = min(100.0, (downloaded / total_size) * 100.0)
    mb_downloaded = downloaded / (1024 * 1024)
    mb_total = total_size / (1024 * 1024)
    sys.stdout.write(f"\rDownloading... {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)")
    sys.stdout.flush()

def download_all(dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    
    for model_name, model_info in MODELS.items():
        dest_path = os.path.join(dest_dir, model_info["filename"])
        if os.path.exists(dest_path):
            print(f"[+] Model '{model_name}' already exists at: {dest_path}")
            continue
            
        print(f"[*] Downloading '{model_name}' from: {model_info['url']}")
        try:
            urllib.request.urlretrieve(
                model_info["url"], 
                dest_path, 
                reporthook=download_progress
            )
            print(f"\n[+] Successfully saved to: {dest_path}\n")
        except Exception as e:
            print(f"\n[-] Error downloading '{model_name}': {e}")
            if os.path.exists(dest_path):
                os.remove(dest_path)
            raise e

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    download_all(current_dir)
