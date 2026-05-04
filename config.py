"""Configuration settings for the E-Commerce Price Tracker."""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data', 'tracker.db')
EXPORT_DIR = os.path.join(BASE_DIR, 'data', 'exports')

# Flask Settings
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-price-tracker')
DEBUG = True
HOST = '0.0.0.0'
PORT = 5001  # Using port 5001 to avoid conflicts with previous projects

# Scraping Settings
MAX_PAGES = 5
DEMO_URL = 'http://books.toscrape.com/catalogue/category/books_1/index.html'
