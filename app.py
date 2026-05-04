import os
from flask import Flask, render_template, request, jsonify, Response
from database.manager import db
from scraper.engine import engine
from export.exporter import export_csv_buffer, export_json_buffer, export_excel_buffer
from config import SECRET_KEY, DEBUG, HOST, PORT, EXPORT_DIR

app = Flask(__name__)
app.secret_key = SECRET_KEY

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scrape', methods=['POST'])
def start_scrape():
    data = request.get_json()
    keyword = data.get('keyword', '').strip()
    mode = data.get('mode', 'demo')

    if not keyword:
        return jsonify({'error': 'Keyword/Category is required'}), 400

    started, error = engine.start_scrape(keyword, mode=mode)
    if error:
        return jsonify({'error': error}), 409

    return jsonify({'message': f'Tracking started for "{keyword}" ({mode})'})

@app.route('/api/scrape/stream')
def scrape_stream():
    def generate():
        try:
            for event in engine.stream_events():
                yield event
        except GeneratorExit:
            pass
    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive'})

@app.route('/api/scrape/stop', methods=['POST'])
def stop_scrape():
    stopped = engine.stop()
    return jsonify({'stopped': stopped})

@app.route('/api/products')
def get_products():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    search = request.args.get('search')
    category = request.args.get('category')

    result = db.get_products(page=page, per_page=per_page, search=search, category=category)
    return jsonify(result)

@app.route('/api/products/<int:product_id>/history')
def get_product_history(product_id):
    history = db.get_product_history(product_id)
    return jsonify({'history': history})

@app.route('/api/stats')
def get_stats():
    stats = db.get_stats()
    categories = db.get_categories()
    return jsonify({'stats': stats, 'categories': categories})

@app.route('/api/clear', methods=['DELETE'])
def clear_data():
    db.delete_all()
    return jsonify({'cleared': True})

@app.route('/api/config', methods=['GET'])
def get_config():
    serpapi_key = os.environ.get('SERPAPI_KEY', '')
    return jsonify({
        'serpapi_configured': bool(serpapi_key),
        'serpapi_key_preview': f"{serpapi_key[:6]}...{serpapi_key[-4:]}" if len(serpapi_key) > 10 else '',
    })

@app.route('/api/config/serpapi', methods=['POST'])
def set_serpapi_key():
    data = request.get_json()
    key = data.get('key', '').strip()
    if not key:
        return jsonify({'error': 'API key is required'}), 400
    os.environ['SERPAPI_KEY'] = key
    return jsonify({
        'message': 'SerpAPI key configured successfully',
        'preview': f"{key[:6]}...{key[-4:]}"
    })

@app.route('/api/analytics')
def get_analytics():
    analytics = db.get_analytics()
    return jsonify(analytics)

@app.route('/api/export/<fmt>')
def export_data(fmt):
    search = request.args.get('search')
    category = request.args.get('category')
    
    products = db.get_all_products_for_export(search=search, category=category)
    if not products:
        return jsonify({'error': 'No products to export'}), 404

    if fmt == 'csv':
        content = export_csv_buffer(products)
        return Response(content, mimetype='text/csv',
                        headers={'Content-Disposition': 'attachment; filename=tracker_export.csv'})
    elif fmt == 'json':
        content = export_json_buffer(products)
        return Response(content, mimetype='application/json',
                        headers={'Content-Disposition': 'attachment; filename=tracker_export.json'})
    elif fmt == 'excel':
        data = export_excel_buffer(products)
        return Response(data, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        headers={'Content-Disposition': 'attachment; filename=tracker_export.xlsx'})
    else:
        return jsonify({'error': f'Unknown format: {fmt}'}), 400

if __name__ == '__main__':
    os.makedirs(EXPORT_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(db.get_connection().execute('PRAGMA database_list').fetchall()[0][2] or 'data'), exist_ok=True)
    app.run(host=HOST, port=PORT, debug=DEBUG, threaded=True)
