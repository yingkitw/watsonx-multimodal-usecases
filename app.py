from flask import Flask, render_template, request, jsonify, send_file
import os
import tempfile
import base64
from PIL import Image
import io
import re

# Import the image_to_text function from the existing script
from image_to_text_granite_vision import image_to_text, get_access_token

app = Flask(__name__)

# Global variable to store the access token
access_token = None

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/authenticate', methods=['POST'])
def authenticate():
    """Authenticate with IBM Cloud and get an access token"""
    global access_token
    access_token = get_access_token()
    if access_token:
        return jsonify({'status': 'success', 'message': 'Successfully authenticated with IBM Cloud'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to authenticate. Check your API key in the .env file'})

@app.route('/refresh_token', methods=['POST'])
def refresh_token():
    """Refresh the access token"""
    global access_token
    access_token = get_access_token()
    if access_token:
        return jsonify({'status': 'success', 'message': 'Token refreshed successfully'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to refresh token'})

@app.route('/process_image', methods=['POST'])
def process_image():
    """Process an uploaded image with IBM Granite Vision"""
    global access_token
    
    # Check if authenticated
    if not access_token:
        return jsonify({'status': 'error', 'message': 'Not authenticated. Please authenticate first'})
    
    # Get form data
    task = request.form.get('task', 'OCR')
    custom_prompt = request.form.get('prompt', '')
    
    # Get uploaded file
    if 'image' not in request.files:
        return jsonify({'status': 'error', 'message': 'No image uploaded'})
    
    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({'status': 'error', 'message': 'No image selected'})
    
    # Determine the prompt based on the selected task
    if not custom_prompt:
        if task == 'OCR':
            prompt = "You are an OCR engine, please extract full text from the page"
        elif task == 'HTML Generation':
            prompt = "Generate an HTML file based on the screenshot image provided"
        elif task == 'Flowchart Analysis':
            prompt = "Generate a flow chart based on the diagram in mermaid format"
        elif task == 'Code Generation':
            prompt = "Generate code based on the diagram"
        else:
            prompt = "Describe this image in detail"
    else:
        prompt = custom_prompt
    
    try:
        # Save the uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            image_file.save(tmp_file.name)
            temp_filename = tmp_file.name
        
        # Process the image
        result = image_to_text(temp_filename, prompt, custom_token=access_token)
        
        # Clean up the temporary file
        os.unlink(temp_filename)
        
        if result:
            # Process the result based on the task
            if task == 'HTML Generation':
                # Return HTML as code
                return jsonify({
                    'status': 'success',
                    'result': result,
                    'result_type': 'html'
                })
            
            elif task == 'Flowchart Analysis':
                # Check for mermaid code
                mermaid_code = None
                if "```mermaid" in result:
                    mermaid_start = result.find("```mermaid")
                    mermaid_end = result.find("```", mermaid_start + 10)
                    if mermaid_start != -1 and mermaid_end != -1:
                        mermaid_code = result[mermaid_start + 10:mermaid_end].strip()
                
                return jsonify({
                    'status': 'success',
                    'result': result,
                    'mermaid_code': mermaid_code,
                    'result_type': 'flowchart'
                })
            
            elif task == 'Code Generation':
                # Extract code blocks if present
                code_blocks = []
                if "```" in result:
                    pattern = r"```(\w*)\n(.*?)```"
                    matches = re.findall(pattern, result, re.DOTALL)
                    for language, code in matches:
                        code_blocks.append({
                            'language': language.strip() or 'text',
                            'code': code.strip()
                        })
                
                return jsonify({
                    'status': 'success',
                    'result': result,
                    'code_blocks': code_blocks,
                    'result_type': 'code'
                })
            
            else:  # OCR and other tasks
                return jsonify({
                    'status': 'success',
                    'result': result,
                    'result_type': 'text'
                })
        else:
            return jsonify({'status': 'error', 'message': 'Failed to process the image'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error: {str(e)}'})

@app.route('/download_result', methods=['POST'])
def download_result():
    """Download the result as a text file"""
    result = request.form.get('result', '')
    task = request.form.get('task', 'result')
    
    # Create a BytesIO object
    result_bytes = result.encode('utf-8')
    buffer = io.BytesIO(result_bytes)
    buffer.seek(0)
    
    # Create a filename based on the task
    filename = f"{task.lower().replace(' ', '_')}_result.txt"
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='text/plain'
    )

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Check if the template file exists, if not create it
    if not os.path.exists('templates/index.html'):
        with open('templates/index.html', 'w') as f:
            f.write('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IBM Granite Vision Demo</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/default.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        body {
            padding-top: 20px;
            padding-bottom: 20px;
        }
        .header {
            padding-bottom: 20px;
            border-bottom: 1px solid #e5e5e5;
            margin-bottom: 30px;
        }
        .sidebar {
            position: sticky;
            top: 20px;
        }
        .result-container {
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            margin-bottom: 20px;
            min-height: 200px;
            max-height: 600px;
            overflow-y: auto;
        }
        .image-preview {
            max-width: 100%;
            max-height: 300px;
            margin-bottom: 15px;
        }
        .code-block {
            background-color: #f5f5f5;
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 10px;
            margin-bottom: 10px;
            overflow-x: auto;
        }
        .loading {
            display: none;
            text-align: center;
            margin: 20px 0;
        }
        .loading-spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 2s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>IBM Granite Vision - Multimodal AI Demo</h1>
            <p class="lead">Explore the capabilities of IBM's Granite Vision model</p>
        </div>

        <div class="row">
            <!-- Sidebar -->
            <div class="col-md-3 sidebar">
                <div class="card mb-4">
                    <div class="card-header">
                        <h5>About</h5>
                    </div>
                    <div class="card-body">
                        <p>This application demonstrates the capabilities of IBM's Granite Vision model for various image-to-text tasks:</p>
                        <ul>
                            <li><strong>OCR</strong>: Extract text from documents</li>
                            <li><strong>HTML Generation</strong>: Convert webpage screenshots to HTML</li>
                            <li><strong>Flowchart Analysis</strong>: Generate descriptions from diagrams</li>
                            <li><strong>Code Generation</strong>: Create code from class diagrams</li>
                        </ul>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <h5>Authentication</h5>
                    </div>
                    <div class="card-body">
                        <div id="auth-status" class="alert alert-warning">Not authenticated</div>
                        <button id="auth-button" class="btn btn-primary mb-2">Authenticate with IBM Cloud</button>
                        <button id="refresh-button" class="btn btn-secondary" disabled>Refresh Token</button>
                    </div>
                </div>
            </div>

            <!-- Main Content -->
            <div class="col-md-9">
                <div class="row">
                    <!-- Input Column -->
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5>Input</h5>
                            </div>
                            <div class="card-body">
                                <form id="process-form">
                                    <div class="mb-3">
                                        <label for="task-select" class="form-label">Select a task</label>
                                        <select id="task-select" class="form-select" name="task">
                                            <option value="OCR">OCR: Extract text from documents</option>
                                            <option value="HTML Generation">HTML Generation: Convert webpage screenshots to HTML</option>
                                            <option value="Flowchart Analysis">Flowchart Analysis: Generate descriptions from diagrams</option>
                                            <option value="Code Generation">Code Generation: Create code from class diagrams</option>
                                        </select>
                                    </div>

                                    <div class="mb-3">
                                        <label for="custom-prompt" class="form-label">Custom prompt (optional)</label>
                                        <textarea id="custom-prompt" class="form-control" name="prompt" rows="3" placeholder="Enter a custom prompt for the model. If left empty, a default prompt will be used based on the selected task."></textarea>
                                    </div>

                                    <div class="mb-3">
                                        <label for="image-upload" class="form-label">Upload an image</label>
                                        <input type="file" id="image-upload" class="form-control" name="image" accept="image/png, image/jpeg, image/jpg">
                                    </div>

                                    <div id="image-preview-container" class="mb-3" style="display: none;">
                                        <img id="image-preview" class="image-preview" src="" alt="Preview">
                                    </div>

                                    <button type="submit" id="process-button" class="btn btn-success" disabled>Process Image</button>
                                </form>

                                <div id="loading" class="loading">
                                    <div class="loading-spinner"></div>
                                    <p>Processing image...</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Output Column -->
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5>Output</h5>
                            </div>
                            <div class="card-body">
                                <div id="result-container" class="result-container">
                                    <div id="result-placeholder" class="text-center text-muted">
                                        <p>Process an image to see the results here</p>
                                    </div>
                                    <div id="result-content" style="display: none;"></div>
                                </div>

                                <div id="result-actions" style="display: none;">
                                    <button id="download-button" class="btn btn-primary">Download Result</button>
                                    <button id="render-html-button" class="btn btn-secondary" style="display: none;">Render HTML</button>
                                    <button id="view-code-button" class="btn btn-info" style="display: none;">View Code</button>
                                </div>

                                <div id="html-preview" class="mt-3" style="display: none;"></div>
                                <div id="code-preview" class="mt-3" style="display: none;"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <footer class="mt-5 pt-3 border-top text-center text-muted">
            <p>Powered by IBM Granite Vision and Flask</p>
        </footer>
    </div>

    <script>
        // Initialize Mermaid
        mermaid.initialize({ startOnLoad: true });

        // DOM elements
        const authButton = document.getElementById('auth-button');
        const refreshButton = document.getElementById('refresh-button');
        const authStatus = document.getElementById('auth-status');
        const processForm = document.getElementById('process-form');
        const processButton = document.getElementById('process-button');
        const imageUpload = document.getElementById('image-upload');
        const imagePreviewContainer = document.getElementById('image-preview-container');
        const imagePreview = document.getElementById('image-preview');
        const loading = document.getElementById('loading');
        const resultContainer = document.getElementById('result-container');
        const resultPlaceholder = document.getElementById('result-placeholder');
        const resultContent = document.getElementById('result-content');
        const resultActions = document.getElementById('result-actions');
        const downloadButton = document.getElementById('download-button');
        const renderHtmlButton = document.getElementById('render-html-button');
        const viewCodeButton = document.getElementById('view-code-button');
        const htmlPreview = document.getElementById('html-preview');
        const codePreview = document.getElementById('code-preview');

        // Store the result for downloading
        let currentResult = '';
        let currentTask = '';

        // Authentication
        authButton.addEventListener('click', async () => {
            authButton.disabled = true;
            authStatus.innerHTML = 'Authenticating...';
            authStatus.className = 'alert alert-info';

            try {
                const response = await fetch('/authenticate', {
                    method: 'POST'
                });
                const data = await response.json();

                if (data.status === 'success') {
                    authStatus.innerHTML = data.message;
                    authStatus.className = 'alert alert-success';
                    refreshButton.disabled = false;
                    processButton.disabled = false;
                } else {
                    authStatus.innerHTML = data.message;
                    authStatus.className = 'alert alert-danger';
                    authButton.disabled = false;
                }
            } catch (error) {
                authStatus.innerHTML = 'Error: ' + error.message;
                authStatus.className = 'alert alert-danger';
                authButton.disabled = false;
            }
        });

        // Refresh token
        refreshButton.addEventListener('click', async () => {
            refreshButton.disabled = true;
            authStatus.innerHTML = 'Refreshing token...';
            authStatus.className = 'alert alert-info';

            try {
                const response = await fetch('/refresh_token', {
                    method: 'POST'
                });
                const data = await response.json();

                if (data.status === 'success') {
                    authStatus.innerHTML = data.message;
                    authStatus.className = 'alert alert-success';
                    refreshButton.disabled = false;
                } else {
                    authStatus.innerHTML = data.message;
                    authStatus.className = 'alert alert-danger';
                    refreshButton.disabled = false;
                }
            } catch (error) {
                authStatus.innerHTML = 'Error: ' + error.message;
                authStatus.className = 'alert alert-danger';
                refreshButton.disabled = false;
            }
        });

        // Image preview
        imageUpload.addEventListener('change', (event) => {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    imagePreview.src = e.target.result;
                    imagePreviewContainer.style.display = 'block';
                };
                reader.readAsDataURL(file);
            } else {
                imagePreviewContainer.style.display = 'none';
            }
        });

        // Process form
        processForm.addEventListener('submit', async (event) => {
            event.preventDefault();

            // Check if an image is selected
            if (!imageUpload.files[0]) {
                alert('Please select an image to process');
                return;
            }

            // Show loading indicator
            loading.style.display = 'block';
            processButton.disabled = true;
            resultPlaceholder.style.display = 'none';
            resultContent.style.display = 'none';
            resultActions.style.display = 'none';
            htmlPreview.style.display = 'none';
            codePreview.style.display = 'none';
            renderHtmlButton.style.display = 'none';
            viewCodeButton.style.display = 'none';

            // Get form data
            const formData = new FormData(processForm);
            currentTask = formData.get('task');

            try {
                const response = await fetch('/process_image', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();

                if (data.status === 'success') {
                    // Store the result
                    currentResult = data.result;

                    // Display the result based on the type
                    if (data.result_type === 'html') {
                        // HTML Generation
                        resultContent.innerHTML = '<pre><code class="language-html">' + escapeHtml(data.result) + '</code></pre>';
                        renderHtmlButton.style.display = 'inline-block';
                    } else if (data.result_type === 'flowchart') {
                        // Flowchart Analysis
                        resultContent.innerHTML = marked.parse(data.result);
                        
                        // If mermaid code is present, render it
                        if (data.mermaid_code) {
                            setTimeout(() => {
                                mermaid.init(undefined, document.querySelectorAll('.mermaid'));
                            }, 100);
                        }
                    } else if (data.result_type === 'code') {
                        // Code Generation
                        resultContent.innerHTML = marked.parse(data.result);
                        
                        // If code blocks are present, highlight them
                        if (data.code_blocks && data.code_blocks.length > 0) {
                            viewCodeButton.style.display = 'inline-block';
                            
                            // Prepare code preview
                            codePreview.innerHTML = '';
                            data.code_blocks.forEach(block => {
                                const codeElement = document.createElement('div');
                                codeElement.className = 'code-block';
                                codeElement.innerHTML = '<h6>' + (block.language || 'Code') + '</h6>' +
                                    '<pre><code class="language-' + block.language + '">' + 
                                    escapeHtml(block.code) + '</code></pre>';
                                codePreview.appendChild(codeElement);
                            });
                            
                            // Highlight code blocks
                            document.querySelectorAll('pre code').forEach((block) => {
                                hljs.highlightElement(block);
                            });
                        }
                    } else {
                        // OCR and other tasks
                        resultContent.innerHTML = marked.parse(data.result);
                    }

                    // Show the result and actions
                    resultContent.style.display = 'block';
                    resultActions.style.display = 'block';
                    
                    // Highlight code blocks
                    document.querySelectorAll('pre code').forEach((block) => {
                        hljs.highlightElement(block);
                    });
                } else {
                    resultContent.innerHTML = '<div class="alert alert-danger">' + data.message + '</div>';
                    resultContent.style.display = 'block';
                }
            } catch (error) {
                resultContent.innerHTML = '<div class="alert alert-danger">Error: ' + error.message + '</div>';
                resultContent.style.display = 'block';
            } finally {
                loading.style.display = 'none';
                processButton.disabled = false;
            }
        });

        // Download result
        downloadButton.addEventListener('click', async () => {
            const formData = new FormData();
            formData.append('result', currentResult);
            formData.append('task', currentTask);

            try {
                const response = await fetch('/download_result', {
                    method: 'POST',
                    body: formData
                });
                
                // Create a blob from the response
                const blob = await response.blob();
                
                // Create a link to download the file
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = currentTask.toLowerCase().replace(' ', '_') + '_result.txt';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
            } catch (error) {
                alert('Error downloading the result: ' + error.message);
            }
        });

        // Render HTML
        renderHtmlButton.addEventListener('click', () => {
            htmlPreview.innerHTML = currentResult;
            htmlPreview.style.display = 'block';
        });

        // View code
        viewCodeButton.addEventListener('click', () => {
            codePreview.style.display = codePreview.style.display === 'none' ? 'block' : 'none';
        });

        // Helper function to escape HTML
        function escapeHtml(unsafe) {
            return unsafe
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }
    </script>
</body>
</html>
            ''')
    
    # Run the Flask app
    app.run(debug=True, port=5000) 