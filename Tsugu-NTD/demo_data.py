# demo_data.py
import sqlite3
import random
from datetime import datetime, timedelta
import os
import math
import shutil

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
        
        for product in self.products:
            source_path = os.path.join(self.image_source_dir, product['image_filename'])
            target_path = os.path.join(self.image_target_dir, product['image_filename'])
            
            # 检查源图片是否存在
            if os.path.exists(source_path):
                try:
                    # 复制图片到目标目录
                    shutil.copy2(source_path, target_path)
                    print(f"✅ 复制图片: {product['image_filename']}")
                except Exception as e:
                    print(f"❌ 复制图片失败 {product['image_filename']}: {e}")
            else:
                print(f"⚠️  图片不存在: {source_path}")
                print(f"   请将 {product['image_filename']} 放入 {self.image_source_dir} 目录")
        
        print("✅ 图片处理完成")
    
    def create_sample_images(self):
        """创建示例图片（如果源图片不存在）"""
        sample_images_created = False
        
        for product in self.products:
            source_path = os.path.join(self.image_source_dir, product['image_filename'])
            target_path = os.path.join(self.image_target_dir, product['image_filename'])
            
            # 如果源图片不存在，创建示例图片
            if not os.path.exists(source_path):
                try:
                    # 创建一个简单的彩色图片作为示例
                    self.create_color_image(target_path, product['name'])
                    print(f"🎨 创建示例图片: {product['image_filename']}")
                    sample_images_created = True
                except Exception as e:
                    print(f"❌ 创建示例图片失败: {e}")
        
        if sample_images_created:
            print("💡 已创建示例图片，建议替换为真实商品图片")
    
    def create_color_image(self, filepath, product_name):
        """创建彩色示例图片"""
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            # 如果PIL不可用，创建一个文本文件说明
            with open(filepath.replace('.jpg', '.txt'), 'w', encoding='utf-8') as f:
                f.write(f"商品图片: {product_name}\n")
                f.write(f"请将商品图片保存为: {os.path.basename(filepath)}\n")
            return
        
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
                
                # 构建图片路径（相对于static目录）
                image_path = f"product_images/{product['image_filename']}"
                
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

    def update_product_images(self):
        """更新商品图片（用于后期添加新图片）"""
        print("🔄 更新商品图片...")
        self.setup_image_directories()
        self.copy_product_images()
        print("✅ 商品图片更新完成")

# 辅助函数：检查图片文件
def check_image_files():
    """检查图片文件是否存在"""
    generator = DemoDataGenerator()
    generator.setup_image_directories()
    
    missing_images = []
    for product in generator.products:
        source_path = os.path.join(generator.image_source_dir, product['image_filename'])
        if not os.path.exists(source_path):
            missing_images.append(product['image_filename'])
    
    if missing_images:
        print("❌ 缺少以下图片文件:")
        for filename in missing_images:
            print(f"   - {filename}")
        print(f"💡 请将图片放入 {generator.image_source_dir} 目录")
        return False
    else:
        print("✅ 所有图片文件都存在")
        return True

if __name__ == '__main__':
    # 创建演示数据
    generator = DemoDataGenerator()
    generator.setup_demo_data()
    
    # 检查图片文件
    check_image_files()