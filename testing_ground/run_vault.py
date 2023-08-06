import hvac
import sys

import subprocess
import threading

def create_vault_client():
    # Set up the Vault client
    client = hvac.Client(url='http://localhost:8200')

    # Authenticate with the root token provided when starting the Vault server in development mode
    client.token = 'dev-only-token' #THIS IS FOR TESTING ONLY, WE WOULD NEVER STORE HERE

    return client

def run_command():
    command = "vault server -dev -dev-root-token-id=dev-only-token" #TESTING ONLY THIS IS IN DEV MODE
    subprocess.run(command, shell=True)
    
def get_stored_token(client):
    # Set up the Vault client
    #client = hvac.Client(url='http://localhost:8200')

    # Authenticate with the root token provided when starting the Vault server in development mode
    #client.token = 'dev-only-token'

    # Retrieve the stored token from Vault
    try:
        response = client.secrets.kv.v2.read_secret_version(
            path='secret/data/token',raise_on_deleted_version=True
        )
        stored_token = response['data']['data']['value']
        return stored_token
    except Exception as e:
        print("Error retrieving stored token:", e)
        return None
        
run_command()        
# Set up the Vault client
client = hvac.Client(url='http://localhost:8200')

# Authenticate with the root token provided when starting the Vault server in development mode
client.token = 'dev-only-token'

# Store the token in the Vault
create_response = client.secrets.kv.v2.create_or_update_secret(
    path='secret/data/token',
    secret=dict(value=b'!Q#E%T&U8i6y4r2w')
)
        
        

# For testing
"""
stored_token = get_stored_token()
if stored_token:
    print("Stored token:", stored_token)
else:
    print("Failed to retrieve stored token")
"""
