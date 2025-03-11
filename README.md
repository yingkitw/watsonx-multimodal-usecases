# IBM Granite Vision - Multimodal AI Use Cases

This repository demonstrates various multimodal AI capabilities using IBM's Granite Vision model, a powerful vision-language model that can understand and process both images and text.

## Overview

IBM Granite Vision is a state-of-the-art multimodal AI model that can analyze images and respond to text prompts about them. This repository showcases several practical use cases:

1. **OCR (Optical Character Recognition)**: Extract text from documents, images, and scanned materials.
2. **HTML Generation**: Convert webpage screenshots to functional HTML code.
3. **Flowchart Analysis**: Generate descriptions or mermaid diagrams from flowchart images.
4. **Code Generation**: Create code from class diagrams and other visual representations.

## Interactive Demo

The repository includes a web application that provides an interactive interface to explore these capabilities:

- Image upload functionality
- Task selection
- Custom prompt options
- Formatted result display
- Download capabilities

## Getting Started

### Prerequisites

- Python 3.7+
- IBM Cloud account with API key
- Project ID for IBM Granite Vision

### Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory with the following content:
   ```
   API_KEY="your-ibm-cloud-api-key"
   PROJECT_ID="your-project-id"
   IAM_IBM_CLOUD_URL=iam.cloud.ibm.com
   ```

### Running the Application

Run the Flask app with:

```
python app.py
```

The application will be available at `http://localhost:5000` in your web browser.

## Web Application

The Flask application (`app.py`) provides a responsive web interface with Bootstrap styling to interact with the IBM Granite Vision model.

### Authentication

Before using the app, you need to authenticate with IBM Cloud:

1. Click the "Authenticate with IBM Cloud" button in the sidebar
2. The app will use your API key from the `.env` file to obtain an access token
3. Once authenticated, the status will change to show success

If your token expires during use, you can click the "Refresh Token" button to obtain a new one.

### Using the App

The application has a responsive layout:

#### Input Section

1. **Task Selection**: Choose from a dropdown of the four main tasks:
   - OCR: Extract text from documents
   - HTML Generation: Convert webpage screenshots to HTML
   - Flowchart Analysis: Generate descriptions from diagrams
   - Code Generation: Create code from class diagrams

2. **Custom Prompt**: Optionally enter a custom prompt to guide the model's response. If left empty, a default prompt will be used based on the selected task.

3. **Image Upload**: Upload an image in PNG, JPG, or JPEG format with real-time preview.

4. **Process Button**: Click "Process Image" to send the image to the IBM Granite Vision model.

#### Output Section

The results are displayed with appropriate formatting:

1. **OCR Results**: Rendered as markdown with proper formatting

2. **HTML Generation**: Displayed as syntax-highlighted code with a "Render HTML" button to see the actual rendered webpage

3. **Flowchart Analysis**: Displayed with mermaid diagrams rendered inline if present

4. **Code Generation**: Code blocks are syntax-highlighted and can be viewed separately

### Features

- **Real-time Image Preview**: See a preview of your uploaded image before processing
- **Syntax Highlighting**: Using highlight.js for code blocks
- **Markdown Rendering**: Using marked.js for text formatting
- **Mermaid Diagram Support**: Automatic rendering of mermaid diagrams
- **Responsive Design**: Works well on desktop and mobile devices
- **Download Option**: Save results as text files

## Using the Command Line Interface

If you prefer to use the command line instead of the web interface, you can use the `image_to_text_granite_vision.py` script directly:

```
python image_to_text_granite_vision.py
```

This will process the example images in the `examples` directory and display the results in the terminal.

## Example Images

The `examples` directory contains sample images for each task:

- `ocr_document.png`: A document for OCR testing
- `webpage.png`: A screenshot of a webpage for HTML generation
- `flowchart.png`: A flowchart diagram for analysis
- `classdiagram.png`: A class diagram for code generation

## Use Cases in Detail

### OCR (Optical Character Recognition)

Extract text from documents, images, and scanned materials. The model can recognize text in various fonts, layouts, and styles.

![OCR sample](examples/ocr_document.png)

### HTML Generation

Convert webpage screenshots to functional HTML code. The model analyzes the visual layout and generates corresponding HTML structure.

![Webpage sample](examples/webpage.png)

### Flowchart Analysis

Generate descriptions or mermaid diagrams from flowchart images. The model understands the structure and relationships in diagrams.

![Flowchart sample](examples/flowchart.png)

### Code Generation

Create code from class diagrams and other visual representations. The model can interpret UML diagrams and generate corresponding code.

![Class diagram sample](examples/classdiagram.png)

## How It Works

The application uses IBM Granite Vision, a multimodal AI model that can process both images and text. The model is accessed through IBM Cloud's API, which requires authentication with an API key.

The workflow is as follows:

1. The image is encoded as a base64 string
2. A prompt is constructed based on the selected task
3. The image and prompt are sent to the IBM Granite Vision API
4. The API returns a text response, which is then processed and displayed

## Technical Details

- **Model**: IBM Granite Vision 3.2 2B (`ibm/granite-vision-3-2-2b`)
- **API**: IBM Cloud ML API for text/chat
- **Authentication**: IBM Cloud IAM token authentication
- **Frontend**: Flask with Bootstrap for a responsive web application
- **Image Processing**: PIL/Pillow for image handling
- **JavaScript Libraries**:
  - marked.js for markdown rendering
  - highlight.js for syntax highlighting
  - mermaid.js for diagram rendering

## Deployment Considerations

For production deployment, consider the following:

- Use a production WSGI server like Gunicorn or uWSGI instead of Flask's development server
- Set up proper error handling and logging
- Implement rate limiting to prevent API abuse
- Consider containerization with Docker for easier deployment
- Use environment variables for sensitive information

## Troubleshooting

- If authentication fails, check your API key in the `.env` file.
- If image processing fails, try refreshing your token or check your internet connection.
- For large images, processing may take longer than expected.

## License

This project is licensed under the Apache 2.0 License - see the LICENSE file for details.

