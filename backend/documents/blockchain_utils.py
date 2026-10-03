import json
from pathlib import Path
from web3 import Web3

# Connect to local Ganache instance
GANACHE_URL = 'http://127.0.0.1:7545'
w3 = Web3(Web3.HTTPProvider(GANACHE_URL))


def get_contract():
  # Path to the Truffle compiled JSON artifact
  # Adjust relative path based on where backend is relative to blockchain
  base_dir = Path(__file__).resolve().parent.parent.parent
  artifact_path = (
      base_dir
      / 'blockchain'
      / 'build'
      / 'contracts'
      / 'EduLocker.json'
  )

  with open(artifact_path, 'r') as f:
    contract_json = json.load(f)

  # Extract ABI and deployed network address for network ID '5777' (Ganache default)
  abi = contract_json['abi']
  network_id = str(w3.net.version)

  # Fallback to get network address if 5777 is used
  try:
    contract_address = contract_json['networks'][network_id]['address']
  except KeyError:
    # Hardcode your deployed address as a safe fallback if network_id lookup acts up
    contract_address = '0x4Ba3e7432e103D34e41076F15fCE537bA19567be'

  return w3.eth.contract(
      address=Web3.to_checksum_address(contract_address), abi=abi
  )


def register_document_on_blockchain(
    document_id, student_id, document_hash, issuer_name='EduLocker Admin'
):
  if not w3.is_connected():
    raise Exception(
        'Could not connect to blockchain network (Ganache is offline).'
    )

  contract = get_contract()

  # Use the first account available in Ganache as the transaction sender
  sender_account = w3.eth.accounts[0]

  # Build the transaction to call the smart contract's registerDocument function
  tx_hash = contract.functions.registerDocument(
      document_id, student_id, document_hash, issuer_name
  ).transact({'from': sender_account})

  # Wait for the transaction receipt
  tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
  return tx_receipt.transactionHash.hex()


def verify_document_on_blockchain(document_hash):
  if not w3.is_connected():
    return {'isValid': False, 'error': 'Blockchain offline'}

  contract = get_contract()
  # Call view function on smart contract
  result = contract.functions.verifyDocumentHash(document_hash).call()

  # Returns: (isValid, documentId, studentId, issuer, timestamp)
  return {
      'isValid': result[0],
      'documentId': result[1],
      'studentId': result[2],
      'issuer': result[3],
      'timestamp': result[4],
  }