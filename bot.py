import os
import pandas as pd
from flask import Flask, request, send_from_directory
from twilio.twiml.messaging_response import MessagingResponse
from thefuzz import process, fuzz
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

app = Flask(__name__)

# --- CONFIGURATION ---
DB_FILE = "schemes_database.csv"
PDF_FOLDER = "applications"

# Create folder for PDFs if not exists
if not os.path.exists(PDF_FOLDER):
    os.makedirs(PDF_FOLDER)

def get_db():
    if not os.path.exists(DB_FILE): return None
    return pd.read_csv(DB_FILE)

def generate_pdf(scheme_name, user_phone):
    """Generates a simple Application Receipt PDF"""
    filename = f"Application_{user_phone[-4:]}.pdf"
    filepath = os.path.join(PDF_FOLDER, filename)
    
    c = canvas.Canvas(filepath, pagesize=letter)
    c.drawString(100, 750, "GOVERNMENT SCHEME APPLICATION RECEIPT")
    c.drawString(100, 730, "------------------------------------------------------")
    c.drawString(100, 700, f"Applicant Mobile: {user_phone}")
    c.drawString(100, 680, f"Scheme Applied For: {scheme_name}")
    c.drawString(100, 660, "Status: Application Generated via Yojna-GPT")
    c.drawString(100, 640, "Date: 2026-02-07")
    c.drawString(100, 600, "Please submit this receipt to your local nodal officer.")
    c.save()
    
    return filename

@app.route("/", methods=['GET'])
def health_check():
    return "Yojna-GPT is Running 🚀"

# --- NEW: ROUTE TO SERVE PDFS ---
@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(PDF_FOLDER, filename)

@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    incoming_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '').replace("whatsapp:", "")
    
    resp = MessagingResponse()
    msg = resp.message()
    df = get_db()

    # --- APPLY LOGIC ---
    if incoming_msg.lower().startswith("apply"):
        try:
            # User sent "Apply 1" -> We get ID 1
            scheme_id = int(incoming_msg.split(" ")[1])
            
            # Find scheme name
            row = df[df['id'] == scheme_id].iloc[0]
            scheme_name = row['title']
            
            # Generate PDF
            pdf_filename = generate_pdf(scheme_name, sender)
            
            # Create Public Link (Dynamic based on where it is hosted)
            # In production, use your actual Render URL
            host_url = request.host_url # e.g., https://yojna-gpt.onrender.com/
            pdf_link = f"{host_url}download/{pdf_filename}"
            
            msg.body(f"✅ *Application Generated!*\n\n"
                     f"We have created your application for *{scheme_name}*.\n"
                     f"Download it here: {pdf_link}")
            return str(resp)
            
        except Exception as e:
            msg.body("❌ Error. To apply, send 'Apply' followed by the ID number. Example: *Apply 1*")
            return str(resp)

    # --- SEARCH LOGIC (Same as before) ---
    results = []
    # Simple search for demo purposes (Fuzzy logic is heavier, keeping it simple for stability)
    if df is not None:
        results = df[df['title'].str.lower().str.contains(incoming_msg.lower()) | 
                     df['industry'].str.lower().str.contains(incoming_msg.lower())]

    if not results.empty:
        reply = f"🔍 Found {len(results)} schemes:\n\n"
        for _, row in results.iterrows():
            reply += (f"📌 *ID {row['id']}: {row['title']}*\n"
                      f"💰 {row['subsidy_amount']}\n"
                      f"👉 To Apply, reply: *Apply {row['id']}*\n\n")
        msg.body(reply)
    else:
        msg.body("👋 Welcome! Search by industry (e.g., 'Textile') or type 'Hi' for menu.")

    return str(resp)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
