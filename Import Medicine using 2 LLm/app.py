# app.py
from flask import Flask, render_template, request, flash, redirect, url_for
import pandas as pd
from pymongo import MongoClient
from werkzeug.utils import secure_filename
import os
import time
from datetime import datetime
import json
import re
from google import genai
import dotenv
import os

app = Flask(__name__)
dotenv.load_dotenv()
app.secret_key = 'super_secret_key'  # For flash messages
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'xlsx'}

# MongoDB Connection (replace with your actual credentials)
password = os.getenv("MONGODB_PASSWORD")
uri = f"mongodb+srv://moksh:{password}@cluster0.6ty3pnm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
db = client["medicine_db"]
collection = db["oct_medicines"]

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Function from your code: llm_data
def llm_data(batch_no, medicine_name, raw_data, max_retries=3):
    # list_category = ['Antipyretics', 'Analgesics', 'Antivirals', 'Antibiotics','Antifungals', 'Antimalarials', 'Anthelmintics', 'Antihistamines','Decongestants', 'Cough Suppressants', 'Expectorants','Bronchodilators', 'Corticosteroids', 'Immunosuppressants','Anticoagulants', 'Antiplatelets', 'Thrombolytics','Antihypertensives', 'Beta-blockers', 'ACE Inhibitors', 'ARBs','Calcium Channel Blockers', 'Diuretics', 'Antiarrhythmics','Antianginals', 'Lipid-lowering Drugs (Statins)','Antidiabetics (Oral)', 'Insulin', 'Antacids','Proton Pump Inhibitors', 'H2 Receptor Blockers', 'Laxatives','Antidiarrheals', 'Anti-emetics', 'Antispasmodics','Antiulcer Agents', 'Antiseptics', 'Vaccines','Hormonal Contraceptives', 'Eye Drops (Lubricant)','Ear Drops (Antifungal)', 'Nasal Sprays (Decongestant)','Nasal Sprays (Steroid)', 'Oral Rehydration Salts','Nutritional Supplements', 'Vitamins', 'Minerals', 'Multivitamins','Herbal Medicines', 'Ayurvedic Medicines', 'Immunotherapy Agents','Biologics', 'DMARDs', 'Disinfectants', 'Thyroid Medications','Corticosteroid Creams', 'Topical Antibiotics','Homeopathic Remedies', 'Antineoplastics (Chemotherapy)','Anti-Gout Medications', 'Anti-Osteoporosis Drugs','Topical Antifungals', 'Ear Drops (Antibiotic)','Anti-thyroid Drugs', 'Eye Drops (Antibiotic)','Ear Drops (Analgesic)', 'Eye Drops (Antihistamine)','Monoclonal Antibodies', 'Muscle Relaxants', 'Antipsychotics','Antidepressants', 'Anxiolytics', 'Mood Stabilizers','Cognitive Enhancers (Nootropics)', 'Stimulants','Smoking Cessation Aids', 'Antivertigo Drugs','Anti-Motion Sickness Drugs', 'Anti-Allergic Drugs','Immunomodulators', 'Blood Products', 'Antidotes','Local Anesthetics', 'General Anesthetics', 'Pain Patches','Combination Drugs (Multi-Action)', 'Analgesics & Pain Relief','Antacids & Acid Reducers', 'Multivitamins & Supplements','Antidiabetics', 'Digestive & Laxatives', 'Anti-Parkinson Drugs','Antiepileptics', 'Hypnotics', 'Sedatives','Weight Loss Medications', 'Antioxidants', 'Chelating Agents','Radiopharmaceuticals', 'Topical Anesthetics','Cough & Cold Medicines','Blood Pressure / Hypertension Medicines','Contrast Agents (Imaging)', 'Antihistamines & Allergy Medicines','Appetite Stimulants', 'Electrolyte Replacements']
    # medi_form = ['Suspension', 'Effervescent Tablet', 'Tablet', 'Injection','Capsule', 'Cream', 'Eye Drops', 'Nasal Spray', 'Syrup', 'Inhaler','Nebulizer Solution', 'Ointment', 'Sublingual Tablet','Nasal Drops', 'Transdermal Patch', 'Enteric Coated Tablet','Powder', 'Chewable Tablet', 'Solution', 'Gel', 'Spray','Oral + Injection', 'Implant + IUD', 'Ear Drops','Powder + Tablet', 'Oral Drops', 'Liquid', 'Intrauterine Device','Juice', 'Mouthwash', 'Ring + Patch', 'Subdermal Implant','Sachet', 'Vaginal Ring', 'Paste', 'Patch', 'Gum', 'Transfusion','Oral', 'Inhalation', 'Oral Suspension', 'Lozenge', 'IV','Gel Patch', 'IV Solution', 'IV Additive', 'Lotion']
    client = genai.Client(api_key=os.getenv("GENAI_API_KEY_llm_data"))

    # default "not_found" JSON
    default_result = {
        "Batch_ID": batch_no,
        "Name of Medicine": medicine_name,
        "Category": "not_found",
        "Medicine Forms": "not_found",
        "Quantity_per_pack": "not_found",
        "Cover Disease": "not_found",
        "Symptoms": "not_found",
        "Side Effects": "not_found",
        "Instructions": "not_found",
        "Description in Hinglish": "not_found"
    }

    for attempt in range(1, max_retries+1):
        try:
            query = f"""
You are a data extraction assistant. Provide ONLY valid JSON output, no Markdown, no extra text, no explanations.

Input:
Batch_no: "{batch_no}"
Medicine name: "{medicine_name}"
Raw text: "{raw_data}"

Task:
Extract the following fields strictly:

- Batch_ID
- Name of Medicine
- Category
- Medicine Forms
- Quantity_per_pack
- Cover Disease
- Symptoms
- Side Effects
- Instructions
- Description in Hinglish

# Output format (strict JSON):
{{
  "Batch_ID": "<batch_id>",
  "Name of Medicine": "<value>",
  "Category": "<select 1 appropriate value>",
  "Medicine Forms": "<select 1 appropriate value>",
  "Quantity_per_pack": "<example: 60 ml Bottle, 10 Tablets, 1 Vial>",
  "Cover Disease": "<3-4 keywords, comma-separated>",
  "Symptoms": "<3-4 keywords, comma-separated>",
  "Side Effects": "<3-4 keywords, comma-separated>",
  "Instructions": "<full phrase>",
  "Description in Hinglish": "<full phrase>"
}}

Rules:
- Do NOT modify Batch_no.
- Provide 3-4 concise keywords for Cover Disease, Symptoms, and Side Effects.
- Provide full phrases for Instructions and Description in Hinglish.
- Choose Category and Medicine Forms appropriately.
- Return ONE JSON object per medicine.
"""
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=query
            )

            result_text = response.text.strip()
            clean_result = re.sub(r"^```json|```$", "", result_text, flags=re.MULTILINE).strip()
            result_json = json.loads(clean_result)
            df = pd.DataFrame([result_json])
            return df
            
        except (json.JSONDecodeError, Exception) as e:
            print(f"Attempt {attempt} failed for {medicine_name} ({batch_no}): {e}")
            time.sleep(1)

    # After 3 attempts, return default
    print(f"All {max_retries} attempts failed for {medicine_name} ({batch_no}), returning default.")
    return pd.DataFrame([default_result])

