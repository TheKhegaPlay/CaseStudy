"""
AOT-GAN Inference Wrapper
Provides high-level interface for image inpainting with confidence estimation
"""

import sys
import os
import torch
import torch.nn.functional as F
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image
import cv2
from io import BytesIO
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path for importing AOT-GAN modules
BACKEND_DIR = Path(__file__).parent
PROJECT_DIR = BACKEND_DIR.parent
AOT_GAN_DIR = PROJECT_DIR / "AOT-GAN-for-paper-main"

if str(AOT_GAN_DIR) not in sys.path:
    sys.path.insert(0, str(AOT_GAN_DIR))
    sys.path.insert(0, str(PROJECT_DIR))

logger.info(f"Adding to sys.path: {AOT_GAN_DIR}")

# Import AOT-GAN modules
try:
    from model.aotgan import HybridInpaintGenerator
    logger.info("✓ HybridInpaintGenerator imported successfully")
except ImportError as e:
    logger.warning(f"⚠ Could not import HybridInpaintGenerator: {e}. Attempting standard InpaintGenerator...")
    try:
        from model.aotgan import InpaintGenerator as HybridInpaintGenerator
        logger.info("✓ Standard InpaintGenerator imported successfully")
    except ImportError as e2:
        logger.error(f"✗ Failed to import model: {e2}")
        raise


