// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract EduLocker {
    struct DocumentRecord {
        string studentId;
        string documentTitle;
        address issuer;
        uint256 timestamp;
        bool exists;
    }

    mapping(bytes32 => DocumentRecord) public documents;

    event DocumentRegistered(bytes32 indexed docHash, string studentId, string documentTitle, uint256 timestamp);

    function registerDocument(bytes32 _docHash, string memory _studentId, string memory _documentTitle) public {
        require(!documents[_docHash].exists, "Document hash already registered!");

        documents[_docHash] = DocumentRecord({
            studentId: _studentId,
            documentTitle: _documentTitle,
            issuer: msg.sender,
            timestamp: block.timestamp,
            exists: true
        });

        emit DocumentRegistered(_docHash, _studentId, _documentTitle, block.timestamp);
    }

    function verifyDocument(bytes32 _docHash) public view returns (bool, string memory, string memory, address, uint256) {
        if (!documents[_docHash].exists) {
            return (false, "", "", address(0), 0);
        }
        DocumentRecord memory doc = documents[_docHash];
        return (true, doc.studentId, doc.documentTitle, doc.issuer, doc.timestamp);
    }
}