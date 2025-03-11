from dotenv import load_dotenv
import os, json
import requests
import base64
import warnings
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv()
api_key = os.getenv("API_KEY", None)
project_id = os.getenv("PROJECT_ID", None)
ibm_cloud_iam_url = os.getenv("IAM_IBM_CLOUD_URL", None)

# Validate environment variables
if not api_key:
    raise ValueError("API_KEY is missing in .env file")
if not project_id:
    raise ValueError("PROJECT_ID is missing in .env file")
if not ibm_cloud_iam_url:
    raise ValueError("IAM_IBM_CLOUD_URL is missing in .env file")

creds = {
    "url"    : "https://us-south.ml.cloud.ibm.com",
    "apikey" : api_key
}

params = {
    "decoding_method":"greedy",
    "max_new_tokens":3000,
    "min_new_tokens":1,
    # "temperature":0.1,
    "top_k":50,
    "top_p":1,
    # "stop_sequences":["```"],
}

def get_access_token():
    # Prepare the payload and headers
    payload = {
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": api_key
    }
    headers = {
        'Content-Type': "application/x-www-form-urlencoded"
    }

    # Make a POST request while ignoring SSL certificate verification
    try:
        print(f"Requesting access token from {ibm_cloud_iam_url}...")
        response = requests.post(f"https://{ibm_cloud_iam_url}/identity/token", data=payload, headers=headers, verify=False)
        
        # Check if the request was successful
        response.raise_for_status()

        # Parse the JSON response
        decoded_json = response.json()
        access_token = decoded_json["access_token"]
        print("Successfully obtained access token")
        return access_token
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while getting access token: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response content: {e.response.text}")
        return None

# Get initial access token for script execution
access_token = get_access_token()
if not access_token:
    print("Failed to obtain access token. Please check your API key and IBM Cloud IAM URL.")
    
# Update model_id to match the example
model_id = "ibm/granite-vision-3-2-2b"

def image_to_text(imagefilename, query, custom_token=None):
    """
    Process an image and generate text based on the query.
    
    Args:
        imagefilename (str): Path to the image file
        query (str): The prompt to send to the model
        custom_token (str, optional): Custom access token to use instead of the global one
    
    Returns:
        str: The generated text response
    """
    global access_token
    
    # Use custom token if provided (for Streamlit integration)
    token_to_use = custom_token if custom_token is not None else access_token
    
    # Check if we have a valid access token
    if not token_to_use:
        print("No valid access token available. Cannot proceed with API request.")
        return None
    
    # Check if image file exists
    if not os.path.exists(imagefilename):
        print(f"Error: Image file '{imagefilename}' not found")
        return None
    
    try:
        print(f"Processing image: {imagefilename}")
        pic = open(imagefilename, "rb").read()
        pic_base64 = base64.b64encode(pic)
        pic_string = pic_base64.decode("utf-8")

        url = "https://us-south.ml.cloud.ibm.com/ml/v1/text/chat?version=2023-05-29"

        # Update body format to match the example
        body = {
            "messages": [
                {"role":"user","content":[
                    {"type":"text","text":query},
                    {"type":"image_url",
                     "image_url":{
                         "url": f"data:image/png;base64,{pic_string}"
                         }}]}
                ],
            "project_id": project_id,
            "model_id": model_id,
            "max_tokens": 900,
            "temperature": 0,
            "top_p": 1
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token_to_use}"
        }

        print("Sending request to IBM Cloud API...")
        response = requests.post(
            url,
            headers=headers,
            json=body
        )

        # If token expired, refresh and retry
        if response.status_code == 401:
            print("Access token expired, refreshing...")
            new_token = get_access_token()
            if not new_token:
                print("Failed to refresh access token. Cannot proceed.")
                return None
                
            # Update the global token if we're not using a custom one
            if custom_token is None:
                access_token = new_token
                
            headers["Authorization"] = f"Bearer {new_token}"
            print("Retrying request with new token...")
            response = requests.post(
                url,
                headers=headers,
                json=body
            )

        if response.status_code != 200:
            print(f"Error response (status code {response.status_code}): {response.text}")
            raise Exception("Non-200 response: " + str(response.text))

        response_data = json.loads(response.text)
        print("Successfully received response from API")

        # Extract the content
        quoted_string = response_data['choices'][0]['message']['content']

        # Remove unwanted escape characters (like \n)
        unquoted_string = quoted_string.replace('\\n', '\n').replace('\\', '')

        # Return the unquoted string
        return unquoted_string
    
    except Exception as e:
        print(f"Error in image_to_text: {e}")
        return None

# Check if running in IPython environment
def is_in_ipython():
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            return True
        return False
    except ImportError:
        return False

# Main execution
if __name__ == "__main__":
    if not access_token:
        print("Exiting due to authentication failure.")
        exit(1)
        
    # Example 1: OCR
    print("\nProcessing OCR example...")
    answer = image_to_text("examples/ocr_document.png", "you are a OCR engine, please extract full text from the page")
    if answer:
        print(answer)
    print("\n" + "-"*50 + "\n")

    # Example 2: HTML Generation
    print("Processing webpage example...")
    answer = image_to_text("examples/webpage.png", "generate an html file based on the screenshot image provided")
    if answer:
        print(answer)
    print("\n" + "-"*50 + "\n")

    # Example 3: Flowchart
    print("Processing flowchart example...")
    answer = image_to_text("examples/flowchart.png", 
                          """Generate a flow chart based on the diagram in mermaid format""")
    
    # Handle IPython display if available
    if answer:
        if is_in_ipython():
            try:
                from IPython.display import display, Markdown
                display(Markdown(answer))
            except ImportError:
                print(answer)
        else:
            print(answer)
    print("\n" + "-"*50 + "\n")

    # Example 4: Class Diagram
    print("Processing class diagram example...")
    answer = image_to_text("examples/classdiagram.png", "Generate Java code based on the diagram")
    
    # Handle IPython display if available
    if answer:
        if is_in_ipython():
            try:
                from IPython.display import display, Code
                display(Code(answer, language="java"))
            except ImportError:
                print(answer)
        else:
            print(answer)