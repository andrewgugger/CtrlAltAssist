import os.path
import base64
import ollama
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import sys
import requests
from dotenv import load_dotenv

# telergram bot token and telegram user id from .env file
load_dotenv()

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)


def get_or_create_label_id(service, label_name):
    """
    Checks if a label exists, returns its ID.
    If not, creates it and returns the new ID.
    """
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    for label in labels:
        if label['name'].lower() == label_name.lower():
            return label['id']

    # Create label if it doesn't exist
    print(f"Creating label: {label_name}")
    label_object = {'name': label_name}
    created_label = service.users().labels().create(userId='me', body=label_object).execute()
    return created_label['id']


def get_email_content(payload):
    """
    Recursively extracts text from email payload.
    Prioritizes plain text, falls back to parsing snippets if complex.
    """
    body = ""
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data')
                if data:
                    body += base64.urlsafe_b64decode(data).decode()
            elif 'parts' in part:  # Nested parts
                body += get_email_content(part)
    elif 'body' in payload and 'data' in payload['body']:
        data = payload['body']['data']
        body += base64.urlsafe_b64decode(data).decode()

    return body


def analyze_email(subject, sender, body):
    """
    Sends email context to Ollama (gemma3:4b) for classification.
    """
    prompt = f"""
    You are an email assistant. Your job is to classify emails into one of three categories:
    1. 'ec_delete': Promotional, marketing, newsletters, spam, or advertising.
    2. 'ec_save': Important documents, bank statements, receipts, receipts for food, travel reservations, personal correspondence.
    3. 'ec_not_sure': Anything ambiguous or mixed.

    Here is the email:
    Sender: {sender}
    Subject: {subject}
    Body Snippet: {body[:1000]} (truncated)

    Reply ONLY with the category name. Do not explain.
    """

    try:
        #Or use a different model
        response = ollama.chat(model='gemma3:4b', messages=[
            {'role': 'user', 'content': prompt},
        ])
        decision = response['message']['content'].strip()

        # Clean up response to ensure it matches a valid label
        valid_labels = ['ec_delete', 'ec_save', 'ec_not_sure']
        for label in valid_labels:
            if label in decision:
                return label
        return 'ec_not_sure'  # Default fallback
    except Exception as e:
        print(f"Ollama Error: {e}")
        return 'ec_not_sure'


def main():
    service = get_gmail_service()

    # ask user for input on number of emails to iterate
    try:
        if len(sys.argv) > 1:
            max_count = int(sys.argv[1])
        else:
            max_count = 10  # Default if run manually without a number
    except ValueError:
        max_count = 10

    # defining counter variables
    deleted_counter = 0
    saved_counter = 0
    not_sure_counter = 0

    # Ensure labels exist and get their IDs
    label_map = {
        'ec_delete': get_or_create_label_id(service, 'ec_delete'),
        'ec_save': get_or_create_label_id(service, 'ec_save'),
        'ec_not_sure': get_or_create_label_id(service, 'ec_not_sure')
    }

    print("Checking for unread emails...")

    # Get unread messages (max 10 to prevent rate limits during testing)
    results = service.users().messages().list(userId='me', q='is:unread', maxResults=max_count).execute()
    messages = results.get('messages', [])

    if not messages:
        print("No unread messages found.")
        return

    for msg in messages:
        msg_detail = service.users().messages().get(userId='me', id=msg['id']).execute()
        headers = msg_detail['payload']['headers']

        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
        sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown Sender")
        snippet = msg_detail.get('snippet', '')

        # Get full body content (or fallback to snippet)
        full_body = get_email_content(msg_detail['payload']) or snippet

        #print(f"\nProcessing: {subject[:50]}...")

        # Ask Local LLM
        decision_label_name = analyze_email(subject, sender, full_body)
        decision_label_id = label_map[decision_label_name]

        #print(f" -> Decision: {decision_label_name}")
        if decision_label_name =="ec_delete":
            deleted_counter+=1
        elif decision_label_name =="ec_save":
            saved_counter+=1
        else:
            not_sure_counter+=1



        # Apply new label
        service.users().messages().batchModify(
            userId='me',
            body={
                'ids': [msg['id']],
                'addLabelIds': [decision_label_id]
            }
        ).execute()


    # Final summary (this will print to your terminal)
    summary = (f"Successfully sorted {len(messages)} emails:\n"
               f"🗑 Deleted: {deleted_counter}\n"
               f"💾 Saved: {saved_counter}\n"
               f"❓ Not sure: {not_sure_counter}")

    print(summary)

    def send_telegram_update(text):
        token = os.getenv("TELEGRAM_TOKEN")
        chat_id = int(os.getenv("ALLOWED_USER_ID"))
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={text}"
        requests.get(url)

    # Call this at the end of main()
    send_telegram_update(summary)

if __name__ == '__main__':
    main()