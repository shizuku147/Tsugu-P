# database.py
import sqlite3
import logging
from datetime import datetime
from config import Config

class DatabaseManager:
    def __init__(self, db_path: str = Config.DATABASE_PATH):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        conn = self._get_connection()
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
        except Exception as e:
            logging.error(f"初始化数据库失败: {e}")
        finally:
            conn.close()
    
    def _get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def add_product(self, name: str, url: str, target_price: float = None) -> int:
        """添加商品"""
        conn = self._get_connection()
        try:
            cursor = conn.execute('''
                INSERT OR REPLACE INTO products (name, url, target_price, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (name, url, target_price))
            
            product_id = cursor.lastrowid
            conn.commit()
            return product_id
        except Exception as e:
            logging.error(f"添加商品失败: {e}")
            return None
        finally:
            conn.close()
    
    def update_product_price(self, product_id: int, price: float, name: str = None, image_path: str = None):
        """更新商品价格和信息"""
        conn = self._get_connection()
        try:
            # 更新商品信息
            if name or image_path:
                conn.execute('''
                    UPDATE products 
                    SET current_price = ?, name = COALESCE(?, name), 
                        image_path = COALESCE(?, image_path), updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (price, name, image_path, product_id))
            else:
                conn.execute('''
                    UPDATE products 
                    SET current_price = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (price, product_id))
            
            # 添加价格历史记录
            conn.execute('''
                INSERT INTO price_history (product_id, price)
                VALUES (?, ?)
            ''', (product_id, price))
            
            conn.commit()
        except Exception as e:
            logging.error(f"更新商品价格失败: {e}")
        finally:
            conn.close()
    
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
        finally:
            conn.close()
    
    def delete_product(self, product_id: int):
        """删除商品"""
        conn = self._get_connection()
        try:
            conn.execute('DELETE FROM price_history WHERE product_id = ?', (product_id,))
            conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
            conn.commit()
        finally:
            conn.close()