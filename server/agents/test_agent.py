from dotenv import load_dotenv
import base64
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Load env vars first
# Try to load from server/.env
server_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(server_env_path):
    print(f"Loading environment from {server_env_path}")
    load_dotenv(server_env_path)
else:
    print("Warning: .env file not found in server directory. API keys may be missing.")
    # Try loading from current directory or parents as fallback
    load_dotenv()

# Check if API key is set
api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    print("Error: DASHSCOPE_API_KEY not found in environment variables.")
    print("Please set it in server/.env file.")
    sys.exit(1)

# Check for placeholder values or non-ASCII characters
if "您的" in api_key or not api_key.isascii():
    print(f"Error: Invalid API Key detected: '{api_key}'")
    print("It seems you are using the placeholder text from .env.example.")
    print("Please update server/.env with your actual DashScope API Key.")
    sys.exit(1)

try:
    from server.agents.agent_building import vl_llm_node, MessagesState
except Exception as e:
    print(f"Error importing agent_building: {e}")
    sys.exit(1)

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

if __name__ == "__main__":
    # Define image paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # server/
    files_dir = os.path.join(base_dir, "files")
    
    # img1 is baseline (基准图), img2 is factual (事实图)
    img1_name = "capture_1772501103802.jpg"
    img2_name = "capture_1772501111574.jpg"
    
    img1_path = os.path.join(files_dir, img1_name)
    img2_path = os.path.join(files_dir, img2_name)
    
    print(f"Reading images from: {files_dir}")
    print(f"Baseline image: {img1_name}")
    print(f"Current image: {img2_name}")
    
    try:
        # Encode images
        if not os.path.exists(img1_path):
            raise FileNotFoundError(f"Image not found: {img1_path}")
        if not os.path.exists(img2_path):
            raise FileNotFoundError(f"Image not found: {img2_path}")

        img1_b64 = encode_image(img1_path)
        img2_b64 = encode_image(img2_path)
        
        # Create state
        state = MessagesState(
            basic_image=img1_b64,
            comparison_image=img2_b64,
        )
        
        print("Calling VL LLM node...")
        response = vl_llm_node(state)
        print("\nResponse Content:")
        print(response.content)
        
    except Exception as e:
        print(f"An error occurred: {e}")