import sqlite3
from datetime import datetime
import os
from config import DB_PATH

class DatabaseManager:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Products table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Product (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT,
                    category TEXT,
                    source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(url)
                )
            ''')
            # Price history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS PriceHistory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    price REAL,
                    in_stock BOOLEAN,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(product_id) REFERENCES Product(id)
                )
            ''')
            # Indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_product_category ON Product(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_product ON PriceHistory(product_id)')
            conn.commit()

    def upsert_product(self, product_data):
        """Insert or update a product and add a price history record."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Upsert product
            cursor.execute('''
                INSERT INTO Product (title, url, category, source)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    title=excluded.title,
                    category=excluded.category,
                    source=excluded.source
            ''', (
                product_data['title'],
                product_data['url'],
                product_data.get('category', ''),
                product_data.get('source', '')
            ))
            
            # Get product_id
            cursor.execute('SELECT id FROM Product WHERE url = ?', (product_data['url'],))
            product_id = cursor.fetchone()['id']
            
            # Insert price history
            price = product_data.get('price')
            in_stock = product_data.get('in_stock', True)
            cursor.execute('''
                INSERT INTO PriceHistory (product_id, price, in_stock)
                VALUES (?, ?, ?)
            ''', (product_id, price, in_stock))
            
            conn.commit()
            return product_id

    def get_products(self, page=1, per_page=25, search=None, category=None):
        """Get products with their latest price and stock status."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            base_query = '''
                SELECT p.*,
                       (SELECT price FROM PriceHistory ph WHERE ph.product_id = p.id ORDER BY timestamp DESC LIMIT 1) as current_price,
                       (SELECT in_stock FROM PriceHistory ph WHERE ph.product_id = p.id ORDER BY timestamp DESC LIMIT 1) as in_stock,
                       (SELECT price FROM PriceHistory ph WHERE ph.product_id = p.id ORDER BY timestamp ASC LIMIT 1) as original_price
                FROM Product p
                WHERE 1=1
            '''
            params = []
            
            if search:
                base_query += ' AND p.title LIKE ?'
                params.append(f'%{search}%')
            if category:
                base_query += ' AND p.category = ?'
                params.append(category)
                
            # Count total
            count_query = f"SELECT COUNT(*) as total FROM ({base_query})"
            cursor.execute(count_query, params)
            total = cursor.fetchone()['total']
            
            # Pagination
            base_query += ' ORDER BY p.id DESC LIMIT ? OFFSET ?'
            params.extend([per_page, (page - 1) * per_page])
            
            cursor.execute(base_query, params)
            rows = cursor.fetchall()
            
            products = [dict(row) for row in rows]
            
            return {
                'products': products,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }

    def get_all_products_for_export(self, search=None, category=None):
        """Get all products without pagination for export."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT p.id, p.title as "Product Name", p.category as Category,
                       p.source as Source, p.url as URL,
                       ph.price as "Current Price",
                       CASE WHEN ph.in_stock THEN 'Yes' ELSE 'No' END as "In Stock",
                       ph.timestamp as "Last Checked"
                FROM Product p
                LEFT JOIN (
                    SELECT product_id, price, in_stock, timestamp
                    FROM PriceHistory
                    WHERE id IN (
                        SELECT MAX(id)
                        FROM PriceHistory
                        GROUP BY product_id
                    )
                ) ph ON p.id = ph.product_id
                WHERE 1=1
            '''
            params = []
            
            if search:
                query += ' AND p.title LIKE ?'
                params.append(f'%{search}%')
            if category:
                query += ' AND p.category = ?'
                params.append(category)
                
            query += ' ORDER BY p.title ASC'
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_product_history(self, product_id):
        """Get price history for a single product."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT price, in_stock, timestamp
                FROM PriceHistory
                WHERE product_id = ?
                ORDER BY timestamp ASC
            ''', (product_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_stats(self):
        """Get dashboard statistics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total products
            cursor.execute('SELECT COUNT(*) as count FROM Product')
            total_products = cursor.fetchone()['count']
            
            # Out of stock products (based on latest history)
            cursor.execute('''
                SELECT COUNT(*) as count
                FROM (
                    SELECT product_id, in_stock
                    FROM PriceHistory
                    WHERE id IN (SELECT MAX(id) FROM PriceHistory GROUP BY product_id)
                ) latest
                WHERE latest.in_stock = 0
            ''')
            out_of_stock = cursor.fetchone()['count']
            
            # Price drops (current price < original price)
            cursor.execute('''
                SELECT COUNT(*) as count
                FROM (
                    SELECT product_id,
                           (SELECT price FROM PriceHistory ph WHERE ph.product_id = p.product_id ORDER BY timestamp ASC LIMIT 1) as orig_price,
                           (SELECT price FROM PriceHistory ph WHERE ph.product_id = p.product_id ORDER BY timestamp DESC LIMIT 1) as curr_price
                    FROM (SELECT DISTINCT product_id FROM PriceHistory) p
                )
                WHERE curr_price < orig_price AND curr_price IS NOT NULL
            ''')
            price_drops = cursor.fetchone()['count']

            # Average price
            cursor.execute('''
                SELECT ROUND(AVG(price), 2) as avg_price
                FROM PriceHistory
                WHERE id IN (SELECT MAX(id) FROM PriceHistory GROUP BY product_id)
                AND price IS NOT NULL
            ''')
            row = cursor.fetchone()
            avg_price = row['avg_price'] if row['avg_price'] else 0

            # Total categories
            cursor.execute('SELECT COUNT(DISTINCT category) as count FROM Product WHERE category != ""')
            total_categories = cursor.fetchone()['count']

            # In stock percentage
            in_stock_pct = 0
            if total_products > 0:
                in_stock_pct = round(((total_products - out_of_stock) / total_products) * 100, 1)
            
            return {
                'total_products': total_products,
                'out_of_stock': out_of_stock,
                'price_drops': price_drops,
                'avg_price': avg_price,
                'total_categories': total_categories,
                'in_stock_pct': in_stock_pct,
            }

    def get_analytics(self):
        """Get rich analytics data for the dashboard charts."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # --- Category Breakdown ---
            cursor.execute('''
                SELECT p.category, COUNT(*) as count,
                       ROUND(AVG(ph.price), 2) as avg_price
                FROM Product p
                LEFT JOIN (
                    SELECT product_id, price FROM PriceHistory
                    WHERE id IN (SELECT MAX(id) FROM PriceHistory GROUP BY product_id)
                ) ph ON p.id = ph.product_id
                WHERE p.category != ""
                GROUP BY p.category
                ORDER BY count DESC
                LIMIT 10
            ''')
            categories = [dict(r) for r in cursor.fetchall()]

            # --- Price Distribution (histogram buckets) ---
            cursor.execute('''
                SELECT price FROM PriceHistory
                WHERE id IN (SELECT MAX(id) FROM PriceHistory GROUP BY product_id)
                AND price IS NOT NULL
                ORDER BY price
            ''')
            prices = [r['price'] for r in cursor.fetchall()]
            price_distribution = self._build_histogram(prices)

            # --- Top Price Drops ---
            cursor.execute('''
                SELECT * FROM (
                    SELECT p.id, p.title, p.category,
                           (SELECT price FROM PriceHistory ph WHERE ph.product_id = p.id ORDER BY timestamp ASC LIMIT 1) as original_price,
                           (SELECT price FROM PriceHistory ph WHERE ph.product_id = p.id ORDER BY timestamp DESC LIMIT 1) as current_price
                    FROM Product p
                ) sub
                WHERE current_price IS NOT NULL AND original_price IS NOT NULL AND current_price < original_price
                ORDER BY (original_price - current_price) DESC
                LIMIT 8
            ''')
            top_drops = [dict(r) for r in cursor.fetchall()]

            # --- Top Price Increases ---
            cursor.execute('''
                SELECT * FROM (
                    SELECT p.id, p.title, p.category,
                           (SELECT price FROM PriceHistory ph WHERE ph.product_id = p.id ORDER BY timestamp ASC LIMIT 1) as original_price,
                           (SELECT price FROM PriceHistory ph WHERE ph.product_id = p.id ORDER BY timestamp DESC LIMIT 1) as current_price
                    FROM Product p
                ) sub
                WHERE current_price IS NOT NULL AND original_price IS NOT NULL AND current_price > original_price
                ORDER BY (current_price - original_price) DESC
                LIMIT 8
            ''')
            top_increases = [dict(r) for r in cursor.fetchall()]

            # --- Stock Status Breakdown ---
            cursor.execute('''
                SELECT 
                    SUM(CASE WHEN in_stock = 1 THEN 1 ELSE 0 END) as in_stock,
                    SUM(CASE WHEN in_stock = 0 THEN 1 ELSE 0 END) as out_of_stock
                FROM PriceHistory
                WHERE id IN (SELECT MAX(id) FROM PriceHistory GROUP BY product_id)
            ''')
            stock_row = cursor.fetchone()
            stock_status = {
                'in_stock': stock_row['in_stock'] or 0,
                'out_of_stock': stock_row['out_of_stock'] or 0
            }

            # --- Price Range Stats per Category ---
            cursor.execute('''
                SELECT p.category,
                       ROUND(MIN(ph.price), 2) as min_price,
                       ROUND(MAX(ph.price), 2) as max_price,
                       ROUND(AVG(ph.price), 2) as avg_price,
                       COUNT(*) as count
                FROM Product p
                LEFT JOIN (
                    SELECT product_id, price FROM PriceHistory
                    WHERE id IN (SELECT MAX(id) FROM PriceHistory GROUP BY product_id)
                ) ph ON p.id = ph.product_id
                WHERE p.category != "" AND ph.price IS NOT NULL
                GROUP BY p.category
                ORDER BY avg_price DESC
                LIMIT 10
            ''')
            category_ranges = [dict(r) for r in cursor.fetchall()]

            return {
                'categories': categories,
                'price_distribution': price_distribution,
                'top_drops': top_drops,
                'top_increases': top_increases,
                'stock_status': stock_status,
                'category_ranges': category_ranges,
            }

    def _build_histogram(self, prices, num_buckets=8):
        """Build histogram buckets from a list of prices."""
        if not prices:
            return {'labels': [], 'values': []}
        min_p = min(prices)
        max_p = max(prices)
        if min_p == max_p:
            return {'labels': [f'${min_p:.0f}'], 'values': [len(prices)]}
        
        step = (max_p - min_p) / num_buckets
        labels = []
        values = []
        for i in range(num_buckets):
            lo = min_p + i * step
            hi = lo + step
            label = f'${lo:.0f}-${hi:.0f}'
            count = sum(1 for p in prices if lo <= p < hi or (i == num_buckets - 1 and p == hi))
            labels.append(label)
            values.append(count)
        return {'labels': labels, 'values': values}

    def get_categories(self):
        """Get list of unique categories."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT category FROM Product WHERE category != "" ORDER BY category')
            return [row['category'] for row in cursor.fetchall()]

    def delete_all(self):
        """Clear all data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM PriceHistory')
            cursor.execute('DELETE FROM Product')
            conn.commit()

db = DatabaseManager()
