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
    DEMO_MODE = True

# 初始化演示数据生成器
class DemoDataGenerator:
    def __init__(self, db_path='products.db'):
        self.db_path = db_path
        
        # 商品数据
        self.products = [
            {
                'name': 'iPhone 15 Pro 256GB',
                'url': 'https://www.apple.com/iphone-15-pro',
                'base_price': 8999,
                'price_variance': 0.15,
                'category': '手机',
                'image_filename': 'iphone15.jpg'
            },
            {
                'name': 'MacBook Air M2 13寸',
                'url': 'https://www.apple.com/macbook-air',
                'base_price': 9499,
                'price_variance': 0.12,
                'category': '电脑',
                'image_filename': 'macbook.jpg'
            },
            {
                'name': 'Samsung Galaxy S24 Ultra',
                'url': 'https://www.samsung.com/galaxy-s24',
                'base_price': 7999,
                'price_variance': 0.18,
                'category': '手机',
                'image_filename': 'samsung.jpg'
            },
            {
                'name': 'Sony WH-1000XM5 耳机',
                'url': 'https://www.sony.com/headphones',
                'base_price': 2299,
                'price_variance': 0.25,
                'category': '音频',
                'image_filename': 'sony.jpg'
            },
            {
                'name': 'Nintendo Switch OLED',
                'url': 'https://www.nintendo.com/switch',
                'base_price': 2599,
                'price_variance': 0.20,
                'category': '游戏',
                'image_filename': 'switch.jpg'
            },
            {
                'name': 'Dyson V12 吸尘器',
                'url': 'https://www.dyson.com/vacuum-cleaners',
                'base_price': 3999,
                'price_variance': 0.22,
                'category': '家电',
                'image_filename': 'dyson.jpg'
            },
            {
                'name': 'iPad Air 5代 64GB',
                'url': 'https://www.apple.com/ipad-air',
                'base_price': 4399,
                'price_variance': 0.16,
                'category': '平板',
                'image_filename': 'ipad.jpg'
            },
            {
                'name': 'PlayStation 5 光驱版',
                'url': 'https://www.sony.com/ps5',
                'base_price': 3899,
                'price_variance': 0.14,
                'category': '游戏',
                'image_filename': 'ps5.jpg'
            }
        ]
        
        # 图片目录配置
        self.image_source_dir = 'local_product_images'  # 源图片目录
        self.image_target_dir = 'static/product_images'  # 目标图片目录
    
    def setup_image_directories(self):
        """创建图片目录结构"""
        # 创建源图片目录（如果不存在）
        if not os.path.exists(self.image_source_dir):
            os.makedirs(self.image_source_dir)
            print(f"📁 创建源图片目录: {self.image_source_dir}")
            print("💡 请将商品图片放入此目录，文件名对应 image_filename")
        
        # 创建目标图片目录
        if not os.path.exists(self.image_target_dir):
            os.makedirs(self.image_target_dir)
            print(f"📁 创建目标图片目录: {self.image_target_dir}")
    
    def copy_product_images(self):
        """复制商品图片到静态文件目录"""
        print("🖼️  正在处理商品图片...")
        images_copied = 0
        
        for product in self.products:
            source_path = os.path.join(self.image_source_dir, product['image_filename'])
            target_path = os.path.join(self.image_target_dir, product['image_filename'])
            
            # 检查源图片是否存在
            if os.path.exists(source_path):
                try:
                    # 复制图片到目标目录
                    import shutil
                    shutil.copy2(source_path, target_path)
                    print(f"✅ 复制图片: {product['image_filename']}")
                    images_copied += 1
                except Exception as e:
                    print(f"❌ 复制图片失败 {product['image_filename']}: {e}")
            else:
                print(f"⚠️  图片不存在: {source_path}")
                # 使用在线图片作为备用
                online_image = f"https://picsum.photos/300/200?random={random.randint(1000, 9999)}"
                product['online_image'] = online_image
                print(f"   使用在线图片: {online_image}")
        
        print(f"✅ 图片处理完成，成功复制 {images_copied} 张图片")
    
    def create_sample_images(self):
        """创建示例图片（如果源图片不存在）"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            has_pil = True
        except ImportError:
            has_pil = False
            print("💡 未安装PIL，无法创建示例图片")
            return
        
        sample_images_created = 0
        
        for product in self.products:
            source_path = os.path.join(self.image_source_dir, product['image_filename'])
            target_path = os.path.join(self.image_target_dir, product['image_filename'])
            
            # 如果源图片不存在，创建示例图片
            if not os.path.exists(source_path) and has_pil:
                try:
                    # 创建一个简单的彩色图片作为示例
                    self.create_color_image(target_path, product['name'])
                    print(f"🎨 创建示例图片: {product['image_filename']}")
                    sample_images_created += 1
                except Exception as e:
                    print(f"❌ 创建示例图片失败: {e}")
        
        if sample_images_created > 0:
            print(f"💡 已创建 {sample_images_created} 张示例图片，建议替换为真实商品图片")
    
    def create_color_image(self, filepath, product_name):
        """创建彩色示例图片"""
        from PIL import Image, ImageDraw, ImageFont
        
        # 创建彩色图片
        width, height = 300, 200
        colors = [
            (255, 99, 132),   # 红色
            (54, 162, 235),   # 蓝色
            (255, 206, 86),   # 黄色
            (75, 192, 192),   # 绿色
            (153, 102, 255),  # 紫色
            (255, 159, 64),   # 橙色
        ]
        
        color = random.choice(colors)
        image = Image.new('RGB', (width, height), color)
        draw = ImageDraw.Draw(image)
        
        try:
            # 尝试使用字体
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            try:
                font = ImageFont.truetype("simhei.ttf", 20)  # 黑体
            except:
                font = ImageFont.load_default()
        
        # 添加商品名称
        text = product_name[:15] + "..." if len(product_name) > 15 else product_name
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # 添加文字背景
        padding = 10
        draw.rectangle([
            x - padding, y - padding,
            x + text_width + padding, y + text_height + padding
        ], fill=(255, 255, 255, 128))
        
        # 添加文字
        draw.text((x, y), text, fill=(0, 0, 0), font=font)
        
        # 保存图片
        image.save(filepath, 'JPEG', quality=85)
    
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
                
                # 构建图片路径
                image_path = f"product_images/{product['image_filename']}"
                
                # 检查图片是否存在，如果不存在使用在线图片
                target_image_path = os.path.join(self.image_target_dir, product['image_filename'])
                if not os.path.exists(target_image_path) and 'online_image' in product:
                    image_path = product['online_image']
                
                # 检查是否已存在
                existing = conn.execute(
                    'SELECT id FROM products WHERE url = ?', 
                    (product['url'],)
                ).fetchone()
                
                if not existing:
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
                        image_path,
                        'demo',
                        product['category']
                    ))
                    
                    product_id = cursor.lastrowid
                    
                    # 生成价格历史数据
                    self.generate_price_history(conn, product_id, product)
                    
                    print(f"✅ 添加商品: {product['name']}")
                else:
                    print(f"⏭️  商品已存在: {product['name']}")
            
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
            
            # 模拟价格波动模式
            day_factor = 1.0
            
            # 周末可能有促销
            if date.weekday() >= 5:  # 周末
                day_factor = random.uniform(0.92, 1.02)
            else:
                day_factor = random.uniform(0.98, 1.08)
            
            # 随机波动
            random_factor = random.uniform(1 - variance/2, 1 + variance/2)
            
            # 长期趋势（轻微下降趋势）
            trend_days = 30 - days_ago
            trend_factor = 1.0 - (trend_days * 0.0005)  # 每天下降0.05%
            
            # 季节性波动（模拟）
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
        
        # 1. 设置图片目录
        self.setup_image_directories()
        
        # 2. 复制图片文件
        self.copy_product_images()
        
        # 3. 创建示例图片（如果需要）
        self.create_sample_images()
        
        # 4. 初始化数据库
        self.init_database()
        
        # 5. 添加商品数据
        self.add_demo_products()
        
        print("🎉 演示数据准备完成！")
        print("📊 已生成8个示例商品")
        print("📈 每个商品包含30天的价格历史")
        print("🖼️  商品图片位置: static/product_images/")
        print("💡 源图片位置: local_product_images/")

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
            return cursor.fetchall()
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
            
            # 为新商品生成图片
            image_filename = f"custom_{random.randint(1000, 9999)}.jpg"
            image_path = f"product_images/{image_filename}"
            
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
            change_percent = random.uniform(-0.05, 0.05)  # -5% 到 +5%
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
                    print(f"演示价格更新: {product[1]} - ¥{new_price}")
        
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
            demo_generator.setup_demo_data()
            products = db_manager.get_all_products()
        
        return render_template('index.html', products=products)
    except Exception as e:
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
        # 删除数据库文件
        if os.path.exists(Config.DATABASE_PATH):
            os.remove(Config.DATABASE_PATH)
        
        # 重新初始化演示数据
        demo_generator.setup_demo_data()
        
        return jsonify({'success': True, 'message': '演示数据已重置'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/demo/update_all_prices')
def update_all_prices_manual():
    """手动更新所有商品价格"""
    try:
        update_all_prices_demo()
        return jsonify({'success': True, 'message': '所有商品价格已更新'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/static/product_images/<filename>')
def serve_product_image(filename):
    """提供商品图片"""
    try:
        return send_from_directory('static/product_images', filename)
    except Exception as e:
        # 如果图片不存在，返回默认图片
        return send_from_directory('static', 'default-product.jpg')

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
    
    # 确保静态文件目录存在
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('local_product_images', exist_ok=True)
    os.makedirs('static/product_images', exist_ok=True)
    
    # 启动演示定时任务
    setup_demo_scheduler()
    
    print("🎉 演示版价格追踪系统启动成功！")
    print("📍 访问地址: http://localhost:5000")
    print("⏰ 价格每30秒自动更新一次（演示模式）")
    print("🔄 自动更新70%的商品价格，模拟真实场景")
    print("🖼️  本地图片支持已启用")
    print("💡 将商品图片放入 local_product_images/ 目录")
    
    # 使用更安全的运行方式
    try:
        app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
    except Exception as e:
        print(f"❌ 程序运行错误: {e}")