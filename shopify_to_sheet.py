import time
import schedule
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import SHOP_URL, API_VERSION, ACCESS_TOKEN, CREDENTIALS_FILE

GOOGLE_SHEET_NAME = "cust"
LAST_ROW_TRACKING_CELL = "Z1"  # We'll store last processed ID here

def get_gsheet_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    return gspread.authorize(creds)

def fetch_and_update_latest_customers():
    client = get_gsheet_client()

    try:
        sheet = client.open(GOOGLE_SHEET_NAME).sheet1
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"❌ Spreadsheet '{GOOGLE_SHEET_NAME}' not found or not shared with the service account.")
        return []

    try:
        last_id = int(sheet.acell(LAST_ROW_TRACKING_CELL).value)
    except:
        last_id = 0  # If cell is empty or invalid

    url = f"{SHOP_URL}/admin/api/{API_VERSION}/customers.json?since_id={last_id}&order=id asc"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": ACCESS_TOKEN
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        new_customers = response.json().get("customers", [])
        count = len(new_customers)

        if count == 0:
            print("ℹ️ No new customers found.")
            return []
        else:
            print(f"✅ {count} new customer{'s' if count > 1 else ''} found. Updating sheet...")

            existing_headers = sheet.row_values(1)
            if not existing_headers:
                existing_headers = list(new_customers[0].keys())
                sheet.update("A1", [existing_headers])

            new_rows = []
            for customer in new_customers:
                # Ensure that customer ID is an integer (not a string)
                row = [int(customer.get(col, "")) if col == "id" else str(customer.get(col, "")) for col in existing_headers]
                new_rows.append(row)

            next_row_index = len(sheet.get_all_values()) + 1
            sheet.update(f"A{next_row_index}", new_rows)

            max_id = max(customer["id"] for customer in new_customers)
            sheet.update_acell(LAST_ROW_TRACKING_CELL, str(max_id))

            print("✅ Sheet updated.")
            return new_customers
    else:
        print(f"❌ Shopify API error {response.status_code}: {response.text}")
        return []

    
if __name__ == "__main__":
    print("⏳ Scheduler started. Waiting for the next run...")
    schedule.every(1).minutes.do(lambda: fetch_and_update_latest_customers())
    while True:
        schedule.run_pending()
        time.sleep(1)
