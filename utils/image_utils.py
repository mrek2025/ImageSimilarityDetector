import io
import requests
import logging
import torch
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image

logger = logging.getLogger(__name__)

# Define image transformations for DINO model
transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def download_image_from_url(url):
    """
    Download an image from a URL.
    
    Args:
        url (str): URL of the image.
        
    Returns:
        PIL.Image: Downloaded image.
        
    Raises:
        Exception: If the image cannot be downloaded or processed.
    """
    try:
        logger.info(f"Downloading image from URL: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        image = Image.open(io.BytesIO(response.content)).convert('RGB')
        return image
        
    except Exception as e:
        logger.error(f"Error downloading image from URL {url}: {str(e)}")
        raise Exception(f"Could not download image from URL: {str(e)}")

def preprocess_image(image):
    """
    Preprocess an image for the DINO model.
    
    Args:
        image (PIL.Image): Image to preprocess.
        
    Returns:
        torch.Tensor: Preprocessed image tensor.
    """
    try:
        # Convert image to RGB if it's not
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        # Apply transformations
        image_tensor = transform(image).unsqueeze(0)  # Add batch dimension
        
        return image_tensor
        
    except Exception as e:
        logger.error(f"Error preprocessing image: {str(e)}")
        raise Exception(f"Error preprocessing image: {str(e)}")

def compute_similarity(features1, features2):
    """
    Compute cosine similarity between two feature vectors.
    
    Args:
        features1 (torch.Tensor): Feature vector of the first image.
        features2 (torch.Tensor): Feature vector of the second image.
        
    Returns:
        float: Cosine similarity score.
    """
    try:
        # Compute cosine similarity
        cos_sim = F.cosine_similarity(features1, features2).item()
        
        # Similarity is between -1 and 1, so we normalize to 0-1 range
        # For logo similarity, this is a reasonable range.
        normalized_sim = (cos_sim + 1) / 2
        
        return normalized_sim
        
    except Exception as e:
        logger.error(f"Error computing similarity: {str(e)}")
        raise Exception(f"Error computing similarity: {str(e)}")
