import hvac
import sys
import os
import platform
from cryptography.fernet import Fernet


def set_environment_variable(variable_name, value):
    current_os = platform.system()
    if current_os == 'Windows': #if we ever want to work on OS nuanced commands, this func will permit
        os.environ[variable_name] = value
    else:
        os.environ[variable_name] = value

# Encrypt the value using AES encryption
def encrypt_value(key, value):
    cipher_suite = Fernet(key)
    encrypted_value = cipher_suite.encrypt(value.encode()).decode()
    return encrypted_value

# Decrypt the encrypted value using AES decryption
def decrypt_value(key, encrypted_value):
    cipher_suite = Fernet(key)
    decrypted_value = cipher_suite.decrypt(encrypted_value.encode()).decode()
    return decrypted_value

# Generate a random encryption key
def generate_encryption_key():
    return Fernet.generate_key()

# Example usage (this is the variable storing the key)
# For demonstration purposes, we can work on better key storage/retrieval
#encryption_key = generate_encryption_key()
encryption_key = b'kly9j-rEKmtCZEECwshd2n2MDVAgJ6KhOZA1tqVjrmE='

# Encrypt the values
encrypted_token = encrypt_value(encryption_key, 'dev-only-token')
encrypted_path = encrypt_value(encryption_key, 'my-secret-password')
encrypted_ip = encrypt_value(encryption_key, '127.0.0.1')
encrypted_port = encrypt_value(encryption_key, '8200')

# Set the encrypted values as environment variables
set_environment_variable('SET_TOKEN', encrypted_token)
set_environment_variable('SET_PATH', encrypted_path)
set_environment_variable('SET_IP', encrypted_ip)
set_environment_variable('SET_PORT', encrypted_port)

print("Environmental variables setup successfully.")



# Authentication
client = hvac.Client(
    url='http://'+decrypt_value(encryption_key,os.environ.get('SET_IP'))+':'+decrypt_value(encryption_key,os.environ.get('SET_PORT')),
    token=decrypt_value(encryption_key,os.environ.get('SET_TOKEN'))
)

# Writing a secret
create_response = client.secrets.kv.v2.create_or_update_secret(
    path='my-secret-password',
    secret=dict(password=encrypt_value(encryption_key,'!Q#E%T&U8i6y4r2w')) # Again, this is example code of how to set the password in our Vault
)

print('Secret written successfully.')

def proof():
    print("OS Environment:\n")
    print("Proof Encrypted - SET_TOKEN: ",os.environ.get('SET_TOKEN'))
    print("Proof Encrypted - SET_PATH: ",os.environ.get('SET_PATH'))
    print("Proof Encrypted - SET_IP: ",os.environ.get('SET_IP'))
    print("Proof Encrypted - SET_PORT: ",os.environ.get('SET_PORT'))
    print ("\nDecrypt the values:")
    print("Proof Decrypted - SET_TOKEN: ",decrypt_value(encryption_key,os.environ.get('SET_TOKEN')))
    print("Proof Decrypted - SET_PATH: ",decrypt_value(encryption_key,os.environ.get('SET_PATH')))
    print("Proof Decrypted - SET_IP: ",decrypt_value(encryption_key,os.environ.get('SET_IP')))
    print("Proof Decrypted - SET_PORT: ",decrypt_value(encryption_key,os.environ.get('SET_PORT')))