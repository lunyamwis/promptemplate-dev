from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from .connection import get_creds

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]




def execute_gsheet_formula(cell_range, formula, spreadsheet_id=None):
    creds = get_creds()
    values = None
    try:
        service = build("sheets", "v4", credentials=creds)

        # Specify the formula to write
        value_input_option = 'USER_ENTERED'
        formula_body = {
            'values': [[formula]],
            'range': cell_range,
            'majorDimension': 'ROWS'
        }

        # Call the Sheets API to update the cell with the specified formula
        request = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=cell_range,
            body=formula_body,
            valueInputOption=value_input_option
        )
        response = request.execute()
        values = get_range(cell_range, spreadsheet_id=spreadsheet_id)
        
        print(response)
        print(f"Formula '{formula}' written to cell '{cell_range}'.")
        print(values)

    except HttpError as err:
        print(err)
    return values


def get_range(cell_range, spreadsheet_id=None):
    creds = get_creds()
    values = None
    try:
        service = build("sheets", "v4", credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = (
            sheet.values()
            .get(spreadsheetId=spreadsheet_id, range=cell_range)
            .execute()
        )
        values = result.get("values", [])

        if not values:
            print("No data found.")
            return

        print("Name, Major:")
    except HttpError as err:
        print(err)
    return values
