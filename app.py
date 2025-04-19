from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import difflib
from docx import Document
import re
import pytesseract
from PIL import Image
import os
from werkzeug.utils import secure_filename
from pdf2image import convert_from_path
import logging
import subprocess
import shutil

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_url_path='', static_folder='')
CORS(app)
app.config['UPLOAD_FOLDER'] = 'uploads'

@app.route('/')
def index():
    return send_from_directory('', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('', path)

@app.route('/check-plagiarism-folder', methods=['POST'])
def check_plagiarism_folder():
    try:
        if 'doc1' not in request.files or 'folder' not in request.files:
            return jsonify({"error": "Missing required files"}), 400
            
        doc1 = request.files['doc1']
        folder_files = request.files.getlist('folder')
        
        if not doc1.filename or not folder_files:
            return jsonify({"error": "Please upload both the document and the folder."}), 400

        try:
            text1, text1_source = read_file_content(doc1)
            if not text1 or text1 in ["Unable to extract text from image", "Unable to extract text from PDF"]:
                logger.error(f"Failed to extract text from main document: {doc1.filename}. Content: {text1}")
                return jsonify({"error": f"Failed to extract text from main document: {doc1.filename}"}), 400
            logger.debug(f"Extracted text from main document ({text1_source}): {text1[:100]}...")
        except Exception as e:
            logger.error(f"Error reading main document {doc1.filename}: {str(e)}")
            return jsonify({"error": f"Error reading main document: {str(e)}"}), 400

        results = []
        for file in folder_files:
            try:
                text2, text2_source = read_file_content(file)
                if text2 is None:  # Skip files that returned None (e.g., .DS_Store)
                    continue
                if not text2 or text2 in ["Unable to extract text from image", "Unable to extract text from PDF"]:
                    logger.warning(f"Failed to extract text from {file.filename}. Content: {text2}")
                    results.append({
                        "file_name": file.filename,
                        "error": f"Failed to extract text from {file.filename}: {text2}"
                    })
                    continue
                
                logger.debug(f"Extracted text from {text2_source} ({file.filename}): {text2[:100]}...")
                if not text2.strip():
                    logger.warning(f"Empty text extracted from {file.filename}")
                    results.append({
                        "file_name": file.filename,
                        "error": "Empty text extracted, possible OCR failure"
                    })
                    continue
                
                plagiarism_percentage, matches = calculate_similarity_and_matches(text1, text2)
                suggestions = suggest_changes(matches)
                results.append({
                    "file_name": file.filename,
                    "plagiarism_percentage": round(plagiarism_percentage, 2),
                    "matches": matches,
                    "suggestions": suggestions,
                    "text_length": len(text2.split())  # Proxy for OCR success
                })
            except Exception as e:
                logger.error(f"Error processing {file.filename}: {str(e)}")
                results.append({
                    "file_name": file.filename,
                    "error": str(e)
                })

        logger.debug(f"Returning results for {len(results)} files: {results}")
        return jsonify({"files": results})

    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

def read_file_content(uploaded_file):
    if not uploaded_file.filename:
        raise ValueError("No file uploaded")
    
    filename = uploaded_file.filename.lower()
    logger.debug(f"Received file for processing: {filename}")  # Log the full filename received
    # Skip .DS_Store files at the end of the filename (accounting for path)
    if filename.endswith('.ds_store'):
        logger.debug(f"Skipping .DS_Store file: {filename}")
        return None, "skipped"

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(uploaded_file.filename))
    uploaded_file.save(file_path)
    logger.debug(f"Saved file to {file_path}")

    try:
        if filename.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read(), "text"
        elif filename.endswith('.docx'):
            doc = Document(file_path)
            return " ".join([paragraph.text for paragraph in doc.paragraphs]), "docx"
        elif filename.endswith(('.jpg', '.png')):
            try:
                image = Image.open(file_path)
                logger.debug(f"Image opened successfully for {filename}, size: {image.size}")
                text = pytesseract.image_to_string(image)
                logger.debug(f"OCR raw output for {filename}: {text[:100]}...")
                return text.strip() if text else "Unable to extract text from image", "image"
            except Exception as e:
                logger.error(f"OCR error for {filename}: {str(e)}")
                return "Unable to extract text from image", "image"
        elif filename.endswith('.pdf'):
            try:
                logger.debug(f"Attempting to convert PDF {filename} to images")
                images = convert_from_path(file_path)
                logger.debug(f"Converted PDF to {len(images)} images")
                full_text = ""
                for i, image in enumerate(images):
                    logger.debug(f"Processing page {i+1} of {filename}")
                    text = pytesseract.image_to_string(image)
                    full_text += text.strip() + " "
                logger.debug(f"OCR result for {filename}: {full_text[:100]}...")
                return full_text.strip() if full_text else "Unable to extract text from PDF", "pdf"
            except Exception as e:
                logger.error(f"PDF to image conversion or OCR error for {filename}: {str(e)}")
                return "Unable to extract text from PDF", "pdf"
        else:
            raise ValueError("Unsupported file type. Supported types: .txt, .docx, .jpg, .png, .pdf")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Cleaned up temporary file {file_path}")

def calculate_similarity_and_matches(text1, text2):
    sentences1 = re.split(r'(?<=[.!?])\s+', text1)
    sentences2 = re.split(r'(?<=[.!?])\s+', text2)

    matcher = difflib.SequenceMatcher(None, sentences1, sentences2)
    similarity = matcher.ratio() * 100

    matches = []
    for match in matcher.get_matching_blocks():
        if match.size > 0:
            matched_text = " ".join(sentences1[match.a:match.a + match.size])
            matches.append(matched_text)

    return similarity, matches

def suggest_changes(matches):
    suggestions = []
    for match in matches:
        words = match.split()
        if len(words) > 5:
            suggestion = f"Consider rephrasing: '{match[:50]}...'"
            suggestions.append(suggestion)
    return suggestions

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
        logger.debug("Created uploads directory")
    
    # Verify Tesseract
    try:
        pytesseract.get_tesseract_version()
        logger.info("Tesseract is installed and accessible")
    except Exception as e:
        logger.error(f"Tesseract not found or not configured: {str(e)}")
        print("Error: Tesseract OCR is not installed or not in PATH. Please install it and add to PATH.")
        exit(1)
    
    # Verify Poppler
    poppler_paths = ['/opt/homebrew/bin/pdftoppm', '/usr/local/bin/pdftoppm']  # Check both Apple Silicon and Intel paths
    poppler_found = False
    for path in poppler_paths:
        if os.path.exists(path):
            try:
                subprocess.check_output([path, '-v'])
                logger.info(f"Poppler found at {path} and is accessible")
                poppler_found = True
                break
            except subprocess.CalledProcessError as e:
                logger.warning(f"Poppler version check failed at {path}: {str(e)}. Proceeding with limited PDF support.")
                poppler_found = True
                break
            except Exception as e:
                logger.debug(f"Poppler check failed at {path}: {str(e)}")
                continue
    if not poppler_found:
        logger.warning("Poppler not found in any standard paths. PDF support will be disabled.")
        print("Warning: Poppler not found. PDF support will be disabled. Install Poppler with 'brew install poppler'.")

    app.run(debug=True, port=5000)