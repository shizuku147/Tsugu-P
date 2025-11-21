import requests
from bs4 import BeautifulSoup
import re
import time
import random
import json
from urllib.parse import urljoin, urlparse
from config import Config

class RealProductCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.config = Config()
        self.update_headers()
    
    def update_headers(self):
        """更新请求头"""
        self.session.headers.update({
            'User-Agent': random.choice(self.config.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def get_random_delay(self):
        """获取随机延迟"""
        return random.uniform(self.config.DELAY_BETWEEN_REQUESTS, self.config.DELAY_BETWEEN_REQUESTS + 2)
    
    def fetch_product_info(self, url, retry_count=0):
        """获取商品信息"""
        try:
            if retry_count > 0:
                time.sleep(self.get_random_delay() * retry_count)
                self.update_headers()  # 重试时更换User-Agent
            
            print(f"🔍 爬取商品信息: {url}")
            response = self.session.get(url, timeout=self.config.REQUEST_TIMEOUT)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            platform = self.detect_platform(url)
            print(f"📱 检测到平台: {platform}")
            
            if platform == 'taobao':
                return self.fetch_taobao_product(soup, url)
            elif platform == 'tmall':
                return self.fetch_tmall_product(soup, url)
            elif platform == 'jd':
                return self.fetch_jd_product(soup, url)
            elif platform == 'pdd':
                return self.fetch_pdd_product(soup, url)
            else:
                return self.fetch_general_product(soup, url)
                
        except requests.exceptions.Timeout:
            print(f"⏰ 请求超时: {url}")
            if retry_count < self.config.MAX_RETRIES:
                return self.fetch_product_info(url, retry_count + 1)
            return None
        except Exception as e:
            print(f"❌ 爬取失败: {e}")
            if retry_count < self.config.MAX_RETRIES:
                return self.fetch_product_info(url, retry_count + 1)
            return None
    
    def detect_platform(self, url):
        """检测电商平台"""
        if 'taobao.com' in url:
            return 'taobao'
        elif 'tmall.com' in url:
            return 'tmall'
        elif 'jd.com' in url:
            return 'jd'
        elif 'pdd' in url or 'yangkeduo' in url:
            return 'pdd'
        else:
            return 'other'
    
    def fetch_taobao_product(self, soup, url):
        """获取淘宝商品信息"""
        try:
            title = self.extract_taobao_title(soup)
            price = self.extract_taobao_price(soup)
            image_url = self.extract_taobao_image(soup, url)
            
            if not title or price == 0:
                return None
                
            return {
                'name': title,
                'price': price,
                'image_url': image_url,
                'platform': 'taobao',
                'success': True
            }
        except Exception as e:
            print(f"淘宝爬取失败: {e}")
            return None
    
    def extract_taobao_title(self, soup):
        """提取淘宝标题"""
        selectors = [
            '#J_Title .tb-main-title',
            '.tb-detail-hd h1',
            '[class*="Title--title"]',
            'h1[data-spm]',
            'title'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text().strip():
                title = element.get_text().strip()
                title = re.sub(r'-\s*淘宝网', '', title)
                title = re.sub(r'\s+', ' ', title)
                return title[:100] if len(title) > 100 else title
        
        return None
    
    def extract_taobao_price(self, soup):
        """提取淘宝价格"""
        # 方法1: 从meta标签获取
        price_meta = soup.find('meta', {'property': 'og:product:price'})
        if price_meta and price_meta.get('content'):
            try:
                return float(price_meta['content'])
            except:
                pass
        
        # 方法2: 从页面元素获取
        price_selectors = [
            '.tb-rmb-num',
            '[class*="Price--price"]',
            '.tm-price',
            '.tb-property .tb-price'
        ]
        
        for selector in price_selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text().strip()
                price = self.parse_price(price_text)
                if price > 0:
                    return price
        
        # 方法3: 从页面文本搜索
        text = soup.get_text()
        price_patterns = [
            r'¥\s*(\d+\.?\d*)',
            r'￥\s*(\d+\.?\d*)',
            r'价格\s*[:：]\s*(\d+\.?\d*)'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(1))
                except:
                    continue
        
        return 0.0
    
    def extract_taobao_image(self, soup, base_url):
        """提取淘宝图片"""
        img_selectors = [
            '#J_ImgBooth',
            '.tb-booth img',
            '.tb-pic img',
            '[class*="main-img"] img'
        ]
        
        for selector in img_selectors:
            elements = soup.select(selector)
            for element in elements:
                img_src = (element.get('src') or 
                          element.get('data-src') or 
                          element.get('data-ks-lazyload'))
                if img_src:
                    full_url = self.process_image_url(img_src, base_url)
                    if self.validate_image_url(full_url):
                        return full_url
        
        # 从meta标签获取
        meta_image = soup.find('meta', {'property': 'og:image'})
        if meta_image and meta_image.get('content'):
            full_url = self.process_image_url(meta_image['content'], base_url)
            if self.validate_image_url(full_url):
                return full_url
        
        return ''
    
    def fetch_jd_product(self, soup, url):
        """获取京东商品信息"""
        try:
            title_element = (soup.select_one('.sku-name') or 
                           soup.select_one('.product-title') or 
                           soup.find('title'))
            title = title_element.get_text().strip() if title_element else None
            if title:
                title = re.sub(r'-\s*京东', '', title)
                title = title[:100] if len(title) > 100 else title
            
            price = self.extract_jd_price(soup)
            image_url = self.extract_jd_image(soup, url)
            
            if not title or price == 0:
                return None
                
            return {
                'name': title,
                'price': price,
                'image_url': image_url,
                'platform': 'jd',
                'success': True
            }
        except Exception as e:
            print(f"京东爬取失败: {e}")
            return None
    
    def extract_jd_price(self, soup):
        """提取京东价格"""
        # 从页面元素获取
        price_selectors = [
            '.p-price .price',
            '.J-p-123456',  # 动态ID，需要从页面获取
            '.price .num',
            '[class*="price J-p-"]'
        ]
        
        for selector in price_selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text().strip()
                price = self.parse_price(price_text)
                if price > 0:
                    return price
        
        # 从JavaScript数据获取
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string:
                # 搜索价格模式
                patterns = [
                    r'jq\$\s*\.\s*extend\s*\(\s*[\'"]price[\'"]\s*,\s*[\'"](\d+\.?\d*)[\'"]',
                    r'price\s*:\s*[\'"](\d+\.?\d*)[\'"]',
                    r'"price"\s*:\s*"(\d+\.?\d*)"'
                ]
                for pattern in patterns:
                    match = re.search(pattern, script.string)
                    if match:
                        try:
                            return float(match.group(1))
                        except:
                            continue
        
        return 0.0
    
    def extract_jd_image(self, soup, base_url):
        """提取京东图片"""
        img_selectors = [
            '#spec-img',
            '.main-img img',
            '[class*="spec-pic"] img',
            '.preview-img img'
        ]
        
        for selector in img_selectors:
            element = soup.select_one(selector)
            if element:
                img_src = (element.get('data-origin') or 
                          element.get('src') or 
                          element.get('data-lazyload'))
                if img_src:
                    full_url = self.process_image_url(img_src, base_url)
                    if self.validate_image_url(full_url):
                        return full_url
        
        return ''
    
    def fetch_tmall_product(self, soup, url):
        """获取天猫商品信息"""
        try:
            title = self.extract_taobao_title(soup)
            price = self.extract_taobao_price(soup)
            image_url = self.extract_taobao_image(soup, url)
            
            if not title or price == 0:
                return None
                
            return {
                'name': title,
                'price': price,
                'image_url': image_url,
                'platform': 'tmall',
                'success': True
            }
        except Exception as e:
            print(f"天猫爬取失败: {e}")
            return None
    
    def fetch_pdd_product(self, soup, url):
        """获取拼多多商品信息"""
        try:
            title_element = soup.find('title')
            title = title_element.get_text().strip() if title_element else None
            
            price = self.extract_pdd_price(soup)
            image_url = self.extract_pdd_image(soup, url)
            
            if not title or price == 0:
                return None
                
            return {
                'name': title[:100] if title else '拼多多商品',
                'price': price,
                'image_url': image_url,
                'platform': 'pdd',
                'success': True
            }
        except Exception as e:
            print(f"拼多多爬取失败: {e}")
            return None
    
    def extract_pdd_price(self, soup):
        """提取拼多多价格"""
        text = soup.get_text()
        price_patterns = [
            r'¥\s*(\d+\.?\d*)',
            r'￥\s*(\d+\.?\d*)',
            r'拼单价\s*[:：]\s*(\d+\.?\d*)',
            r'price\s*:\s*[\'"](\d+\.?\d*)[\'"]'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(1))
                except:
                    continue
        
        return 0.0
    
    def extract_pdd_image(self, soup, base_url):
        """提取拼多多图片"""
        img_selectors = [
            '.goods-gallery__main img',
            '.slide-main img',
            '[class*="image"] img'
        ]
        
        for selector in img_selectors:
            element = soup.select_one(selector)
            if element:
                img_src = element.get('src') or element.get('data-src')
                if img_src:
                    full_url = self.process_image_url(img_src, base_url)
                    if self.validate_image_url(full_url):
                        return full_url
        
        return ''
    
    def fetch_general_product(self, soup, url):
        """通用商品信息获取"""
        try:
            title_element = soup.find('title')
            title = title_element.get_text().strip() if title_element else '商品'
            
            # 从meta标签获取价格
            price_meta = soup.find('meta', {'property': 'product:price'})
            price = float(price_meta['content']) if price_meta and price_meta.get('content') else 0.0
            
            # 从meta标签获取图片
            image_meta = soup.find('meta', {'property': 'og:image'})
            image_url = self.process_image_url(image_meta['content'], url) if image_meta and image_meta.get('content') else ''
            
            if price == 0:
                # 尝试从页面文本搜索价格
                text = soup.get_text()
                match = re.search(r'¥\s*(\d+\.?\d*)', text)
                if match:
                    price = float(match.group(1))
            
            return {
                'name': title[:100],
                'price': price,
                'image_url': image_url,
                'platform': 'other',
                'success': True
            }
        except Exception as e:
            print(f"通用爬取失败: {e}")
            return None
    
    def process_image_url(self, img_src, base_url):
        """处理图片URL"""
        if not img_src:
            return ''
        
        # 处理相对路径
        if img_src.startswith('//'):
            return 'https:' + img_src
        elif img_src.startswith('/'):
            parsed_base = urlparse(base_url)
            return f"{parsed_base.scheme}://{parsed_base.netloc}{img_src}"
        elif not img_src.startswith('http'):
            return urljoin(base_url, img_src)
        else:
            return img_src
    
    def validate_image_url(self, url):
        """验证图片URL是否有效"""
        if not url:
            return False
        
        # 检查常见的图片格式
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
        if any(ext in url.lower() for ext in valid_extensions):
            return True
        
        # 检查常见的图片域名
        image_domains = ['img', 'image', 'pic', 'photo', 'tbcdn', 'jdimg', 'alicdn']
        if any(domain in url.lower() for domain in image_domains):
            return True
        
        return False
    
    def parse_price(self, price_text):
        """解析价格文本"""
        try:
            # 移除货币符号和空格
            cleaned = re.sub(r'[^\d.]', '', price_text)
            return float(cleaned) if cleaned else 0.0
        except:
            return 0.0