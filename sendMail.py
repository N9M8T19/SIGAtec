from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os

# Incluye Gmail + Google Sheets
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/spreadsheets.readonly'
]

def get_credentials():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def send_email():
    creds = get_credentials()
    service = build('gmail', 'v1', credentials=creds)
    from email.mime.text import MIMEText
    import base64

    message = MIMEText("Recibido")
    message['to'] = "nicolas.montefinal@bue.edu.ar"
    message['from'] = "det_7_de5@bue.edu.ar"
    message['subject'] = "Constancia"

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {'raw': raw}

    result = service.users().messages().send(userId='me', body=body).execute()
    print(f"✅ Correo enviado, ID: {result['id']}")

if __name__ == "__main__":
    send_email()
