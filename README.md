Yojna-GPT: AI Subsidy Automator

1. Installation

Open your terminal/command prompt in this folder and run:

pip install -r requirements.txt


2. Phase 1: Build the Data (The Scraper)

Run the scraper to fetch data from the government website. This script includes pagination logic (it will click "Next" automatically).

python scraper.py


Wait for it to finish. It will create a file named schemes_database.csv.

3. Phase 2: Run the Bot

Start the bot server:

python bot.py


4. Connect to WhatsApp (Tunneling)

While bot.py is running, open a new terminal window and use ngrok to expose your local server to the internet:

ngrok http 5000


Copy the https://....ngrok-free.app URL.

Go to your Twilio Console (Messaging > Sandbox Settings).

Paste the URL into the webhook field and add /whatsapp at the end.

Example: https://a1b2.ngrok-free.app/whatsapp

Send "Hi" to your Twilio WhatsApp number!