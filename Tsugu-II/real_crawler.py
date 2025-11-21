# real_crawler.py
import requests
import time
import logging
import sqlite3
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from config import Config

class RealPriceCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(Config.DEFAULT_HEADERS)
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        logger = logging.getLogger('PriceCrawler')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def detect_website(self, url: str) -> str:
        """检测网站类型"""
        domain = urlparse(url).netloc.lower()
        
        if 'amazon' in domain:
            return 'amazon'
        elif 'jd.com' in domain:
            return 'jd'
        elif 'taobao.com' in domain:
            return 'taobao'
        else:
            return 'generic'
    
    def fetch_product_info(self, url: str) -> dict:
        """获取商品信息"""
        website_type = self.detect_website(url)
        
        for attempt in range(Config.MAX_RETRIES):
            try:
                self.logger.info(f"获取商品信息: {url} (尝试 {attempt + 1})")
                
                response = self.session.get(url, timeout=Config.REQUEST_TIMEOUT)
                
                if response.status_code == 200:
                    product_info = self.parse_product_info(response.text, url, website_type)
                    if product_info.get('name') or product_info.get('price'):
                        return product_info
                
                elif response.status_code == 429:
                    wait_time = (attempt + 1) * 10
                    self.logger.warning(f"请求过于频繁，等待 {wait_time}秒")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"HTTP错误: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"请求异常: {e}")
            
            time.sleep(Config.RETRY_DELAY ** attempt)
        
        return {'error': '获取商品信息失败', 'url': url}
    
    def parse_product_info(self, html: str, url: str, website_type: str) -> dict:
        """解析商品信息"""
        soup = BeautifulSoup(html, 'html.parser')
        
        product_info = {
            'url': url,
            'website': website_type,
            'timestamp': time.time(),
            'name': None,
            'price': None,
            'image_url': None
        }
        
        # 获取网站特定配置
        site_config = Config.SITE_CONFIGS.get(website_type, {})
        
        # 解析商品名称
        product_info['name'] = self._find_element(soup, site_config.get('name_selectors', []))
        
        # 解析价格
        price_text = self._find_element(soup, site_config.get('price_selectors', []))
        product_info['price'] = self._clean_price(price_text) if price_text else None
        
        # 解析图片
        product_info['image_url'] = self._find_image(soup, site_config.get('image_selectors', []))
        
        return product_info
    
    def _find_element(self, soup, selectors: list) -> str:
        """使用选择器查找元素"""
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element and element.get_text().strip():
                    return element.get_text().strip()
            except Exception as e:
                continue
        return None
    
    def _find_image(self, soup, selectors: list) -> str:
        """查找商品图片"""
        for selector in selectors:
            try:
                img_element = soup.select_one(selector)
                if img_element and img_element.get('src'):
                    src = img_element.get('src')
                    if src.startswith('//'):
                        return 'https:' + src
                    elif src.startswith('http'):
                        return src
                    else:
                        return 'https:' + src if src.startswith('/') else src
            except Exception:
                continue
        return None
    
    def _clean_price(self, price_text: str) -> float:
        """清理价格文本"""
        import re
        if not price_text:
            return None
        
        # 移除货币符号和空格，只保留数字和小数点
        cleaned = re.sub(r'[^\d.,]', '', price_text)
        
        # 处理千位分隔符
        if ',' in cleaned and '.' in cleaned:
            # 如果同时有逗号和点，通常逗号是千位分隔符
            cleaned = cleaned.replace(',', '')
        
        try:
            return float(cleaned)
        except ValueError:
            # 尝试另一种清理方式
            matches = re.findall(r'\d+\.?\d*', price_text)
            if matches:
                try:
                    return float(matches[0])
                except ValueError:
                    pass
        return None
    
    def download_image(self, image_url: str, product_id: int) -> str:
        """下载商品图片"""
        if not image_url:
            return None
        
        try:
            response = self.session.get(image_url, timeout=10)
            if response.status_code == 200:
                # 确保static/product_images目录存在
                import os
                image_dir = 'static/product_images'
                os.makedirs(image_dir, exist_ok=True)
                
                # 保存图片
                filename = f"product_{product_id}.jpg"
                filepath = os.path.join(image_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                return f"product_images/{filename}"
        except Exception as e:
            self.logger.error(f"下载图片失败: {e}")
        
        return None