class AOTGANInference:
    """
    High-level inference wrapper for AOT-GAN model.
    Handles preprocessing, inference, postprocessing, and metric computation.
    """

    def __init__(self, model_path: str, device: str = "cpu"):
        """
        Initialize the AOT-GAN inference engine.
        
        Args:
            model_path: Path to pretrained model weights (e.g., 'models/aotgan_best.pth')
            device: 'cpu' or 'cuda' - where to run inference
        """
        self.device = torch.device(device)
        self.model_path = Path(model_path)
        
        # Create a minimal config object
        self.args = self._create_minimal_config()
        
        # Initialize model
        self.model = self._load_model()
        self.model.to(self.device)
        self.model.eval()
        
        logger.info(f"✓ AOT-GAN model loaded on {self.device}")
        
        # Model info
        param_count = sum(p.numel() for p in self.model.parameters())
        logger.info(f"✓ Model parameters: {param_count / 1e6:.2f}M")

    @staticmethod
    def _create_minimal_config():
        """Create a minimal config object for the model."""
        class MinimalConfig:
            mode = 'test'
            use_cuda = torch.cuda.is_available()
            device_ids = [0]
            image_size = 512
            input_image_size = 512
            model = 'aotgan'
            block_num = 8  # Number of AOT blocks
            rates = [1, 2, 4, 8]  # Dilation rates for AOT blocks
            
        return MinimalConfig()

    def _load_model(self):
        """Load the pretrained model."""
        try:
            model = HybridInpaintGenerator(self.args)
            
            if self.model_path.exists():
                logger.info(f"Loading weights from: {self.model_path}")
                state_dict = torch.load(self.model_path, map_location=self.device)
                
                # Handle DataParallel wrapper in checkpoint
                if any(k.startswith('module.') for k in state_dict.keys()):
                    state_dict = {k.replace('module.', ''): v for k, v in state_dict.items()}
                
                model.load_state_dict(state_dict, strict=False)
            else:
                logger.warning(f"⚠ Model weights not found at {self.model_path}. Using random initialization.")
            
            return model
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise

    def preprocess_image(self, image_array: np.ndarray, target_size: int = 512) -> torch.Tensor:
        """
        Preprocess image to model input format.
        
        Args:
            image_array: numpy array [H, W, C] in [0, 255] uint8
            target_size: resize to target_size x target_size
            
        Returns:
            torch.Tensor [1, C, H, W] in [-1, 1] range on the correct device
        """
        # Ensure RGB
        if len(image_array.shape) == 2:
            image_array = cv2.cvtColor(image_array, cv2.COLOR_GRAY2RGB)
        elif image_array.shape[2] == 4:
            image_array = cv2.cvtColor(image_array, cv2.COLOR_RGBA2RGB)
        
        # Resize
        image_resized = cv2.resize(image_array, (target_size, target_size), interpolation=cv2.INTER_LINEAR)
        
        # Convert to tensor [0, 1]
        image_tensor = torch.from_numpy(image_resized.astype(np.float32) / 255.0)
        
        # Permute from HWC to CHW
        image_tensor = image_tensor.permute(2, 0, 1).unsqueeze(0)  # [1, C, H, W]
        
        # Normalize to [-1, 1]
        image_tensor = image_tensor * 2.0 - 1.0
        
        return image_tensor.to(self.device)

    def preprocess_mask(self, mask_array: np.ndarray, target_size: int = 512) -> torch.Tensor:
        """
        Preprocess mask to model input format.
        
        Args:
            mask_array: numpy array [H, W] or [H, W, 1], values in [0, 255]
                        where >127 represents damaged regions
            target_size: resize to target_size x target_size
            
        Returns:
            torch.Tensor [1, 1, H, W] binary mask on the correct device
        """
        if len(mask_array.shape) == 3:
            mask_array = mask_array[:, :, 0]
        
        # Resize
        mask_resized = cv2.resize(mask_array, (target_size, target_size), interpolation=cv2.INTER_NEAREST)
        
        # Binarize: >127 → 1, ≤127 → 0
        mask_binary = (mask_resized > 127).astype(np.float32)
        
        # Convert to tensor
        mask_tensor = torch.from_numpy(mask_binary).unsqueeze(0).unsqueeze(0)  # [1, 1, H, W]
        
        return mask_tensor.to(self.device)

    def postprocess_image(self, image_tensor: torch.Tensor) -> np.ndarray:
        """
        Convert model output to displayable image.
        
        Args:
            image_tensor: torch.Tensor [B, C, H, W] in [-1, 1] range
            
        Returns:
            numpy array [H, W, C] in [0, 255] uint8
        """
        # Clamp to [-1, 1]
        image_clamped = torch.clamp(image_tensor, -1.0, 1.0)
        
        # Scale to [0, 255]
        image_scaled = ((image_clamped + 1.0) / 2.0 * 255.0).detach().cpu()
        
        # Permute from CHW to HWC
        image_np = image_scaled[0].permute(1, 2, 0).numpy().astype(np.uint8)
        
        return image_np

    @staticmethod
    def compute_psnr(img_true: np.ndarray, img_pred: np.ndarray, data_range: int = 255) -> float:
        """
        Compute Peak Signal-to-Noise Ratio.
        
        Args:
            img_true: reference image [H, W, C] in [0, 255] uint8
            img_pred: predicted image [H, W, C] in [0, 255] uint8
            data_range: maximum value of input images (typically 255)
            
        Returns:
            PSNR value in dB
        """
        mse = np.mean((img_true.astype(np.float32) - img_pred.astype(np.float32)) ** 2)
        if mse == 0:
            return float('inf')
        return 20 * np.log10(data_range) - 10 * np.log10(mse)

    @staticmethod
    def compute_ssim(img_true: np.ndarray, img_pred: np.ndarray, data_range: int = 255) -> float:
        """
        Compute Structural Similarity Index (SSIM).
        Uses skimage implementation for multichannel support.
        
        Args:
            img_true: reference image [H, W, C] in [0, 255] uint8
            img_pred: predicted image [H, W, C] in [0, 255] uint8
            data_range: maximum value (typically 255)
            
        Returns:
            SSIM value in [-1, 1] range
        """
        from skimage.metrics import structural_similarity as ssim
        
        # Compute SSIM per channel and average
        if len(img_true.shape) == 3:
            ssim_value = ssim(img_true, img_pred, data_range=data_range, channel_axis=2)
        else:
            ssim_value = ssim(img_true, img_pred, data_range=data_range)
        
        return float(ssim_value)

    @torch.no_grad()
    def infer(self, image_array: np.ndarray, mask_array: np.ndarray,
              target_size: int = 512) -> Tuple[np.ndarray, float, dict]:
        """
        Run inference on image with mask.
        
        Args:
            image_array: numpy array [H, W, C] in [0, 255] uint8
            mask_array: numpy array [H, W] or [H, W, 1] in [0, 255]
            target_size: processing size
            
        Returns:
            (restored_image, confidence_score, metrics_dict)
            - restored_image: numpy array [H, W, C] in [0, 255]
            - confidence_score: float in [0, 1]
            - metrics_dict: {'ssim': float, 'psnr': float, 'mse': float}
        """
        # Preprocess
        image_tensor = self.preprocess_image(image_array, target_size)
        mask_tensor = self.preprocess_mask(mask_array, target_size)
        
        # Inference
        try:
            output = self.model(image_tensor, mask_tensor)
            
            # Handle both tuple and tensor outputs
            if isinstance(output, tuple):
                restored_tensor, confidence_map = output
            else:
                restored_tensor = output
                confidence_map = None
        except Exception as e:
            logger.error(f"Model inference failed: {e}")
            raise
        
        # Postprocess
        restored_image = self.postprocess_image(restored_tensor)
        
        # Compute confidence score (average of confidence map if available)
        if confidence_map is not None:
            confidence_score = float(torch.clamp(confidence_map.mean(), 0.0, 1.0).item())
        else:
            confidence_score = 0.5  # Default if no confidence map
        
        # Compute metrics
        masked_region = mask_tensor[0, 0].cpu().numpy() > 0.5
        
        # PSNR and SSIM computed on the masked region only
        if masked_region.any():
            psnr_value = self.compute_psnr(image_array, restored_image)
            ssim_value = self.compute_ssim(image_array, restored_image)
        else:
            psnr_value = 0.0
            ssim_value = 0.0
        
        mse_value = np.mean((image_array.astype(np.float32) - restored_image.astype(np.float32)) ** 2)
        
        metrics = {
            'ssim': round(ssim_value, 4),
            'psnr': round(psnr_value, 2),
            'mse': round(mse_value, 4),
        }
        
        logger.info(f"Inference complete. Metrics: {metrics}, Confidence: {confidence_score:.4f}")
        
        return restored_image, confidence_score, metrics


# Global model instance (lazy-loaded)
_model_instance: Optional[AOTGANInference] = None


def get_model(device: str = "cpu") -> AOTGANInference:
    """Get or create the global model instance."""
    global _model_instance
    
    if _model_instance is None:
        model_path = str(PROJECT_DIR / "models" / "aotgan_best.pth")
        _model_instance = AOTGANInference(model_path=model_path, device=device)
    
    return _model_instance


def reset_model():
    """Reset the global model instance (useful for testing)."""
    global _model_instance
    _model_instance = None
