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
API_KEY = "AIzaSyC6G3jfWF-hMyFyIlEU-VtkdQ1gez_lXRM"
PDF_FOLDER = "applications"
if not os.path.exists(PDF_FOLDER): os.makedirs(PDF_FOLDER)

# --- 1. EXPANDED DATABASE (Smart Tags) ---
SCHEMES_DB = [
    # BUSINESS
    {"id": 1, "title": "PMEGP Loan", "tags": "factory loan business manufacturing money fund capital", "desc": "Subsidy up to 35% (Max 50L)."},
    {"id": 2, "title": "MUDRA (Shishu)", "tags": "small shop startup vendor store tea stall", "desc": "Loan up to ₹50,000."},
    {"id": 3, "title": "MUDRA (Tarun)", "tags": "big business trade expansion company", "desc": "Loan up to ₹10 Lakhs."},
    {"id": 4, "title": "Stand-Up India", "tags": "sc st women dalit lady entrepreneur", "desc": "10L-1Cr Loan."},
    {"id": 5, "title": "PM SVANidhi", "tags": "street vendor hawker food truck thela", "desc": "₹50k Micro-credit."},
    {"id": 6, "title": "Startup India", "tags": "tech app cloud software internet new business", "desc": "₹20L Grant for Prototypes."},
    # FARMING
    {"id": 7, "title": "PM Kisan", "tags": "farmer money agri land income", "desc": "₹6,000/year income support."},
    {"id": 8, "title": "Kisan Credit Card", "tags": "crop loan bank card kcc farming", "desc": "Low interest crop loans."},
    {"id": 9, "title": "National Livestock", "tags": "goat sheep poultry animal chicken", "desc": "50% Subsidy farming."},
    {"id": 10, "title": "PM Kusum", "tags": "solar pump irrigation water farm", "desc": "60% Subsidy on Pumps."},
    # WOMEN & SKILLS
    {"id": 11, "title": "PM Vishwakarma", "tags": "artisan carpenter tailor tools blacksmith", "desc": "Loan @ 5% + Toolkits."},
    {"id": 12, "title": "Lakhpati Didi", "tags": "women shg drone training lady", "desc": "Skill training for SHG."},
    {"id": 13, "title": "Mahila Samman", "tags": "save deposit bank interest women", "desc": "7.5% Interest Savings."},
    {"id": 14, "title": "Sukanya Samriddhi", "tags": "girl daughter child education marriage", "desc": "8.2% Interest."},
    # GENERAL
    {"id": 15, "title": "PM Awas (Urban)", "tags": "home house flat city loan construction", "desc": "Home Loan Subsidy."},
    {"id": 16, "title": "Ayushman Bharat", "tags": "hospital medical sick health insurance", "desc": "₹5 Lakh Free Insurance."},
    {"id": 17, "title": "Rooftop Solar", "tags": "solar panel electric bill power sun", "desc": "₹78k Subsidy for Home."},
    {"id": 18, "title": "Vidya Lakshmi", "tags": "student loan college study education degree", "desc": "Education Loans."},
    {"id": 19, "title": "PLI Textile", "tags": "textile cloth fabric cotton wear", "desc": "Incentives for Textile."},
    {"id": 20, "title": "FAME II EV", "tags": "electric vehicle car bike scooter", "desc": "Subsidy on EV."}
]

# --- 2. PREMIUM PDF ENGINE (Official Look) ---
def generate_pdf(type, data):
    filename = f"{type}_{data['phone'][-4:]}_{random.randint(100,999)}.pdf"
    filepath = os.path.join(PDF_FOLDER, filename)
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    
    # 1. Header Bar
    c.setFillColor(colors.darkblue)
    c.rect(0, height-100, width, 100, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width/2, height-50, "GOVERNMENT SCHEME PORTAL")
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, height-75, "DIGITAL VERIFICATION RECEIPT")

    # 2. Watermark
    c.saveState()
    c.translate(width/2, height/2)
    c.rotate(45)
    c.setFillColor(colors.lightgrey)
    c.setFont("Helvetica-Bold", 70)
    c.drawCentredString(0, 0, "APPROVED")
    c.restoreState()

    # 3. Content
    c.setFillColor(colors.black)
    
    if type == "Card":
        # ID CARD
        c.rect(150, 450, 300, 180, fill=0)
        c.setFillColor(colors.navy)
        c.rect(150, 590, 300, 40, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(300, 605, "MEMBERSHIP CARD")
        
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 12)
        c.drawString(170, 560, f"Holder: Preferred User")
        c.drawString(170, 535, f"Mobile: +{data['phone']}")
        c.drawString(170, 510, f"ID No: YJ-{random.randint(10000,99999)}")
        c.drawString(170, 485, f"Valid: 2026-2027")
        
        # QR Code Placeholder
        c.rect(370, 470, 60, 60)
        c.setFont("Helvetica-Oblique", 8)
        c.drawCentredString(400, 500, "DIGITAL ID")
        
    else:
        # APPLICATION FORM
        c.setFont("Helvetica-Bold", 18)
        c.drawString(70, height-160, "APPLICATION SUMMARY")
        c.line(70, height-170, 500, height-170)
        
        c.setFont("Helvetica", 12)
        y = height - 220
        for k, v in data.items():
            c.drawString(80, y, f"{k}:")
            c.drawString(250, y, f"{v}")
            y -= 35
            
        c.setFont("Helvetica-Oblique", 10)
        c.rect(70, 100, 470, 50)
        c.drawString(80, 130, "NOTE: This receipt confirms your preliminary application.")
        c.drawString(80, 115, "Please visit the nearest Common Service Centre (CSC) with documents.")

    c.save()
    return filename

