"""
Utility functions for image processing, mask generation, and data handling.
"""

import cv2
import numpy as np
import base64
from io import BytesIO
from pathlib import Path
from PIL import Image
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


def image_to_base64(image_array: np.ndarray, format: str = "png") -> str:
    """
    Convert numpy image to base64 string for JSON serialization.
    
    Args:
        image_array: numpy array [H, W, C] in [0, 255] uint8
        format: output format ('png' or 'jpeg')
        
    Returns:
        base64 encoded string with data URI prefix
    """
    # Convert numpy array to PIL Image
    if len(image_array.shape) == 2:
        pil_image = Image.fromarray(image_array, mode='L')
    else:
        # Ensure RGB (no alpha channel)
        if image_array.shape[2] == 4:
            image_array = cv2.cvtColor(image_array, cv2.COLOR_RGBA2RGB)
        pil_image = Image.fromarray(image_array, mode='RGB')
    
    # Save to bytes
    buffer = BytesIO()
    pil_image.save(buffer, format=format.upper())
    buffer.seek(0)
    
    # Encode to base64
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/{format};base64,{img_base64}"


def base64_to_image(base64_string: str) -> np.ndarray:
    """
    Convert base64 string to numpy image array.
    
    Args:
        base64_string: base64 encoded string (with or without data URI prefix)
        
    Returns:
        numpy array [H, W, C] in [0, 255] uint8 (RGB)
    """
    # Remove data URI prefix if present
    if "," in base64_string:
        base64_string = base64_string.split(",", 1)[1]
    
    # Decode from base64
    img_bytes = base64.b64decode(base64_string)
    
    # Load with PIL
    pil_image = Image.open(BytesIO(img_bytes))
    
    # Convert to RGB if needed
    if pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')
    
    # Convert to numpy array
    image_array = np.array(pil_image, dtype=np.uint8)
    
    return image_array


