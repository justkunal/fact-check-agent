import streamlit as st
import PyPDF2
from duckduckgo_search import DDGS
from groq import Groq
import json
import os

# ----------------------------
# PAGE CONFIG
# ----------------------------

st.set_page_config(
    page_title="Fact-Checking AI Web App",
    page_icon="🕵️",
    layout="wide"
)

st.title("🕵️ Fact-Checking AI Web App")
st.write(
    "Upload a PDF and automatically verify factual claims using live web data."
)

# ----------------------------
# GEMINI API SETUP
# ----------------------------

groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    st.error("GROQ_API_KEY not found in Streamlit Secrets.")
    st.stop()

client = Groq(api_key=groq_api_key)

def ask_llm(prompt):

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content

# ----------------------------
# PDF TEXT EXTRACTION
# ----------------------------

def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


# --------------------------------------------------
# CLAIM EXTRACTION
# --------------------------------------------------

def extract_claims(text):

    prompt = f"""
You are a professional fact checker.

Extract all factual and verifiable claims.

Focus on:
- statistics
- percentages
- dates
- company facts
- financial figures
- technical specifications
- historical facts

Return ONLY a valid JSON array.

Example:

[
  "Google was founded in 1998.",
  "India's population is 1.4 billion."
]

TEXT:

{text}
"""

    try:

        response_text = ask_llm(prompt)

        cleaned = response_text.replace("```json", "")
        cleaned = cleaned.replace("```", "")
        cleaned = cleaned.strip()

        claims = json.loads(cleaned)

        return claims

    except Exception as e:

        st.error(f"Claim Extraction Error: {e}")

        return []

# ----------------------------
# WEB SEARCH
# ----------------------------

def search_web(query):

    try:

        results = list(
            DDGS().text(
                query,
                max_results=5
            )
        )

        if not results:
            return "No search results found."

        context = []

        for result in results:

            context.append(
                f"""
Title: {result.get('title','')}
Source: {result.get('href','')}
Snippet: {result.get('body','')}
"""
            )

        return "\n".join(context)

    except Exception as e:

        return f"Search failed: {str(e)}"


# ----------------------------
# VERIFY ALL CLAIMS
# ----------------------------

def evaluate_all_claims(claims):

    claims_context = []

    for claim in claims:

        web_context = search_web(claim)

        claims_context.append({
            "claim": claim,
            "web_context": web_context
        })

    prompt = f"""
You are a professional fact checker.

For each claim classify as:

Verified
Inaccurate
False

Return ONLY JSON.

Format:

[
 {{
   "claim":"",
   "status":"",
   "explanation":"",
   "real_fact":""
 }}
]

Claims:

{json.dumps(claims_context)}
"""

    try:

        response_text = ask_llm(prompt)

        cleaned = response_text.replace("```json", "")
        cleaned = cleaned.replace("```", "")
        cleaned = cleaned.strip()

        return json.loads(cleaned)

    except Exception as e:

        st.error(f"Verification Error: {e}")

        return []


# ----------------------------
# FILE UPLOAD
# ----------------------------

uploaded_file = st.file_uploader(
    "Upload a PDF document",
    type=["pdf"]
)

# ----------------------------
# START BUTTON
# ----------------------------

if st.button("Start Fact-Checking"):

    if not uploaded_file:

        st.warning("Please upload a PDF file.")

    else:

        with st.spinner("Extracting PDF text..."):

            text = extract_text_from_pdf(uploaded_file)

        if not text.strip():

            st.error("No text could be extracted from the PDF.")

        else:

            with st.spinner("Extracting claims..."):

                claims = extract_claims(text[:30000])

            if not claims:

                st.warning("No verifiable claims found.")

            else:

                st.success(
                    f"Found {len(claims)} claims."
                )

                with st.spinner("Verifying claims..."):

                    results_data = evaluate_all_claims(
                        claims
                    )

                st.subheader("Verification Report")

                for result in results_data:

                    claim = result.get(
                        "claim",
                        ""
                    )

                    status = result.get(
                        "status",
                        "Unknown"
                    )

                    if status == "Verified":

                        st.success(
                            f"✅ Verified: {claim}"
                        )

                    elif status == "Inaccurate":

                        st.warning(
                            f"⚠️ Inaccurate: {claim}"
                        )

                    elif status == "False":

                        st.error(
                            f"❌ False: {claim}"
                        )

                    else:

                        st.info(
                            f"❓ Unknown: {claim}"
                        )

                    with st.expander("Details"):

                        st.write(
                            "**Explanation:**",
                            result.get(
                                "explanation",
                                ""
                            )
                        )

                        st.write(
                            "**Real Fact:**",
                            result.get(
                                "real_fact",
                                ""
                            )
                        )