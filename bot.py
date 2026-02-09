import os
import datetime
import random
from flask import Flask, request, send_from_directory
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

# --- INTERNAL DATABASE ---
SCHEMES_DB = [
    {"id": 1, "title": "PMEGP Loan", "cat": "Business", "tags": "factory manufacturing loan business money fund", "desc": "Subsidy up to 35% on loans up to 50 Lakhs."},
    {"id": 2, "title": "MUDRA Loan (Shishu)", "cat": "Business", "tags": "small shop vendor startup store", "desc": "Loan up to ₹50,000 for startups."},
    {"id": 3, "title": "MUDRA Loan (Kishore)", "cat": "Business", "tags": "expansion trade shop business", "desc": "Loan ₹50k to ₹5 Lakhs."},
    {"id": 4, "title": "PM SVANidhi", "cat": "Business", "tags": "hawker thela food truck street vendor", "desc": "₹50k Micro-credit for Street Vendors."},
    {"id": 5, "title": "Startup India Seed Fund", "cat": "Business", "tags": "tech app innovation cloud software internet mobile", "desc": "₹20L Grant for Prototypes."},
    {"id": 6, "title": "PM Kisan Samman Nidhi", "cat": "Farming", "tags": "farmer money agriculture land crop", "desc": "₹6,000/year income support."},
    {"id": 7, "title": "Kisan Credit Card", "cat": "Farming", "tags": "crop loan bank card kcc", "desc": "Low interest crop loans (4%)."},
    {"id": 8, "title": "PM Vishwakarma", "cat": "Skills", "tags": "artisan carpenter tailor blacksmith tools", "desc": "Loan @ 5% + ₹15k Toolkits."},
    {"id": 9, "title": "Lakhpati Didi", "cat": "Women", "tags": "women self help group drone shg", "desc": "Skill training for SHG Women."},
    {"id": 10, "title": "Mahila Samman Savings", "cat": "Women", "tags": "save bank deposit lady woman wife", "desc": "7.5% Interest Savings Certificate."},
    {"id": 11, "title": "Sukanya Samriddhi", "cat": "Women", "tags": "daughter girl education marriage child", "desc": "8.2% Interest for Girl Child."},
    {"id": 12, "title": "PM Awas (Urban)", "cat": "Housing", "tags": "home house flat city loan construction", "desc": "Home Loan Interest Subsidy."},
    {"id": 13, "title": "Ayushman Bharat", "cat": "Health", "tags": "hospital medical treatment sick health", "desc": "₹5 Lakh Free Health Insurance."},
    {"id": 14, "title": "Rooftop Solar", "cat": "Energy", "tags": "solar panel electric bill power sun", "desc": "₹78k Subsidy for Home Solar."},
    {"id": 15, "title": "Vidya Lakshmi Loan", "cat": "Education", "tags": "student college study abroad education", "desc": "Easy Education Loans."}
]

# --- PDF ENGINE ---
def generate_pdf(type, data_dict):
    filename = f"{type}_{data_dict['phone'][-4:]}_{random.randint(100,999)}.pdf"
    filepath = os.path.join(PDF_FOLDER, filename)
    c = canvas.Canvas(filepath, pagesize=letter)
    
    if type == "Card":
        c.setFillColor(colors.aliceblue)
        c.rect(150, 450, 300, 180, fill=1)
        c.setFillColor(colors.darkblue)
        c.rect(150, 580, 300, 50, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(300, 600, "YOJNA-GPT MEMBER")
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 12)
        c.drawString(170, 550, f"Name: User {data_dict['phone'][-4:]}")
        c.drawString(170, 530, f"ID: YJ-{random.randint(1000,9999)}")
        c.drawString(170, 510, f"Status: VERIFIED")
    else:
        c.setFont("Helvetica-Bold", 20)
        c.drawString(100, 700, "SCHEME APPLICATION RECEIPT")
        c.setFont("Helvetica", 12)
        y = 650
        for k, v in data_dict.items():
            c.drawString(100, y, f"{k}: {v}")
            y -= 25
    c.save()
    return filename

# --- FAIL-SAFE AI ---
def get_ai_reply(query):
    # 1. Try Google AI
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        res = model.generate_content(f"Explain Indian Govt Scheme for '{query}' in 2 sentences.")
        return f"🤖 *AI Insight:*\n{res.text}"
    except Exception as e:
        print(f"[LOG] AI Failed: {e}") # This prints to Render Logs
    
    # 2. Smart Backup (If AI fails)
    q = query.lower()
    if "loan" in q or "fund" in q: return "🤖 *AI (Backup):* For funding, check **PMEGP** (ID 1) or **Mudra Loan** (ID 2)."
    if "student" in q: return "🤖 *AI (Backup):* Students can check **Vidya Lakshmi Loans** (ID 15)."
    return "🤖 *AI (Backup):* Network busy. Try searching 'Loan', 'Farm', or 'Solar'."

