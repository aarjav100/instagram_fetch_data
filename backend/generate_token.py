import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/spreadsheets",
]

cred_file = "credentials.json" if os.path.exists("credentials.json") else "credential.json"
flow = InstalledAppFlow.from_client_secrets_file(cred_file, SCOPES)

print("\nStarting local authentication server...")
print("Please keep this terminal window open while you approve in your browser!\n")
creds = flow.run_local_server(port=0)

with open("token.json", "w") as f:
    f.write(creds.to_json())

print("\nSUCCESS: token.json created successfully!")

