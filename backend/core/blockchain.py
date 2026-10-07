import hashlib
import json
import os
from web3 import Web3

# Connect to Ganache local blockchain
GANACHE_URL = "http://127.0.0.1:7545"
w3 = Web3(Web3.HTTPProvider(GANACHE_URL))

# Path to Truffle compiled artifact JSON file
# After running `truffle migrate`, Truffle saves the contract details here:
ARTIFACT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'build', 'contracts', 'EduLocker.json')

def load_contract():
    if not os.path.exists(ARTIFACT_PATH):
        raise FileNotFoundError(f"Truffle artifact not found at {ARTIFACT_PATH}. Did you run 'truffle migrate'?")
    
    with open(ARTIFACT_PATH, 'r') as f:
        artifact = json.load(f)
    
    # Get network ID dynamically or default to the latest deployed network
    network_id = str(w3.eth.chain_id)
    networks = artifact.get('networks', {})
    
    # Fallback to any available network key if exact chain ID isn't matched
    if network_id not in networks and len(networks) > 0:
        network_id = list(networks.keys())[0]
        
    if network_id not in networks:
        raise Exception("Smart contract not deployed on the current network in Ganache.")
        
    contract_address = networks[network_id]['address']
    contract_abi = artifact['abi']
    
    return w3.eth.contract(address=contract_address, abi=contract_abi)

def generate_sha256(file_obj):
    """Generates a SHA-256 cryptographic hash of an uploaded file."""
    sha256_hash = hashlib.sha256()
    for chunk in file_obj.chunks():
        sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def register_hash_on_chain(doc_hash_hex, student_id, doc_title):
    """Commits the document hash to the blockchain via Web3.py"""
    if not w3.is_connected():
        raise Exception("Failed to connect to Ganache blockchain node.")
        
    contract = load_contract()
    
    # Use the first account in Ganache as the administrator/issuer sender
    admin_account = w3.eth.accounts[0]
    
    # Convert hex string to bytes32 format required by Solidity
    bytes32_hash = bytes.fromhex(doc_hash_hex)
    
    # Send transaction to smart contract
    tx_hash = contract.functions.registerDocument(
        bytes32_hash,
        student_id,
        doc_title
    ).transact({'from': admin_account})
    
    # Wait for the blockchain transaction receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt

def verify_hash_on_chain(doc_hash_hex):
    """Verifies if the document hash exists on the blockchain and returns record details."""
    if not w3.is_connected():
        raise Exception("Failed to connect to Ganache blockchain node.")
        
    contract = load_contract()
    bytes32_hash = bytes.fromhex(doc_hash_hex)
    
    # Call the read-only 'verifyDocument' function from Solidity
    exists, student_id, doc_title, issuer, timestamp = contract.functions.verifyDocument(bytes32_hash).call()
    
    return {
        "is_authentic": exists,
        "student_id": student_id,
        "document_title": doc_title,
        "issuer": issuer,
        "timestamp": timestamp
    }