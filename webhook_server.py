from flask import Flask, request
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import CREDENTIALS_FILE, GOOGLE_SHEET_NAME

app = Flask(__name__)

def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    return client.open(GOOGLE_SHEET_NAME).sheet1

@app.route('/webhook/customers/delete', methods=['POST'])
def handle_customer_deleted():
    data = request.get_json()
    customer_id = str(data.get("id"))

    if customer_id:
        sheet = get_sheet()
        records = sheet.get_all_records()
        for i, row in enumerate(records):
            if str(row.get("id")) == customer_id:
                sheet.delete_rows(i + 2)  # +2 accounts for 0-index and header
                print(f"✅ Deleted customer ID {customer_id} from sheet.")
                break
        else:
            print(f"⚠️ Customer ID {customer_id} not found in sheet.")
    return '', 200

if __name__ == "__main__":
    app.run(port=5000)
