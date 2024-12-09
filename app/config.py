import os
from dotenv import load_dotenv

load_dotenv()

COGNITO_REGION = os.getenv("COGNITO_REGION")
USER_POOL_ID = os.getenv("USER_POOL_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
COGNITO_DOMAIN = os.getenv("COGNITO_DOMAIN")
DATABASE_URL = os.getenv("DATABASE_URL")
REDIRECT_URI = os.getenv("REDIRECT_URI")
DATABASE_PORT = os.getenv("DATABASE_PORT")
FRONTEND_URL = os.getenv("FRONTEND_URL")