# --- ROUTER ---
@app.route("/", methods=['GET'])
def health(): return "✅ Yojna-GPT is Live"

@app.route("/download/<filename>")
def download(filename): return send_from_directory(PDF_FOLDER, filename)

@app.route("/whatsapp", methods=['POST'])
def whatsapp():
    try:
        msg = request.values.get('Body', '').strip().lower()
        sender = request.values.get('From', '').replace("whatsapp:", "")
        resp = MessagingResponse()
        reply = resp.message()

        # 1. PRIORITY GREETING (No AI)
        if msg in ['hi', 'hello', 'menu', 'start', 'help', 'hey', 'h']:
            reply.body("🇮🇳 *Welcome to Yojna-GPT Enterprise*\n\n"
                       "🔥 *Menu:*\n"
                       "1️⃣ *@Card* : Membership ID\n"
                       "2️⃣ *@Calc <Amt>* : Subsidy Calc\n"
                       "3️⃣ *@EMI <Amt>* : EMI Calc\n"
                       "4️⃣ *@Docs* : Checklist\n"
                       "5️⃣ *@Share* : Share Bot\n"
                       "6️⃣ *@Bank* : Find Banks\n\n"
                       "🔍 *Search:* 'Textile', 'Solar', 'Loan'")
            return str(resp)

        # 2. FEATURES
        if msg.startswith("@card"):
            pdf = generate_pdf("Card", {"phone": sender})
            reply.body(f"💳 *ID Card Generated!*\n⬇️ {request.host_url}download/{pdf}")
            return str(resp)

        if msg.startswith("@calc"):
            try:
                amt = int(msg.split()[1])
                reply.body(f"💰 *Subsidy Calc*\nLoan: ₹{amt:,}\nSubsidy (35%): ₹{int(amt*0.35):,}\nRepayable: ₹{int(amt*0.65):,}")
            except:
                reply.body("❌ Usage: @Calc <Amount>")
            return str(resp)

        if msg.startswith("@emi"):
            try:
                amt = int(msg.split()[1])
                emi = (amt * 0.0083 * pow(1.0083, 60)) / (pow(1.0083, 60) - 1)
                reply.body(f"🧮 *EMI Calc*\nLoan: ₹{amt:,}\nTenure: 5 Years\nMonthly EMI: ₹{int(emi):,}")
            except:
                reply.body("❌ Usage: @EMI <Amount>")
            return str(resp)
            
        if msg.startswith("@bank"):
            reply.body("🏦 *Nodal Banks:*\n1. SBI\n2. Bank of Baroda\n3. Canara Bank")
            return str(resp)

        if msg.startswith("@docs"):
            reply.body("📂 *Docs Needed:*\n1. Aadhar\n2. PAN\n3. Udyam Reg\n4. Project Report")
            return str(resp)

        if msg.startswith("@share"):
            reply.body("🔗 Share: https://wa.me/14155238886?text=Hi")
            return str(resp)

        # 3. APPLY
        if msg.startswith("apply"):
            try:
                sid = int(msg.split()[1])
                s = next((x for x in SCHEMES_DB if x['id'] == sid), None)
                if s:
                    pdf = generate_pdf("App", {"Scheme": s['title'], "phone": sender})
                    reply.body(f"✅ *Applied for {s['title']}*\n⬇️ {request.host_url}download/{pdf}")
                else:
                    reply.body("❌ Invalid ID.")
            except:
                reply.body("❌ Usage: Apply <ID>")
            return str(resp)

        # 4. DATABASE SEARCH (No AI)
        results = [s for s in SCHEMES_DB if msg in s['tags'] or msg in s['title'].lower()]
        if results:
            txt = f"🔍 *Found {len(results)} Schemes:*\n\n"
            for x in results[:3]:
                txt += f"📌 *{x['title']}* (ID: {x['id']})\n💰 {x['desc']}\n👉 Reply *Apply {x['id']}*\n\n"
            reply.body(txt)
            return str(resp)

        # 5. AI FALLBACK
        reply.body(get_ai_reply(msg))
        return str(resp)

    except Exception as e:
        # Emergency Response
        r = MessagingResponse()
        r.message("⚠️ System updating. Type 'Hi' to restart.")
        return str(r)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
