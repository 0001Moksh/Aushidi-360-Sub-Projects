from flask import Flask, request, render_template, jsonify
from search_engine import SearchEngine
from pymongo import MongoClient
from qdrant_client import QdrantClient
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB Connection
password = "moksh0001"
uri = f"mongodb+srv://moksh:{password}@cluster0.6ty3pnm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
try:
    mongo_client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    mongo_client.server_info()  # Test connection
    logger.info("Connected to MongoDB successfully.")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise
db = mongo_client["medicine_db"]
collection = db["oct_medicines"]

# Qdrant Connection
qdrant_client = None
try:
    qdrant_client = QdrantClient(host="localhost", port=6333)
    # Test Qdrant connection by getting collections
    qdrant_client.get_collections()
    logger.info("Connected to Qdrant successfully.")
except Exception as e:
    logger.error(f"Failed to connect to Qdrant on localhost:6333: {e}")
    logger.info("Please ensure Qdrant is running (e.g., via 'docker run -d -p 6333:6333 qdrant/qdrant'). Exiting.")
    raise

search_engine = SearchEngine(collection, qdrant_client)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/search", methods=["POST"])
def search():
    query = request.form.get("query", "").strip()
    filters = {
        "category": request.form.get("category"),
        "min_price": request.form.get("min_price"),
        "max_price": request.form.get("max_price"),
        "min_quantity": request.form.get("min_quantity"),
        "max_quantity": request.form.get("max_quantity")
    }
    # Clean up filters (remove None or empty values)
    filters = {k: v for k, v in filters.items() if v not in [None, ""]}
    if not query and not any(filters.values()):
        return jsonify({"error": "No query or filters provided"}), 400
    results = search_engine.search(query, filters)
    logger.info(f"Search endpoint returned {len(results)} results for query: {query}, filters: {filters}")
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)