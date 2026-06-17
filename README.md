# Fact-Checking AI Web App

This is a Streamlit-based web application that automates claim verification from PDF documents. It acts as a "Truth Layer," extracting statistics, dates, and financial figures from an uploaded PDF, cross-referencing them against the live web (using DuckDuckGo Search), and evaluating their accuracy using Google's Gemini AI.

## Features
- **Extract**: Identifies specific verifiable claims from PDF text.
- **Verify**: Searches the live web to find sources and context.
- **Report**: Flags claims as "Verified", "Inaccurate", or "False" and provides the actual facts and explanations.

## Running Locally

1. Make sure you have Python 3.8+ installed.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```
4. Enter your Gemini API key in the application sidebar/input to start checking facts.

## Deployment (Mandatory Requirement)

To make this app live and available via a URL (e.g., to test with a "Trap Document"), the simplest and free option is **Streamlit Community Cloud**.

### Steps to Deploy to Streamlit Cloud:

1. **Create a GitHub Repository**: 
   - Push `app.py`, `requirements.txt`, and this `README.md` to a public (or private) GitHub repository.

2. **Sign up / Log in to Streamlit**:
   - Go to [Streamlit Community Cloud](https://share.streamlit.io/) and log in with your GitHub account.

3. **Deploy the App**:
   - Click the **"New app"** button.
   - Select the GitHub repository you just created.
   - Set the **Branch** to `main` (or your default branch).
   - Set the **Main file path** to `app.py`.
   - Click **"Deploy!"**

4. **Testing**:
   - Once deployed, you will get a live URL (e.g., `https://your-app-name.streamlit.app`).
   - Open the URL, enter your Gemini API key, upload the "Trap Document" PDF, and verify the claims!

## Evaluation Criteria
- It successfully uses live web search to prove/disprove PDF claims.
- It returns a categorized response (Verified, Inaccurate, False).
- It provides the "real" facts alongside the explanation.
