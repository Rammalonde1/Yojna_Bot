from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import pandas as pd
import os

app = Flask(__name__)

# CONFIG
DB_FILE = "schemes_database.csv"

def load_data():
    """Safely loads the CSV file."""
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    else:
        return pd.DataFrame() # Return empty if file missing

@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    incoming_msg = request.values.get('Body', '').strip().lower()
    sender = request.values.get('From', '')
    
    print(f"Message from {sender}: {incoming_msg}")
    
    resp = MessagingResponse()
    msg = resp.message()
    
    df = load_data()
    
    # GREETING
    if incoming_msg in ['hi', 'hello', 'start', 'menu']:
        msg.body("🇮🇳 *Namaste! Welcome to Yojna-GPT.*\n\n"
                 "I can help you find government subsidies.\n"
                 "Type a keyword to search, for example:\n"
                 "- *Textile*\n"
                 "- *Agriculture*\n"
                 "- *Loan*\n"
                 "- *Solar*")
        return str(resp)
    
    # SEARCH LOGIC
    if df.empty:
        msg.body("⚠️ System Update: Database is currently being built. Please try again later.")
        return str(resp)
    
    # Search in 'title' or 'description' columns
    results = df[df['title'].str.lower().str.contains(incoming_msg) | 
                 df['description'].str.lower().str.contains(incoming_msg)]
    
    if not results.empty:
        # Return top 3 results
        reply = f"✅ I found *{len(results)}* schemes for '{incoming_msg}'. Here are the top 3:\n\n"
        
        for i, row in results.head(3).iterrows():
            title = row['title']
            desc = row['description'].replace(" | ", " ") # Clean up text
            reply += f"🔹 *{title}*\n_{desc[:100]}..._\n\n"
            
        reply += "Reply with another keyword to search again."
        msg.body(reply)
    else:
        msg.body(f"❌ No schemes found for '{incoming_msg}'.\nTry broader terms like 'Business' or 'Loan'.")

    return str(resp)

if __name__ == "__main__":
    # Standard Flask Run
    app.run(port=5000, debug=True)