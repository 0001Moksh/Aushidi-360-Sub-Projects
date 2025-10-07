import os
import warnings
import re
from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from rapidfuzz import fuzz
from sentence_transformers import SentenceTransformer
import faiss
from functools import lru_cache
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Suppress TensorFlow warnings and oneDNN optimizations
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
warnings.filterwarnings('ignore', category=DeprecationWarning)

app = Flask(__name__)

# ---------------------- Load Data & Embeddings ----------------------
try:
    dfe = pd.read_parquet("embedding files/medicine_with_both_filters.parquet")
    logger.info("Loaded data: %s", dfe.shape)
except Exception as e:
    logger.error("Error loading parquet file: %s", e)
    raise

# Embeddings for vector search
try:
    embeddings1 = np.array(dfe["embedding_filter_2"].tolist(), dtype=np.float32)
    embeddings2 = np.array(dfe["embedding_filter_3"].tolist(), dtype=np.float32)
    logger.info("Loaded embeddings1: %s, embeddings2: %s", embeddings1.shape, embeddings2.shape)
except Exception as e:
    logger.error("Error processing embeddings: %s", e)
    raise

# Build FAISS indexes
try:
    dim1 = embeddings1.shape[1]
    dim2 = embeddings2.shape[1]
    index1 = faiss.IndexFlatL2(dim1)
    index2 = faiss.IndexFlatL2(dim2)
    index1.add(embeddings1)
    index2.add(embeddings2)
    logger.info("FAISS indexes built successfully")
except Exception as e:
    logger.error("Error building FAISS indexes: %s", e)
    raise

# Load multilingual sentence transformer
try:
    model = SentenceTransformer("intfloat/multilingual-e5-base")
    logger.info("Model loaded: %s", model)
except Exception as e:
    logger.error("Error loading model: %s", e)
    raise

# Cache query encoding
@lru_cache(maxsize=100)
def encode_query(query):
    return model.encode(query)

