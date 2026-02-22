// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title CommitmentRegistry
 * @dev Stores cryptographic commitments of model updates to ensure auditability.
 */
contract CommitmentRegistry {
    struct Commitment {
        address hospital;
        uint256 round;
        bytes32 updateHash; // Hash of the local model weights
        uint256 timestamp;
    }

    // Mapping: taskId => round => list of commitments
    mapping(uint256 => mapping(uint256 => Commitment[])) public commitments;
    
    // Mapping: taskId => final model hash (on-chain verification)
    mapping(uint256 => bytes32) public finalModelWeights;

    mapping(address => bool) public isAuthorized;
    address public admin;

    event CommitmentPosted(uint256 indexed taskId, uint256 indexed round, address hospital, bytes32 updateHash);
    event FinalModelWeightsPosted(uint256 indexed taskId, bytes32 modelWeightsHash);
    event HospitalAuthorized(address hospital, bool status);

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can perform this action");
        _;
    }

    constructor() {
        admin = msg.sender;
    }

    function authorizeHospital(address _hospital, bool _status) public onlyAdmin {
        isAuthorized[_hospital] = _status;
        emit HospitalAuthorized(_hospital, _status);
    }

    /**
     * @dev Hospitals post a commitment before sending updates to the aggregator.
     */
    function postCommitment(uint256 _taskId, uint256 _round, bytes32 _updateHash) public {
        require(isAuthorized[msg.sender], "Hospital is not authorized");
        commitments[_taskId][_round].push(Commitment({
            hospital: msg.sender,
            round: _round,
            updateHash: _updateHash,
            timestamp: block.timestamp
        }));

        emit CommitmentPosted(_taskId, _round, msg.sender, _updateHash);
    }

    /**
     * @dev The aggregator posts the final model weights hash for auditability.
     */
    function postFinalWeights(uint256 _taskId, bytes32 _weightsHash) public onlyAdmin {
        // Ideally only the authorized aggregator can call this.
        finalModelWeights[_taskId] = _weightsHash;
        emit FinalModelWeightsPosted(_taskId, _weightsHash);
    }

    function getCommitments(uint256 _taskId, uint256 _round) public view returns (Commitment[] memory) {
        return commitments[_taskId][_round];
    }
}
