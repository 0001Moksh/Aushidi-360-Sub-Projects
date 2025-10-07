# from rapidfuzz import fuzz
# import pandas as pd
# import numpy as np
# from sentence_transformers import SentenceTransformer
# import faiss

# # ---------------------- Load Data & Embeddings ----------------------
# dfe = pd.read_parquet("embedding files/medicine_with_both_filters.parquet")

# # Embeddings for vector search
# embeddings1 = np.array(dfe["embedding_filter_2"].tolist())
# print("✅ Loaded embeddings1:", embeddings1.shape)
# embeddings2 = np.array(dfe["embedding_filter_3"].tolist())
# print("✅ Loaded embeddings2:", embeddings2.shape)

# # Build FAISS indexes
# dim1 = embeddings1.shape[1]
# dim2 = embeddings2.shape[1]

# index1 = faiss.IndexFlatL2(dim1)
# index2 = faiss.IndexFlatL2(dim2)

# index1.add(embeddings1)
# index2.add(embeddings2)

# # Load multilingual sentence transformer
# model = SentenceTransformer("intfloat/multilingual-e5-base")
# print(f"Model Load {model}")

# # ---------------------- Search Pipeline ----------------------
# def search_medicine_pipeline(search_query, top_k=15, fuzzy_threshold=60, vector_threshold=0.6):
#     results = pd.DataFrame()
    
#     # --- Fuzzy search ---
#     exclude_cols = ["Medicine Forms", "Price_INR", "Quantity_per_pack", "Total_Quantity",
#                     "embedding_filter_2", "embedding_filter_3"]
#     search_cols = [col for col in dfe.columns if col not in exclude_cols]

#     def fuzzy_score(row):
#         return max([fuzz.partial_ratio(str(val), search_query) for val in row])
    
#     dfe['fuzzy_score'] = dfe[search_cols].apply(fuzzy_score, axis=1)
#     result1 = dfe[dfe['fuzzy_score'] >= fuzzy_threshold].copy()
#     results = pd.concat([results, result1])
    
#     # --- Vector search ---
#     vec = model.encode(search_query)
#     svec = np.array(vec).reshape(1, -1)

#     # Filter 2
#     distances2, indices2 = index1.search(svec, k=10)
#     relevant_indices2 = [i for i, d in zip(indices2[0], distances2[0]) if d >= vector_threshold]
#     result2 = dfe.loc[relevant_indices2].copy()
#     result2['vector_score'] = [distances2[0][i] for i in range(len(relevant_indices2))]
    
#     # Filter 3
#     distances3, indices3 = index2.search(svec, k=10)
#     relevant_indices3 = [i for i, d in zip(indices3[0], distances3[0]) if d >= vector_threshold]
#     result3 = dfe.loc[relevant_indices3].copy()
#     result3['vector_score'] = [distances3[0][i] for i in range(len(relevant_indices3))]
    
#     # --- Combine results ---
#     results = pd.concat([results, result2, result3])
    
#     # --- Safe deduplication using Batch_ID ---
#     results = results.drop_duplicates(subset=['Batch_ID']).reset_index(drop=True)
    
#     # --- Normalize scores ---
#     if 'fuzzy_score' in results:
#         results['fuzzy_score_norm'] = results['fuzzy_score'] / 100
#     else:
#         results['fuzzy_score_norm'] = 0
#     if 'vector_score' in results:
#         results['vector_score_norm'] = results['vector_score'] / results['vector_score'].max()
#     else:
#         results['vector_score_norm'] = 0
    
#     # --- Combined relevance ---
#     results['relevance_score'] = results['fuzzy_score_norm'] + results['vector_score_norm']
    
#     # --- Sort by combined score and limit top_k ---
#     results = results.sort_values(by='relevance_score', ascending=False).head(top_k)
    
#     print(f"✅ Showing top {len(results)} most relevant medicines for || {search_query}")
    
#     # Drop helper columns before returning
#     return results.drop(columns=['fuzzy_score', 'vector_score', 'fuzzy_score_norm', 'vector_score_norm'])
