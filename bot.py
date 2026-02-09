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

# --- 1. THE MASSIVE DATABASE (30+ SCHEMES) ---
SCHEMES_DB = [
    # BUSINESS
    {"id": 1, "title": "PMEGP Loan", "cat": "Biz", "tags": "factory loan business manufacturing", "desc": "Subsidy up to 35% on loans (Max 50L)."},
    {"id": 2, "title": "MUDRA (Shishu)", "cat": "Biz", "tags": "small shop startup vendor", "desc": "Loan up to ₹50,000 for new biz."},
    {"id": 3, "title": "MUDRA (Kishore)", "cat": "Biz", "tags": "expansion trade shop", "desc": "Loan ₹50k - ₹5 Lakhs."},
    {"id": 4, "title": "MUDRA (Tarun)", "cat": "Biz", "tags": "big business trade", "desc": "Loan up to ₹10 Lakhs (No Collateral)."},
    {"id": 5, "title": "Stand-Up India", "cat": "Biz", "tags": "sc st women dalit", "desc": "10L-1Cr Loan for SC/ST/Women."},
    {"id": 6, "title": "PM SVANidhi", "cat": "Biz", "tags": "street vendor hawker food truck", "desc": "₹50k Micro-credit for Vendors."},
    {"id": 7, "title": "Startup India Seed", "cat": "Biz", "tags": "tech app cloud software startup", "desc": "₹20L Grant for Prototypes."},
    {"id": 8, "title": "CGTMSE Cover", "cat": "Biz", "tags": "guarantee security collateral", "desc": "Govt guarantee for loans up to ₹5 Cr."},
    
    # FARMING
    {"id": 9, "title": "PM Kisan Samman", "cat": "Farm", "tags": "farmer money agri land", "desc": "₹6,000/year income support."},
    {"id": 10, "title": "Kisan Credit Card", "cat": "Farm", "tags": "crop loan bank card", "desc": "Low interest crop loans (4%)."},
    {"id": 11, "title": "National Livestock", "cat": "Farm", "tags": "goat sheep poultry animal", "desc": "50% Subsidy for animal farming."},
    {"id": 12, "title": "PM Kusum Solar", "cat": "Farm", "tags": "solar pump irrigation water", "desc": "60% Subsidy on Water Pumps."},
    {"id": 13, "title": "Agri Infra Fund", "cat": "Farm", "tags": "warehouse storage cold chain", "desc": "Loans for post-harvest infra."},
    
    # WOMEN & SKILLS
    {"id": 14, "title": "PM Vishwakarma", "cat": "Skill", "tags": "artisan carpenter tailor tools", "desc": "Loan @ 5% + ₹15k Toolkits."},
    {"id": 15, "title": "Lakhpati Didi", "cat": "Women", "tags": "women shg drone training", "desc": "Skill training for SHG Women."},
    {"id": 16, "title": "Mahila Samman", "cat": "Women", "tags": "save deposit bank lady", "desc": "7.5% Interest Savings Certificate."},
    {"id": 17, "title": "Sukanya Samriddhi", "cat": "Women", "tags": "girl daughter child education", "desc": "8.2% Interest for Girl Child."},
    {"id": 18, "title": "DDU-GKY Skills", "cat": "Skill", "tags": "job training placement youth", "desc": "Free Job Training for Rural Youth."},
    
    # HEALTH & HOUSING
    {"id": 19, "title": "PM Awas (Urban)", "cat": "Home", "tags": "home house flat city", "desc": "Home Loan Interest Subsidy."},
    {"id": 20, "title": "PM Awas (Gramin)", "cat": "Home", "tags": "village house construction", "desc": "Cash for building village house."},
    {"id": 21, "title": "Ayushman Bharat", "cat": "Health", "tags": "hospital medical treatment", "desc": "₹5 Lakh Free Health Insurance."},
    {"id": 22, "title": "Rooftop Solar", "cat": "Power", "tags": "solar panel electric bill", "desc": "₹78k Subsidy for Home Solar."},
    {"id": 23, "title": "Ujjwala Yojana", "cat": "Power", "tags": "gas cylinder lpg cooking", "desc": "Free LPG Connection."},
    
    # EDUCATION
    {"id": 24, "title": "Vidya Lakshmi", "cat": "Edu", "tags": "student loan college study", "desc": "Easy Education Loans."},
    {"id": 25, "title": "National Scholarship", "cat": "Edu", "tags": "scholarship merit sc st", "desc": "Scholarships for Merit/SC/ST."},
    {"id": 26, "title": "PM YUVA", "cat": "Edu", "tags": "writer author book", "desc": "Mentorship for young authors."},
    
    # SPECIAL
    {"id": 27, "title": "PLI Textile", "cat": "Ind", "tags": "textile cloth fabric", "desc": "Incentives for Textile Mfg."},
    {"id": 28, "title": "FAME II EV", "cat": "Auto", "tags": "electric vehicle car bike", "desc": "Subsidy on Electric Vehicles."},
    {"id": 29, "title": "ZED Certification", "cat": "Ind", "tags": "quality iso msme", "desc": "Subsidy on Quality Certs."},
    {"id": 30, "title": "PM DIVINE", "cat": "Infra", "tags": "north east development", "desc": "Funds for NE India Infra."}
]

