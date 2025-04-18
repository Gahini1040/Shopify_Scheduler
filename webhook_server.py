from flask import Flask, request
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import base64

app = Flask(__name__)

# Function to get the credentials from environment variables (assuming base64-encoded)
def get_credentials():
    google_creds = os.getenv("GOOGLE_SHEET_CREDENTIALS")  # Environment variable with base64 credentials
    credentials_data = base64.b64decode(google_creds)  # Decode the base64 string
    credentials_path = "/tmp/credentials.json"  # Store temporarily in /tmp folder
    with open(credentials_path, "wb") as f:
        f.write(credentials_data)
    return credentials_path

# Function to connect to Google Sheets
def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_path = get_credentials()  # Get credentials file path
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(creds)
    return client.open("cust").sheet1  # Replace with actual sheet name

# Webhook route for customer deletion
@app.route('/webhook/customers/delete', methods=['POST'])
def handle_customer_deleted():
    data = request.get_json()  # Get the incoming JSON payload from Shopify
    customer_id = str(data.get("id"))  # Get the customer ID from the payload

    if customer_id:
        sheet = get_sheet()  # Get the Google Sheet
        records = sheet.get_all_records()  # Fetch all records from the sheet
        for i, row in enumerate(records):
            if str(row.get("id")) == customer_id:  # Match the customer ID
                sheet.delete_rows(i + 2)  # +2 accounts for 0-index and header row
                print(f"✅ Deleted customer ID {customer_id} from sheet.")
                break
        else:
            print(f"⚠️ Customer ID {customer_id} not found in sheet.")
    return '', 200  # Respond with a 200 status to acknowledge receipt

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