# Function from your code: google_search_data_provider (adapted for actual Google Generative AI, note: GoogleSearch tool might need adjustment if not exact)
def google_search_data_provider(batch_no, medicine_name):
    from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
    category_list = ['Antipyretics', 'Analgesics', 'Antivirals', 'Antibiotics','Antifungals', 'Antimalarials', 'Anthelmintics', 'Antihistamines','Decongestants', 'Cough Suppressants', 'Expectorants','Bronchodilators', 'Corticosteroids', 'Immunosuppressants','Anticoagulants', 'Antiplatelets', 'Thrombolytics','Antihypertensives', 'Beta-blockers', 'ACE Inhibitors', 'ARBs','Calcium Channel Blockers', 'Diuretics', 'Antiarrhythmics','Antianginals', 'Lipid-lowering Drugs (Statins)','Antidiabetics (Oral)', 'Insulin', 'Antacids','Proton Pump Inhibitors', 'H2 Receptor Blockers', 'Laxatives','Antidiarrheals', 'Anti-emetics', 'Antispasmodics','Antiulcer Agents', 'Antiseptics', 'Vaccines','Hormonal Contraceptives', 'Eye Drops (Lubricant)','Ear Drops (Antifungal)', 'Nasal Sprays (Decongestant)','Nasal Sprays (Steroid)', 'Oral Rehydration Salts','Nutritional Supplements', 'Vitamins', 'Minerals', 'Multivitamins','Herbal Medicines', 'Ayurvedic Medicines', 'Immunotherapy Agents','Biologics', 'DMARDs', 'Disinfectants', 'Thyroid Medications','Corticosteroid Creams', 'Topical Antibiotics','Homeopathic Remedies', 'Antineoplastics (Chemotherapy)','Anti-Gout Medications', 'Anti-Osteoporosis Drugs','Topical Antifungals', 'Ear Drops (Antibiotic)','Anti-thyroid Drugs', 'Eye Drops (Antibiotic)','Ear Drops (Analgesic)', 'Eye Drops (Antihistamine)','Monoclonal Antibodies', 'Muscle Relaxants', 'Antipsychotics','Antidepressants', 'Anxiolytics', 'Mood Stabilizers','Cognitive Enhancers (Nootropics)', 'Stimulants','Smoking Cessation Aids', 'Antivertigo Drugs','Anti-Motion Sickness Drugs', 'Anti-Allergic Drugs','Immunomodulators', 'Blood Products', 'Antidotes','Local Anesthetics', 'General Anesthetics', 'Pain Patches','Combination Drugs (Multi-Action)', 'Analgesics & Pain Relief','Antacids & Acid Reducers', 'Multivitamins & Supplements','Antidiabetics', 'Digestive & Laxatives', 'Anti-Parkinson Drugs','Antiepileptics', 'Hypnotics', 'Sedatives','Weight Loss Medications', 'Antioxidants', 'Chelating Agents','Radiopharmaceuticals', 'Topical Anesthetics','Cough & Cold Medicines','Blood Pressure / Hypertension Medicines','Contrast Agents (Imaging)', 'Antihistamines & Allergy Medicines','Appetite Stimulants', 'Electrolyte Replacements']
    medicine_forms_list = ['Suspension', 'Effervescent Tablet', 'Tablet', 'Injection','Capsule', 'Cream', 'Eye Drops', 'Nasal Spray', 'Syrup', 'Inhaler','Nebulizer Solution', 'Ointment', 'Sublingual Tablet','Nasal Drops', 'Transdermal Patch', 'Enteric Coated Tablet','Powder', 'Chewable Tablet', 'Solution', 'Gel', 'Spray','Oral + Injection', 'Implant + IUD', 'Ear Drops','Powder + Tablet', 'Oral Drops', 'Liquid', 'Intrauterine Device','Juice', 'Mouthwash', 'Ring + Patch', 'Subdermal Implant','Sachet', 'Vaginal Ring', 'Paste', 'Patch', 'Gum', 'Transfusion','Oral', 'Inhalation', 'Oral Suspension', 'Lozenge', 'IV','Gel Patch', 'IV Solution', 'IV Additive', 'Lotion']
    client = genai.Client(api_key= os.getenv("GENAI_API_KEY_google_search"))
    model_id = "gemini-2.0-flash"
    
    google_search_tool = Tool(
        google_search = GoogleSearch()
    )

    response = client.models.generate_content(
        model=model_id,
        contents = f"""
        Medicine Name: {medicine_name}
        
        Please provide the following details:
        
        1. Category: (select from: {category_list})
        2. Medicine Forms: (select from: {medicine_forms_list})
        3. Quantity per Pack: (e.g., 60 ml Bottle, 10 Tablets, 1 Vial, etc.)
        
        Details to collect:
        
        - Cover Disease: (what the medicine helps to treat or recover from)
        - Symptoms: (when this medicine can be taken)
        - Side Effects: (possible adverse effects)
        - Instructions: (how to take/use the medicine correctly)
        - Description in Hinglish: (short, 1-line description)
        """,
            config=GenerateContentConfig(
            tools=[google_search_tool],
            response_modalities=["TEXT"],
        )
    )
    # response = response_cleaner(response)
    response = response.candidates[0].content.parts[0].text
    raw_data = response
    final_result = llm_data(batch_no, medicine_name, raw_data)
    return final_result

