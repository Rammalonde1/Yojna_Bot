import os
import pandas as pd
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from thefuzz import process, fuzz # For smart keyword matching
import google.generativeai as genai

app = Flask(__name__)

# --- CONFIGURATION ---
DB_FILE = "schemes_database.csv"
GOOGLE_API_KEY = os.environ.get("GEMINI_API_KEY") # Reads from Render Environment

# Initialize AI if key exists
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')
    print("[SYSTEM] AI Mode Enabled ✅")
else:
    model = None
    print("[SYSTEM] AI Key not found. Running in Fuzzy Match Mode (Robust) ⚠️")

def get_db():
    """Robust Database Loader"""
    try:
        # Check if file exists
        if not os.path.exists(DB_FILE):
            return None
        return pd.read_csv(DB_FILE)
    except Exception as e:
        print(f"[ERROR] DB Load Failed: {e}")
        return None

def fuzzy_search(query, df):
    """
    Searches the database even if spelling is wrong.
    e.g., "txtile" will find "Textile"
    """
    results = []
    
    # 1. Search in Title
    titles = df['title'].tolist()
    # Find top 3 matches with > 60% similarity
    matches = process.extract(query, titles, limit=3, scorer=fuzz.partial_ratio)
    
    for match, score in matches:
        if score > 60:
            row = df[df['title'] == match].iloc[0]
            results.append(row)
            
    # 2. If low results, Search in Industry
    if len(results) < 2:
        industries = df['industry'].unique().tolist()
        ind_matches = process.extract(query, industries, limit=2, scorer=fuzz.partial_ratio)
        for match, score in ind_matches:
            if score > 70:
                rows = df[df['industry'] == match]
                for _, row in rows.iterrows():
                    results.append(row)
    
    # Remove duplicates
    unique_results = []
    seen_ids = set()
    for item in results:
        if item['id'] not in seen_ids:
            unique_results.append(item)
            seen_ids.add(item['id'])
            
    return unique_results[:3] # Return top 3 unique

@app.route("/", methods=['GET'])
def health_check():
    """Browser Check - Call this to wake up the server"""
    return "Yojna-GPT is Live and Ready! 🚀"

@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    incoming_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '')
    print(f"[MSG] From: {sender} | Content: {incoming_msg}")

    resp = MessagingResponse()
    msg = resp.message()
    
    df = get_db()
    
    if df is None or df.empty:
        msg.body("⚠️ System Maintenance: Database is currently reloading. Please try in 2 mins.")
        return str(resp)

    # --- MODE 1: GREETING ---
    if incoming_msg.lower() in ['hi', 'hello', 'start', 'test']:
        msg.body("🇮🇳 *Namaste! Welcome to Yojna-GPT Pro.*\n\n"
                 "I can help you find subsidies for your business.\n"
                 "Try searching for:\n"
                 "👉 *Textile*\n"
                 "👉 *Farming / Solar*\n"
                 "👉 *Business Loan*\n"
                 "👉 *Women*")
        return str(resp)

    # --- MODE 2: AI SEARCH (If API Key is set) ---
    if model:
        try:
            # Create a mini-context for the AI
            context = df.to_string(index=False)
            prompt = f"""
            Act as an expert Indian Government Scheme consultant.
            Here is the database of schemes:
            {context}
            
            User Query: "{incoming_msg}"
            
            Task:
            1. Find the best matching schemes from the list above.
            2. Explain WHY it fits their query in 1 sentence.
            3. Provide the Link.
            4. If nothing matches perfectly, suggest the closest one.
            """
            response = model.generate_content(prompt)
            msg.body(response.text)
            return str(resp)
        except Exception as e:
            print(f"[AI Error] {e}. Falling back to Fuzzy Search.")
            # Fall through to Fuzzy Search if AI fails

    # --- MODE 3: FUZZY SEARCH (Backup / Default) ---
    results = fuzzy_search(incoming_msg, df)
    
    if results:
        reply = f"🔍 I found *{len(results)} matches* for '{incoming_msg}':\n\n"
        for row in results:
            reply += (f"📌 *{row['title']}*\n"
                      f"🏭 {row['industry']}\n"
                      f"💰 *Benefit:* {row['subsidy_amount']}\n"
                      f"🔗 {row['link']}\n\n")
        reply += "Reply with another industry to search again."
        msg.body(reply)
    else:
        msg.body(f"❌ No direct matches for '{incoming_msg}'.\n"
                 "Try keywords like: *Loan, Startup, Manufacturing*")

    return str(resp)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
