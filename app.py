import streamlit as st
import PyPDF2 as pdf
import json
import os
from dotenv import load_dotenv
import google.generativeai as genai
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.probability import FreqDist
from nltk.stem import WordNetLemmatizer
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer

# Download necessary NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize stop words and lemmatizer
stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

# Function to extract text from uploaded PDF
def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in range(len(reader.pages)):
        page = reader.pages[page]
        text += str(page.extract_text())
    return text

# Function to preprocess text (tokenization, stop word removal, lemmatization)
def preprocess_text(text):
    words = word_tokenize(text)
    words = [word.lower() for word in words if word.isalnum()]
    words = [word for word in words if word not in stop_words]
    words = [lemmatizer.lemmatize(word) for word in words]
    return words

# Function to extract keywords
def extract_keywords(text):
    words = preprocess_text(text)
    return FreqDist(words)

# Function to rank missing keywords
def rank_missing_keywords(jd_keywords, resume_keywords):
    missing_keywords = {word: jd_keywords[word] for word in jd_keywords if word not in resume_keywords}
    sorted_missing = sorted(missing_keywords.items(), key=lambda item: item[1], reverse=True)
    return sorted_missing

# Function to interact with generative AI for resume evaluation
def get_gemini_response(input_prompt):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(input_prompt)
    return json.loads(response.text)

# Streamlit app layout and functionality
def main():
    st.title("Smart Resume ATS")
    st.write("Welcome to Smart Resume ATS! Improve your resume's relevance to job descriptions with AI-driven analysis.")

    st.sidebar.title("Applicant Tracking Software - ATS")
    st.sidebar.info("This app evaluates your resume against a job description using AI. Upload your resume (PDF format) and paste the job description to get feedback.")

    st.subheader("Upload Your Resume")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf", help="Please upload your resume in PDF format.")

    if uploaded_file is not None:
        job_description = st.text_area("Paste the Job Description", help="Copy and paste the job description for which you're applying.")

        if st.button("Evaluate Resume"):
            resume_text = input_pdf_text(uploaded_file)
            
            # Extract keywords
            jd_keywords = extract_keywords(job_description)
            resume_keywords = extract_keywords(resume_text)
            
            # Find common keywords
            common_keywords = {word: (jd_keywords[word], resume_keywords[word]) for word in jd_keywords if word in resume_keywords}
            
            # Rank missing keywords
            missing_keywords = rank_missing_keywords(jd_keywords, resume_keywords)
            
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

            st.markdown("### Matching Keywords:")
            for word, (jd_freq, resume_freq) in common_keywords.items():
                st.markdown(f"- **{word}**: Job Description ({jd_freq}), Resume ({resume_freq})")

            st.markdown("### Missing Keywords:")
            if missing_keywords:
                for word, freq in missing_keywords:
                    st.markdown(f"- **{word}**: Job Description ({freq}) - Recommended occurrences: {freq}")
            else:
                st.markdown("- None")

if __name__ == "__main__":
    main()
