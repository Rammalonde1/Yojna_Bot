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
from reportlab.lib.units import inch
import google.generativeai as genai

app = Flask(__name__)

# --- CONFIGURATION ---
API_KEY = "AIzaSyCshP-OBAHoq6VLHhtIHRebx0Q0AcUD5Yo"
PDF_FOLDER = "applications"
if not os.path.exists(PDF_FOLDER): os.makedirs(PDF_FOLDER)

# --- INTERNAL DATABASE (EXPANDED) ---
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

# --- PROFESSIONAL PDF ENGINE (Visual Upgrade) ---
def generate_pdf(type, data):
    filename = f"{type}_{data['phone'][-4:]}_{random.randint(100,999)}.pdf"
    filepath = os.path.join(PDF_FOLDER, filename)
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    
    # 1. Decorative Header Bar
    c.setFillColor(colors.darkblue)
    c.rect(0, height-100, width, 100, fill=1, stroke=0)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height-50, "GOVERNMENT OF INDIA SCHEMES")
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, height-75, "DIGITAL FACILITATION CENTER")

    # 2. Watermark
    c.saveState()
    c.translate(width/2, height/2)
    c.rotate(45)
    c.setFillColor(colors.lightgrey)
    c.setFont("Helvetica-Bold", 60)
    c.drawCentredString(0, 0, "OFFICIAL VALID")
    c.restoreState()

    # 3. Content Box
    c.setFillColor(colors.black)
    c.setStrokeColor(colors.black)
    c.setLineWidth(2)
    c.rect(50, height-600, width-100, 450)
    
    if type == "Card":
        c.setFont("Helvetica-Bold", 18)
        c.drawString(70, height-150, "BENEFICIARY IDENTITY CARD")
        c.line(70, height-160, 300, height-160)
        
        c.setFont("Helvetica", 14)
        c.drawString(80, height-200, f"Name: Preferred User")
        c.drawString(80, height-230, f"Mobile: +{data['phone']}")
        c.drawString(80, height-260, f"Card ID: GOI-{random.randint(10000,99999)}")
        c.drawString(80, height-290, f"Issued: {datetime.datetime.now().strftime('%Y-%m-%d')}")
        c.drawString(80, height-320, f"Status: VERIFIED (Tier-1)")
        
        # Simulated Barcode
        c.rect(80, height-450, 200, 50, fill=1) 
        
    else:
        c.setFont("Helvetica-Bold", 18)
        c.drawString(70, height-150, "APPLICATION ACKNOWLEDGMENT")
        c.line(70, height-160, 400, height-160)
        
        c.setFont("Helvetica", 12)
        y = height - 200
        for k, v in data.items():
            c.drawString(80, y, f"{k}:")
            c.drawString(250, y, f"{v}")
            y -= 30
            
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(70, 100, "* Note: This receipt is valid for 30 days. Visit CSC for KYC.")

    c.save()
    return filename

# --- SMART OFFLINE BRAIN (Free AI) ---
# This runs if Google AI fails. It detects intent intelligently.
def smart_offline_ai(query):
    q = query.lower()
    
    # 1. Greetings / Chat
    if any(x in q for x in ["who are you", "what is this", "bot"]):
        return "🤖 *AI:* I am Yojna-GPT, an AI agent designed to help Indians find government schemes and loans."
    
    if any(x in q for x in ["thank", "good", "nice", "great"]):
        return "🤖 *AI:* You're welcome! Let me know if you need to Apply for any scheme."

    if any(x in q for x in ["mad", "stupid", "idiot", "bad"]):
        return "🤖 *AI:* I apologize if I made a mistake. I am still learning. Try searching for 'Loan' or 'Farm'."

    # 2. Scheme Matching
    if "loan" in q or "money" in q or "fund" in q:
        return "🤖 *AI:* Based on your request for funds, I recommend **PMEGP** (ID 1) for large loans or **Mudra** (ID 2) for small business loans."
    
    if "farm" in q or "agri" in q or "crop" in q:
        return "🤖 *AI:* For agriculture, you should check **PM Kisan** (ID 7) for income support or **KCC** (ID 8) for crop loans."
    
    if "student" in q or "study" in q:
        return "🤖 *AI:* Students can apply for **Vidya Lakshmi Loans** (ID 18) or check the **National Scholarship Portal**."
    
    if "women" in q or "lady" in q or "girl" in q:
        return "🤖 *AI:* We have special schemes like **Lakhpati Didi** (ID 12) and **Sukanya Samriddhi** (ID 14) for women."

    # 3. Default Fallback
    return "🤖 *AI:* I found several schemes in our database. You can try searching for categories like: \n- *Business*\n- *Farming*\n- *Education*\n- *Housing*"

# --- AI ENGINE (Hybrid) ---
def get_ai_reply(query):
    # Try Google AI first
    try:
        genai.configure(api_key=API_KEY)
        # Trying gemini-pro as it is the most stable legacy model endpoint
        model = genai.GenerativeModel('gemini-pro')
        res = model.generate_content(f"Explain Indian Govt Scheme for '{query}' in 2 sentences.")
        return f"🤖 *Google AI:*\n{res.text}"
    except Exception as e:
        print(f"Google AI Failed: {e}")
        # Switch to Offline Brain
        return smart_offline_ai(query)

# --- ROUTER ---
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

        # 1. PRIORITY GREETING
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
                    pdf = generate_pdf("App", {"Scheme": s['title'], "phone": sender, "Date": "Today"})
                    resp.message(f"✅ *Applied for {s['title']}*\n⬇️ {request.host_url}download/{pdf}")
                else:
                    resp.message("❌ Invalid ID.")
            except:
                resp.message("❌ Usage: Apply <ID>")
            return Response(str(resp), mimetype='application/xml')

        # 4. DATABASE SEARCH (Exact & Tag Match)
        results = [s for s in SCHEMES_DB if m in s['tags'] or m in s['title'].lower()]
        if results:
            txt = f"🔍 *Found {len(results)} Schemes:*\n\n"
            for x in results[:3]:
                txt += f"📌 *{x['title']}* (ID: {x['id']})\n💰 {x['desc']}\n👉 Reply *Apply {x['id']}*\n\n"
            resp.message(txt)
            return Response(str(resp), mimetype='application/xml')

        # 5. AI FALLBACK (Now with Offline Brain)
        resp.message(get_ai_reply(msg))
        return Response(str(resp), mimetype='application/xml')

    except Exception as e:
        print(f"Error: {e}")
        r = MessagingResponse()
        r.message("⚠️ System updating. Type 'Hi' to restart.")
        return Response(str(r), mimetype='application/xml')

if __name__ == "__main__":
    app.run(port=5000, debug=True)
