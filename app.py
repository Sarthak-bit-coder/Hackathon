from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# In-memory list of reports
reports = []

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/reports', methods=['GET'])
def get_reports():
    zip_code = request.args.get('zip')
    if zip_code:
        filtered = [r for r in reports if r['zip'] == zip_code]
        return jsonify(filtered)
    return jsonify(reports)

@app.route('/api/reports', methods=['POST'])
def post_report():
    data = request.json
    report = {
        "type": data.get("type"),
        "description": data.get("description"),
        "zip": data.get("zip")
    }
    reports.append(report)
    return jsonify(report), 201

if __name__ == '__main__':
    app.run(debug=True)