# --- 3. INTELLIGENT AI HANDLER ---
def get_ai_reply(query):
    # Try Google AI first
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        res = model.generate_content(f"Act as a government agent. Explain Indian scheme for '{query}' in 2 sentences. Professional tone.")
        return f"🤖 *AI Assistant:*\n{res.text}"
    except Exception as e:
        print(f"AI Error: {e}")
        # Smart Backup (If AI Fails)
        q = query.lower()
        if "loan" in q: return "🤖 *AI:* For business loans, check **PMEGP** (ID 1) or **Mudra** (ID 2)."
        if "farm" in q: return "🤖 *AI:* For farming, check **PM Kisan** (ID 7) or **KCC** (ID 8)."
        if "education" in q or "student" in q: return "🤖 *AI:* Students should apply for **Vidya Lakshmi Loans** (ID 18)."
        return "🤖 *AI:* I found relevant schemes. Please check the list by typing 'Hi'."

# --- 4. ROUTES ---
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

        # 1. GREETING (Fastest)
        if m in ['hi', 'hello', 'menu', 'start', 'help']:
            resp.message("🇮🇳 *Welcome to Yojna-GPT*\n\n"
                       "🚀 *Commands:*\n"
                       "1️⃣ *@Card* : ID Card\n"
                       "2️⃣ *@Idea <Money>* : Business Idea\n"
                       "3️⃣ *@Calc <Amt>* : Subsidy Calc\n"
                       "4️⃣ *@News* : Updates\n\n"
                       "🔍 *Search:* Type 'Education', 'Farm', 'Loan'\n"
                       "🔢 *Quick View:* Type any ID (e.g. '18')")
            return Response(str(resp), mimetype='application/xml')

        # 2. FEATURE COMMANDS
        if m.startswith("@card"):
            pdf = generate_pdf("Card", {"phone": sender})
            resp.message(f"💳 *ID Card Generated!*\n⬇️ {request.host_url}download/{pdf}")
            return Response(str(resp), mimetype='application/xml')

        if m.startswith("@calc"):
            try:
                amt = int(m.split()[1])
                resp.message(f"💰 *Subsidy Estimator*\nLoan: ₹{amt:,}\nSubsidy (35%): ₹{int(amt*0.35):,}\nPayable: ₹{int(amt*0.65):,}")
            except:
                resp.message("❌ Usage: @Calc <Amount>")
            return Response(str(resp), mimetype='application/xml')

        if m.startswith("@idea"):
            ai_txt = get_ai_reply(f"Business ideas for budget {m}")
            resp.message(ai_txt)
            return Response(str(resp), mimetype='application/xml')

        if m.startswith("@news"):
            resp.message("📰 *Govt News:*\n1. PMEGP budget doubled.\n2. Solar Subsidy in 7 days.\n3. New Portal for Street Vendors.")
            return Response(str(resp), mimetype='application/xml')

        # 3. APPLY COMMAND
        if m.startswith("apply"):
            try:
                sid = int(m.split()[1])
                s = next((x for x in SCHEMES_DB if x['id'] == sid), None)
                if s:
                    pdf = generate_pdf("App", {"Scheme": s['title'], "phone": sender, "Date": datetime.datetime.now().strftime("%Y-%m-%d")})
                    resp.message(f"✅ *Application Submitted!*\nScheme: {s['title']}\n⬇️ {request.host_url}download/{pdf}")
                else:
                    resp.message("❌ Invalid ID.")
            except:
                resp.message("❌ Usage: Apply <ID>")
            return Response(str(resp), mimetype='application/xml')

        # 4. NUMBER SHORTCUT (New Feature!)
        # If user types "1" or "18", show that scheme immediately
        if m.isdigit():
            sid = int(m)
            s = next((x for x in SCHEMES_DB if x['id'] == sid), None)
            if s:
                resp.message(f"📌 *{s['title']}* (ID: {s['id']})\n"
                             f"💰 {s['desc']}\n"
                             f"👉 To Apply: Type *Apply {s['id']}*")
                return Response(str(resp), mimetype='application/xml')

        # 5. DATABASE SEARCH (Expanded Tags)
        results = [s for s in SCHEMES_DB if m in s['tags'] or m in s['title'].lower()]
        if results:
            txt = f"🔍 *Found {len(results)} Schemes:*\n\n"
            for x in results[:3]:
                txt += f"📌 *{x['title']}* (ID: {x['id']})\n💰 {x['desc']}\n👉 Reply *Apply {x['id']}*\n\n"
            resp.message(txt)
            return Response(str(resp), mimetype='application/xml')

        # 6. AI FALLBACK
        resp.message(get_ai_reply(msg))
        return Response(str(resp), mimetype='application/xml')

    except Exception as e:
        print(f"Error: {e}")
        r = MessagingResponse()
        r.message("⚠️ System updating. Type 'Hi' to restart.")
        return Response(str(r), mimetype='application/xml')

if __name__ == "__main__":
    app.run(port=5000, debug=True)
