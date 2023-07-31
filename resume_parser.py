# resume_parser.py

import os
import io
import re
import json
import zipfile
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdftypes import resolve1

# array manipulation
import numpy as np
import pandas as pd

# systems
import os, io, re
import zipfile
import datetime
import json

# NLP
import spacy
from sklearn.metrics.pairwise import cosine_similarity
from spacy.lang.en.stop_words import STOP_WORDS
from spacy.matcher import PhraseMatcher

# Add the skillNer.general_params and skillNer.skill_extractor_class imports here
from skillNer.general_params import SKILL_DB
from skillNer.skill_extractor_class import SkillExtractor
# NLP
nlp = spacy.load("en_core_web_lg")
allow_stop_words = ["\n\n"]
allow_punct = ["-", "+", "@", ".", "\", ""/", "(", ")"]
for word in allow_stop_words:
    nlp.vocab[word].is_stop = True

for word in allow_punct:
    nlp.vocab[word].is_punct = False

skill_extractor = SkillExtractor(nlp, SKILL_DB, PhraseMatcher)
ngramed_score_threshold = 0.7

# Reg
education_keywords = ["education", "degree", "university", "college"]
degree_patterns = r"\b(bachelor|b\.?a\.?|master|m\.?a\.?|ph\.?d|doctorate|b\.?sc\.?|m\.?sc\.?)\b[^,]*"
phone_pattern = re.compile(r'(\+\d{1,2}\s?)?(\(?\d{3}\)?[\s.-]?)?\d{3}[\s.-]?\d{4}')

# Custom
URL_PRE = "https://"
ALLOWED_FILE_TYPES = [".pdf", ".doc", ".docx"]
UNZIP_TO_FLD = "resumes"

# PDF Miner
def extract_text_from_pdf(pdf_path):
    extracted_text = ""
    with open(pdf_path, 'rb') as fh:
        for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
            resource_manager = PDFResourceManager()
            fake_file_handle = io.StringIO()
            converter = TextConverter(resource_manager, fake_file_handle, codec='utf-8', laparams=LAParams())
            page_interpreter = PDFPageInterpreter(resource_manager, converter)
            page_interpreter.process_page(page)
            extracted_text += fake_file_handle.getvalue()
            converter.close()
            fake_file_handle.close()
    return extracted_text

import docx2txt
def extract_text_from_doc(doc_path):
    temp = docx2txt.process(doc_path)
    text = [line.replace('\t', ' ') for line in temp.split('\n') if line]
    return ' '.join(text)

def preprocess(text):
    doc = nlp(text) 
    clean_tokens = [token.lemma_ for token in doc if not token.is_punct and not token.is_stop]
    nlp_text = nlp(" ".join(clean_tokens))
    return nlp_text

def extractNER(doc):
    persons = []
    organizations = []
    for entity in doc.ents:
        if entity.label_ == 'PERSON':
            persons.append(entity.text)
        elif entity.label_ == 'ORG':
            organizations.append(entity.text)
    return persons, organizations

def extract_email_addresses(doc):
    email_addresses = set()
    for token in doc:
        if token.like_email:
            email_addresses.add(token.text)
    return email_addresses

def extract_phones(doc):
    phone_numbers = set()
    for sentence in doc.sents:
        lines = sentence.text.split("\n")
        for line in lines:
            matches = re.finditer(phone_pattern, line.replace(" ", ""))
            for match in matches:
                phone_numbers.add(match.group())
    return phone_numbers

def extractSkills(text):
    annotations = skill_extractor.annotate(text)
    skills = set()
    skills_full_match = annotations["results"]["full_matches"]
    for skill in skills_full_match:
        skills.add((skill["doc_node_value"], skill_extractor.skills_db.get(skill["skill_id"])["skill_name"], skill["score"]))

    skills_ngramed_scored = annotations["results"]["ngram_scored"]
    for skill in skills_ngramed_scored:
        n_gramed_score = skill["score"] / skill["len"]
        if n_gramed_score > ngramed_score_threshold:
            skills.add((skill["doc_node_value"], skill_extractor.skills_db.get(skill["skill_id"])["skill_name"], n_gramed_score))
    return skills

def extractEducation(doc):
    education_sections = []
    for sentence in doc.sents:
        if any(keyword in sentence.text.lower() for keyword in education_keywords):
            education_sections.append(sentence)

    education_entities = []
    for section in education_sections:
        for entity in section.ents:
            if entity.label_ in ["ORG"]:
                education_entities.append(entity.text)

    degrees = []
    for section in education_sections:
        sentence_text = section.text
        extracted_degrees = re.findall(degree_patterns, sentence_text, flags=re.IGNORECASE)
        for degree in extracted_degrees:
            degrees.append(degree)

    return set(education_entities + degrees)

