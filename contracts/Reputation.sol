// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title Reputation
 * @dev Tracks the reliability and contribution quality of hospitals in the MedShare network.
 */
contract Reputation {
    // Mapping from hospital address to their reputation score
    mapping(address => int256) public scores;
    
    // Mapping from hospital address to total contributions
    mapping(address => uint256) public totalContributions;

    address public admin;

    event ReputationUpdated(address indexed hospital, int256 newScore, string reason);

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can update reputation");
        _;
    }

    constructor() {
        admin = msg.sender;
    }

    /**
     * @dev Increases or decreases reputation score.
     * @param _hospital The address of the hospital.
     * @param _change The amount to change (positive for rewards, negative for penalties).
     * @param _reason A brief description of why the change occurred.
     */
    function updateReputation(address _hospital, int256 _change, string memory _reason) public onlyAdmin {
        scores[_hospital] += _change;
        if (_change > 0) {
            totalContributions[_hospital]++;
        }
        emit ReputationUpdated(_hospital, scores[_hospital], _reason);
    }

    /**
     * @dev Returns the score for a specific hospital.
     */
    function getScore(address _hospital) public view returns (int256) {
        return scores[_hospital];
    }
}
