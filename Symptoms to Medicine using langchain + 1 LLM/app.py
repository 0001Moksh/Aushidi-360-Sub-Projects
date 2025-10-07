from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from google import genai
from sentence_transformers import SentenceTransformer
import faiss
import os
import json
import re
import dotenv

app = Flask(__name__)
dotenv.load_dotenv()

client = genai.Client(api_key=os.getenv("GENAI_API_KEY_llm_data"))  

try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parquet_path = os.path.join(current_dir, "medicine_with_embeddings.parquet")
    dfe = pd.read_parquet(parquet_path)
    embeddings = np.array(dfe["embedding"].tolist())
    dim = embeddings.shape[1]
    faiss_index = faiss.IndexFlatL2(dim)
    faiss_index.add(embeddings)
    model = SentenceTransformer("intfloat/multilingual-e5-base")
    print("FAISS index and model initialized successfully.")
except Exception as e:
    print(f"Error initializing data: {e}")
    raise

def collect_data_for_advance(search_query, top_k=7):
    try:
        query_vec = model.encode(search_query, convert_to_numpy=True).reshape(1, -1)
        distances, indices = faiss_index.search(query_vec, k=top_k)
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx != -1:
                results.append({
                    "Batch_ID": dfe.loc[idx, "Batch_ID"],
                    "combined_text": dfe.loc[idx, "combined_text"],
                    "Price_INR": dfe.loc[idx, "Price_INR"],
                    "Quantity_per_pack": dfe.loc[idx, "Quantity_per_pack"],
                })
        print(f"collect_data_for_advance results: {results}")
        return results
    except Exception as e:
        print(f"Error in collect_data_for_advance: {e}")
        return []

def llm(query, vector_result):
    print(f"llm input - query: {query}, vector_result: {vector_result}")
    if not vector_result:
        return json.dumps({"error": "No matching medicines found."})
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"""
You are a medical assistant AI. You will ONLY use the provided medicine records to answer.  
Do not invent new medicines outside the given records.  

Medicine_data: {vector_result}  
Patient Query: {query}  

AI Response:  

1️⃣ Detect the problem from the patient query.  
2️⃣ Select ONLY relevant medicines from the given data that match the detected problem.  
3️⃣ If multiple medicines serve the same purpose, select only one (the most suitable based on dosage, availability, or relevance).  
4️⃣ If no medicine is related to the detected problem, return an empty medicine list and note "No medicine found for this query."  

Return the result STRICTLY in valid JSON format as a list of objects.  
Do not add any text outside the JSON.  

Each object must have these keys:
- "S.no" (serial number starting from 1)
- "Name" (medicine name)
- "Batch No." (batch id from given data)
- "Price_INR" (price in INR)
- "Quantity_per_pack" (pack size)
- "Description" (1-line purpose of medicine)
- "Instructions" (include dosage + doctor-style one-line prescription)

After the JSON array, return a single JSON key-value line for accuracy:  
"Score": "XX%"  

### Example format:
{{"AI Response": "This person has {{detected problem}} issue", 
  "Medicines": [
    {{"S.no": 1, "Name": "Cyclopam", "Batch No.": "BATCH_101", "Price_INR": 25, "Quantity_per_pack": "10 tabs", "Description": "Relieves stomach pain", "Instructions": "Take 1 tab after lunch"}},
    {{"S.no": 2, "Name": "ORS", "Batch No.": "BATCH_102", "Price_INR": 22, "Quantity_per_pack": "21g sachet", "Description": "Rehydrates body", "Instructions": "Dissolve 1 sachet in 1 glass of water, twice daily"}}
  ],
  "Score": "92%",
  "overall instructions": "diet + exercise + lifestyle + trust-building lines, short 2–3 line friendly advice about lifestyle, exercise, prevention tips related to the issue"
}}

### Rules:
- Output must be valid JSON (no markdown, no extra text).  
- Use only medicines from provided records.  
- Descriptions must be 1 simple line.  
- Instructions must include dosage + short doctor notes.  
- Remove any medicine not relevant to the query.  
- If multiple medicines serve the same purpose, pick only one.  
- If no medicine matches the detected problem, return an empty "Medicines" list and note "No medicine found for this query."
"""
)
    # Remove markdown code block if present
    text = response.text
    json_str = re.sub(r'^```json\n|\n```$', '', text, flags=re.MULTILINE).strip()
    try:
        return json_str  # Return cleaned JSON string
    except Exception as e:
        print(f"Error processing LLM response: {e}")
        return json.dumps({"error": "Failed to process AI response."})

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form['query']
    vector_result = collect_data_for_advance(query)
    response = llm(query, vector_result)
    try:
        data = json.loads(response)
        return jsonify(data)
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}, Response: {response}")
        return jsonify({"error": "Invalid response format from AI."})

if __name__ == '__main__':
    app.run(debug=True)