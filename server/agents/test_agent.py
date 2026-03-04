from dotenv import load_dotenv
import base64
import os

load_dotenv()

from agent_building import vl_llm_node, MessagesState


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

if __name__ == "__main__":
    # Define image paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # server/
    files_dir = os.path.join(base_dir, "files")
    
    # img1 is baseline (基准图), img2 is factual (事实图)
    img1_name = "capture_1772607854707.jpg"
    img2_name = "capture_1772607866667.jpg"
    
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
        
        print("Calling VL LLM node (streaming)...")
        response_generator = vl_llm_node(state)
        print("\nResponse Content:")
        
        for chunk in response_generator:
            if chunk.content:
                print(chunk.content, end="", flush=True)
        print() # Newline at end
        
    except Exception as e:
        print(f"An error occurred: {e}")