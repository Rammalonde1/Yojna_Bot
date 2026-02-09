import os
import pandas as pd
import datetime
from flask import Flask, request, send_from_directory
from twilio.twiml.messaging_response import MessagingResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
import google.generativeai as genai

app = Flask(__name__)

# --- CONFIGURATION ---
DB_FILE = "schemes_database.csv"
PDF_FOLDER = "applications"
GOOGLE_API_KEY = os.environ.get("GEMINI_API_KEY")

# Configure AI (Safely)
model = None
if GOOGLE_API_KEY:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash')
        print("✅ AI Engine Connected")
    except Exception as e:
        print(f"⚠️ AI Connection Failed: {e}")

if not os.path.exists(PDF_FOLDER):
    os.makedirs(PDF_FOLDER)

def get_db():
    """Robust Database Loader that ignores bad lines"""
    if not os.path.exists(DB_FILE): 
        print("❌ DB File Missing")
        return None
    try:
        # on_bad_lines='skip' is the magic fix for your error
        return pd.read_csv(DB_FILE, on_bad_lines='skip')
    except Exception as e:
        print(f"❌ DB Read Error: {e}")
        return None

def generate_professional_pdf(scheme_name, user_phone, scheme_id):
    """Generates an Official-Looking Application Request Form"""
    filename = f"Application_{scheme_id}_{user_phone[-4:]}.pdf"
    filepath = os.path.join(PDF_FOLDER, filename)
    
    try:
        c = canvas.Canvas(filepath, pagesize=letter)
        width, height = letter
        
        # Professional Layout
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.rect(30, 30, width-60, height-60)
        
        c.setFillColor(colors.darkblue)
        c.setFont("Helvetica-Bold", 22)
        c.drawCentredString(width/2, height-80, "APPLICATION RECEIPT")
        
        c.setFont("Helvetica", 10)
        c.drawCentredString(width/2, height-100, "Automated Filing System | Yojna-GPT")
        
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(60, height-150, "APPLICANT DETAILS")
        c.setFont("Helvetica", 12)
        c.drawString(60, height-170, f"Mobile: {user_phone}")
        c.drawString(60, height-190, f"Date: {datetime.datetime.now().strftime('%Y-%m-%d')}")
        
        c.setFont("Helvetica-Bold", 14)
        c.drawString(60, height-230, "SCHEME DETAILS")
        c.setFont("Helvetica", 12)
        c.drawString(60, height-250, f"Scheme: {scheme_name}")
        c.drawString(60, height-270, f"ID: {scheme_id}")
        
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(60, height-400, "Submit this receipt to your nearest nodal agency.")
        c.save()
        return filename
    except Exception as e:
        print(f"PDF Error: {e}")
        return None

@app.route("/", methods=['GET'])
def health_check():
    return "Yojna-GPT is Online and Healthy 🟢"

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
    
    # --- 1. APPLY LOGIC ---
    if incoming_msg.lower().startswith("apply"):
        try:
            scheme_id = int(incoming_msg.split()[1])
            if df is not None:
                row = df[df['id'] == scheme_id]
                if not row.empty:
                    scheme_name = row.iloc[0]['title']
                    pdf_file = generate_professional_pdf(scheme_name, sender, scheme_id)
                    
                    # Create Link
                    link = f"{request.host_url}download/{pdf_file}"
                    
                    msg.body(f"✅ *Application Generated!*\n\n"
                             f"Scheme: {scheme_name}\n"
                             f"📄 *Download:* {link}")
                    return str(resp)
        except:
            msg.body("❌ Error. Send 'Apply' followed by ID (e.g., 'Apply 1').")
            return str(resp)

    # --- 2. SEARCH LOGIC ---
    results = pd.DataFrame()
    if df is not None:
        query = incoming_msg.lower()
        # Safe search that doesn't crash on empty data
        results = df[df['title'].str.lower().str.contains(query, na=False) | 
                     df['industry'].str.lower().str.contains(query, na=False)]

    if not results.empty:
        reply = f"🔍 Found {len(results)} schemes:\n\n"
        for _, row in results.head(3).iterrows():
            reply += (f"📌 *ID {row['id']}: {row['title']}*\n"
                      f"💰 {row['subsidy_amount']}\n"
                      f"👉 Type *Apply {row['id']}* to get form.\n\n")
        msg.body(reply)
        return str(resp)

    # --- 3. AI FALLBACK ---
    if model:
        try:
            prompt = f"Explain the Indian government scheme '{incoming_msg}' in 2 sentences."
            response = model.generate_content(prompt)
            msg.body(f"🤖 *AI Info:*\n{response.text}")
            return str(resp)
        except:
            pass # Fail silently if AI is overloaded

    msg.body("❌ Scheme not found in database. Try 'Textile' or 'Solar'.")
    return str(resp)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
