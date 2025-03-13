import os
import logging
import io
from flask import Flask, render_template, request, jsonify, url_for
import requests
from PIL import Image
import torch
from utils.dino_model import DinoModel
from utils.image_utils import preprocess_image, compute_similarity, download_image_from_url

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

# Initialize DINO model
model = DinoModel()

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/compare', methods=['POST'])
def compare_images():
    """Compare two images using DINO model."""
    try:
        # Get images from request
        image1 = None
        image2 = None
        
        # First image could be from file upload or URL
        if 'image1_file' in request.files and request.files['image1_file']:
            image1 = Image.open(request.files['image1_file'])
        elif request.form.get('image1_url'):
            image_url = request.form.get('image1_url')
            image1 = download_image_from_url(image_url)
        
        # Second image could be from file upload or URL
        if 'image2_file' in request.files and request.files['image2_file']:
            image2 = Image.open(request.files['image2_file'])
        elif request.form.get('image2_url'):
            image_url = request.form.get('image2_url')
            image2 = download_image_from_url(image_url)
        
        # Validate that both images are provided
        if image1 is None or image2 is None:
            return jsonify({
                'success': False,
                'error': 'Please provide two images (upload or URL) for comparison.'
            }), 400
        
        # Preprocess images and get features
        image1_tensor = preprocess_image(image1)
        image2_tensor = preprocess_image(image2)
        
        # Get features from DINO model
        with torch.no_grad():
            image1_features = model.extract_features(image1_tensor)
            image2_features = model.extract_features(image2_tensor)
        
        # Compute similarity scores
        cosine_similarity = compute_similarity(image1_features, image2_features)
        
        # Convert similarity to percentage
        similarity_percentage = float(cosine_similarity) * 100
        
        return jsonify({
            'success': True,
            'similarity': similarity_percentage,
            'cosine_similarity': float(cosine_similarity)
        })
    
    except Exception as e:
        logger.error(f"Error processing images: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error processing images: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
