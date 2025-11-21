# config.py
import os

class Config:
    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'demo-secret-key')
    DEMO_MODE = True
    
    # 数据库配置
    DATABASE_PATH = 'products.db'