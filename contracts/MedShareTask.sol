// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title IReputation
 * @dev Interface for the Reputation contract to allow score querying.
 */
interface IReputation {
    function getScore(address _hospital) external view returns (int256);
}

/**
 * @title MedShareTask
 * @dev Manages the creation and lifecycle of federated learning tasks with reputation-gated rewards.
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
    address public reputationContract;

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

    /**
     * @dev Sets the reputation contract address to enable filtered payouts.
     */
    function setReputationContract(address _reputation) public onlyAdmin {
        reputationContract = _reputation;
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

    /**
     * @dev Finalizes the task and distributes bounty to HONEST hospitals only.
     */
    function completeTask(uint256 _taskId, string memory _finalModelHash) public onlyResearcher(_taskId) {
        require(tasks[_taskId].status == TaskStatus.Training, "Task must be in progress");
        
        tasks[_taskId].finalModelHash = _finalModelHash;
        tasks[_taskId].status = TaskStatus.Completed;

        address[] memory allHospitals = tasks[_taskId].hospitals;
        address[] memory honestHospitals = new address[](allHospitals.length);
        uint256 honestCount = 0;

        // Step 1: Filter out malicious hospitals (Reputation < 0)
        for (uint i = 0; i < allHospitals.length; i++) {
            if (reputationContract == address(0)) {
                // Fallback if reputation is not set: pay everyone
                honestHospitals[honestCount++] = allHospitals[i];
            } else {
                int256 score = IReputation(reputationContract).getScore(allHospitals[i]);
                if (score >= 0) {
                    honestHospitals[honestCount++] = allHospitals[i];
                }
            }
        }

        // Step 2: Distribute reward among honest participants
        if (honestCount > 0) {
            uint256 reward = tasks[_taskId].bounty / honestCount;
            for (uint i = 0; i < honestCount; i++) {
                payable(honestHospitals[i]).transfer(reward);
            }
        } else {
            // If No one is honest (unlikely but safe), refund researcher
            payable(tasks[_taskId].researcher).transfer(tasks[_taskId].bounty);
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