# Function from your code: client_data_preparation
def client_data_preparation(client_data):
    all_data = []
    
    start_time = time.time()
    
    for idx, (batch_no, medicine_name) in enumerate(client_data.items(), 1):
        df = google_search_data_provider(batch_no, medicine_name)
        all_data.append(df)
    
    final_df = pd.concat(all_data, ignore_index=True)
    
    return final_df

# Function from your code: validate_client_file
def validate_client_file(client_df):
    required_cols = ["Batch_ID", "Name of Medicine", "Price_INR", "Total_Quantity"]
    
    missing_cols = [col for col in required_cols if col not in client_df.columns]
    
    if not missing_cols:
        return client_df
    else:
        return None

# Function from your code: update_medicine_records (adapted to not print, return messages)
def update_medicine_records(mongo_df, client_df):
    client_df = validate_client_file(client_df)
    if client_df is None:
        return None, None, None, "Missing required columns in uploaded file."
    
    df = mongo_df
    sd = client_df
    
    match_df = pd.merge(df, sd, on=["Batch_ID", "Name of Medicine"], how="inner")
    match_df["Price_INR_x"] = match_df["Price_INR_y"].combine_first(match_df["Price_INR_x"])
    match_df["Total_Quantity_x"] = match_df["Total_Quantity_x"].fillna(0) + match_df["Total_Quantity_y"].fillna(0)
    
    final_df = match_df.drop(columns=["Price_INR_y", "Total_Quantity_y"])
    final_df = final_df.rename(columns={
        "Price_INR_x": "Price_INR",
        "Total_Quantity_x": "Total_Quantity"
    })
    
    unmatched_sd = sd.merge(df, on=["Batch_ID", "Name of Medicine"], how="left", indicator=True)
    unmatched_sd = unmatched_sd[unmatched_sd["_merge"] == "left_only"]
    unmatched_dict = dict(zip(unmatched_sd["Batch_ID"], unmatched_sd["Name of Medicine"]))
    
    updated_df_existing_data = final_df
    new_df = pd.DataFrame()
    if unmatched_dict:
        unmatch_data_prepared = client_data_preparation(unmatched_dict)
        
        new_df = pd.merge(unmatch_data_prepared, sd, on=["Batch_ID", "Name of Medicine"], how="inner")
        new_df = new_df[[
            "Batch_ID", "Name of Medicine", "Category","Medicine Forms","Price_INR",
            "Quantity_per_pack","Total_Quantity","Cover Disease","Symptoms","Side Effects",
            "Instructions","Description in Hinglish"
        ]]
        new_df['status_import'] = 'new item added'
    else:
        new_df = pd.DataFrame(columns=updated_df_existing_data.columns)
    
    updated_df_existing_data['status_import'] = 'updated price & quantity'
    
    combined_df = pd.concat([new_df, updated_df_existing_data], ignore_index=True)
    combined_df['Batch_ID'] = pd.Categorical(combined_df['Batch_ID'], categories=sd['Batch_ID'], ordered=True)
    combined_df = combined_df.sort_values('Batch_ID').reset_index(drop=True)
    
    # # Update MongoDB with combined_df (assuming you want to upsert)
    # for _, row in combined_df.iterrows():
    #     collection.update_one(
    #         {"Batch_ID": row["Batch_ID"], "Name of Medicine": row["Name of Medicine"]},
    #         {"$set": row.to_dict()},
    #         upsert=True
    #     )
    
    return combined_df, updated_df_existing_data, new_df, "Success"

