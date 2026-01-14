import streamlit as st
import PyPDF2
import google.generativeai as genai
import tempfile
import os


st.set_page_config(
    page_title="Public Policy Insight & Impact Analyzer (PPIIA)",
    layout="wide"
)

st.title("📜 Public Policy Insight & Impact Analyzer (PPIIA)")
st.subheader("Simplifying Government Bills for Every Citizen")


# API Key config

genai.configure(api_key="AIzaSyCIrNiPVwDuqWUOwG3hAL1oxcC2J_6dvgE")
model = genai.GenerativeModel(model_name="models/gemini-2.5-flash")


uploaded_file = st.file_uploader(
    "Upload a Government / Constitutional / Public Policy PDF only",
    type=["pdf"]
)

if uploaded_file:

    st.success("PDF uploaded successfully")


    pdf_text = ""

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(uploaded_file.read())
        temp_pdf_path = temp_pdf.name

    with open(temp_pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pdf_text += text + "\n"

    os.remove(temp_pdf_path)

    if len(pdf_text.strip()) == 0:
        st.error("No readable text found in this PDF.")
        st.stop()


    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as temp_txt:
        temp_txt.write(pdf_text)
        txt_path = temp_txt.name

    text_file = genai.upload_file(path=txt_path)

# RELEVANCE PROMPT
    relevance_prompt = """
    You are a document classifier.

    Check whether the given document is related to:
    - Government bills
    - Constitutional law
    - Public policy
    - Acts, amendments, or regulations
    - Parliamentary or legislative documents

    Respond with only:
    YES or NO
    """

    relevance_response = model.generate_content(
        [relevance_prompt, text_file],
        request_options={"timeout": 600}
    )

    if relevance_response.text.strip().upper() != "YES":
        st.warning("❌ Please upload a government, constitutional, or public policy related PDF only.")
        st.stop()

    st.success("✅ Valid public policy document detected")


# ANALYSIS PROMPT
    analysis_prompt = """
    You are an AI public policy analyst.

    Analyze the given government bill and extract the following information:

    TITLE
    - Official or inferred title

    MINISTRY
    - Responsible ministry or department

    OBJECTIVE
    - Main purpose of the bill in simple language

    KEY PROVISIONS
    - Important clauses or changes (bullet points)

    RELATED PREVIOUS BILLS / ACTS
    - Acts or amendments referenced (if any)

    STAKEHOLDERS
    - Citizens, industries, government bodies, NGOs, etc.

    RISKS & OPPORTUNITIES
    - Risks: challenges or negative impacts
    - Opportunities: benefits and positive outcomes

    Use clear headings and simple language.
    """

    if st.button("🔍 Analyze Bill"):
        with st.spinner("Analyzing policy document..."):
            response = model.generate_content(
                [analysis_prompt, text_file],
                request_options={"timeout": 600}
            )

        st.session_state["analysis"] = response.text

    
    if "analysis" in st.session_state:
        st.markdown("## 📊 Policy Analysis Result")
        st.markdown(st.session_state["analysis"])

        
        st.markdown("## 💬 Ask about this Bill")

        question = st.text_input(
            "Ask a question about the uploaded bill",
            placeholder="Example: What is the main penalty mentioned?"
        )

        if question:
            chat_prompt = f"""
            You are answering questions about a government bill.

            Rules:
            1. Use ONLY the content of the given bill.
            2. You MAY rephrase, summarize, or infer logically from the bill's language.
            3. Do NOT use outside knowledge.
            4. If the information is truly absent or cannot be reasonably inferred, say:
            "This information is not clearly mentioned in the bill."

            Question:
            {question}
            """

            chat_response = model.generate_content(
                [chat_prompt, text_file],
                request_options={"timeout": 600}
            )

            st.write(chat_response.text)


        os.remove(txt_path)
        genai.delete_file(text_file.name)



st.markdown("---")
st.caption("CivicTech & Public Policy Analytics")
