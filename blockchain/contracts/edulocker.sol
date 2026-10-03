// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

contract EduLocker {
    
    // Structure to hold document metadata on the blockchain
    struct DocumentRecord {
        string documentId;
        string studentId;
        string documentHash; // SHA-256 hash (64 hex characters)
        string issuer;
        uint256 timestamp;
        bool exists;
    }

    // Mapping from document hash to its record
    mapping(string => DocumentRecord) private documents;

    // Mapping from documentId to its hash for easy lookup if needed
    mapping(string => string) private idToHash;

    // Events for tracking actions on the blockchain
    event DocumentRegistered(
        string indexed documentId, 
        string studentId, 
        string documentHash, 
        uint256 timestamp
    );
    
    event DocumentVerified(
        string indexed documentId, 
        bool isValid, 
        uint256 timestamp
    );

    // Function to register a document hash on the blockchain
    function registerDocument(
        string memory _documentId,
        string memory _studentId,
        string memory _documentHash,
        string memory _issuer
    ) public {
        // Ensure this hash hasn't already been registered
        require(!documents[_documentHash].exists, "Document with this hash already exists on-chain.");

        documents[_documentHash] = DocumentRecord({
            documentId: _documentId,
            studentId: _studentId,
            documentHash: _documentHash,
            issuer: _issuer,
            timestamp: block.timestamp,
            exists: true
        });

        idToHash[_documentId] = _documentHash;

        emit DocumentRegistered(_documentId, _studentId, _documentHash, block.timestamp);
    }

    // Function to verify if a given hash exists and matches on-chain records
    function verifyDocumentHash(string memory _documentHash) public view returns (
        bool isValid,
        string memory documentId,
        string memory studentId,
        string memory issuer,
        uint256 timestamp
    ) {
        if (documents[_documentHash].exists) {
            DocumentRecord memory rec = documents[_documentHash];
            return (true, rec.documentId, rec.studentId, rec.issuer, rec.timestamp);
        } else {
            return (false, "", "", "", 0);
        }
    }
}