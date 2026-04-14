import os
from google import genai
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

def test_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    # Create a small blank image for testing
    img = Image.new('RGB', (100, 100), color = (73, 109, 137))
    img.save('test_img.png')
    
    print("Testing Gemini Vision...")
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=["What is in this image?", Image.open('test_img.png')]
        )
        print("Success!")
        print("Response:", response.text)
    except Exception as e:
        print("Failed!")
        print("Error Type:", type(e).__name__)
        print("Error Details:", str(e))

if __name__ == "__main__":
    test_gemini()
