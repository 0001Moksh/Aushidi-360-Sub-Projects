# Advanced Medicine Search AI

A Flask-based web application for intelligent medicine retrieval using **fuzzy matching** and **vector search** with sentence embeddings. The app supports multi-filter searches, relevance scoring, and prioritizes exact and semantic matches.

---

## Features

- **Batch ID search:** Direct lookup for specific medicine batches.
- **Fuzzy search:** Handles typos and partial matches in medicine names or attributes.
- **Vector search:** Uses **SentenceTransformer embeddings** and **FAISS** for semantic similarity search.
- **Multi-filter support:** Filter medicines by forms (e.g., tablets, syrup).
- **Relevance scoring:** Combines fuzzy and vector similarity scores to rank results.
- **Top-k results:** Returns a limited number of the most relevant medicines.
- **Detailed logging:** Tracks search processing for debugging and analytics.

---

## Tech Stack

- **Backend:** Python, Flask  
- **Semantic Search:** [Sentence Transformers](https://www.sbert.net/), FAISS  
- **Fuzzy Search:** [RapidFuzz](https://github.com/maxbachmann/RapidFuzz)  
- **Data Storage:** Parquet files (`medicine_with_both_filters.parquet`)  
- **Caching:** `functools.lru_cache` for query embeddings  
- **Logging:** Python `logging` module  

---

## Installation

1. Clone the repository:

```bash
git clone <repo-url>
cd <repo-folder>
````

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate      # Linux / macOS
venv\Scripts\activate         # Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Place the medicine Parquet file:

```
embedding files/medicine_with_both_filters.parquet
```

---

## Usage

1. Start the Flask server:

```bash
python app.py
```

2. Access the web app in your browser:

```
http://127.0.0.1:5000/
```

3. Perform a medicine search:

* **Query:** Any medicine name, description, or Batch_ID (e.g., `BATCH_101`)
* **Form filter (optional):** Select medicine form (e.g., Tablet, Syrup)

4. Results are returned in JSON format, including:

* Medicine details (`Batch_ID`, `Price_INR`, `Quantity_per_pack`, etc.)
* Relevance scores

---

## Search Pipeline Overview

1. **Batch ID Detection:**
   If the query matches `BATCH_<number>`, returns exact records.

2. **Fuzzy Search:**
   Uses `RapidFuzz` to score partial matches across medicine attributes.

3. **Vector Search:**

   * Encodes the query using `SentenceTransformer`
   * Searches two separate FAISS indexes (`embedding_filter_2` and `embedding_filter_3`)
   * Filters by distance threshold for relevance

4. **Combination & Ranking:**

   * Combines fuzzy and vector results
   * Deduplicates by `Batch_ID`
   * Normalizes scores and ranks results prioritizing fuzzy matches
   * Supports optional form filtering

---

## Example API Request

```
GET /search?query=Paracetamol&form_filter=Tablet
```

**Response:**

```json
{
  "results": [
    {
      "Batch_ID": "BATCH_101",
      "Name": "Paracetamol",
      "Price_INR": 25,
      "Quantity_per_pack": "10 tabs",
      "Medicine Forms": "Tablet",
      "relevance_score": 2.0
    },
    ...
  ],
  "total": 5
}
```

---

## Logging

* Logs are output to console with timestamps and severity levels.
* Key logs include data loading, query processing, search type results, and final top-k results.

---

## Notes

* Ensure `medicine_with_both_filters.parquet` exists in the specified path.
* The app suppresses TensorFlow warnings for cleaner logs.
* Debug mode is enabled by default; disable it in production.
* FAISS indexes are memory-resident; large datasets may require more RAM.

---
