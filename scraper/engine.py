import threading
import queue
import time
from database.manager import db
from scraper.amazon import AmazonScraper
from scraper.demo import DemoScraper
from config import MAX_PAGES

class ScrapingEngine:
    def __init__(self):
        self._active = False
        self._should_stop = False
        self._thread = None
        self._events = queue.Queue()

    @property
    def is_active(self):
        return self._active

    def stop(self):
        if self._active:
            self._should_stop = True
            return True
        return False

    def stream_events(self):
        while True:
            try:
                event = self._events.get(timeout=30)
                import json
                yield f"data: {json.dumps(event)}\n\n"
                if event['type'] == 'complete' or event['type'] == 'error':
                    break
            except queue.Empty:
                yield f": keepalive\n\n"

    def start_scrape(self, keyword, mode='demo'):
        if self._active:
            return False, "A scrape is already running"

        self._active = True
        self._should_stop = False

        # Clear old events
        while not self._events.empty():
            try: self._events.get_nowait()
            except queue.Empty: break

        self._thread = threading.Thread(
            target=self._run_scrape,
            args=(keyword, mode),
            daemon=True
        )
        self._thread.start()
        return True, None

    def _run_scrape(self, keyword, mode):
        self._events.put({'type': 'start', 'keyword': keyword, 'mode': mode})
        
        try:
            count = 0
            
            def on_product(product):
                if self._should_stop:
                    raise StopIteration("Stopped by user")
                
                # Save to DB
                product_id = db.upsert_product(product)
                product['id'] = product_id
                
                # Emit event
                self._events.put({'type': 'product', 'product': product})
                nonlocal count
                count += 1
                
                # Small delay for demo feel
                time.sleep(0.05)

            if mode == 'amazon':
                scraper = AmazonScraper()
                scraper.scrape(keyword, on_product=on_product)
            else:
                scraper = DemoScraper()
                scraper.scrape(keyword, max_pages=MAX_PAGES, on_product=on_product)
                
            self._events.put({'type': 'complete', 'count': count})
            
        except StopIteration:
            self._events.put({'type': 'complete', 'count': count, 'stopped': True})
        except Exception as e:
            self._events.put({'type': 'error', 'message': str(e)})
        finally:
            self._active = False
            self._should_stop = False

engine = ScrapingEngine()
