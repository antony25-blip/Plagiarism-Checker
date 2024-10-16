from flask import Flask, request, jsonify
from flask_cors import CORS
import difflib
from docx import Document
import re

app = Flask(__name__)


CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins

@app.route('/')
def home():
    return "Flask is running!" 

@app.route('/check-plagiarism-folder', methods=['POST'])
def check_plagiarism_folder():
    doc1 = request.files.get('doc1')
    folder = request.files.getlist('folder')

    if not doc1 or not folder:
        return jsonify({"error": "Please upload both the document and the folder."}), 400

    text1 = read_file_content(doc1)
    results = []

    for file in folder:
        text2 = read_file_content(file)
        plagiarism_percentage, matches = calculate_similarity_and_matches(text1, text2)
        suggestions = suggest_changes(matches)
        results.append({
            "file_name": file.filename,
            "plagiarism_percentage": plagiarism_percentage,
            "matches": matches,
            "suggestions": suggestions
        })

    return jsonify({"files": results})

def read_file_content(uploaded_file):
    if uploaded_file.content_type == "text/plain":
        return uploaded_file.read().decode("utf-8")
    elif uploaded_file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(uploaded_file)
        return " ".join([paragraph.text for paragraph in doc.paragraphs])
    else:
        raise ValueError("Unsupported file type")

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
            suggestion = f"Consider rephrasing: '{match}'"
            suggestions.append(suggestion)
    return suggestions

if __name__ == '__main__':
    app.run(debug=True)
