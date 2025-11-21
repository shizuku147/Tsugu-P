from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
import sqlite3
import os
import time

app = Flask(__name__)
DB_NAME = 'products.db'

# 启用 CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://127.0.0.1:5000", "http://localhost:5000"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type"]
    }
})

# 检查并创建必要的文件夹
if not os.path.exists('templates'):
    print("📁 创建 templates 文件夹...")
    os.makedirs('templates')

print(f"📁 当前工作目录: {os.getcwd()}")
print(f"📁 templates 路径: {os.path.join(os.getcwd(), 'templates')}")

def init_db():
    """初始化数据库"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                image_url TEXT,
                platform TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                price REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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

def get_simple_product_info(url):
    """简化版商品信息获取"""
    try:
        if 'taobao' in url:
            return {
                'name': '淘宝商品示例 - 高达模型',
                'price': 299.0,
                'image_url': '',
                'platform': 'taobao'
            }
        elif 'jd.com' in url:
            return {
                'name': '京东商品示例 - 乐高玩具', 
                'price': 399.0,
                'image_url': '',
                'platform': 'jd'
            }
        else:
            return {
                'name': '测试商品',
                'price': 199.0,
                'image_url': '',
                'platform': 'other'
            }
    except Exception as e:
        print(f"获取商品信息失败: {e}")
        return None

@app.route('/')
def index():
    """主页"""
    try:
        print("🔄 正在渲染首页...")
        return render_template('index.html')
    except Exception as e:
        print(f"❌ 渲染模板失败: {e}")
        return f"""
        <html>
            <head><title>商品价格追踪系统</title></head>
            <body>
                <h1>商品价格追踪系统</h1>
                <p>后端服务运行正常！</p>
                <p>错误信息: {e}</p>
            </body>
        </html>
        """

@app.route('/api/test')
@cross_origin()
def test_api():
    """测试API"""
    print("✅ API测试端点被调用")
    return jsonify({
        'status': 'success', 
        'message': 'API工作正常',
        'timestamp': time.time()
    })

@app.route('/api/status')
@cross_origin()
def status():
    """服务状态检查"""
    return jsonify({
        'status': 'running',
        'service': '商品价格追踪系统',
        'timestamp': time.time(),
        'database': os.path.exists(DB_NAME)
    })

@app.route('/api/products', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_products():
    """获取所有商品"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        print("📦 获取商品列表请求")
        conn = sqlite3.connect(DB_NAME)
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
        products = [dict(row) for row in c.fetchall()]
        conn.close()
        
        print(f"✅ 返回 {len(products)} 个商品")
        return jsonify(products)
    except Exception as e:
        print(f"❌ 获取商品列表失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/products', methods=['POST', 'OPTIONS'])
@cross_origin()
def add_product():
    """添加商品"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        print("🔄 添加商品请求")
        print(f"📨 请求头: {dict(request.headers)}")
        print(f"📦 请求数据: {request.get_data()}")
        
        data = request.get_json()
        print(f"📋 解析后的数据: {data}")
        
        if not data:
            return jsonify({'error': '无效的请求数据'}), 400
            
        url = data.get('url', '').strip()
        if not url:
            return jsonify({'error': '请输入商品链接'}), 400
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT id FROM products WHERE url = ?', (url,))
        if c.fetchone():
            conn.close()
            return jsonify({'error': '该商品已在监控列表中'}), 400
        
        product_info = get_simple_product_info(url)
        if not product_info:
            conn.close()
            return jsonify({'error': '无法获取商品信息'}), 400
        
        c.execute('''
            INSERT INTO products (name, url, image_url, platform)
            VALUES (?, ?, ?, ?)
        ''', (product_info['name'], url, product_info['image_url'], product_info['platform']))
        product_id = c.lastrowid
        
        c.execute('''
            INSERT INTO price_history (product_id, price)
            VALUES (?, ?)
        ''', (product_id, product_info['price']))
        
        conn.commit()
        conn.close()
        
        print(f"✅ 成功添加商品: {product_info['name']}")
        return jsonify({
            'message': '添加成功', 
            'product': {
                'id': product_id,
                'name': product_info['name'],
                'price': product_info['price']
            }
        })
        
    except Exception as e:
        print(f"❌ 添加商品失败: {e}")
        return jsonify({'error': '服务器内部错误: ' + str(e)}), 500

@app.route('/api/products/<int:product_id>/prices', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_prices(product_id):
    """获取价格历史"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        print(f"📊 获取商品 {product_id} 的价格历史")
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute('''
            SELECT price, timestamp 
            FROM price_history 
            WHERE product_id = ? 
            ORDER BY timestamp ASC
        ''', (product_id,))
        prices = [dict(row) for row in c.fetchall()]
        conn.close()
        
        if not prices:
            # 生成一些测试数据
            prices = [
                {'price': 299.0, 'timestamp': '2024-01-01 10:00:00'},
                {'price': 289.0, 'timestamp': '2024-01-02 10:00:00'},
                {'price': 279.0, 'timestamp': '2024-01-03 10:00:00'},
                {'price': 269.0, 'timestamp': '2024-01-04 10:00:00'}
            ]
            
        print(f"✅ 返回 {len(prices)} 条价格记录")
        return jsonify(prices)
    except Exception as e:
        print(f"❌ 获取价格历史失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug')
@cross_origin()
def debug_info():
    """调试信息"""
    return jsonify({
        'current_directory': os.getcwd(),
        'templates_exists': os.path.exists('templates'),
        'database_exists': os.path.exists(DB_NAME),
        'python_version': os.sys.version
    })

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 启动商品价格追踪系统")
    print("=" * 50)
    
    # 初始化数据库
    if init_db():
        print("✅ 系统初始化完成")
        print("🌐 服务将在 http://127.0.0.1:5000 启动")
        print("🔧 CORS 已启用")
        print("=" * 50)
        
        # 启动Flask应用
        app.run(debug=True, port=5000, host='127.0.0.1')
    else:
        print("❌ 系统初始化失败，请检查错误信息")