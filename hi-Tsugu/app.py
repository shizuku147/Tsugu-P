from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
import time
import threading
import requests
from datetime import datetime, timedelta
from real_crawler import RealProductCrawler
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# 启用 CORS
CORS(app)

# 初始化组件
crawler = RealProductCrawler()
config = Config()

# 创建必要的目录
os.makedirs(config.IMAGE_DIR, exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('static', exist_ok=True)

def init_db():
    """初始化数据库"""
    try:
        conn = sqlite3.connect('products.db')
        c = conn.cursor()
        
        # 商品表
        c.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                image_url TEXT,
                local_image_path TEXT,
                platform TEXT,
                current_price REAL DEFAULT 0,
                lowest_price REAL DEFAULT 0,
                highest_price REAL DEFAULT 0,
                price_change REAL DEFAULT 0,
                is_available BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 价格历史表
        c.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                price REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        # 价格提醒表
        c.execute('''
            CREATE TABLE IF NOT EXISTS price_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                target_price REAL NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ 数据库初始化成功")
        return True
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False

def download_product_image(image_url, product_id):
    """下载商品图片到本地"""
    try:
        if not image_url:
            return None
            
        # 生成图片文件名
        file_extension = get_image_extension(image_url)
        filename = f"product_{product_id}{file_extension}"
        filepath = os.path.join(config.IMAGE_DIR, filename)
        
        # 下载图片
        response = requests.get(image_url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if response.status_code == 200:
            # 检查图片大小
            if len(response.content) > config.MAX_IMAGE_SIZE:
                print(f"⚠️ 图片过大，跳过下载: {filename}")
                return None
                
            with open(filepath, 'wb') as f:
                f.write(response.content)
            print(f"✅ 图片下载成功: {filename}")
            return f"product_images/{filename}"
        else:
            print(f"❌ 图片下载失败，状态码: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 图片下载失败: {e}")
        return None

def get_image_extension(url):
    """从URL获取图片扩展名"""
    common_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
    for ext in common_extensions:
        if ext in url.lower():
            return ext
    return '.jpg'

def update_product_prices():
    """定时更新商品价格"""
    while True:
        try:
            print(f"\n🔄 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始定时价格更新...")
            conn = sqlite3.connect('products.db')
            c = conn.cursor()
            
            # 获取需要更新的商品（按最后检查时间排序）
            c.execute('''
                SELECT id, url, current_price, lowest_price, highest_price 
                FROM products 
                WHERE is_available = 1
                ORDER BY last_checked ASC
                LIMIT ?
            ''', (config.BATCH_SIZE,))
            
            products = c.fetchall()
            print(f"📊 本次更新 {len(products)} 个商品")
            
            updated_count = 0
            for product_id, url, current_price, lowest_price, highest_price in products:
                try:
                    print(f"  🔍 更新商品 {product_id}: {url}")
                    product_info = crawler.fetch_product_info(url)
                    
                    if product_info and product_info.get('success'):
                        new_price = product_info['price']
                        
                        # 计算价格变化
                        price_change = 0
                        if current_price > 0:
                            price_change = round(((new_price - current_price) / current_price) * 100, 2)
                        
                        # 更新价格历史
                        c.execute('''
                            INSERT INTO price_history (product_id, price)
                            VALUES (?, ?)
                        ''', (product_id, new_price))
                        
                        # 更新商品信息
                        update_data = {
                            'current_price': new_price,
                            'price_change': price_change,
                            'last_checked': datetime.now().isoformat()
                        }
                        
                        # 更新最低价和最高价
                        if new_price > 0:
                            if lowest_price == 0 or new_price < lowest_price:
                                update_data['lowest_price'] = new_price
                            if new_price > highest_price:
                                update_data['highest_price'] = new_price
                        
                        set_clause = ', '.join([f"{k} = ?" for k in update_data.keys()])
                        values = list(update_data.values()) + [product_id]
                        
                        c.execute(f'''
                            UPDATE products 
                            SET {set_clause}
                            WHERE id = ?
                        ''', values)
                        
                        # 检查价格提醒
                        check_price_alerts(product_id, new_price)
                        
                        updated_count += 1
                        print(f"  ✅ 商品 {product_id} 价格更新: {current_price} → {new_price} ({price_change}%)")
                    
                    else:
                        print(f"  ❌ 商品 {product_id} 更新失败")
                        # 标记为不可用
                        c.execute('UPDATE products SET is_available = 0 WHERE id = ?', (product_id,))
                    
                    # 避免请求过快
                    time.sleep(crawler.get_random_delay())
                    
                except Exception as e:
                    print(f"  ❌ 更新商品 {product_id} 失败: {e}")
                    continue
            
            conn.commit()
            conn.close()
            print(f"✅ 价格更新完成，成功更新 {updated_count} 个商品")
            
        except Exception as e:
            print(f"❌ 定时更新失败: {e}")
        
        # 等待下一次更新
        print(f"⏰ 下次更新在 {config.UPDATE_INTERVAL//60} 分钟后...")
        time.sleep(config.UPDATE_INTERVAL)

def check_price_alerts(product_id, current_price):
    """检查价格提醒"""
    try:
        conn = sqlite3.connect('products.db')
        c = conn.cursor()
        
        c.execute('''
            SELECT id, target_price 
            FROM price_alerts 
            WHERE product_id = ? AND is_active = 1
        ''', (product_id,))
        
        alerts = c.fetchall()
        for alert_id, target_price in alerts:
            if current_price <= target_price:
                print(f"🎯 价格提醒触发! 商品 {product_id} 当前价格 {current_price} <= 目标价格 {target_price}")
                # 这里可以添加邮件/短信通知
                # send_notification(alert_id, product_id, current_price, target_price)
        
        conn.close()
    except Exception as e:
        print(f"❌ 检查价格提醒失败: {e}")

# API路由
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/product_images/<filename>')
def serve_product_image(filename):
    """提供商品图片"""
    return send_from_directory(config.IMAGE_DIR, filename)

@app.route('/api/status')
def api_status():
    """API状态检查"""
    return jsonify({
        'status': 'running',
        'service': 'Daily Price Tracker',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/products', methods=['GET'])
def get_products():
    """获取所有商品"""
    try:
        conn = sqlite3.connect('products.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute('''
            SELECT p.*, 
                   (SELECT price FROM price_history 
                    WHERE product_id = p.id 
                    ORDER BY timestamp DESC LIMIT 1) as current_price,
                   (SELECT timestamp FROM price_history 
                    WHERE product_id = p.id 
                    ORDER BY timestamp DESC LIMIT 1) as last_updated
            FROM products p
            ORDER BY p.created_at DESC
        ''')
        
        products = []
        for row in c.fetchall():
            product = dict(row)
            
            # 确定使用哪个图片URL
            if product['local_image_path'] and os.path.exists(os.path.join('static', product['local_image_path'])):
                product['display_image'] = f"/static/{product['local_image_path']}"
            elif product['image_url']:
                product['display_image'] = product['image_url']
            else:
                product['display_image'] = '/static/placeholder.png'
            
            products.append(product)
        
        conn.close()
        return jsonify(products)
        
    except Exception as e:
        print(f"❌ 获取商品列表失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/products', methods=['POST'])
def add_product():
    """添加商品"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': '请输入商品链接'}), 400
        
        # 验证URL格式
        if not url.startswith(('http://', 'https://')):
            return jsonify({'error': '请输入有效的URL链接'}), 400
        
        print(f"🔄 添加商品: {url}")
        
        # 使用真实爬虫获取商品信息
        product_info = crawler.fetch_product_info(url)
        if not product_info or not product_info.get('success'):
            return jsonify({'error': '无法获取商品信息，请检查链接是否正确或稍后重试'}), 400
        
        conn = sqlite3.connect('products.db')
        c = conn.cursor()
        
        # 检查是否已存在
        c.execute('SELECT id, name FROM products WHERE url = ?', (url,))
        existing = c.fetchone()
        if existing:
            conn.close()
            return jsonify({'error': f'该商品已在监控列表中: {existing[1]}'}), 400
        
        # 下载图片
        local_image_path = None
        if product_info.get('image_url'):
            local_image_path = download_product_image(product_info['image_url'], 'new')
        
        # 保存商品
        c.execute('''
            INSERT INTO products (name, url, image_url, local_image_path, platform, 
                                current_price, lowest_price, highest_price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            product_info['name'], 
            url, 
            product_info['image_url'],
            local_image_path,
            product_info['platform'],
            product_info['price'],
            product_info['price'],
            product_info['price']
        ))
        product_id = c.lastrowid
        
        # 如果图片下载成功，更新文件名包含真实ID
        if local_image_path:
            new_filename = f"product_{product_id}{get_image_extension(product_info['image_url'])}"
            new_filepath = os.path.join(config.IMAGE_DIR, new_filename)
            old_filepath = os.path.join('static', local_image_path)
            
            if os.path.exists(old_filepath):
                os.rename(old_filepath, new_filepath)
                c.execute('UPDATE products SET local_image_path = ? WHERE id = ?', 
                         (f"product_images/{new_filename}", product_id))
        
        # 保存价格历史
        c.execute('''
            INSERT INTO price_history (product_id, price)
            VALUES (?, ?)
        ''', (product_id, product_info['price']))
        
        conn.commit()
        
        # 获取完整的商品信息返回
        c.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        product = dict(c.fetchone())
        
        conn.close()
        
        print(f"✅ 商品添加成功: {product_info['name']}")
        return jsonify({
            'message': '商品添加成功！系统将自动监控价格变化', 
            'product': {
                'id': product['id'],
                'name': product['name'],
                'price': product['current_price'],
                'platform': product['platform'],
                'display_image': f"/static/{product['local_image_path']}" if product['local_image_path'] else product['image_url']
            }
        })
        
    except Exception as e:
        print(f"❌ 添加商品失败: {e}")
        return jsonify({'error': f'添加失败: {str(e)}'}), 500

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """删除商品"""
    try:
        conn = sqlite3.connect('products.db')
        c = conn.cursor()
        
        # 获取商品信息用于删除图片
        c.execute('SELECT local_image_path FROM products WHERE id = ?', (product_id,))
        result = c.fetchone()
        
        if result and result[0]:
            image_path = os.path.join('static', result[0])
            if os.path.exists(image_path):
                os.remove(image_path)
        
        # 删除商品及相关数据
        c.execute('DELETE FROM price_history WHERE product_id = ?', (product_id,))
        c.execute('DELETE FROM price_alerts WHERE product_id = ?', (product_id,))
        c.execute('DELETE FROM products WHERE id = ?', (product_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': '商品删除成功'})
        
    except Exception as e:
        return jsonify({'error': f'删除失败: {str(e)}'}), 500

@app.route('/api/products/<int:product_id>/prices')
def get_prices(product_id):
    """获取价格历史"""
    try:
        conn = sqlite3.connect('products.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # 获取最近30天的价格数据
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
        c.execute('''
            SELECT price, timestamp 
            FROM price_history 
            WHERE product_id = ? AND timestamp >= ?
            ORDER BY timestamp ASC
        ''', (product_id, thirty_days_ago))
        
        prices = [dict(row) for row in c.fetchall()]
        conn.close()
        
        return jsonify(prices)
    except Exception as e:
        print(f"❌ 获取价格历史失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<int:product_id>/stats')
def get_product_stats(product_id):
    """获取商品统计信息"""
    try:
        conn = sqlite3.connect('products.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # 获取商品基本信息
        c.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        product = dict(c.fetchone())
        
        # 获取价格统计
        c.execute('''
            SELECT 
                COUNT(*) as total_records,
                AVG(price) as average_price,
                MIN(price) as min_price,
                MAX(price) as max_price
            FROM price_history 
            WHERE product_id = ?
        ''', (product_id,))
        stats = dict(c.fetchone())
        
        conn.close()
        
        return jsonify({
            'product': product,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts', methods=['POST'])
def set_price_alert():
    """设置价格提醒"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        target_price = data.get('target_price')
        
        if not product_id or not target_price:
            return jsonify({'error': '缺少必要参数'}), 400
        
        conn = sqlite3.connect('products.db')
        c = conn.cursor()
        
        c.execute('''
            INSERT OR REPLACE INTO price_alerts (product_id, target_price)
            VALUES (?, ?)
        ''', (product_id, target_price))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': '价格提醒设置成功'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 启动后台任务
def start_background_tasks():
    """启动后台任务"""
    price_update_thread = threading.Thread(target=update_product_prices, daemon=True)
    price_update_thread.start()
    print("✅ 后台价格更新任务已启动")

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 启动日常可用商品价格追踪系统")
    print("=" * 60)
    print(f"📊 数据库: products.db")
    print(f"🖼️ 图片目录: {config.IMAGE_DIR}")
    print(f"⏰ 更新间隔: {config.UPDATE_INTERVAL//60} 分钟")
    print(f"🔍 每次更新: {config.BATCH_SIZE} 个商品")
    print("=" * 60)
    
    if init_db():
        start_background_tasks()
        print("🌐 服务启动: http://127.0.0.1:5000")
        app.run(debug=False, port=5000, host='127.0.0.1')
    else:
        print("❌ 系统启动失败")