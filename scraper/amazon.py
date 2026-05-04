import os
import requests

class AmazonScraper:
    """
    Scrapes real Amazon products using SerpAPI.
    Free tier: 250 searches/month at serpapi.com
    """

    API_URL = "https://serpapi.com/search.json"

    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get('SERPAPI_KEY', '')

    @property
    def is_configured(self):
        return bool(self.api_key)

    def scrape(self, keyword, on_product=None):
        """
        Scrape Amazon products using SerpAPI.
        """
        if not self.is_configured:
            raise ValueError(
                "SerpAPI key not configured. "
                "Sign up at https://serpapi.com/ and set SERPAPI_KEY in the dashboard."
            )

        params = {
            'engine': 'amazon',
            'k': keyword,
            'api_key': self.api_key,
        }

        try:
            resp = requests.get(self.API_URL, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            raise ValueError(f"Request failed: {e}")
        except ValueError:
            raise ValueError("Failed to parse SerpAPI response")

        if 'error' in data:
            raise ValueError(f"SerpAPI error: {data['error']}")

        organic_results = data.get('organic_results', [])
        
        products = []
        for result in organic_results:
            # Parse price
            price_field = result.get('price')
            price_raw = None
            
            if isinstance(price_field, dict):
                price_raw = price_field.get('raw')
            elif isinstance(price_field, str):
                price_raw = price_field
                
            price = None
            if price_raw:
                try:
                    price = float(price_raw.replace('$', '').replace(',', '').strip())
                except ValueError:
                    price = None

            product = {
                'title': result.get('title', ''),
                'url': result.get('link', ''),
                'category': keyword,
                'source': 'amazon',
                'price': price,
                'in_stock': True # SerpAPI amazon engine organic results don't easily indicate OOS, assume True if listed
            }
            
            # Check delivery/stock text if available
            delivery = result.get('delivery', '')
            if isinstance(delivery, list):
                delivery = ' '.join([str(d) for d in delivery])
            elif not isinstance(delivery, str):
                delivery = str(delivery)
                
            if delivery and 'out of stock' in delivery.lower():
                product['in_stock'] = False
                
            if product['title'] and product['url']:
                products.append(product)
                if on_product:
                    on_product(product)

        return products