def extractLinks(doc):
    links = []
    for token in doc:
        if token.like_url:
            link = token.text
            link = URL_PRE + link if not link.startswith(URL_PRE) else link
            links.append(link)
    return links

def compute_cosine_similarity(text1, text2):
    text1 = list(text1)
    text2 = list(text2)
    all_text = set(text1 + text2)
    vector1 = np.array([1 if t in text1 else 0 for t in all_text])
    vector2 = np.array([1 if t in text2 else 0 for t in all_text])
    vector1 = vector1.reshape(1, -1)
    vector2 = vector2.reshape(1, -1)
    return cosine_similarity(vector1, vector2)[0, 0]

def compute_jaccard_index(text1, text2):
    text1 = set(text1)
    text2 = set(text2)
    intersection = text1.intersection(text2)
    union = text1.union(text2)
    similarity = len(intersection) / len(union)
    return similarity

def similarity_score(source, target):
    weight_cosine = 0.7
    weight_jaccard = 0.3
    weight_em = 0.7
    weight_fm = 0.3
    text1 = [sublist[0] for sublist in source if sublist[1] == 1]
    text2 = [sublist[0] for sublist in target if sublist[1] == 1]
    cosine_similarity_score_em = compute_cosine_similarity(text1, text2)
    jaccard_similarity_score_em = compute_jaccard_index(text1, text2)
    text1 = [sublist[0] for sublist in text1]
    text2 = [sublist[0] for sublist in text2]
    cosine_similarity_score_fm = compute_cosine_similarity(text1, text2)
    jaccard_similarity_score_fm = compute_jaccard_index(text1, text2)
    cosine_similarity_score = ((cosine_similarity_score_fm * weight_fm) + (cosine_similarity_score_em * weight_em))
    jaccard_similarity_score = ((jaccard_similarity_score_fm * weight_fm) + (jaccard_similarity_score_em * weight_em))
    combined_score = (cosine_similarity_score * weight_cosine) + (jaccard_similarity_score * weight_jaccard)
    return combined_score

def main(zip_file_path, job_desc):
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(UNZIP_TO_FLD)

    job_desc_skills = list(extractSkills(job_desc))
    skills_source = [(sublist[1], sublist[2]) for sublist in job_desc_skills]

    data = []
    counter = 1
    for filename in os.listdir(UNZIP_TO_FLD):
        file_path = os.path.join(UNZIP_TO_FLD, filename)
        if os.path.isfile(file_path):
            print("Processing file:", file_path)
            text = extract_text_from_pdf(file_path)  # Corrected function call here
            print("Extracted text:", text)  # Print the extracted text

            # Check if the extracted text is empty or contains invalid characters
            if not text.strip():
                print("Empty or invalid text. Skipping file.")
                continue

            # Add try-except block to handle JSON parsing
            try:
                out = json.loads(text)  # Parse the extracted text as JSON
            except json.JSONDecodeError as e:
                print("Error parsing JSON:", e)
                continue  # Skip this file and proceed to the next

            out = json.loads(text)  # Parse the extracted text as JSON
            skills_target = [(sublist[1], sublist[2]) for sublist in out["data"]["skills"]]
            match_score = similarity_score(skills_source, skills_target)
            ele = {
                "id": counter,
                "match_score": match_score,
                "name": out["data"]["persons"],
                "emails": out["data"]["emails"],
                "phones": out["data"]["phones"],
                "educations": out["data"]["educations"],
                "links": out["data"]["links"],
                "skills": skills_target,
                "resume": file_path
            }
            data.append(ele)
            counter += 1

    jout = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "zip_file": zip_file_path,
        "data": data
    }

    return json.dumps(jout)

# Check if the script is being run directly (not imported)
if __name__ == "__main__":
    import sys

    # Check if the correct number of arguments is provided
    if len(sys.argv) != 3:
        print("Usage: python resume_parser.py <zip_file_path> <job_description>")
        sys.exit(1)

    # Get the command-line arguments
    zip_file_path = sys.argv[1]
    job_desc = sys.argv[2]

    # Call the main function with the provided arguments
    result = main(zip_file_path, job_desc)

    # Print the result (you can redirect it to a file if needed)
    print(result)