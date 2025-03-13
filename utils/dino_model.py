import torch
import torch.nn as nn
import torchvision.models as models
import logging

logger = logging.getLogger(__name__)

class DinoModel:
    """
    Class to handle ViT model for feature extraction, similar to Facebook AI's DINO.
    """
    def __init__(self, model_name="vit_b_16"):
        """
        Initialize the Vision Transformer model.
        
        Args:
            model_name (str): Name of the model to use.
        """
        logger.info(f"Initializing Vision Transformer model: {model_name}")
        
        try:
            # Load pre-trained Vision Transformer model from torchvision
            if model_name == "vit_b_16":
                self.model = models.vit_b_16(weights=models.ViT_B_16_Weights.IMAGENET1K_V1)
            elif model_name == "vit_l_16":
                self.model = models.vit_l_16(weights=models.ViT_L_16_Weights.IMAGENET1K_V1)
            elif model_name == "vit_b_32":
                self.model = models.vit_b_32(weights=models.ViT_B_32_Weights.IMAGENET1K_V1)
            else:
                # Default to vit_b_16 if an invalid model name is provided
                logger.warning(f"Unknown model {model_name}, defaulting to vit_b_16")
                self.model = models.vit_b_16(weights=models.ViT_B_16_Weights.IMAGENET1K_V1)
            
            # Remove the classification head to get feature vectors
            self.model.heads = nn.Identity()
            
            # Set model to evaluation mode
            self.model.eval()
            
            # Move model to GPU if available
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model = self.model.to(self.device)
            
            logger.info(f"Vision Transformer model loaded successfully. Using device: {self.device}")
            
        except Exception as e:
            logger.error(f"Error initializing Vision Transformer model: {str(e)}")
            raise
    
    def extract_features(self, image_tensor):
        """
        Extract features from an image using the DINO model.
        
        Args:
            image_tensor (torch.Tensor): Preprocessed image tensor.
            
        Returns:
            torch.Tensor: Feature vector from the DINO model.
        """
        try:
            # Move image to the same device as the model
            image_tensor = image_tensor.to(self.device)
            
            # Extract features
            features = self.model(image_tensor)
            
            # Normalize features
            features = nn.functional.normalize(features, dim=1)
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features: {str(e)}")
            raise
