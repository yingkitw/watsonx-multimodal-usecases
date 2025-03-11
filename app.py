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
    app.run(debug=True) 