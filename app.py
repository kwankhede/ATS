import streamlit as st
import PyPDF2 as pdf
import json
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


# Function to extract text from uploaded PDF
def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in range(len(reader.pages)):
        page = reader.pages[page]
        text += str(page.extract_text())
    return text


# Function to interact with generative AI for resume evaluation
def get_gemini_response(input_prompt):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(input_prompt)
    return json.loads(response.text)


# Streamlit app layout and functionality
def main():
    st.title("Smart Resume ATS")
    st.write(
        "Welcome to Smart Resume ATS! Improve your resume's relevance to job descriptions with AI-driven analysis."
    )

    st.sidebar.title("Applicant Tracking Software -ATS")
    st.sidebar.info(
        "This app evaluates your resume against a job description using AI. Upload your resume (PDF format) and paste the job description to get feedback."
    )

    st.subheader("Upload Your Resume")
    uploaded_file = st.file_uploader(
        "Choose a PDF file", type="pdf", help="Please upload your resume in PDF format."
    )

    if uploaded_file is not None:
        job_description = st.text_area(
            "Paste the Job Description",
            help="Copy and paste the job description for which you're applying.",
        )

        if st.button("Evaluate Resume"):
            resume_text = input_pdf_text(uploaded_file)
            input_prompt = f"""
                Imagine you're an experienced ATS evaluating a resume for a tech role.
                Please assess the resume based on the job description provided below.
                
                Resume:
                {resume_text}
                
                Job Description:
                {job_description}
                
                I want the response in one single string having the structure:
                {{"JD Match":"%","MissingKeywords":[], "Profile Summary":""}}
            """

            response = get_gemini_response(input_prompt)

            st.subheader("Resume Evaluation Result")
            st.markdown(f"**JD Match:** {response['JD Match']}")

            st.markdown("### Profile Summary:")
            st.write(response["Profile Summary"])

            st.markdown("### Missing Keywords:")

            if response["MissingKeywords"]:
                for idx, keyword in enumerate(response["MissingKeywords"]):
                    st.markdown(f"- {keyword}")
            else:
                st.markdown("- None")


if __name__ == "__main__":
    main()
