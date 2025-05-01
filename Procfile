web: hypercorn app:app --bind 0.0.0.0:$PORT --worker-class asyncio
worker: gunicorn app:app --bind 0.0.0.0:$PORT --worker-class sync
worker: python app.py