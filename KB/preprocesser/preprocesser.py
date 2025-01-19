import logging
import os
from langchain_core.runnables import RunnablePassthrough
from KB.config import DATA_FOLDER_PATH
import fitz
import docx
from bs4 import BeautifulSoup  # For HTML parsing
import csv


def load_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page_num in range(len(doc)):
        page = doc[page_num]
        # print(f"Page {page_num + 1} Text:")
        # print(page.get_text())
        text += page.get_text()
    return text


def load_docx(file_path):
    doc = docx.Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    text = "\n".join(full_text).strip()

    return text


def load_html(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    soup = BeautifulSoup(html_content, "html.parser")
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()
    text = soup.get_text(separator="\n").strip()
    return text


def load_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read().strip()
        return text


def load_csv(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        csv_content = []
        for row in reader:
            csv_content.append(", ".join(row))
        text = "\n".join(csv_content).strip()
        return text


def load_documents(state):
    files_content = []
    for root, _, files in os.walk(DATA_FOLDER_PATH):
        for file in files:
            text = None
            file_path = os.path.join(root, file)

            if not 'domande' in file_path:
                if file.lower().endswith('.pdf'):
                    text = load_pdf(file_path)
                elif file.lower().endswith('.docx'):
                    text = load_docx(file_path)
                elif file.lower().endswith('.html'):
                    text = load_html(file_path)
                elif file.lower().endswith('.txt'):
                    text = load_txt(file_path)
                elif file.lower().endswith('.csv'):
                    text = load_csv(file_path)
                else:
                    logging.warning(f"No parser for: {file_path}")

                files_content.append(text)

    logging.info(f"{len(files_content)} file proccessed")

    return files_content



preprocceser_chain = (
    RunnablePassthrough.assign(files=load_documents)
)