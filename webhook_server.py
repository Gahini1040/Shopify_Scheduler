from flask import Flask, request
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import base64

app = Flask(__name__)

# Decode credentials from environment variable and save temporarily
def get_credentials():
    google_creds = os.getenv("GOOGLE_SHEET_CREDENTIALS")
    if not google_creds:
        raise ValueError("❌ GOOGLE_SHEET_CREDENTIALS environment variable is not set.")
    credentials_data = base64.b64decode(google_creds)
    credentials_path = "credentials.json"
    with open(credentials_path, "wb") as f:
        f.write(credentials_data)
    return credentials_path

# Connect to the Google Sheet
def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_path = get_credentials()
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(creds)
    return client.open("cust").sheet1  # Update with your actual sheet name if different

# Webhook endpoint to handle customer deletion
@app.route('/webhook/customers/delete', methods=['POST'])
def handle_customer_deleted():
    data = request.get_json()
    if not data or "id" not in data:
        print("⚠️ Invalid payload received.")
        return "Invalid payload", 400

    customer_id = str(data["id"])
    print(f"🛠️ Processing delete webhook for customer ID: {customer_id}")

    try:
        sheet = get_sheet()
        records = sheet.get_all_records()

        for i, row in enumerate(records):
            if str(row.get("id")) == customer_id:
                sheet.delete_rows(i + 2)  # i+2 to skip header row
                print(f"✅ Deleted customer ID {customer_id} from Google Sheet.")
                break
        else:
            print(f"⚠️ Customer ID {customer_id} not found in sheet.")

    except Exception as e:
        print(f"❌ Error processing request: {e}")
        return "Internal Server Error", 500

    return '', 200

# Optional root route to test server status
@app.route("/")
def home():
    return "✅ Shopify webhook listener is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
