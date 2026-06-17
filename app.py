import streamlit as st
import PyPDF2
import google.generativeai as genai
from duckduckgo_search import DDGS
import json
import time

st.set_page_config(page_title="Fact-Checking AI Web App", page_icon="🕵️", layout="wide")

st.title("🕵️ Fact-Checking AI Web App")
st.write("Upload a document, and this AI will extract claims, search the live web, and verify their accuracy.")

# API Key Setup
import os

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("Gemini API key not configured.")
    st.stop()

genai.configure(api_key=api_key)

if api_key:
    genai.configure(api_key=api_key)

def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text

def extract_claims(text):
    prompt = f"""
    You are an expert fact-checker. Read the following text and extract all verifiable claims.
    Focus on statistics, dates, financial figures, technical specifications, and categorical statements.
    Return ONLY a JSON list of strings, where each string is a distinct claim.
    Example: ["The company's revenue grew by 20% in 2023.", "The product features a 5000mAh battery."]
    
    Text:
    {text}
    """
    model = genai.GenerativeModel("gemini-2.5-flash")
    try:
        response = model.generate_content(prompt)
        # Clean up response to ensure it's valid JSON
        cleaned_response = response.text.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:-3]
        elif cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:-3]
        
        claims = json.loads(cleaned_response)
        return claims
    except Exception as e:
        st.error(f"Error parsing claims from AI: {e}")
        return []

def search_web(query):
    try:
        def search_web(query):
    try:
        results = list(DDGS().text(query, max_results=5))

        st.write("Search Results:", results)

        if not results:
            return ""

        return "\n".join([
            f"Title: {r.get('title','')}\n"
            f"Source: {r.get('href','')}\n"
            f"Snippet: {r.get('body','')}"
            for r in results
        ])

    except Exception as e:
        st.error(f"Search Error: {e}")
        return ""
        context = "\n".join([f"Source: {res.get('href')}\nSnippet: {res.get('body')}" for res in results])
        return context
    except Exception as e:
        return f"Web search failed: {e}"

def evaluate_claim(claim, web_context):
    prompt = f"""
    You are an expert fact-checker. Evaluate the following claim based ONLY on the provided web search context.
    
    Claim: "{claim}"
    
    Web Context:
    {web_context}
    
    Determine if the claim is "Verified" (matches context), "Inaccurate" (partially wrong or outdated), or "False" (contradicts context or no evidence).
    Provide a JSON response with three keys:
    "status": One of "Verified", "Inaccurate", "False"
    "explanation": A brief explanation of your finding.
    "real_fact": The correct fact based on the web context (if inaccurate or false).
    
    Respond ONLY with the JSON object, formatted strictly as JSON without markdown blocks.
    """
    model = genai.GenerativeModel("gemini-2.5-flash")
    try:
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:-3]
        elif cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:-3]
        
        evaluation = json.loads(cleaned_response)
        return evaluation
    except Exception as e:
        return {"status": "Error", "explanation": f"Failed to parse evaluation: {e}", "real_fact": ""}

uploaded_file = st.file_uploader("Upload a PDF to fact-check", type=["pdf"])

if st.button("Start Fact-Checking"):
    if not api_key:
        st.error("Please enter your Gemini API Key to proceed.")
    elif not uploaded_file:
        st.error("Please upload a PDF document.")
    else:
        with st.spinner("Extracting text from PDF..."):
            text = extract_text_from_pdf(uploaded_file)
            
        if not text.strip():
            st.error("Could not extract any text from the PDF. It might be scanned or empty.")
        else:
            with st.spinner("Extracting claims from text..."):
                # If text is too long, truncate for MVP (first 30,000 characters)
                claims = extract_claims(text[:30000])
                
            if not claims:
                st.warning("No clear verifiable claims found in the document.")
            else:
                st.success(f"Found {len(claims)} claims to verify!")
                
                results_data = []
                progress_text = "Verifying claims..."
                my_bar = st.progress(0, text=progress_text)
                
                for i, claim in enumerate(claims):
                    # Update progress bar
                    progress = (i + 1) / len(claims)
                    my_bar.progress(progress, text=f"Verifying claim {i+1}/{len(claims)}: {claim[:50]}...")
                    
                    # 1. Search web
                    web_context = search_web(claim)
                    
                    # 2. Evaluate
                    evaluation = evaluate_claim(claim, web_context)
                    
                    # 3. Store result
                    results_data.append({
                        "Claim": claim,
                        "Status": evaluation.get("status", "Unknown"),
                        "Explanation": evaluation.get("explanation", ""),
                        "Real Fact": evaluation.get("real_fact", "")
                    })
                    
                    time.sleep(1) # Rate limit protection for DuckDuckGo/Gemini
                    
                my_bar.empty()
                st.subheader("Verification Report")
                
                # Display Results
                for res in results_data:
                    status = res["Status"]
                    if status == "Verified":
                        st.success(f"✅ **Verified:** {res['Claim']}")
                        with st.expander("Details"):
                            st.write(res["Explanation"])
                    elif status == "Inaccurate":
                        st.warning(f"⚠️ **Inaccurate:** {res['Claim']}")
                        with st.expander("Details"):
                            st.write(f"**Explanation:** {res['Explanation']}")
                            st.write(f"**Real Fact:** {res['Real Fact']}")
                    elif status == "False":
                        st.error(f"❌ **False:** {res['Claim']}")
                        with st.expander("Details"):
                            st.write(f"**Explanation:** {res['Explanation']}")
                            st.write(f"**Real Fact:** {res['Real Fact']}")
                    else:
                        st.info(f"❓ **Unknown/Error:** {res['Claim']}")
                        with st.expander("Details"):
                            st.write(res["Explanation"])