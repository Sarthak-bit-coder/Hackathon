from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
import pyotp
import re
app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reports.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Session(app)
CORS(app)
db = SQLAlchemy(app)

EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")
ADMINS = {
    "Sarthak": "JBSWY3DPEHPK3PXP",
    "Ayesha": "KZXW6YTBMFWWKZLU",
    "Shubham": "MFRGGZDFMZTWQ2LK",
    "Anav": "ONSWG4TFOQYTEMY="
}

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    zip = db.Column(db.String(10), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    resolved = db.Column(db.Boolean, default=False)
    lat = db.Column(db.Float, nullable=True)
    lng = db.Column(db.Float, nullable=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/reports', methods=['GET'])
def get_reports():
    zip_code = request.args.get('zip')
    query = Report.query
    if zip_code:
        query = query.filter_by(zip=zip_code)
    reports = query.order_by(Report.resolved.asc()).all()

    print(f"[DEBUG] Returning {len(reports)} reports")  # ADDED
    return jsonify([{
        "id": r.id,
        "type": r.type,
        "description": r.description,
        "zip": r.zip,
        "email": r.email,
        "phone": r.phone,
        "resolved": r.resolved,
        "lat": r.lat,
        "lng": r.lng
    } for r in reports])

@app.route('/api/reports', methods=['POST'])
def post_report():
    data = request.json
    print("[DEBUG] Received report:", data)  # ADDED

    required_fields = ['type', 'description', 'zip', 'email', 'phone']
    if not all(data.get(k) for k in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    if not EMAIL_REGEX.match(data['email']):
        return jsonify({"error": "Invalid email"}), 400

    session['email'] = data['email']

    report = Report(
        type=data['type'],
        description=data['description'],
        zip=data['zip'],
        email=data['email'],
        phone=data['phone'],
        lat=data.get('lat'),
        lng=data.get('lng')
    )

    db.session.add(report)
    db.session.commit()
    print(f"[DEBUG] Report saved with ID: {report.id}")  # ADDED
    return jsonify({"message": "Report submitted", "id": report.id}), 201

@app.route('/api/resolve/<int:id>', methods=['POST'])
def resolve_report(id):
    report = Report.query.get(id)
    if not report:
        return jsonify({"error": "Not found"}), 404
    if session.get('admin') or session.get('email') == report.email:
        report.resolved = True
        db.session.commit()
        return jsonify({"message": "Report resolved"}), 200
    return jsonify({"error": "Forbidden"}), 403

@app.route('/api/reports/<int:id>', methods=['DELETE'])
def delete_report(id):
    if not session.get('admin'):
        return jsonify({"error": "Unauthorized"}), 401
    report = Report.query.get(id)
    if not report:
        return jsonify({"error": "Not found"}), 404
    if not report.resolved:
        return jsonify({"error": "Cannot delete unresolved report"}), 403
    db.session.delete(report)
    db.session.commit()
    return jsonify({"message": "Deleted"}), 200

@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    username = data.get("username")
    token = data.get("token")
    secret = ADMINS.get(username)
    if secret and pyotp.TOTP(secret).verify(token):
        session['admin'] = username
        return jsonify({"message": f"Logged in as {username}"}), 200
    return jsonify({"error": "Unauthorized"}), 401

@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('admin', None)
    return jsonify({"message": "Logged out"}), 200

@app.before_request
def create_tables():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)