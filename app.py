from flask import Flask, request, render_template, jsonify, send_from_directory
from agents.manager import get_agent_manager
import json
import asyncio
import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler

# Load environment variables
load_dotenv()

# Configure logging
def setup_logging(app):
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = RotatingFileHandler('logs/queryguard.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    
    app.logger.setLevel(logging.INFO)
    app.logger.info('QueryGuard startup')

# Create Flask app
app = Flask(__name__)

# Development specific configurations
if os.getenv('FLASK_ENV') == 'development':
    app.config.update(
        DEBUG=True,
        TEMPLATES_AUTO_RELOAD=True,
        SEND_FILE_MAX_AGE_DEFAULT=0
    )
    # Enable CORS for development
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

# Setup logging
setup_logging(app)

@app.route('/')
def home():
    """Render the main webpage."""
    app.logger.info('Home page accessed')
    return render_template("index.html")

@app.route('/about')
def about():
    """Render the about page with API documentation."""
    app.logger.info('About page accessed')
    base_url = os.getenv('BASE_URL', 'http://localhost:8000')
    return render_template("about.html", base_url=base_url)

@app.route('/api/query', methods=['POST'])
async def handle_query():
    """Handle incoming queries to the agent manager."""
    try:
        data = request.get_json()
        if not data:
            app.logger.warning('Empty request received')
            return jsonify({'error': 'No data provided'}), 400

        app.logger.info(f'Processing query: {data.get("message", "No message")}')
        manager = get_agent_manager()
        response = await manager.get_response(json.dumps(data))
        
        app.logger.info('Query processed successfully')
        return jsonify({
            'status': 'success',
            'response': response
        })
    except Exception as e:
        app.logger.error(f'Error processing query: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    return send_from_directory('static', filename)

if __name__ == "__main__":
    # Development server settings
    port = int(os.getenv('PORT', 8000))
    host = os.getenv('HOST', '0.0.0.0')
    debug = os.getenv('FLASK_ENV') == 'development'
    
    app.logger.info(f'Starting QueryGuard server on {host}:{port} (debug={debug})')
    app.run(host=host, port=port, debug=debug)
