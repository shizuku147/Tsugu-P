import os

class Config:
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # 数据库配置
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///products.db'
    
    # 爬虫配置
    REQUEST_TIMEOUT = 15
    MAX_RETRIES = 3
    DELAY_BETWEEN_REQUESTS = 2
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36'
    ]
    
    # 图片配置
    IMAGE_DIR = 'static/product_images'
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
    
    # 价格更新配置
    UPDATE_INTERVAL = 1800  # 30分钟
    BATCH_SIZE = 5  # 每次更新的商品数量
    
    # 通知配置
    ENABLE_EMAIL_NOTIFICATIONS = False
    SMTP_SERVER = os.environ.get('SMTP_SERVER', '')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    EMAIL_USER = os.environ.get('EMAIL_USER', '')
    EMAIL_PASS = os.environ.get('EMAIL_PASS', '')