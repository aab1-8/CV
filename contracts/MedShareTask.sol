// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title MedShareTask
 * @dev Manages the creation and lifecycle of federated learning tasks.
 */
contract MedShareTask {
    enum TaskStatus { Open, Training, Completed, Cancelled }

    struct Task {
        address researcher;
        uint256 bounty;
        string modelDescription;
        uint256 minClients;
        uint256 rounds;
        TaskStatus status;
        address[] hospitals;
        string finalModelHash;
    }

    mapping(uint256 => Task) public tasks;
    uint256 public taskCount;
    address public admin;

    mapping(address => bool) public authorizedHospitals;

    event TaskCreated(uint256 taskId, address researcher, uint256 bounty);
    event HospitalAuthorized(address hospital, bool status);
    event HospitalRegistered(uint256 taskId, address hospital);
    event TaskCompleted(uint256 taskId, string finalModelHash);

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can perform this action");
        _;
    }

    modifier onlyResearcher(uint256 _taskId) {
        require(msg.sender == tasks[_taskId].researcher, "Only researcher can perform this action");
        _;
    }

    constructor() {
        admin = msg.sender;
    }

    function authorizeHospital(address _hospital, bool _status) public onlyAdmin {
        authorizedHospitals[_hospital] = _status;
        emit HospitalAuthorized(_hospital, _status);
    }

    function createTask(string memory _description, uint256 _minClients, uint256 _rounds) public payable {
        require(msg.value > 0, "Bounty must be greater than zero");
        
        uint256 taskId = taskCount++;
        Task storage newTask = tasks[taskId];
        newTask.researcher = msg.sender;
        newTask.bounty = msg.value;
        newTask.modelDescription = _description;
        newTask.minClients = _minClients;
        newTask.rounds = _rounds;
        newTask.status = TaskStatus.Open;

        emit TaskCreated(taskId, msg.sender, msg.value);
    }

    function joinTask(uint256 _taskId) public {
        require(authorizedHospitals[msg.sender], "Hospital is not authorized");
        require(tasks[_taskId].status == TaskStatus.Open, "Task is not open for registration");
        
        // Check if already joined
        for (uint i = 0; i < tasks[_taskId].hospitals.length; i++) {
            require(tasks[_taskId].hospitals[i] != msg.sender, "Hospital already joined");
        }

        tasks[_taskId].hospitals.push(msg.sender);
        emit HospitalRegistered(_taskId, msg.sender);

        if (tasks[_taskId].hospitals.length >= tasks[_taskId].minClients) {
            tasks[_taskId].status = TaskStatus.Training;
        }
    }

    function completeTask(uint256 _taskId, string memory _finalModelHash) public onlyResearcher(_taskId) {
        require(tasks[_taskId].status == TaskStatus.Training, "Task must be in progress");
        
        tasks[_taskId].finalModelHash = _finalModelHash;
        tasks[_taskId].status = TaskStatus.Completed;

        // Simple reward distribution: split bounty equally among hospitals
        uint256 reward = tasks[_taskId].bounty / tasks[_taskId].hospitals.length;
        for (uint i = 0; i < tasks[_taskId].hospitals.length; i++) {
            payable(tasks[_taskId].hospitals[i]).transfer(reward);
        }

        emit TaskCompleted(_taskId, _finalModelHash);
    }

    function cancelTask(uint256 _taskId) public onlyResearcher(_taskId) {
        require(tasks[_taskId].status == TaskStatus.Open, "Can only cancel before training starts");
        tasks[_taskId].status = TaskStatus.Cancelled;
        payable(msg.sender).transfer(tasks[_taskId].bounty);
    }

    function getHospitals(uint256 _taskId) public view returns (address[] memory) {
        return tasks[_taskId].hospitals;
    }
}
