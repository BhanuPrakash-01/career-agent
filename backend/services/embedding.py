from dotenv import load_dotenv
import os
from google import genai
from typing import List

load_dotenv()
# Initialize Client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def get_embedding(text: str) -> List[float]:
    """
    Turns text into a vector (list of numbers).
    """
    
    try:
        # We use the specialized embedding model
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
            config={"output_dimensionality": 768}
        )
        return result.embeddings[0].values
    except Exception as e:
        print(f"Embedding Error: {e}")
        return []