def color_row(row):
    if row['status_import'] == 'new item added':
        # Soft gray-blue tone for new items
        return ['background-color: #2f3640; color: #e0e0e0; font-weight: 500;'] * len(row)
    elif row['status_import'] == 'updated price & quantity':
        # Muted steel gray tone for updated records
        return ['background-color: #3b3b3b; color: #f1f1f1; font-weight: 500;'] * len(row)
    return ['background-color: #1e1e1e; color: #d0d0d0;'] * len(row)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Load client_df from uploaded Excel
            client_df = pd.read_excel(filepath)
            
            # Load mongo_df
            docs = list(collection.find({}))
            mongo_df = pd.DataFrame(docs)
            if '_id' in mongo_df.columns:
                mongo_df = mongo_df.drop(columns=['_id'])
            
            # Process
            combined_df, updated_df, new_df, message = update_medicine_records(mongo_df, client_df)
            if combined_df is None:
                flash(message)
                return redirect(request.url)
            
            # Apply styling
            styled = combined_df.style.apply(color_row, axis=1)
            
            # Convert to HTML for display
            combined_html = styled.to_html(classes='table table-striped', index=False)
            
            flash('File processed successfully!')
            return render_template('index.html', table=combined_html)
    
    return render_template('index.html')

@app.route('/view')
def view():
    docs = list(collection.find({}))
    df = pd.DataFrame(docs)
    if '_id' in df.columns:
        df = df.drop(columns=['_id'])
    html = df.to_html(classes='table table-striped', index=False)
    return render_template('view.html', table=html)

if __name__ == '__main__':
    app.run(debug=True)