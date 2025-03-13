$(document).ready(function() {
    // Initialize variables for chart
    let similarityGauge = null;
    let centerTextPlugin = {
        id: 'centerText',
        beforeDraw: function(chart) {
            if (chart.config.type === 'doughnut') {
                const width = chart.width;
                const height = chart.height;
                const ctx = chart.ctx;
                
                ctx.restore();
                const fontSize = (height / 114).toFixed(2);
                ctx.font = fontSize + "em sans-serif";
                ctx.textBaseline = "middle";
                
                // Use the current value from chart data
                const value = chart.data.datasets[0].data[0];
                const text = value.toFixed(1) + "%";
                const textX = Math.round((width - ctx.measureText(text).width) / 2);
                const textY = height - (height / 4);
                
                ctx.fillStyle = "#fff";
                ctx.fillText(text, textX, textY);
                ctx.save();
            }
        }
    };
    // Register plugin once at initialization
    Chart.register(centerTextPlugin);
    
    // File input preview handling
    $('#image1-file').change(function() {
        previewImage(this, '#image1-preview');
        // Clear URL input when file is selected
        $('#image1-url').val('');
    });
    
    $('#image2-file').change(function() {
        previewImage(this, '#image2-preview');
        // Clear URL input when file is selected
        $('#image2-url').val('');
    });
    
    // URL input preview handling
    $('#image1-url').on('blur', function() {
        const url = $(this).val();
        if (url) {
            // Clear file input when URL is provided
            $('#image1-file').val('');
            loadImagePreviewFromUrl(url, '#image1-preview');
        }
    });
    
    $('#image2-url').on('blur', function() {
        const url = $(this).val();
        if (url) {
            // Clear file input when URL is provided
            $('#image2-file').val('');
            loadImagePreviewFromUrl(url, '#image2-preview');
        }
    });
    
    // Form submission
    $('#image-comparison-form').submit(function(e) {
        e.preventDefault();
        
        // Reset previous results and errors
        hideResults();
        hideError();
        showLoading();
        
        // Check if at least one image source is provided for each image
        const image1File = $('#image1-file').prop('files')[0];
        const image1Url = $('#image1-url').val();
        const image2File = $('#image2-file').prop('files')[0];
        const image2Url = $('#image2-url').val();
        
        if ((!image1File && !image1Url) || (!image2File && !image2Url)) {
            showError('Please provide two images (upload or URL) for comparison.');
            hideLoading();
            return;
        }
        
        // Create form data for API request
        const formData = new FormData(this);
        
        // Send request to server
        $.ajax({
            url: '/compare',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                hideLoading();
                if (response.success) {
                    displayResults(response);
                } else {
                    showError(response.error || 'An unknown error occurred.');
                }
            },
            error: function(xhr) {
                hideLoading();
                let errorMsg = 'An error occurred while processing the request.';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                }
                showError(errorMsg);
            }
        });
    });
    
    // Function to preview image from file input
    function previewImage(input, previewSelector) {
        const preview = $(previewSelector);
        preview.empty();
        
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                const img = $('<img>').attr('src', e.target.result);
                preview.append(img);
            }
            
            reader.readAsDataURL(input.files[0]);
        } else {
            // Show placeholder if no file is selected
            preview.html(`
                <div class="no-image-placeholder">
                    <i class="fas fa-image fa-3x"></i>
                    <p>Image preview will appear here</p>
                </div>
            `);
        }
    }
    
    // Function to preview image from URL
    function loadImagePreviewFromUrl(url, previewSelector) {
        const preview = $(previewSelector);
        preview.empty();
        
        if (url) {
            // Show loading indicator
            preview.html(`
                <div class="no-image-placeholder">
                    <div class="spinner-border text-secondary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p>Loading image...</p>
                </div>
            `);
            
            // Create temporary image to check if URL is valid
            const img = new Image();
            img.onload = function() {
                preview.empty();
                const displayImg = $('<img>').attr('src', url);
                preview.append(displayImg);
            };
            
            img.onerror = function() {
                preview.html(`
                    <div class="no-image-placeholder">
                        <i class="fas fa-exclamation-triangle fa-3x"></i>
                        <p>Invalid image URL</p>
                    </div>
                `);
            };
            
            img.src = url;
        } else {
            // Show placeholder if no URL is provided
            preview.html(`
                <div class="no-image-placeholder">
                    <i class="fas fa-image fa-3x"></i>
                    <p>Image preview will appear here</p>
                </div>
            `);
        }
    }
    
    // Function to display results
    function displayResults(data) {
        // Display similarity score
        $('#similarity-percentage').text(`${data.similarity.toFixed(2)}%`);
        $('#cosine-similarity').text(`${data.cosine_similarity.toFixed(4)}`);
        
        // Set interpretation text based on similarity value
        let interpretationText = '';
        let interpretationClass = '';
        
        if (data.similarity > 80) {
            interpretationText = 'The images are highly similar. They may be the same brand or very closely related logos.';
            interpretationClass = 'bg-success bg-opacity-25';
        } else if (data.similarity > 50) {
            interpretationText = 'The images have moderate similarity. They share some common visual elements.';
            interpretationClass = 'bg-warning bg-opacity-25';
        } else {
            interpretationText = 'The images have low similarity. They appear to be different brands.';
            interpretationClass = 'bg-danger bg-opacity-25';
        }
        
        $('#similarity-interpretation').text(interpretationText).attr('class', interpretationClass + ' p-3 rounded');
        
        // Draw gauge chart
        drawGaugeChart(data.similarity);
        
        // Show results section
        $('#results-section').removeClass('d-none');
    }
    
    // Function to draw gauge chart
    function drawGaugeChart(similarityValue) {
        const ctx = document.getElementById('similarity-gauge').getContext('2d');
        
        // Destroy previous chart if it exists
        if (similarityGauge) {
            similarityGauge.destroy();
        }
        
        // Configuration for gauge chart
        similarityGauge = new Chart(ctx, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [similarityValue, 100 - similarityValue],
                    backgroundColor: [
                        getColorForSimilarity(similarityValue),
                        'rgba(220, 220, 220, 0.2)'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                circumference: 180,
                rotation: 270,
                cutout: '70%',
                plugins: {
                    tooltip: {
                        enabled: false
                    },
                    legend: {
                        display: false
                    },
                    datalabels: {
                        display: false
                    }
                },
                elements: {
                    arc: {
                        borderWidth: 0
                    }
                },
                responsive: true,
                maintainAspectRatio: true
            }
        });
        
        // Plugin already registered at initialization
        // We just need to make sure similarityGauge is updated with the correct value
    }
    
    // Function to get color based on similarity value
    function getColorForSimilarity(value) {
        if (value > 80) {
            return 'rgba(40, 167, 69, 0.8)'; // Green for high similarity
        } else if (value > 50) {
            return 'rgba(255, 193, 7, 0.8)'; // Yellow for medium similarity
        } else {
            return 'rgba(220, 53, 69, 0.8)'; // Red for low similarity
        }
    }
    
    // Helper functions for UI state management
    function showLoading() {
        $('#loading-indicator').removeClass('d-none');
        $('#compare-btn').prop('disabled', true);
    }
    
    function hideLoading() {
        $('#loading-indicator').addClass('d-none');
        $('#compare-btn').prop('disabled', false);
    }
    
    function hideResults() {
        $('#results-section').addClass('d-none');
    }
    
    function showError(message) {
        $('#error-message').text(message);
        $('#error-section').removeClass('d-none');
    }
    
    function hideError() {
        $('#error-section').addClass('d-none');
    }
});
