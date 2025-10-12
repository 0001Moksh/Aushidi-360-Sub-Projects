# Medicine Assistant AI

A Flask-based web application that provides intelligent medicine recommendations using semantic search and AI-generated guidance. The app uses **FAISS**, **Sentence Transformers**, and **Google GenAI** to retrieve relevant medicine information and generate doctor-style advice based on patient queries.

---

## Features

- Search medicines by natural language queries.
- Retrieve the most relevant medicines using semantic similarity with **FAISS** and **Sentence Transformers**.
- Generate AI-powered responses with dosage instructions and one-line descriptions.
- Strictly uses the provided medicine database—does not invent medicines.
- Returns results in **valid JSON format** for frontend rendering.

---

## Tech Stack

- **Backend:** Python, Flask  
- **Semantic Search:** [Sentence Transformers](https://www.sbert.net/), FAISS  
- **AI Generation:** Google GenAI (`gemini-2.5-flash`)  
- **Data Storage:** Parquet files (`medicine_with_embeddings.parquet`)  
- **Environment Variables:** `python-dotenv`

---

## Installation

1. Clone the repository:

```bash
git clone <repo-url>
cd <repo-folder>
````

2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate      # Linux / macOS
venv\Scripts\activate         # Windows
```

3. Install required packages:

```bash
pip install -r requirements.txt
```

4. Set up environment variables:

Create a `.env` file in the project root:

```env
GENAI_API_KEY_llm_data=<your_genai_api_key>
```

5. Add your `medicine_with_embeddings.parquet` file in the root directory.

---

## Usage

1. Start the Flask server:

```bash
python app.py
```

2. Open your browser and navigate to:

```
http://127.0.0.1:5000/
```

3. Enter a query in the search box, and get AI-powered medicine recommendations.

---

## Project Structure

```
├── app.py                   # Main Flask application
├── templates/
│   └── index.html           # Frontend HTML page
├── medicine_with_embeddings.parquet  # Medicine dataset with embeddings
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
└── README.md
```

---

## How It Works

1. **Data Loading:**
   Loads a Parquet file containing medicine records and their embeddings.

2. **Semantic Search:**
   Uses `SentenceTransformer` to encode queries and searches nearest medicine embeddings using FAISS.

3. **AI Response Generation:**

   * Sends top-k search results to Google GenAI (`gemini-2.5-flash`) with the user query.
   * Generates JSON output with medicine details, dosage instructions, and one-line description.

4. **Frontend:**
   Simple Flask template (`index.html`) displays the AI-recommended medicines to the user.

---

## Example Output

```json
{
  "AI Response": "This person has stomach pain issue",
  "Medicines": [
    {
      "S.no": 1,
      "Name": "Cyclopam",
      "Batch No.": "BATCH_101",
      "Price_INR": 25,
      "Quantity_per_pack": "10 tabs",
      "Description": "Relieves stomach pain",
      "Instructions": "Take 1 tab after lunch"
    },
    {
      "S.no": 2,
      "Name": "ORS",
      "Batch No.": "BATCH_102",
      "Price_INR": 22,
      "Quantity_per_pack": "21g sachet",
      "Description": "Rehydrates body",
      "Instructions": "Dissolve 1 sachet in 1 glass of water, twice daily"
    }
  ],
  "Score": "92%",
  "overall instructions": "Maintain diet, exercise, and hydration; short friendly advice on prevention."
}
```

---

## Notes

* Ensure your `.env` contains a valid **GenAI API key**.
* The medicine list is **strictly restricted** to the records in `medicine_with_embeddings.parquet`.
* FAISS and embedding model initialization may take a few seconds on the first run.
* Debug mode is enabled by default for development; disable it in production.

---
