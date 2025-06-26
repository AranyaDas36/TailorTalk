import google.generativeai as genai
import os
import dotenv

# Load environment variables from .env file for local use
dotenv.load_dotenv()

# Get the API key from environment variables
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: GEMINI_API_KEY environment variable not found.")
    print("Please create a .env file with GEMINI_API_KEY='your-key' or set the environment variable.")
else:
    try:
        genai.configure(api_key=api_key)

        print("--- Available Generative Models ---")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
        print("---------------------------------")
        print("\nPlease use one of the model names from the list above in your code.")

    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please ensure your API key is correct and has access to the Gemini API.") 