# Using Google Colab with your Local Project

This guide explains how to use the Google Colab VS Code extension to run your local `bxp267` project on Colab's cloud resources.

## Prerequisites
1.  **Google Colab Extension**: Ensure you have installed the "Google Colab" extension by Google in VS Code.
2.  **Jupyter Extension**: The standard "Jupyter" extension for VS Code is also required.

## Steps to Connect
1.  **Open an `.ipynb` File**: Open any Jupyter Notebook in your project (e.g., `test_colab.ipynb`).
2.  **Select Kernel**: Click on the kernel selector in the top-right corner of the editor.
3.  **Choose Colab**: Select **Select Another Kernel...** > **Colab**.
4.  **Authenticate**: Follow the browser prompts to sign in with your Google account.
5.  **Provision Runtime**: Once connected, you can choose to connect to an existing runtime or create a new one (CPU, GPU, or TPU).

## Accessing Local Files
When you connect to Colab via the VS Code extension, your **local files** are accessible to the runtime. You can import scripts from your `backend/` or `fl/` directories as if you were running locally.

> [!NOTE]
> Training data or large files should ideally be uploaded to Google Drive or a cloud bucket for faster access if they are very large, but for standard scripts, the VS Code extension handles the synchronization.

## Verification
Use the provided `test_colab.ipynb` to verify your connection and environment.
