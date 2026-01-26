// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract MedShareTask {
    struct ModelTask {
        string name;
        string description;
        address dataset;
        uint256 budget;
        address researcher;
        bool isActive;
    }

    mapping(uint256 => ModelTask) public tasks;
    uint256 public taskCount;
    address public admin;

    mapping(address => bool) public authorizedHospitals;

    event TaskCreated(uint256 indexed taskId, string name, address researcher);
    event HospitalAuthorized(address hospital, bool status);

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can perform this action");
        _;
    }

    constructor() {
        admin = msg.sender;
    }

    function createTask(string memory _name, string memory _description, address _dataset) public payable {
        taskCount++;
        tasks[taskCount] = ModelTask({
            name: _name,
            description: _description,
            dataset: _dataset,
            budget: msg.value,
            researcher: msg.sender,
            isActive: true
        });
        emit TaskCreated(taskCount, _name, msg.sender);
    }

    function authorizeHospital(address _hospital, bool _status) public onlyAdmin {
        authorizedHospitals[_hospital] = _status;
        emit HospitalAuthorized(_hospital, _status);
    }
}
