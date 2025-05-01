from flask import Flask, request, render_template, jsonify, send_from_directory
from agents.manager import get_agent_manager
import json
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

@app.route('/')
def home():
    """Render the main webpage."""
    return render_template("index.html")

@app.route('/about')
def about():
    """Render the about page with API documentation."""
    base_url = os.getenv('BASE_URL', request.host_url.rstrip('/'))
    return render_template("about.html", base_url=base_url)

@app.route('/api/query', methods=['POST'])
async def handle_query():
    """Handle incoming queries to the agent manager."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        manager = get_agent_manager()
        response = await manager.get_response(json.dumps(data))
        
        return jsonify({
            'status': 'success',
            'response': response
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    return send_from_directory('static', filename)

if __name__ == "__main__":
    # Development server
    if os.environ.get('FLASK_ENV') == 'development':
        port = int(os.environ.get('PORT', 8000))
        app.run(host='0.0.0.0', port=port, debug=True)
    else:
        # Production server
        port = int(os.environ.get('PORT', 8000))
        app.run(host='0.0.0.0', port=port)
