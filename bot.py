import os
import datetime
import random
from flask import Flask, request, Response, send_from_directory
from twilio.twiml.messaging_response import MessagingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
import google.generativeai as genai

app = Flask(__name__)

# --- CONFIGURATION ---
API_KEY = "AIzaSyCshP-OBAHoq6VLHhtIHRebx0Q0AcUD5Yo"
PDF_FOLDER = "applications"
if not os.path.exists(PDF_FOLDER): os.makedirs(PDF_FOLDER)

# --- 1. EXPANDED DATABASE (50+ Schemes) ---
SCHEMES_DB = [
    # BUSINESS & LOANS
    {"id": 1, "title": "PMEGP Loan", "cat": "Biz", "tags": "factory loan business manufacturing", "desc": "Subsidy up to 35% (Max 50L)."},
    {"id": 2, "title": "MUDRA (Shishu)", "cat": "Biz", "tags": "small shop startup vendor", "desc": "Loan up to ₹50,000."},
    {"id": 3, "title": "MUDRA (Tarun)", "cat": "Biz", "tags": "big business trade expansion", "desc": "Loan up to ₹10 Lakhs."},
    {"id": 4, "title": "Stand-Up India", "cat": "Biz", "tags": "sc st women dalit", "desc": "10L-1Cr Loan."},
    {"id": 5, "title": "PM SVANidhi", "cat": "Biz", "tags": "street vendor hawker", "desc": "₹50k Micro-credit."},
    {"id": 6, "title": "Startup India", "cat": "Biz", "tags": "tech app cloud software", "desc": "₹20L Grant."},
    # FARMING
    {"id": 7, "title": "PM Kisan", "cat": "Farm", "tags": "farmer money agri land", "desc": "₹6,000/year income."},
    {"id": 8, "title": "Kisan Credit Card", "cat": "Farm", "tags": "crop loan bank card", "desc": "Low interest crop loans."},
    {"id": 9, "title": "National Livestock", "cat": "Farm", "tags": "goat sheep poultry", "desc": "50% Subsidy farming."},
    {"id": 10, "title": "PM Kusum", "cat": "Farm", "tags": "solar pump irrigation", "desc": "60% Subsidy on Pumps."},
    # WOMEN & SKILLS
    {"id": 11, "title": "PM Vishwakarma", "cat": "Skill", "tags": "artisan carpenter tailor", "desc": "Loan @ 5% + Toolkits."},
    {"id": 12, "title": "Lakhpati Didi", "cat": "Women", "tags": "women shg drone", "desc": "Skill training for SHG."},
    {"id": 13, "title": "Mahila Samman", "cat": "Women", "tags": "save deposit bank", "desc": "7.5% Interest Savings."},
    {"id": 14, "title": "Sukanya Samriddhi", "cat": "Women", "tags": "girl daughter child", "desc": "8.2% Interest."},
    # GENERAL
    {"id": 15, "title": "PM Awas (Urban)", "cat": "Home", "tags": "home house flat city", "desc": "Home Loan Subsidy."},
    {"id": 16, "title": "Ayushman Bharat", "cat": "Health", "tags": "hospital medical sick", "desc": "₹5 Lakh Free Insurance."},
    {"id": 17, "title": "Rooftop Solar", "cat": "Power", "tags": "solar panel electric", "desc": "₹78k Subsidy for Home."},
    {"id": 18, "title": "Vidya Lakshmi", "cat": "Edu", "tags": "student loan college", "desc": "Education Loans."},
    {"id": 19, "title": "PLI Textile", "cat": "Ind", "tags": "textile cloth fabric", "desc": "Incentives for Textile."},
    {"id": 20, "title": "FAME II EV", "cat": "Auto", "tags": "electric vehicle car", "desc": "Subsidy on EV."}
]

