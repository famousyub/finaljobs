import pdfminer
from pdfminer.high_level import extract_text
from nltk import word_tokenize, pos_tag

import nltk
import re 


import re

def extract_contact_number_from_resume(text):
    contact_number = None

    # Use regex pattern to find a potential contact number
    pattern = r"\b(?:\+?\d{2}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}\b"
    match = re.search(pattern, text)
    if match:
        contact_number = match.group()

    return contact_number

import re

def extract_email_from_resume(text):
    email = None

    # Use regex pattern to find a potential email address
    pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    match = re.search(pattern, text)
    if match:
        email = match.group()

    return email

def extract_email_from_resume_type(text):
    email = None

    # Split the text into words
    words = text.split()

    # Iterate through the words and check for a potential email address
    for word in words:
        if "@" in word:
            email = word.strip()
            break

    return email


skills_list=["java","Php","python","ruby","c++","devops","nodejs","laravel","symfony","full stack","javascript","ruby","designer","reactJs"]

def extract_skills_from_resume(text, skills_list):
    skills = []

    for skill in skills_list:
        pattern = r"\b{}\b".format(re.escape(skill))
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            skills.append(skill)

    return skills

nltk.download("punkt")
nltk.download("stopwords")

def extract_data_from_resume(resume_path):
    # Extract text from the PDF resume
    resume_text = extract_text(resume_path)

    # Perform NLP using NLTK
    tokens = word_tokenize(resume_text)
    tagged_tokens = pos_tag(tokens)

    # Extract relevant data (e.g., name, email, phone number) from the tagged tokens
    # Implement your custom logic here based on the structure of your resumes

    # Sample logic to extract name, email, and phone number
    name = ""
    email = ""
    phone = ""
    phonenumber=""
    mail=""
    skills =""
    phonenumber = extract_contact_number_from_resume(resume_text)
    mail = extract_email_from_resume(resume_text)
    skills = extract_skills_from_resume(resume_text,skills_list)
    for token, tag in tagged_tokens:
        if tag == "NNP" and not name:
            name = token
        elif tag == "NN" and not email and "@" in token:
            email = token
        elif tag == "CD" and not phone and len(token) >= 10:
            phone = token

    # Return the extracted data as a JSON string
    extracted_data = {
        "name": name,
      
        "location": phonenumber.strip(),
        "mail":mail,
        "phonenumber":phonenumber,
        "skills" : ",".join(skills)
    }

    return extracted_data