# --- 2. PDF ENGINE (ID CARDS + FORMS) ---
def generate_pdf(type, data_dict):
    filename = f"{type}_{data_dict['phone'][-4:]}_{random.randint(100,999)}.pdf"
    filepath = os.path.join(PDF_FOLDER, filename)
    c = canvas.Canvas(filepath, pagesize=letter)
    
    if type == "Card":
        # ID CARD DESIGN
        c.setStrokeColor(colors.black)
        c.setFillColor(colors.aliceblue)
        c.rect(150, 450, 300, 180, fill=1) 
        c.setFillColor(colors.darkblue)
        c.rect(150, 580, 300, 50, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(300, 600, "YOJNA-GPT MEMBER")
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 12)
        c.drawString(170, 550, f"Member: Preferred User")
        c.drawString(170, 530, f"Mobile: +{data_dict['phone']}")
        c.drawString(170, 510, f"ID: YJ-{random.randint(1000,9999)}")
        c.drawString(170, 490, f"Valid Thru: 2027")
        c.setFont("Helvetica-Oblique", 10)
        c.drawCentredString(300, 460, "Official Beneficiary Card")
    else:
        # APPLICATION FORM DESIGN
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(300, 750, "GOVERNMENT SCHEME RECEIPT")
        c.line(50, 740, 550, 740)
        c.setFont("Helvetica", 12)
        y = 700
        for k, v in data_dict.items():
            c.drawString(100, y, f"{k}:")
            c.drawString(250, y, f"{v}")
            y -= 25
        c.rect(80, y-20, 450, 700-y+40)
        c.drawString(100, 100, "* Take this to your nearest CSC or Bank.")
    
    c.save()
    return filename