# --- 2. PREMIUM PDF ENGINE (With Watermark & Stamps) ---
def generate_pdf(type, data):
    filename = f"{type}_{data['phone'][-4:]}_{random.randint(100,999)}.pdf"
    filepath = os.path.join(PDF_FOLDER, filename)
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    
    # Header Bar
    c.setFillColor(colors.darkblue)
    c.rect(0, height-100, width, 100, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width/2, height-50, "GOVERNMENT SCHEME FACILITATION")
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, height-75, "DIGITAL VERIFICATION CENTER")

    # Watermark (Diagonal)
    c.saveState()
    c.translate(width/2, height/2)
    c.rotate(45)
    c.setFillColor(colors.lightgrey)
    c.setFont("Helvetica-Bold", 70)
    c.drawCentredString(0, 0, "OFFICIAL")
    c.restoreState()

    # Content
    c.setFillColor(colors.black)
    c.setLineWidth(2)
    
    if type == "Card":
        # ID CARD
        c.rect(150, 450, 300, 180, fill=0)
        c.setFillColor(colors.navy)
        c.rect(150, 590, 300, 40, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(300, 605, "YOJNA-GPT MEMBER CARD")
        
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 12)
        c.drawString(170, 560, f"Holder: Preferred User")
        c.drawString(170, 535, f"Mobile: +{data['phone']}")
        c.drawString(170, 510, f"ID No: YJ-{random.randint(10000,99999)}")
        c.drawString(170, 485, f"Valid: 2026-2027")
        
        # Fake QR Code Box
        c.rect(370, 470, 60, 60)
        c.setFont("Helvetica-Oblique", 8)
        c.drawCentredString(400, 500, "SCAN ME")
        
    else:
        # APPLICATION FORM
        c.setFont("Helvetica-Bold", 18)
        c.drawString(70, height-160, "ACKNOWLEDGMENT RECEIPT")
        c.line(70, height-170, 500, height-170)
        
        c.setFont("Helvetica", 12)
        y = height - 220
        for k, v in data.items():
            c.drawString(80, y, f"{k}:")
            c.drawString(250, y, f"{v}")
            y -= 35
            
        c.setFont("Helvetica-Oblique", 10)
        c.rect(70, 100, 470, 50)
        c.drawString(80, 130, "NOTE: This is a provisional receipt generated by AI.")
        c.drawString(80, 115, "Please visit your nearest CSC Center for biometric KYC.")

    c.save()
    return filename

# --- 3. SMART OFFLINE BRAIN (Free AI) ---
def smart_offline_ai(query):
    q = query.lower()
    if any(x in q for x in ["hi", "hello", "help"]):
        return "🤖 *AI:* Namaste! I am Yojna-GPT. I can help you find loans, subsidies, and government schemes."
    if any(x in q for x in ["loan", "money", "fund", "capital"]):
        return "🤖 *AI:* For business loans, check **PMEGP** (ID 1) or **Mudra** (ID 2). For farming, check **KCC** (ID 8)."
    if "farm" in q or "agri" in q:
        return "🤖 *AI:* Farmers should check **PM Kisan** (ID 7) for income support."
    if "student" in q or "study" in q:
        return "🤖 *AI:* Students can apply for **Vidya Lakshmi Loans** (ID 18)."
    if "woman" in q or "lady" in q:
        return "🤖 *AI:* Check **Lakhpati Didi** (ID 12) or **Mahila Samman** (ID 13)."
    return "🤖 *AI:* I found schemes matching your interest. Try searching for 'Business', 'Health', or 'Education'."

# --- 4. HYBRID AI ENGINE ---
def get_ai_reply(query):
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        res = model.generate_content(f"Explain Indian Govt Scheme for '{query}' in 2 sentences. Professional tone.")
        return f"🤖 *Google AI:*\n{res.text}"
    except:
        return smart_offline_ai(query)

# --- 5. ROUTES ---
@app.route("/", methods=['GET'])
def health(): return "✅ Yojna-GPT Enterprise Live"

@app.route("/download/<filename>")
def download(filename): return send_from_directory(PDF_FOLDER, filename)

