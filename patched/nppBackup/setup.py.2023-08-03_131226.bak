# This not secure, and is purely for testing purposes

# Make sure you install vault for your environment


import subprocess
import threading

def run_command():
    command = "vault server -dev -dev-root-token-id=dev-only-token"
    subprocess.run(command, shell=True)

# Create a separate thread for running the command
thread = threading.Thread(target=run_command)

# Start the thread
thread.start()

# code keeps running

# We are not just storing as an environmental variable but also encrypted with AES

import os
import platform
from cryptography.fernet import Fernet

# OS specific set
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
encryption_key = generate_encryption_key()

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

# Copyright (c) HashiCorp, Inc.
# SPDX-License-Identifier: MPL-2.0
# modified by Group 15 for ISSEM Lab 4

import hvac
import sys

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