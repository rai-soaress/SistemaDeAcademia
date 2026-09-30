import os
import tempfile
from dotenv import load_dotenv
from sqlalchemy.pool import NullPool

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

PRODUCTION = os.getenv("APP_ENV") == "production" or os.getenv("RENDER") == "true" or os.getenv("VERCEL") == "1"
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
for prefix in ("postgres://", "postgresql://"):
    if DATABASE_URL.startswith(prefix):
        DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len(prefix):]
        break

if PRODUCTION and not DATABASE_URL.startswith("postgresql+"):
    raise RuntimeError("Configure DATABASE_URL com a URL PostgreSQL em producao.")
if PRODUCTION and (not os.getenv("SECRET_KEY") or os.getenv("SECRET_KEY") == "dev-secret-change-me"):
    raise RuntimeError("Configure uma SECRET_KEY privada em producao.")

class Config:
    PUBLIC_BASE_URL = os.getenv('PUBLIC_BASE_URL', '')
    RESEND_API_KEY = os.getenv('RESEND_API_KEY', '')
    SMTP_HOST = os.getenv('SMTP_HOST', '')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_SSL = os.getenv('SMTP_SSL', 'false').lower() == 'true'
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    SMTP_FROM = os.getenv('SMTP_FROM', '')
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-change-me"
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or "sqlite:///" + os.path.join(BASE_DIR, "instance", "academia.db")
    SQLALCHEMY_ENGINE_OPTIONS = {"poolclass": NullPool} if os.getenv("VERCEL") == "1" else {"pool_pre_ping": True}
    INSTANCE_PATH = os.path.abspath(os.getenv("INSTANCE_PATH") or (
        os.path.join(tempfile.gettempdir(), "sistema_academia") if os.getenv("VERCEL") == "1"
        else os.path.join(BASE_DIR, "instance")
    ))
    AUTO_INIT_DB = not PRODUCTION and not DATABASE_URL
    SESSION_COOKIE_SECURE = PRODUCTION
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024