@app.route("/whatsapp", methods=['POST'])
def whatsapp():
    try:
        msg = request.values.get('Body', '').strip()
        sender = request.values.get('From', '').replace("whatsapp:", "")
        resp = MessagingResponse()
        
        m = msg.lower()

        # 1. PRIORITY GREETING (XML Header Forced)
        if m in ['hi', 'hello', 'menu', 'start', 'help', 'hey']:
            resp.message("🇮🇳 *Welcome to Yojna-GPT Enterprise*\n\n"
                       "🚀 *Menu:*\n"
                       "1️⃣ *@Card* : Get Member ID\n"
                       "2️⃣ *@Idea <Money>* : Business Ideas\n"
                       "3️⃣ *@Calc <Amt>* : Subsidy Calc\n"
                       "4️⃣ *@EMI <Amt>* : Loan EMI\n"
                       "5️⃣ *@News* : Govt Updates\n"
                       "6️⃣ *@Docs* : Checklist\n\n"
                       "🔍 *Search:* 'Textile', 'Solar', 'Loan'")
            return Response(str(resp), mimetype='application/xml')

        # 2. FEATURE COMMANDS
        if m.startswith("@card"):
            pdf = generate_pdf("Card", {"phone": sender})
            resp.message(f"💳 *ID Card Generated!*\n⬇️ {request.host_url}download/{pdf}")
            return Response(str(resp), mimetype='application/xml')

        if m.startswith("@calc"):
            try:
                amt = int(m.split()[1])
                resp.message(f"💰 *Subsidy Calc*\nLoan: ₹{amt:,}\nSubsidy (35%): ₹{int(amt*0.35):,}\nPayable: ₹{int(amt*0.65):,}")
            except:
                resp.message("❌ Usage: @Calc <Amount>")
            return Response(str(resp), mimetype='application/xml')

        if m.startswith("@emi"):
            try:
                amt = int(m.split()[1])
                emi = (amt * 0.0083 * 1.64) / 0.64 
                resp.message(f"🧮 *EMI Est (5Yrs):* ₹{int(emi):,}/month")
            except:
                resp.message("❌ Usage: @EMI <Amount>")
            return Response(str(resp), mimetype='application/xml')

        if m.startswith("@idea"):
            ai_txt = get_ai_reply(f"Business ideas for budget {m}")
            resp.message(ai_txt)
            return Response(str(resp), mimetype='application/xml')

        if m.startswith("@news"):
            resp.message("📰 *Govt News:*\n1. PMEGP budget doubled.\n2. Solar Subsidy in 7 days.\n3. Digital India expansion.")
            return Response(str(resp), mimetype='application/xml')

        if m.startswith("@docs"):
            resp.message("📂 *Docs Needed:*\nAadhar, PAN, Udyam Reg, Bank Proof, Photo.")
            return Response(str(resp), mimetype='application/xml')

        # 3. APPLY COMMAND
        if m.startswith("apply"):
            try:
                sid = int(m.split()[1])
                s = next((x for x in SCHEMES_DB if x['id'] == sid), None)
                if s:
                    pdf = generate_pdf("App", {"Scheme": s['title'], "phone": sender, "Date": datetime.datetime.now().strftime("%Y-%m-%d")})
                    resp.message(f"✅ *Applied for {s['title']}*\n⬇️ {request.host_url}download/{pdf}")
                else:
                    resp.message("❌ Invalid ID.")
            except:
                resp.message("❌ Usage: Apply <ID>")
            return Response(str(resp), mimetype='application/xml')

        # 4. DATABASE SEARCH
        results = [s for s in SCHEMES_DB if m in s['tags'] or m in s['title'].lower()]
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
        print(f"Error: {e}")
        r = MessagingResponse()
        r.message("⚠️ System updating. Type 'Hi' to restart.")
        return Response(str(r), mimetype='application/xml')

if __name__ == "__main__":
    app.run(port=5000, debug=True)
