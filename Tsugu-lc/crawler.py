import requests
from bs4 import BeautifulSoup
import re

def get_product_info(url):
    """获取商品信息"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 淘宝/天猫
        if 'taobao.com' in url or 'tmall.com' in url:
            return parse_taobao(soup, url)
        # 京东
        elif 'jd.com' in url:
            return parse_jd(soup, url)
        else:
            return parse_general(soup, url)
            
    except Exception as e:
        print(f"爬取失败: {e}")
        return None

def parse_taobao(soup, url):
    """解析淘宝商品"""
    # 商品名称
    title_elem = soup.find('h1') or soup.find('title')
    title = title_elem.get_text().strip() if title_elem else '淘宝商品'
    
    # 价格（简化处理）
    price = extract_price(soup)
    
    # 图片
    img_elem = soup.find('img', {'alt': title}) or soup.find('img', class_=re.compile('img'))
    img_url = img_elem.get('src') if img_elem else ''
    
    return {
        'name': clean_title(title),
        'price': price,
        'image_url': img_url,
        'platform': 'taobao'
    }

def parse_jd(soup, url):
    """解析京东商品"""
    title_elem = soup.find('div', class_=re.compile('sku-name')) or soup.find('title')
    title = title_elem.get_text().strip() if title_elem else '京东商品'
    
    price = extract_price(soup)
    
    img_elem = soup.find('img', {'alt': title}) or soup.find('img', id=re.compile('spec-img'))
    img_url = img_elem.get('src') or img_elem.get('data-origin') if img_elem else ''
    
    return {
        'name': clean_title(title),
        'price': price,
        'image_url': img_url,
        'platform': 'jd'
    }

def parse_general(soup, url):
    """通用解析"""
    title_elem = soup.find('title')
    title = title_elem.get_text().strip() if title_elem else '未知商品'
    
    return {
        'name': clean_title(title),
        'price': 0,
        'image_url': '',
        'platform': 'other'
    }

def extract_price(soup):
    """提取价格"""
    # 查找价格相关的元素
    price_patterns = [
        r'¥\s*(\d+\.?\d*)',
        r'￥\s*(\d+\.?\d*)',
        r'价格\s*[:：]\s*(\d+\.?\d*)',
        r'price\s*[:：]\s*(\d+\.?\d*)'
    ]
    
    text = soup.get_text()
    for pattern in price_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except:
                continue
    
    return 0

def clean_title(title):
    """清理标题"""
    # 移除多余空格和换行
    title = re.sub(r'\s+', ' ', title)
    # 限制长度
    return title[:50] if len(title) > 50 else title