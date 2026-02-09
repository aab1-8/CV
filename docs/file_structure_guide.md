# MedShare Project Configuration & File Guide

This document provides a detailed breakdown of every file and directory in the MedShare project, explaining their roles in the Federated Learning (FL) simulation, blockchain auditing, and dashboard visualization.

---

## 🐍 Core Python & Simulation Files

### `requirements.txt`
The "shopping list" for your Python environment. It contains all the necessary libraries (like `flwr`, `torch`, `opacus`, and `web3`) required to run the simulation. You use this with `pip install -r requirements.txt`.

### `federated_survival.py`
The **Main Engine** of the project. This is the script you run to actually start the Federated Learning simulation. It handles partitioning the data among hospitals and orchestrating the training rounds via the Flower framework.

### `medshare/` (Directory)
The brain of your project. It contains the modularized Python code:
*   `blockchain.py`: Connects Python to the smart contracts.
*   `client.py`: Mimics an individual hospital's training logic.
*   `data.py`: Loads and cleans clinical datasets (SUPPORT2, Stroke, etc.).
*   `engine.py`: Contains the actual PyTorch training and evaluation loops (where AUC is calculated).
*   `models.py`: Defines the Neural Network architecture.
*   `strategy.py`: Implements the Server-side logic (Anomaly Detection & Reputation).
*   `utils.py`: Helper functions for logging results for the dashboard.

### `test/plot_results.py`
A specialist tool used to generate static visual charts (PNGs). After running multiple experiments (like Differential Privacy or Robustness), you run this to create comparison graphs for your final report.

### `test/best_model.pth`
A binary file representing the "saved state" of your most accurate global model. It stores the weights and biases of the neural network so you can reload the model later without retraining.

---

## ⛓️ Blockchain & Configuration

### `hardhat.config.js`
The settings file for **Hardhat**, your blockchain development environment. It tells the system which version of Solidity to use and how to connect to local networks like Ganache.

### `contracts/` (Directory)
Contains the **Solidity Smart Contracts**:
*   `MedShareTask.sol`: Manages research bounties and hospital authorization.
*   `CommitmentRegistry.sol`: Acts as the immutable audit trail for model updates.
*   `Reputation.sol`: Manages the trust scores for every hospital on the network.

### `package.json` (Root)
The configuration file for the **Blockchain Backend**. It lists the Node.js tools needed to compile contracts and run Ganache.

### `package-lock.json` (Root)
An automatically generated file that locks the exact versions of the blockchain tools to ensure the backend runs perfectly on every machine.

### `build/` (Directory)
Stores the "compiled" versions of your smart contracts. These are the JSON files that the Python simulation and the Frontend dashboard read to know how to talk to the blockchain.

---

## 🌐 Frontend (Dashboard) Files

### `frontend/package.json`
The configuration for your **Dashboard Website**. It lists libraries like `Vite` (the server) and `Chart.js` (the graphs). Use `npm run dev` in the frontend folder to start the site.

### `frontend/package-lock.json`
Similar to the root version, this locks the versions of the dashboard's web tools to prevent bugs caused by unexpected updates.

### `frontend/index.html`
The "Structure" of your dashboard. It defines the layout, the buttons, the sidebar, and where the charts should appear on the screen.

### `frontend/src/` (Directory)
The **Source Code** for the dashboard logic. This is where I wrote the JavaScript that makes the website interactive, fetches data from the simulation, and draws the live graphs.

### `frontend/public/` (Directory)
Contains static assets for the website that don't change, such as the project favicon or the `vite.svg` logo.

### `frontend/dist/` (Directory)
The "Distributed" folder. This is a compact, optimized version of your website that is generated when you run `npm run build`. This is what you would actually upload to a web host.

### `frontend/node_modules/` (Directory)
A massive folder containing all the pre-built web libraries required to run the dashboard. You should never edit files inside here.

---

## 🛠️ Internal / Infrastructure Files

### `.gitignore` (Root) & `frontend/.gitignore`
Hidden files that tell Git to **ignore** certain files (like `node_modules` or large datasets). This keeps your project size manageable and ensures you don't accidentally share private settings or massive log files.

### `scripts/` (Directory)
Contains utility scripts used for setup, such as:
*   `deploy_colab.py`: Assists in setting up the environment when running on Google Colab.
*   `clean_nb.py`: A cleanup tool for notebook files.

### `node_modules/` (Root)
The massive folder containing the pre-built tools required for the blockchain backend (Hardhat, etc.).

### `cache/` (Directory)
A temporary folder used by Hardhat to speed up the compilation of your smart contracts. It stores intermediate files so it doesn't have to start from scratch every time you make a change.