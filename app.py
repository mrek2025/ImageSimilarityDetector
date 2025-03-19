import os
import logging
import io
import base64
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

@app.route('/api/docs')
def api_docs():
    """Render the API documentation page."""
    return render_template('api_docs.html')

@app.route('/api/v1/compare', methods=['POST'])
def api_compare_images():
    """API endpoint for comparing two images."""
    try:
        # Check Content-Type
        if request.is_json:
            data = request.get_json()
            
            # Validate request body
            if not data or ('image1_url' not in data and 'image1_base64' not in data) or \
               ('image2_url' not in data and 'image2_base64' not in data):
                return jsonify({
                    'success': False,
                    'error': 'Invalid request. Provide image URLs or Base64 encoded images.'
                }), 400
            
            # Process images
            image1 = None
            image2 = None
            
            # First image from URL or Base64
            if 'image1_url' in data and data['image1_url']:
                try:
                    image1 = download_image_from_url(data['image1_url'])
                except Exception as e:
                    return jsonify({
                        'success': False,
                        'error': f'Failed to download image 1: {str(e)}'
                    }), 400
            elif 'image1_base64' in data and data['image1_base64']:
                try:
                    image_data = base64.b64decode(data['image1_base64'])
                    image1 = Image.open(io.BytesIO(image_data))
                except Exception as e:
                    return jsonify({
                        'success': False,
                        'error': f'Invalid Base64 data for image 1: {str(e)}'
                    }), 400
            
            # Second image from URL or Base64
            if 'image2_url' in data and data['image2_url']:
                try:
                    image2 = download_image_from_url(data['image2_url'])
                except Exception as e:
                    return jsonify({
                        'success': False,
                        'error': f'Failed to download image 2: {str(e)}'
                    }), 400
            elif 'image2_base64' in data and data['image2_base64']:
                try:
                    image_data = base64.b64decode(data['image2_base64'])
                    image2 = Image.open(io.BytesIO(image_data))
                except Exception as e:
                    return jsonify({
                        'success': False,
                        'error': f'Invalid Base64 data for image 2: {str(e)}'
                    }), 400
            
            # Validate that both images are provided
            if image1 is None or image2 is None:
                return jsonify({
                    'success': False,
                    'error': 'Unable to process one or both images.'
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
            
            # Prepare interpretation
            interpretation = ""
            if similarity_percentage > 80:
                interpretation = "High similarity. The images may be the same trademark or very closely related logos."
            elif similarity_percentage > 50:
                interpretation = "Moderate similarity. The images share some common visual elements."
            else:
                interpretation = "Low similarity. The images appear to be different trademarks."
            
            return jsonify({
                'success': True,
                'similarity': similarity_percentage,
                'cosine_similarity': float(cosine_similarity),
                'interpretation': interpretation
            })
            
        else:
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json'
            }), 415
    
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error processing request: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
