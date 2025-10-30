import os
from dotenv import load_dotenv

# โหลดค่าจาก .env (ถ้ามี)
load_dotenv()


class Config:
    """Base configuration class."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:postgres@db:5432/todo_dev'
    )


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False

    # ✅ ดึง DATABASE_URL จาก environment (Railway จะส่งเข้ามาให้)
    db_url = os.getenv('DATABASE_URL')

    # ✅ ถ้าเป็น postgres:// ให้เปลี่ยนเป็น postgresql:// เพื่อให้ SQLAlchemy รองรับ
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = db_url

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        # ถ้าไม่มี DATABASE_URL ให้แจ้งเตือน (ป้องกัน production พัง)
        if not os.getenv('DATABASE_URL'):
            raise RuntimeError('DATABASE_URL must be set in production')


# Mapping config name -> class
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