# --- 3. AI ENGINE (SAFE MODE) ---
def get_ai_reply(query):
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        res = model.generate_content(f"Explain Indian Govt Scheme '{query}' in 2 sentences.")
        return f"🤖 *AI Insight:*\n{res.text}"
    except:
        # Fallback if AI fails
        q = query.lower()
        if "loan" in q: return "🤖 *AI:* Check **PMEGP** (ID 1) or **Mudra** (ID 2)."
        if "farm" in q: return "🤖 *AI:* Check **PM Kisan** (ID 9)."
        return "🤖 *AI:* Network busy. Try searching keywords like 'Loan' or 'Solar'."

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
        reply = resp.message()
        m = msg.lower()

        # 1. GREETING (Priority)
        if m in ['hi', 'hello', 'menu', 'start', 'help', 'hey']:
            reply.body("🇮🇳 *Namaste! Welcome to Yojna-GPT*\n"
                       "The Ultimate Govt Scheme Super App.\n\n"
                       "🚀 *Feature Menu:*\n"
                       "1️⃣ *@Card* : Get Member ID\n"
                       "2️⃣ *@Idea <Money>* : Business Ideas\n"
                       "3️⃣ *@Calc <Amt>* : Subsidy Check\n"
                       "4️⃣ *@EMI <Amt>* : Loan EMI\n"
                       "5️⃣ *@News* : Govt Updates\n"
                       "6️⃣ *@Bank* : Find Banks\n"
                       "7️⃣ *@Center* : Find CSC\n"
                       "8️⃣ *@Docs* : Checklist\n"
                       "9️⃣ *@Share* : Invite Friends\n\n"
                       "🔍 *Search:* 'Textile', 'Solar', 'Loan'")
            return Response(str(resp), mimetype='application/xml')

        # 2. FEATURE COMMANDS
        if m.startswith("@card"):
            pdf = generate_pdf("Card", {"phone": sender})
            reply.body(f"💳 *ID Card Generated!*\n⬇️ {request.host_url}download/{pdf}")
            return Response(str(resp), mimetype='application/xml')

        if m.startswith("@calc"):
            try:
                amt = int(m.split()[1])
                reply.body(f"💰 *Subsidy Calc*\nLoan: ₹{amt:,}\nSubsidy (35%): ₹{int(amt*0.35):,}\nPayable: ₹{int(amt*0.65):,}")
            except:
                reply.body("❌ Usage: @Calc <Amount>")
            return Response(str(resp), mimetype='application/xml')

        if m.startswith("@emi"):
            try:
                amt = int(m.split()[1])
                emi = (amt * 0.0083 * 1.64) / 0.64 # Simple calculation
                reply.body(f"🧮 *EMI Est (5Yrs):* ₹{int(emi):,}/month")
            except:
                reply.body("❌ Usage: @EMI <Amount>")
            return Response(str(resp), mimetype='application/xml')

        if m.startswith("@idea"):
            ai_txt = get_ai_reply(f"Business ideas for budget {m}")
            reply.body(ai_txt)
            return Response(str(resp), mimetype='application/xml')

        if m.startswith("@news"):
            reply.body("📰 *Latest News:*\n1. PMEGP target doubled.\n2. Solar Subsidy within 7 days.\n3. New Portal for Street Vendors.")
            return Response(str(resp), mimetype='application/xml')

        if m.startswith("@bank"):
            reply.body("🏦 *Nodal Banks:*\n1. SBI (Agri)\n2. Bank of Baroda (MSME)\n3. Canara Bank (Edu)")
            return Response(str(resp), mimetype='application/xml')

        if m.startswith("@docs"):
            reply.body("📂 *Documents:*\nAadhar, PAN, Udyam Reg, Bank Proof, Photo.")
            return Response(str(resp), mimetype='application/xml')

        if m.startswith("@share"):
            reply.body("🔗 *Share Link:* https://wa.me/14155238886?text=Hi")
            return Response(str(resp), mimetype='application/xml')

        # 3. APPLY COMMAND
        if m.startswith("apply"):
            try:
                sid = int(m.split()[1])
                s = next((x for x in SCHEMES_DB if x['id'] == sid), None)
                if s:
                    pdf = generate_pdf("App", {"Scheme": s['title'], "phone": sender, "Date": "Today"})
                    reply.body(f"✅ *Applied for {s['title']}*\n⬇️ {request.host_url}download/{pdf}")
                else:
                    reply.body("❌ Invalid ID.")
            except:
                reply.body("❌ Usage: Apply <ID>")
            return Response(str(resp), mimetype='application/xml')

        # 4. SEARCH ENGINE
        results = []
        for s in SCHEMES_DB:
            if any(t in m for t in s['tags'].split()) or m in s['title'].lower():
                results.append(s)
        
        if results:
            txt = f"🔍 *Found {len(results)} Schemes:*\n\n"
            for x in results[:3]:
                txt += (f"📌 *{x['title']}* (ID: {x['id']})\n"
                        f"💰 {x['desc']}\n"
                        f"👉 Apply: *Apply {x['id']}*\n\n")
            reply.body(txt)
            return Response(str(resp), mimetype='application/xml')

        # 5. AI FALLBACK
        reply.body(get_ai_reply(msg))
        return Response(str(resp), mimetype='application/xml')

    except Exception as e:
        print(f"Error: {e}")
        r = MessagingResponse()
        r.message("⚠️ System updating. Type 'Hi' to restart.")
        return Response(str(r), mimetype='application/xml')

if __name__ == "__main__":
    app.run(port=5000, debug=True)
