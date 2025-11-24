# app.py
from flask import Flask, render_template, request, jsonify, send_from_directory
import logging
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import os
import sqlite3
from datetime import datetime, timedelta
import random
import math

app = Flask(__name__)
app.config['SECRET_KEY'] = 'demo-secret-key'

# 配置
class Config:
    DATABASE_PATH = 'products.db'
    IMAGE_DIR = 'static/product_images'

# 演示数据生成器
class DemoDataGenerator:
    def __init__(self, db_path='products.db'):
        self.db_path = db_path
        
        # 商品数据 - 仅使用本地图片
        self.products = [
            {
                'name': 'iPhone 15 Pro 256GB',
                'url': 'https://www.apple.com/iphone-15-pro',
                'base_price': 8999,
                'price_variance': 0.15,
                'category': '手机',
                'image_file': 'iphone15.jpg'
            },
            {
                'name': 'MacBook Air M2 13寸',
                'url': 'https://www.apple.com/macbook-air',
                'base_price': 9499,
                'price_variance': 0.12,
                'category': '电脑',
                'image_file': 'macbook.jpg'
            },
            {
                'name': 'Samsung Galaxy S24 Ultra',
                'url': 'https://www.samsung.com/galaxy-s24',
                'base_price': 7999,
                'price_variance': 0.18,
                'category': '手机',
                'image_file': 'samsung.jpg'
            },
            {
                'name': 'Sony WH-1000XM5 耳机',
                'url': 'https://www.sony.com/headphones',
                'base_price': 2299,
                'price_variance': 0.25,
                'category': '音频',
                'image_file': 'sony.jpg'
            },
            {
                'name': 'Nintendo Switch OLED',
                'url': 'https://www.nintendo.com/switch',
                'base_price': 2599,
                'price_variance': 0.20,
                'category': '游戏',
                'image_file': 'switch.jpg'
            },
            {
                'name': 'Dyson V12 吸尘器',
                'url': 'https://www.dyson.com/vacuum-cleaners',
                'base_price': 3999,
                'price_variance': 0.22,
                'category': '家电',
                'image_file': 'dyson.jpg'
            }
        ]
    
    def check_images_exist(self):
        """检查本地图片文件是否存在"""
        print("🔍 检查本地图片文件...")
        missing_images = []
        for product in self.products:
            image_path = os.path.join(Config.IMAGE_DIR, product['image_file'])
            if os.path.exists(image_path):
                print(f"✅ 找到图片: {product['image_file']}")
            else:
                missing_images.append(product['image_file'])
                print(f"❌ 缺少图片: {product['image_file']}")
        
        if missing_images:
            print("❌ 缺少以下本地图片文件:")
            for filename in missing_images:
                print(f"   - {filename}")
            print(f"💡 请将图片放入 {Config.IMAGE_DIR} 目录")
            return False
        return True
    
    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        try:
            # 商品表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    current_price REAL,
                    target_price REAL,
                    image_path TEXT,
                    website_type TEXT,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 价格历史表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    price REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')
            
            conn.commit()
            print("✅ 数据库初始化完成")
        except Exception as e:
            print(f"❌ 初始化数据库失败: {e}")
        finally:
            conn.close()
    
    def clear_existing_data(self):
        """清空现有数据"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute('DELETE FROM price_history')
            conn.execute('DELETE FROM products')
            conn.commit()
            print("✅ 清空现有数据")
        except Exception as e:
            print(f"❌ 清空数据失败: {e}")
        finally:
            conn.close()
    
    def add_demo_products(self):
        """添加演示商品到数据库"""
        conn = sqlite3.connect(self.db_path)
        try:
            for product in self.products:
                # 设置目标价格（比基础价格低10-30%）
                target_discount = random.uniform(0.1, 0.3)
                target_price = product['base_price'] * (1 - target_discount)
                
                # 初始当前价格（在基础价格附近波动）
                initial_price = product['base_price'] * random.uniform(0.95, 1.05)
                
                # 使用本地图片路径 - 确保使用正确的路径
                image_path = f"/static/product_images/{product['image_file']}"
                
                print(f"📝 添加商品: {product['name']} -> 图片: {image_path}")
                
                # 插入商品
                cursor = conn.execute('''
                    INSERT INTO products 
                    (name, url, current_price, target_price, image_path, website_type, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    product['name'],
                    product['url'],
                    round(initial_price, 2),
                    round(target_price, 2),
                    image_path,  # 使用绝对路径
                    'demo',
                    product['category']
                ))
                
                product_id = cursor.lastrowid
                
                # 生成价格历史数据
                self.generate_price_history(conn, product_id, product)
                
                print(f"✅ 成功添加商品: {product['name']}")
            
            conn.commit()
            print("✅ 所有演示商品添加完成！")
        except Exception as e:
            print(f"❌ 添加演示商品失败: {e}")
        finally:
            conn.close()
    
    def generate_price_history(self, conn, product_id, product):
        """生成价格历史数据"""
        base_price = product['base_price']
        variance = product['price_variance']
        
        # 生成过去30天的价格数据
        for days_ago in range(30, -1, -1):
            date = datetime.now() - timedelta(days=days_ago)
            
            # 模拟价格波动
            day_factor = 1.0
            if date.weekday() >= 5:  # 周末
                day_factor = random.uniform(0.92, 1.02)
            else:
                day_factor = random.uniform(0.98, 1.08)
            
            random_factor = random.uniform(1 - variance/2, 1 + variance/2)
            trend_days = 30 - days_ago
            trend_factor = 1.0 - (trend_days * 0.0005)
            seasonal_factor = 1.0 + 0.1 * math.sin(trend_days * 0.1)
            
            price = base_price * day_factor * random_factor * trend_factor * seasonal_factor
            
            # 插入价格历史
            conn.execute('''
                INSERT INTO price_history (product_id, price, created_at)
                VALUES (?, ?, ?)
            ''', (product_id, round(price, 2), date))
    
    def setup_demo_data(self):
        """设置完整的演示数据"""
        print("🔄 正在生成演示数据...")
        
        # 检查图片文件
        if not self.check_images_exist():
            print("❌ 无法启动：缺少本地图片文件")
            return False
        
        # 初始化数据库
        self.init_database()
        
        # 清空现有数据
        self.clear_existing_data()
        
        # 添加商品数据
        self.add_demo_products()
        
        print("🎉 演示数据准备完成！")
        print("📊 已生成6个示例商品")
        print("📈 每个商品包含30天的价格历史")
        print("🖼️  使用本地图片文件")
        return True

# 初始化演示数据生成器
demo_generator = DemoDataGenerator()

class DatabaseManager:
    def __init__(self, db_path: str = Config.DATABASE_PATH):
        self.db_path = db_path
    
    def _get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def get_all_products(self):
        """获取所有商品"""
        conn = self._get_connection()
        try:
            cursor = conn.execute('''
                SELECT id, name, url, current_price, target_price, image_path, website_type,
                       created_at, updated_at
                FROM products 
                ORDER BY updated_at DESC
            ''')
            products = cursor.fetchall()
            
            # 调试：打印图片路径
            for product in products:
                print(f"📦 商品: {product[1]}, 图片路径: {product[5]}")
            
            return products
        except Exception as e:
            print(f"获取商品列表错误: {e}")
            return []
        finally:
            conn.close()
    
    def get_price_history(self, product_id: int, limit: int = 30):
        """获取价格历史"""
        conn = self._get_connection()
        try:
            cursor = conn.execute('''
                SELECT price, created_at 
                FROM price_history 
                WHERE product_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (product_id, limit))
            return cursor.fetchall()
        except Exception as e:
            print(f"获取价格历史错误: {e}")
            return []
        finally:
            conn.close()
    
    def add_demo_product(self, name: str, url: str, target_price: float = None):
        """添加演示商品"""
        conn = self._get_connection()
        try:
            # 基础价格（比目标价格高一些）
            base_price = target_price * 1.2 if target_price else random.uniform(1000, 5000)
            current_price = base_price * random.uniform(0.9, 1.1)
            
            # 为新商品使用默认图片
            image_path = "/static/product_images/default.jpg"
            
            cursor = conn.execute('''
                INSERT INTO products (name, url, current_price, target_price, image_path, website_type)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, url, round(current_price, 2), target_price, 
                  image_path, 
                  "demo"))
            
            product_id = cursor.lastrowid
            
            # 生成价格历史
            self._generate_price_history(conn, product_id, base_price)
            
            conn.commit()
            return product_id
        except Exception as e:
            print(f"添加演示商品失败: {e}")
            return None
        finally:
            conn.close()
    
    def _generate_price_history(self, conn, product_id: int, base_price: float):
        """为新产品生成价格历史"""
        # 生成过去15天的价格数据
        for days_ago in range(15, -1, -1):
            date = datetime.now() - timedelta(days=days_ago)
            
            # 价格波动
            fluctuation = random.uniform(0.8, 1.2)
            price = base_price * fluctuation
            
            conn.execute('''
                INSERT INTO price_history (product_id, price, created_at)
                VALUES (?, ?, ?)
            ''', (product_id, round(price, 2), date))
    
    def update_product_price(self, product_id: int):
        """更新商品价格（模拟价格变化）"""
        conn = self._get_connection()
        try:
            # 获取当前价格
            result = conn.execute(
                'SELECT current_price FROM products WHERE id = ?', 
                (product_id,)
            ).fetchone()
            
            if not result:
                return None
                
            current_price = result[0]
            
            # 生成新的价格（小幅度波动）
            change_percent = random.uniform(-0.05, 0.05)
            new_price = current_price * (1 + change_percent)
            new_price = round(new_price, 2)
            
            # 更新商品价格
            conn.execute('''
                UPDATE products 
                SET current_price = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_price, product_id))
            
            # 添加价格历史记录
            conn.execute('''
                INSERT INTO price_history (product_id, price)
                VALUES (?, ?)
            ''', (product_id, new_price))
            
            conn.commit()
            return new_price
        except Exception as e:
            print(f"更新商品价格失败: {e}")
            return None
        finally:
            conn.close()
    
    def delete_product(self, product_id: int):
        """删除商品"""
        conn = self._get_connection()
        try:
            conn.execute('DELETE FROM price_history WHERE product_id = ?', (product_id,))
            conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"删除商品失败: {e}")
            return False
        finally:
            conn.close()

# 初始化数据库管理器
db_manager = DatabaseManager()

def setup_demo_scheduler():
    """设置演示用的定时任务"""
    try:
        scheduler = BackgroundScheduler()
        
        # 每30秒更新一次价格（演示用）
        scheduler.add_job(
            func=update_all_prices_demo,
            trigger='interval',
            seconds=30,
            id='demo_price_update',
            name='演示价格更新'
        )
        
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown())
        print("✅ 定时任务启动成功")
    except Exception as e:
        print(f"❌ 定时任务启动失败: {e}")

def update_all_prices_demo():
    """演示模式：更新所有商品价格"""
    try:
        products = db_manager.get_all_products()
        updated_count = 0
        
        for product in products:
            product_id = product[0]
            # 随机决定是否更新这个商品的价格（70%概率更新）
            if random.random() < 0.7:
                new_price = db_manager.update_product_price(product_id)
                if new_price:
                    updated_count += 1
        
        print(f"演示模式: 更新了 {updated_count}/{len(products)} 个商品的价格")
    except Exception as e:
        print(f"演示价格更新失败: {e}")

@app.route('/')
def index():
    """主页"""
    try:
        # 如果是第一次运行，初始化演示数据
        products = db_manager.get_all_products()
        if not products:
            print("🔄 首次运行，初始化演示数据...")
            success = demo_generator.setup_demo_data()
            if not success:
                return "❌ 启动失败：请检查本地图片文件是否齐全", 500
            products = db_manager.get_all_products()
        else:
            print(f"📊 从数据库加载 {len(products)} 个商品")
        
        return render_template('index.html', products=products)
    except Exception as e:
        print(f"❌ 主页错误: {e}")
        return f"错误: {e}", 500

@app.route('/api/add_product', methods=['POST'])
def add_product():
    """添加商品API（演示版）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '无效的请求数据'})
            
        url = data.get('url')
        target_price = data.get('target_price')
        name = data.get('name', '自定义商品')
        
        if not url:
            return jsonify({'success': False, 'error': 'URL不能为空'})
        
        # 在演示模式下，使用提供的名称或生成默认名称
        if not name or name == '自定义商品':
            name = f"自定义商品 {datetime.now().strftime('%H:%M:%S')}"
        
        # 添加到数据库
        product_id = db_manager.add_demo_product(name, url, target_price)
        
        if product_id:
            return jsonify({
                'success': True, 
                'message': '商品添加成功！',
                'product': {
                    'id': product_id,
                    'name': name
                }
            })
        else:
            return jsonify({'success': False, 'error': '添加商品失败'})
            
    except Exception as e:
        print(f"添加商品失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/check_price/<int:product_id>')
def check_price(product_id):
    """手动检查价格（演示版）"""
    try:
        new_price = db_manager.update_product_price(product_id)
        
        if new_price is not None:
            return jsonify({
                'success': True, 
                'price': new_price,
                'message': f'价格已更新: ¥{new_price}'
            })
        else:
            return jsonify({'success': False, 'error': '更新价格失败'})
            
    except Exception as e:
        print(f"检查价格失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/price_history/<int:product_id>')
def get_price_history(product_id):
    """获取价格历史"""
    try:
        history = db_manager.get_price_history(product_id, 50)
        return jsonify({
            'success': True,
            'history': [
                {'price': price, 'date': date} 
                for price, date in history
            ]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/delete_product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """删除商品"""
    try:
        success = db_manager.delete_product(product_id)
        if success:
            return jsonify({'success': True, 'message': '商品删除成功'})
        else:
            return jsonify({'success': False, 'error': '删除商品失败'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/demo/reset')
def reset_demo_data():
    """重置演示数据"""
    try:
        print("🔄 重置演示数据...")
        # 删除数据库文件
        if os.path.exists(Config.DATABASE_PATH):
            os.remove(Config.DATABASE_PATH)
            print("✅ 删除数据库文件")
        
        # 重新初始化演示数据
        success = demo_generator.setup_demo_data()
        if success:
            return jsonify({'success': True, 'message': '演示数据已重置'})
        else:
            return jsonify({'success': False, 'error': '重置失败：图片文件不完整'})
    except Exception as e:
        print(f"❌ 重置失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/static/product_images/<filename>')
def serve_product_image(filename):
    """提供本地商品图片"""
    try:
        return send_from_directory(Config.IMAGE_DIR, filename)
    except Exception as e:
        print(f"❌ 图片服务错误: {e}")
        return "图片未找到", 404

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': '页面未找到'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': '服务器内部错误'}), 500

if __name__ == '__main__':
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 确保目录存在
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs(Config.IMAGE_DIR, exist_ok=True)
    
    # 启动演示定时任务
    setup_demo_scheduler()
    
    print("🎉 本地图片版价格追踪系统启动成功！")
    print("📍 访问地址: http://localhost:5000")
    print("⏰ 价格每30秒自动更新一次")
    print("🖼️  仅使用本地图片文件")
    print("📁 图片目录: static/product_images/")
    print("💡 必需图片文件:")
    
    
    # 运行应用
    try:
        app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
    except Exception as e:
        print(f"❌ 程序运行错误: {e}")