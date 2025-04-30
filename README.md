# QueryGuard Analytics

QueryGuard is an AI-powered cryptocurrency analysis platform designed to help both novice and experienced investors navigate the complex crypto market with confidence. The platform combines advanced AI technology with comprehensive market data to provide real-time insights, market sentiment analysis, and trading signals.

## Features

- **Market Analysis**: Real-time price movements, trading volumes, market capitalization, and overall market trends
- **News Analysis**: News articles, social media trends, and public sentiment tracking
- **Signal Analysis**: Technical indicators and trading signals based on price patterns and volume analysis
- **Fraud Detection**: Identification of potential fraud and market anomalies
- **Comprehensive Reports**: Detailed analysis and insights for informed decision making

## Technology Stack

- Python for backend services
- Flask for web server
- Mistral AI for advanced analysis
- Modern frontend with responsive design
- RESTful API architecture

## Project Structure

```
QueryGuard/
├── agents/
│   ├── market_agent.py
│   ├── news_agent.py
│   ├── signal_agent.py
│   ├── chat_agent.py
│   └── manager.py
├── tools/
│   ├── signal/
│   │   ├── messari_signal_assets.py
│   │   └── messari_signal_sentiment.py
│   └── signal_tools.yaml
├── static/
│   └── logo.png
├── templates/
│   ├── index.html
│   └── about.html
├── app.py
├── .env
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/queryguard.git
cd queryguard
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file with:
```
BASE_URL=your_base_url_here
MISTRAL_API_KEY=your_mistral_api_key
MESSARI_API_KEY=your_messari_api_key
```

5. Start the server:
```bash
python app.py
```

The application will be available at `http://localhost:8000`.

## API Documentation

The platform exposes a RESTful API endpoint for analysis:

### Base URL
```
http://localhost:8000
```

### Endpoint
```
POST /api/query
```

### Request Format
```json
{
    "message": "Your analysis query",
    "type": "analysis_type"
}
```

Supported analysis types:
- `market_analysis`: For market trends and price analysis
- `news_analysis`: For news and sentiment analysis
- `signal_analysis`: For trading signals and technical indicators

### Response Format
```json
{
    "status": "success",
    "response": "Analysis results..."
}
```

## Architecture

QueryGuard uses an agent-based architecture with specialized components:

- **Market Agent**: Handles market analysis queries, providing insights into price movements and market trends
- **News Agent**: Processes news and social media data for sentiment analysis
- **Signal Agent**: Generates trading signals and technical indicators
- **Chat Agent**: Manages general queries and interactions
- **Agent Manager**: Coordinates between different agents and handles request routing

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the ISC License - see the LICENSE file for details.

## Acknowledgments

- Thanks to all contributors who have helped shape this project
- Special thanks to the open-source community for their invaluable tools and libraries 