import uvicorn
from app.main import app
from dotenv import load_dotenv
import os

load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"Running on port {port}")
    uvicorn.run(app, host="127.0.0.0", port=port)