# ---------------------- Search Pipeline ----------------------
def search_medicine_pipeline(search_query, form_filter=None, top_k=100, fuzzy_threshold=50, vector_threshold=0.6):
    try:
        logger.info("Processing query: %s, form_filter: %s", search_query, form_filter or 'None')
        
        # Check if query is a Batch_ID (e.g., starts with "BATCH_")
        if re.match(r'^BATCH_\d+$', search_query, re.IGNORECASE):
            mask = dfe['Batch_ID'].str.contains(search_query, case=False, na=False)
            results = dfe[mask].copy()
            logger.info("Batch_ID search results: %d records", len(results))
            if not results.empty:
                results['relevance_score'] = 1.0  # Exact match, high relevance
                drop_cols = ['embedding_filter_2', 'embedding_filter_3', 'filter_2', 'filter_3']
                results = results.drop(columns=[col for col in drop_cols if col in results.columns])
                return results
            else:
                logger.info("No records found for Batch_ID: %s", search_query)

        # --- Initialize results ---
        results = []

        # --- Fuzzy search (prioritized for exact keyword matches) ---
        exclude_cols = ["Medicine Forms", "Price_INR", "Quantity_per_pack", "Total_Quantity",
                        "embedding_filter_2", "embedding_filter_3", "filter_2", "filter_3"]
        search_cols = [col for col in dfe.columns if col not in exclude_cols]

        def fuzzy_score(row):
            return max([fuzz.partial_ratio(str(val).lower(), search_query.lower()) for val in row])
        
        dfe['fuzzy_score'] = dfe[search_cols].apply(fuzzy_score, axis=1)
        result_fuzzy = dfe[dfe['fuzzy_score'] >= fuzzy_threshold].copy()
        result_fuzzy['search_type'] = 'fuzzy'
        logger.info("Fuzzy search results: %d records", len(result_fuzzy))
        if not result_fuzzy.empty:
            results.append(result_fuzzy)

        # --- Vector search (embeddings1, k=5) ---
        vec = encode_query(search_query)
        svec = np.array(vec, dtype=np.float32).reshape(1, -1)
        distances1, indices1 = index1.search(svec, k=5)
        relevant_indices1 = [i for i, d in zip(indices1[0], distances1[0]) if d <= vector_threshold]
        result_vec1 = dfe.loc[relevant_indices1].copy()
        result_vec1['vector_score'] = [distances1[0][i] for i in range(len(relevant_indices1))]
        result_vec1['search_type'] = 'vector1'
        logger.info("Vector search (embeddings1): %d records", len(result_vec1))
        if not result_vec1.empty:
            results.append(result_vec1)

        # --- Vector search (embeddings2, k=10) ---
        distances2, indices2 = index2.search(svec, k=10)
        relevant_indices2 = [i for i, d in zip(indices2[0], distances2[0]) if d <= vector_threshold]
        result_vec2 = dfe.loc[relevant_indices2].copy()
        result_vec2['vector_score'] = [distances2[0][i] for i in range(len(relevant_indices2))]
        result_vec2['search_type'] = 'vector2'
        logger.info("Vector search (embeddings2): %d records", len(result_vec2))
        if not result_vec2.empty:
            results.append(result_vec2)

        # --- Combine results ---
        if results:
            results = pd.concat(results, ignore_index=True)
            logger.info("Combined results before deduplication: %d records", len(results))
        else:
            logger.info("No results from fuzzy or vector searches")
            return pd.DataFrame()

        # --- Apply form filter if provided ---
        if form_filter and form_filter != '':
            results = results[results['Medicine Forms'] == form_filter].copy()
            logger.info("Results after form filter (%s): %d records", form_filter, len(results))

        # --- Safe deduplication using Batch_ID ---
        if not results.empty:
            results = results.drop_duplicates(subset=['Batch_ID']).reset_index(drop=True)
            logger.info("Results after deduplication: %d records", len(results))

            # --- Normalize scores ---
            results['fuzzy_score_norm'] = results.get('fuzzy_score', 0) / 100
            results['vector_score_norm'] = results.get('vector_score', 0) / results['vector_score'].max() if 'vector_score' in results and results['vector_score'].max() != 0 else 0
            
            # --- Combined relevance with priority to fuzzy matches ---
            results['relevance_score'] = results.apply(
                lambda x: 2.0 if x['search_type'] == 'fuzzy' else (1.0 + x['fuzzy_score_norm'] - x.get('vector_score_norm', 0)), axis=1
            )
            
            # --- Sort by search_type (fuzzy first, then vector1, then vector2) and relevance ---
            results['search_type_rank'] = results['search_type'].map({'fuzzy': 0, 'vector1': 1, 'vector2': 2})
            results = results.sort_values(by=['search_type_rank', 'relevance_score'], ascending=[True, False]).head(top_k)
            logger.info("Final results after sorting and top_k: %d records", len(results))

        # Drop helper columns before returning
        drop_cols = ['fuzzy_score', 'vector_score', 'fuzzy_score_norm', 'vector_score_norm', 
                     'embedding_filter_2', 'embedding_filter_3', 'filter_2', 'filter_3', 'search_type', 'search_type_rank']
        results = results.drop(columns=[col for col in drop_cols if col in results.columns])
        
        return results
    except Exception as e:
        logger.error("Error in search pipeline: %s", e)
        return pd.DataFrame()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    try:
        query = request.args.get('query')
        form_filter = request.args.get('form_filter', '')
        
        if not query:
            logger.warning("No query provided in search request")
            return jsonify({'error': 'No query provided'}), 400
        
        results_df = search_medicine_pipeline(query, form_filter=form_filter)
        
        if results_df.empty:
            logger.info("No results found for query: %s, filter: %s", query, form_filter or 'None')
            return jsonify({'results': [], 'total': 0})
        
        results = results_df.to_dict(orient='records')
        logger.info("Returning %d results for query: %s, filter: %s", len(results), query, form_filter or 'None')
        return jsonify({
            'results': results,
            'total': len(results_df)
        })
    except Exception as e:
        logger.error("Error in search endpoint: %s", e)
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)