# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    
    # 数据库配置
    DATABASE_PATH = 'products.db'
    
    # 爬虫配置
    REQUEST_TIMEOUT = 15
    MAX_RETRIES = 3
    RETRY_DELAY = 2
    
    # 请求头
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
    }
    
    # 调度器配置
    SCHEDULER_INTERVAL_HOURS = 6  # 每6小时检查一次价格
    
    # 网站特定配置
    SITE_CONFIGS = {
        'amazon': {
            'name_selectors': ['#productTitle', 'h1.a-size-large'],
            'price_selectors': ['.a-price-whole', '.a-offscreen', '#priceblock_dealprice', '#priceblock_ourprice'],
            'image_selectors': ['#landingImage', '.a-dynamic-image']
        },
        'jd': {
            'name_selectors': ['.sku-name', '.p-name'],
            'price_selectors': ['.p-price .price', '.J-p-{}'],
            'image_selectors': ['#spec-img', '.main-img img']
        },
        'taobao': {
            'name_selectors': ['.tb-detail-hd h1', '.tb-main-title'],
            'price_selectors': ['.tb-rmb-num', '.tm-price'],
            'image_selectors': ['#J_ImgBooth', '.tb-pic img']
        }
    }