def generate_random_mask(image_shape: Tuple[int, int], 
                        mask_type: str = 'irregular',
                        mask_ratio: float = 0.3) -> np.ndarray:
    """
    Generate a random mask for image inpainting.
    
    Args:
        image_shape: (height, width) of the image
        mask_type: 'irregular', 'center', 'random_brush', or 'rectangular'
        mask_ratio: percentage of image to mask (0.0 to 1.0)
        
    Returns:
        numpy array [H, W] with values 0 (background) and 255 (damaged region)
    """
    height, width = image_shape
    mask = np.zeros((height, width), dtype=np.uint8)
    
    if mask_type == 'center':
        # Center square mask
        mask_size = int(np.sqrt(height * width * mask_ratio))
        y_start = (height - mask_size) // 2
        x_start = (width - mask_size) // 2
        mask[y_start:y_start + mask_size, x_start:x_start + mask_size] = 255
    
    elif mask_type == 'rectangular':
        # Random rectangles
        num_rects = max(1, int(mask_ratio * 3))
        for _ in range(num_rects):
            h = np.random.randint(20, int(height * 0.4))
            w = np.random.randint(20, int(width * 0.4))
            y = np.random.randint(0, height - h)
            x = np.random.randint(0, width - w)
            mask[y:y + h, x:x + w] = 255
    
    elif mask_type == 'random_brush':
        # Random brush strokes
        num_strokes = max(1, int(mask_ratio * 5))
        for _ in range(num_strokes):
            # Random line
            pt1 = (np.random.randint(0, width), np.random.randint(0, height))
            pt2 = (np.random.randint(0, width), np.random.randint(0, height))
            thickness = np.random.randint(5, 20)
            cv2.line(mask, pt1, pt2, 255, thickness)
    
    else:  # irregular
        # Irregular mask using morphological operations
        mask = np.random.randint(0, 2, (height // 4, width // 4), dtype=np.uint8) * 255
        mask = cv2.resize(mask, (width, height), interpolation=cv2.INTER_NEAREST)
        
        # Apply morphological operations to create more organic shapes
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Adjust mask ratio
        current_ratio = np.sum(mask > 127) / (height * width)
        if current_ratio > mask_ratio:
            mask = (mask * (mask_ratio / current_ratio)).astype(np.uint8)
    
    return mask


def load_mask_from_file(mask_path: str) -> np.ndarray:
    """
    Load mask from file (PNG or JPG).
    
    Args:
        mask_path: path to mask file
        
    Returns:
        numpy array [H, W] in [0, 255]
    """
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    if mask is None:
        raise FileNotFoundError(f"Mask file not found: {mask_path}")
    return mask


def apply_mask_to_image(image: np.ndarray, mask: np.ndarray, 
                       mask_color: Tuple[int, int, int] = (128, 128, 128)) -> np.ndarray:
    """
    Apply mask visualization to image (darken masked regions).
    
    Args:
        image: numpy array [H, W, C] in [0, 255] uint8
        mask: numpy array [H, W] in [0, 255]
        mask_color: RGB color for masked regions
        
    Returns:
        masked image with darkened/colored regions
    """
    # Resize mask if needed
    if mask.shape != image.shape[:2]:
        mask = cv2.resize(mask, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)
    
    # Create masked image
    masked_image = image.copy().astype(np.float32)
    mask_bool = mask > 127
    
    # Darken masked regions
    masked_image[mask_bool] = (masked_image[mask_bool] * 0.5).astype(np.uint8)
    
    return masked_image.astype(np.uint8)


def resize_image(image: np.ndarray, max_size: int = 512) -> np.ndarray:
    """
    Resize image to fit within max_size while preserving aspect ratio.
    
    Args:
        image: numpy array [H, W, C]
        max_size: maximum dimension size
        
    Returns:
        resized image
    """
    height, width = image.shape[:2]
    
    if height > max_size or width > max_size:
        scale = min(max_size / height, max_size / width)
        new_height = int(height * scale)
        new_width = int(width * scale)
        image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
    
    return image


def pad_to_square(image: np.ndarray, target_size: int = 512) -> Tuple[np.ndarray, dict]:
    """
    Pad image to square with target_size, keeping original aspect ratio.
    Useful for models that expect square inputs.
    
    Args:
        image: numpy array [H, W, C]
        target_size: output size (target_size x target_size)
        
    Returns:
        (padded_image, padding_info)
        padding_info: dict with padding coordinates for restoration
    """
    height, width = image.shape[:2]
    
    # Calculate padding
    if height > width:
        pad_left = (height - width) // 2
        pad_right = height - width - pad_left
        pad_top = pad_bottom = 0
    else:
        pad_top = (width - height) // 2
        pad_bottom = width - height - pad_top
        pad_left = pad_right = 0
    
    # Apply padding
    if len(image.shape) == 3:
        padded = cv2.copyMakeBorder(image, pad_top, pad_bottom, pad_left, pad_right,
                                   cv2.BORDER_CONSTANT, value=[0, 0, 0])
    else:
        padded = cv2.copyMakeBorder(image, pad_top, pad_bottom, pad_left, pad_right,
                                   cv2.BORDER_CONSTANT, value=0)
    
    # Resize to target
    padded = cv2.resize(padded, (target_size, target_size), interpolation=cv2.INTER_LINEAR)
    
    padding_info = {
        'original_shape': (height, width),
        'pad_top': pad_top,
        'pad_bottom': pad_bottom,
        'pad_left': pad_left,
        'pad_right': pad_right,
        'target_size': target_size,
    }
    
    return padded, padding_info


def crop_from_padding(image: np.ndarray, padding_info: dict) -> np.ndarray:
    """
    Reverse the pad_to_square operation.
    
    Args:
        image: numpy array (typically from model output)
        padding_info: dict returned by pad_to_square
        
    Returns:
        original-sized image
    """
    # Resize back to padded size
    padded_size = padding_info['target_size']
    if image.shape[0] != padded_size or image.shape[1] != padded_size:
        h, w = padding_info['original_shape']
        max_dim = max(h, w)
        image = cv2.resize(image, (max_dim, max_dim), interpolation=cv2.INTER_LINEAR)
    
    # Crop padding
    pad_top = padding_info['pad_top']
    pad_bottom = padding_info['pad_bottom']
    pad_left = padding_info['pad_left']
    pad_right = padding_info['pad_right']
    
    h_start = pad_top
    h_end = image.shape[0] - pad_bottom if pad_bottom > 0 else image.shape[0]
    w_start = pad_left
    w_end = image.shape[1] - pad_right if pad_right > 0 else image.shape[1]
    
    cropped = image[h_start:h_end, w_start:w_end]
    
    # Resize to original dimensions
    original_h, original_w = padding_info['original_shape']
    cropped = cv2.resize(cropped, (original_w, original_h), interpolation=cv2.INTER_LINEAR)
    
    return cropped


def validate_image(image_bytes: bytes, max_size_mb: float = 10.0) -> Tuple[bool, str]:
    """
    Validate uploaded image file.
    
    Args:
        image_bytes: raw image bytes
        max_size_mb: maximum file size in MB
        
    Returns:
        (is_valid, error_message)
    """
    # Check size
    size_mb = len(image_bytes) / (1024 * 1024)
    if size_mb > max_size_mb:
        return False, f"File too large: {size_mb:.2f}MB (max {max_size_mb}MB)"
    
    # Check if valid image
    try:
        pil_image = Image.open(BytesIO(image_bytes))
        if pil_image.format not in ['JPEG', 'PNG', 'BMP']:
            return False, f"Unsupported format: {pil_image.format}"
        pil_image.verify()
    except Exception as e:
        return False, f"Invalid image file: {str(e)}"
    
    return True, ""


def get_evidence_masks(evidence_dir: str = None) -> list:
    """
    Get list of available mask files from evidence directory.
    
    Args:
        evidence_dir: path to evidence directory (defaults to ../evidence/)
        
    Returns:
        list of mask file paths
    """
    if evidence_dir is None:
        evidence_dir = Path(__file__).parent.parent / "evidence"
    
    evidence_path = Path(evidence_dir)
    
    if not evidence_path.exists():
        logger.warning(f"Evidence directory not found: {evidence_dir}")
        return []
    
    # Look for mask files
    mask_extensions = ['*.png', '*.jpg', '*.jpeg']
    masks = []
    
    for ext in mask_extensions:
        masks.extend(evidence_path.glob(f"**/{ext}"))
    
    return [str(m.relative_to(evidence_path)) for m in masks]
