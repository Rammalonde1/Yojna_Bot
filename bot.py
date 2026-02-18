import os
import datetime
import random
import csv
from flask import Flask, request, Response, send_from_directory, send_file
from twilio.twiml.messaging_response import MessagingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
import google.generativeai as genai

app = Flask(__name__)

# --- CONFIGURATION ---
API_KEY = os.environ.get("GOOGLE_API_KEY")
PDF_FOLDER = "applications"
LEADS_FILE = "customer_leads.csv"

if not os.path.exists(PDF_FOLDER): os.makedirs(PDF_FOLDER)

# --- INTERNAL DATABASE ---
SCHEMES_DB = [
    {"id": 101, "title": "PMEGP Loan", "cat": "Biz", "tags": "factory loan business manufacturing", "desc": "Subsidy up to 35%."},
    {"id": 102, "title": "MUDRA (Shishu)", "cat": "Biz", "tags": "small shop startup vendor", "desc": "Loan up to ₹50,000."},
    {"id": 103, "title": "PM Kisan", "cat": "Farm", "tags": "farmer money agri land", "desc": "₹6,000/year income."},
    {"id": 104, "title": "Vidya Lakshmi", "cat": "Edu", "tags": "student loan college", "desc": "Education Loans."},
    {"id": 105, "title": "PM Vishwakarma", "cat": "Skill", "tags": "artisan carpenter tailor", "desc": "Loan @ 5% + Toolkits."},
    {"id": 106, "title": "Lakhpati Didi", "cat": "Women", "tags": "women shg drone", "desc": "Skill training."},
    {"id": 107, "title": "Rooftop Solar", "cat": "Power", "tags": "solar panel electric", "desc": "₹78k Subsidy."},
]

# --- PDF ENGINE ---
def generate_pdf(type, data):
    filename = f"{type}_{data['phone'][-4:]}_{random.randint(100,999)}.pdf"
    filepath = os.path.join(PDF_FOLDER, filename)
    c = canvas.Canvas(filepath, pagesize=letter)
    
    c.setFillColor(colors.darkblue)
    c.rect(0, 700, 612, 100, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(300, 750, "YOJNA SEVA KENDRA")
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 12)
    y = 650
    for k, v in data.items():
        c.drawString(50, y, f"{k}: {v}")
        y -= 25
    c.save()
    return filename

# --- AI ENGINE ---
def get_ai_reply(query):
    if not API_KEY:
        return "🤖 *AI Offline:* I recommend searching for 'Loan', 'Farm', or 'Student'."
    
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        res = model.generate_content(f"Explain Indian Govt Scheme for '{query}' in 2 sentences.")
        return f"🤖 *AI Assistant:*\n{res.text}"
    except:
        return "🤖 *AI Error:* Network busy. Try searching specific keywords."

# --- UNIVERSAL ROUTER ---
@app.route("/", methods=['GET', 'POST'])
def root_handler():
    # HANDLES BOTH BROWSER VISITS AND ACCIDENTAL TWILIO POSTS
    if request.method == 'GET':
        status = "✅ Loaded" if API_KEY else "❌ Missing"
        return f"""
        <h1>Yojna-GPT is Online 🟢</h1>
        <p>API Key Status: <b>{status}</b></p>
        <hr>
        <h3>⚠️ Twilio Setup Instruction:</h3>
        <p>Copy this EXACT link below and paste it into Twilio "When a message comes in":</p>
        <code style="background: #eee; padding: 5px; font-size: 1.2em;">{request.host_url}whatsapp</code>
        """
    elif request.method == 'POST':
        # If user forgot /whatsapp, we handle it here anyway
        return process_whatsapp_message()

@app.route("/whatsapp", methods=['POST'])
def whatsapp_handler():
    return process_whatsapp_message()

# --- MAIN LOGIC ---
def process_whatsapp_message():
    try:
        msg = request.values.get('Body', '').strip().lower()
        sender = request.values.get('From', '').replace("whatsapp:", "")
        print(f"[*] New Message: {msg} from {sender}") # Log to console
        
        resp = MessagingResponse()
        
        # 1. GREETING
        if msg in ['hi', 'hello', 'menu', 'start']:
            resp.message("🇮🇳 *Welcome to Yojna-GPT*\n\n"
                       "🚀 *Menu:*\n"
                       "1️⃣ *@Card* : ID Card\n"
                       "2️⃣ *@Idea <Money>* : Business Idea\n"
                       "3️⃣ *@Calc <Amt>* : Subsidy Calc\n\n"
                       "🔍 *Search:* 'Loan', 'Farm', 'Student'")
            return Response(str(resp), mimetype='application/xml')

        # 2. FEATURES
        if msg.startswith("@card"):
            pdf = generate_pdf("Card", {"phone": sender})
            resp.message(f"💳 *ID Card Ready!*\n⬇️ {request.host_url}download/{pdf}")
            return Response(str(resp), mimetype='application/xml')

        if msg.startswith("@calc"):
            try:
                amt = int(msg.split()[1])
                resp.message(f"💰 *Subsidy:*\nLoan: {amt}\nSubsidy (35%): {int(amt*0.35)}")
            except:
                resp.message("❌ Usage: @Calc <Amount>")
            return Response(str(resp), mimetype='application/xml')

        if msg.startswith("@idea"):
            ai_txt = get_ai_reply(f"Business ideas for budget {msg}")
            resp.message(ai_txt)
            return Response(str(resp), mimetype='application/xml')

        # 3. APPLY
        if msg.startswith("apply"):
            try:
                sid = int(msg.split()[1])
                s = next((x for x in SCHEMES_DB if x['id'] == sid), None)
                if s:
                    pdf = generate_pdf("Receipt", {"Scheme": s['title'], "phone": sender})
                    resp.message(f"✅ *Applied: {s['title']}*\n⬇️ {request.host_url}download/{pdf}")
                else:
                    resp.message("❌ Invalid ID.")
            except:
                resp.message("❌ Usage: Apply <ID>")
            return Response(str(resp), mimetype='application/xml')

        # 4. DATABASE SEARCH
        results = [s for s in SCHEMES_DB if msg in s['tags'] or msg in s['title'].lower()]
        if results:
            txt = f"🔍 *Found {len(results)} Schemes:*\n\n"
            for x in results[:3]:
                txt += f"📌 *{x['title']}* (ID: {x['id']})\n💰 {x['desc']}\n👉 Reply *Apply {x['id']}*\n\n"
            resp.message(txt)
            return Response(str(resp), mimetype='application/xml')

        # 5. AI FALLBACK
        resp.message(get_ai_reply(msg))
        return Response(str(resp), mimetype='application/xml')

    except Exception as e:
        print(f"[ERROR] {e}")
        r = MessagingResponse()
        r.message("⚠️ Server waking up. Please reply 'Hi' again.")
        return Response(str(r), mimetype='application/xml')

@app.route("/download/<filename>")
def download(filename): return send_from_directory(PDF_FOLDER, filename)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
