from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

app = Flask(__name__, static_folder='.', static_url_path='')

# SQLite database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reports.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
CORS(app)

# Report model
class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    description = db.Column(db.Text)
    type = db.Column(db.String(50))
    email = db.Column(db.String(120))
    zip_code = db.Column(db.String(10))
    resolved = db.Column(db.Boolean, default=False)

# Create tables
with app.app_context():
    db.create_all()

# ✅ Serve the frontend (index.html)
@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'index.html')

# ✅ API route to get reports by ZIP code
@app.route('/api/reports', methods=['GET'])
def get_reports():
    zip_code = request.args.get('zip_code')
    if not zip_code:
        return jsonify([])

    reports = Report.query.filter_by(zip_code=zip_code).all()
    return jsonify([{
        'id': r.id,
        'title': r.title,
        'description': r.description,
        'type': r.type,
        'email': r.email,
        'zip_code': r.zip_code,
        'resolved': r.resolved
    } for r in reports])

# ✅ API route to add a new report
@app.route('/api/reports', methods=['POST'])
def add_report():
    data = request.json
    report = Report(
        title=data['title'],
        description=data['description'],
        type=data['type'],
        email=data['email'],
        zip_code=data['zip_code']
    )
    db.session.add(report)
    db.session.commit()
    return jsonify({'message': 'Report added'}), 201

# ✅ API route to mark report as resolved
@app.route('/api/reports/<int:report_id>/resolve', methods=['PATCH'])
def resolve_report(report_id):
    report = Report.query.get_or_404(report_id)
    report.resolved = True
    db.session.commit()
    return jsonify({'message': 'Report marked as resolved'})

# Run the app
if __name__ == '__main__':
    app.run(debug=True)