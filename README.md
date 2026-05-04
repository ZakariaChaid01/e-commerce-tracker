# E-Commerce Price Tracker

A full-stack web application designed to track, analyze, and export e-commerce product pricing data in real time. This system automates the extraction of pricing information from e-commerce platforms and provides a professional dashboard for data visualization, statistical analysis, and inventory monitoring.

## Features

* **Real-time Price Scraping:** Extract live product pricing and stock availability.
* **Historical Data Tracking:** Maintain a persistent history of price fluctuations over time.
* **Dual Scraping Modes:**
  * **Amazon Mode:** Live data extraction via the SerpAPI Amazon search engine.
  * **Demo Mode:** A simulated sandbox environment scraping a demonstration bookstore, featuring randomized price drops and stock changes for testing purposes.
* **Comprehensive Analytics Dashboard:**
  * Price distribution histograms.
  * Stock status overview.
  * Category breakdown and average price comparisons.
  * Automated detection of top price drops and increases.
* **Server-Sent Events (SSE):** Live feed of the scraping process streaming directly to the client without polling.
* **Data Export:** Export tracked data and analysis reports into CSV, JSON, and formatted Excel formats.

## Architecture

The project follows a standard client-server architecture with an SQLite database for persistence.

* **Backend:** Python and Flask. Handles routing, REST API endpoints, streaming data, and business logic.
* **Scraping Engine:** Modular python scrapers leveraging `requests` and `BeautifulSoup4`. Managed by a threaded background engine to prevent blocking the main server loop.
* **Database:** SQLite managed via a custom `DatabaseManager` class. Utilizes separate tables for Products and Price History to enable time-series analysis.
* **Frontend:** Vanilla HTML, CSS, and JavaScript. Designed with a dark theme and glassmorphism styling. Charting is handled by `Chart.js`.

## Prerequisites

* Python 3.10+
* A SerpAPI account and API key (if you intend to use the live Amazon scraping mode).

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/ZakariaChaid01/e-commerce-tracker.git
   cd e-commerce-tracker
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the Flask server:
   ```bash
   python app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://localhost:5001
   ```

3. To begin tracking, enter a keyword (e.g., "Laptops"), select your target source mode, and click "Track Items". The system will begin processing products and updating the dashboard in real time.

## Configuration

The application settings can be found in `config.py`. 

* **Port:** The default application port is `5001`.
* **Database Path:** Local data is saved by default in `data/tracker.db`.
* **Export Directory:** Generated reports are saved to `data/exports`.

To utilize the Amazon tracking mode, you must provide a SerpAPI key. This can be configured directly through the Settings modal in the web dashboard or by setting the `SERPAPI_KEY` environment variable on your system.

## API Documentation

The application exposes several REST endpoints for external integrations:

* `POST /api/scrape` - Initialize a scraping job (requires `keyword` and `mode` JSON payload).
* `GET /api/scrape/stream` - Subscribe to the Server-Sent Events stream for live scraping updates.
* `POST /api/scrape/stop` - Terminate the currently active scraping job.
* `GET /api/products` - Retrieve paginated product data, filterable by search query or category.
* `GET /api/products/<id>/history` - Retrieve the complete time-series price history for a specific product ID.
* `GET /api/stats` - Retrieve aggregate statistics (total products, out of stock, price drops, etc.).
* `GET /api/analytics` - Retrieve structured data for dashboard charts (distributions, movers, etc.).
* `GET /api/export/<format>` - Generate and download an export file (`csv`, `json`, or `excel`).
* `DELETE /api/clear` - Wipe all products and history from the database.
