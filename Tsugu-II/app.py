# app.py
from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit
import os

from real_crawler import RealPriceCrawler
from database import DatabaseManager
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# 初始化组件
crawler = RealPriceCrawler()
db_manager = DatabaseManager()

def setup_scheduler():
    """设置定时任务"""
    scheduler = BackgroundScheduler()
    
    # 定时检查价格
    trigger = IntervalTrigger(hours=Config.SCHEDULER_INTERVAL_HOURS)
    scheduler.add_job(
        func=check_all_prices,
        trigger=trigger,
        id='price_check',
        name='定时检查商品价格',
        replace_existing=True
    )
    
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())

def check_all_prices():
    """检查所有商品价格"""
    with app.app_context():
        try:
            products = db_manager.get_all_products()
            for product in products:
                product_id, name, url, current_price, target_price, image_path, website_type, created_at, updated_at = product
                
                # 获取最新价格
                product_info = crawler.fetch_product_info(url)
                
                if product_info.get('price') is not None:
                    # 下载图片（如果还没有图片）
                    if not image_path and product_info.get('image_url'):
                        new_image_path = crawler.download_image(product_info.get('image_url'), product_id)
                    else:
                        new_image_path = None
                    
                    # 更新数据库
                    db_manager.update_product_price(
                        product_id, 
                        product_info['price'],
                        product_info.get('name'),
                        new_image_path
                    )
                    
                    app.logger.info(f"更新商品价格: {name} - {product_info['price']}")
                
                # 避免请求过于频繁
                import time
                time.sleep(2)
                
        except Exception as e:
            app.logger.error(f"定时检查价格失败: {e}")

@app.route('/')
def index():
    """主页"""
    products = db_manager.get_all_products()
    return render_template('index.html', products=products)

@app.route('/api/add_product', methods=['POST'])
def add_product():
    """添加商品API"""
    try:
        data = request.get_json()
        url = data.get('url')
        target_price = data.get('target_price')
        
        if not url:
            return jsonify({'success': False, 'error': 'URL不能为空'})
        
        # 获取商品信息
        product_info = crawler.fetch_product_info(url)
        
        if product_info.get('error'):
            return jsonify({'success': False, 'error': product_info['error']})
        
        # 添加到数据库
        product_id = db_manager.add_product(
            product_info.get('name', '未知商品'),
            url,
            target_price
        )
        
        if product_id:
            # 下载图片
            image_path = crawler.download_image(product_info.get('image_url'), product_id)
            
            # 更新价格和图片
            if product_info.get('price') is not None:
                db_manager.update_product_price(
                    product_id,
                    product_info['price'],
                    product_info.get('name'),
                    image_path
                )
            
            return jsonify({'success': True, 'message': '商品添加成功'})
        else:
            return jsonify({'success': False, 'error': '添加商品失败'})
            
    except Exception as e:
        app.logger.error(f"添加商品失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/check_price/<int:product_id>')
def check_price(product_id):
    """手动检查价格"""
    try:
        products = db_manager.get_all_products()
        product = next((p for p in products if p[0] == product_id), None)
        
        if not product:
            return jsonify({'success': False, 'error': '商品不存在'})
        
        _, name, url, current_price, target_price, image_path, website_type, _, _ = product
        
        # 获取最新价格
        product_info = crawler.fetch_product_info(url)
        
        if product_info.get('price') is not None:
            # 下载图片（如果还没有图片）
            if not image_path and product_info.get('image_url'):
                new_image_path = crawler.download_image(product_info.get('image_url'), product_id)
            else:
                new_image_path = None
            
            # 更新数据库
            db_manager.update_product_price(
                product_id, 
                product_info['price'],
                product_info.get('name'),
                new_image_path
            )
            
            return jsonify({
                'success': True, 
                'price': product_info['price'],
                'name': product_info.get('name', name)
            })
        else:
            return jsonify({'success': False, 'error': '无法获取价格'})
            
    except Exception as e:
        app.logger.error(f"检查价格失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/price_history/<int:product_id>')
def get_price_history(product_id):
    """获取价格历史"""
    try:
        history = db_manager.get_price_history(product_id)
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
        db_manager.delete_product(product_id)
        return jsonify({'success': True, 'message': '商品删除成功'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/static/product_images/<filename>')
def serve_image(filename):
    """提供商品图片"""
    return send_from_directory('static/product_images', filename)

if __name__ == '__main__':
    # 启动定时任务
    setup_scheduler()
    
    # 确保静态文件目录存在
    os.makedirs('static/product_images', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)