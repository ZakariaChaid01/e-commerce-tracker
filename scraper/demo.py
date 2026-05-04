import requests
from bs4 import BeautifulSoup
import random

class DemoScraper:
    """
    Scrapes books.toscrape.com to provide a sandbox e-commerce environment.
    Simulates price changes and out-of-stock events randomly on subsequent runs.
    """

    BASE_URL = "http://books.toscrape.com/catalogue/category/books_1/page-{page}.html"

    def scrape(self, keyword='Books', max_pages=2, on_product=None):
        """Scrape books from the sandbox site."""
        products = []
        
        for page in range(1, max_pages + 1):
            url = self.BASE_URL.format(page=page)
            try:
                resp = requests.get(url, timeout=10)
                if resp.status_code == 404:
                    if page == 1:
                        # Fallback to index if pagination fails on page 1
                        url = "http://books.toscrape.com/catalogue/category/books_1/index.html"
                        resp = requests.get(url, timeout=10)
                    else:
                        break
                resp.raise_for_status()
            except requests.RequestException:
                break

            soup = BeautifulSoup(resp.text, 'html.parser')
            articles = soup.find_all('article', class_='product_pod')
            
            if not articles:
                break
                
            for article in articles:
                title = article.h3.a['title']
                link = "http://books.toscrape.com/catalogue/" + article.h3.a['href'].replace('../../../', '')
                
                # Extract price
                price_str = article.find('p', class_='price_color').text
                try:
                    # Strip the currency symbol
                    price = float(price_str.replace('£', '').replace('Â', '').strip())
                except ValueError:
                    price = 0.0

                # Determine stock
                instock_elem = article.find('p', class_='instock availability')
                in_stock = 'in stock' in instock_elem.text.lower() if instock_elem else False

                # Simulate dynamic changes (price drops, out of stock) for demo purposes
                # 15% chance to drop price by up to 20%
                if random.random() < 0.15:
                    price = round(price * (1.0 - random.uniform(0.05, 0.20)), 2)
                # 5% chance to be out of stock
                if random.random() < 0.05:
                    in_stock = False

                product = {
                    'title': title,
                    'url': link,
                    'category': keyword,
                    'source': 'demo',
                    'price': price,
                    'in_stock': in_stock
                }
                
                products.append(product)
                if on_product:
                    on_product(product)
                    
        return products
