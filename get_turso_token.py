"""Use Turso Platform API to create a database auth token."""
import requests

PLATFORM_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJqdGkiOiIwVHVjWEZ3ekVmR1NUaGFDMTk5U3VnIiwib3JnX2lkIjoxMDAxNzM4NjJ9.S95ReGp3iaIv2SeELq5d16SX5WCinlPqqGovRXlgzfTHGlo8eNUng5SMYc80ZbwU-SlBYoYkxzEwthEgoTGnDA"
ORG_SLUG = "guerillaradio"
DB_NAME  = "lsn2k"

headers = {"Authorization": f"Bearer {PLATFORM_TOKEN}"}

# Get org info
print("Getting org info...")
resp = requests.get("https://api.turso.tech/v1/organizations", headers=headers)
print(f"Status: {resp.status_code}")
if resp.ok:
    orgs = resp.json()
    print(f"Orgs: {orgs}")
else:
    print(f"Error: {resp.text}")

# Create database token
print(f"\nCreating database token for {DB_NAME}...")
resp = requests.post(
    f"https://api.turso.tech/v1/organizations/{ORG_SLUG}/databases/{DB_NAME}/auth/tokens",
    headers=headers,
    json={"expiration": "never", "authorization": "full-access"}
)
print(f"Status: {resp.status_code}")
if resp.ok:
    token = resp.json().get("jwt")
    print(f"\nDatabase token:\n{token}")
else:
    print(f"Error: {resp.text}")
