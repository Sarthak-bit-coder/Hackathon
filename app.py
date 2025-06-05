from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

# In-memory storage for reports
reports = []

# Basic email validation regex
EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/reports', methods=['GET'])
def get_reports():
    zip_code = request.args.get('zip')
    if zip_code:
        filtered_reports = [r for r in reports if r.get('zip') == zip_code]
        return jsonify(filtered_reports)
    return jsonify(reports)

@app.route('/api/reports', methods=['POST'])
def post_report():
    data = request.json
    report_type = data.get("type")
    description = data.get("description")
    zip_code = data.get("zip")
    email = data.get("email")

    # Basic validation
    if not report_type or not description or not zip_code or not email:
        return jsonify({"error": "All fields (type, description, zip, email) are required"}), 400

    if not EMAIL_REGEX.match(email):
        return jsonify({"error": "Invalid email address"}), 400

    report = {
        "type": report_type,
        "description": description,
        "zip": zip_code,
        "email": email
    }

    reports.append(report)
    return jsonify(report), 201

if __name__ == '__main__':
    app.run(debug=True)