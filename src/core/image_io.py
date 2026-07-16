import cv2
import numpy as np
from PIL import Image, ImageOps

def load_image_with_exif(path):
    """
    Loads an image from path using Pillow, preserves its EXIF orientation,
    and returns a BGR numpy array and the original PIL Image object (with EXIF data).
    """
    pil_img = Image.open(path)
    # Apply EXIF orientation correction
    pil_img_corrected = ImageOps.exif_transpose(pil_img)
    
    # Convert to numpy array
    img_np = np.array(pil_img_corrected)
    
    # Check number of channels and convert to BGR
    if len(img_np.shape) == 2:  # Grayscale
        bgr_np = cv2.cvtColor(img_np, cv2.COLOR_GRAY2BGR)
    elif img_np.shape[2] == 4:  # RGBA
        bgr_np = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
    else:  # RGB
        bgr_np = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        
    return bgr_np, pil_img_corrected

def save_image_with_exif(rgba_np, original_pil_img, output_path, bg_color=(255, 255, 255)):
    """
    Saves an RGBA numpy array to output_path.
    If the file format is JPEG, it composites the image over a solid background color.
    Copies EXIF metadata from the original PIL Image.
    """
    # Determine the target format
    lower_path = output_path.lower()
    is_jpeg = lower_path.endswith('.jpg') or lower_path.endswith('.jpeg')
    
    if is_jpeg:
        # Composite over solid background
        bgr = rgba_np[:, :, :3]
        alpha = rgba_np[:, :, 3] / 255.0
        alpha = np.expand_dims(alpha, axis=2)
        
        # Background color image
        bg = np.full(bgr.shape, bg_color, dtype=np.uint8)
        
        # Blend: fg * alpha + bg * (1 - alpha)
        blended = (bgr * alpha + bg * (1.0 - alpha)).astype(np.uint8)
        rgb_out = cv2.cvtColor(blended, cv2.COLOR_BGR2RGB)
        pil_out = Image.fromarray(rgb_out)
    else:
        # PNG/WebP (Supports transparency)
        rgba_rgb = cv2.cvtColor(rgba_np, cv2.COLOR_BGRA2RGBA)
        pil_out = Image.fromarray(rgba_rgb)
        
    # Extract EXIF info if present
    exif = original_pil_img.info.get('exif')
    
    if exif:
        pil_out.save(output_path, exif=exif)
    else:
        pil_out.save(output_path)
