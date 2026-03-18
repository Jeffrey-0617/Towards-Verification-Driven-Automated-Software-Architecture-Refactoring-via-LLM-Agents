import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
GLM_API_KEY = os.getenv("GLM_API_KEY")