from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
import pyotp
import re
import os
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='your_email@gmail.com',       # <-- Replace this
    MAIL_PASSWORD='your_email_password',        # <-- Replace this
)
mail = Mail(app)
app.secret_key = 'supersecretkey'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reports.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    zip = db.Column(db.String(10), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    resolved = db.Column(db.Boolean, default=False)
    lat = db.Column(db.Float, nullable=True)
    lng = db.Column(db.Float, nullable=True)
    image_url = db.Column(db.String(300), nullable=True)

    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(120), nullable=False)
        email = db.Column(db.String(120), unique=True, nullable=False)
        zip = db.Column(db.String(10), nullable=True)

        def __repr__(self):
            return f'<User {self.email}>'
@app.route('/')
def home():
    return render_template('index.html')
@app.route('/login')
def login_page():
    return render_template('login.html')
@app.route('/api/reports', methods=['GET'])
def get_reports():
    zip_code = request.args.get('zip')
    query = Report.query
    if zip_code:
        query = query.filter_by(zip=zip_code)
    reports = query.order_by(Report.resolved.asc()).all()

    print(f"[DEBUG] Returning {len(reports)} reports")
    return jsonify([{
        "id": r.id,
        "type": r.type,
        "description": r.description,
        "zip": r.zip,
        "email": r.email,
        "phone": r.phone,
        "resolved": r.resolved,
        "lat": r.lat,
        "lng": r.lng,
        "imageUrl": r.image_url
    } for r in reports])

@app.route('/api/reports', methods=['POST'])
def post_report():
    if request.content_type.startswith('multipart/form-data'):
        data = request.form.to_dict()
        file = request.files.get('image')
    else:
        return jsonify({"error": "Content-Type must be multipart/form-data"}), 400

    print("[DEBUG] Received report:", data)

    required_fields = ['type', 'description', 'zip', 'email', 'phone']
    if not all(data.get(k) for k in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    if not EMAIL_REGEX.match(data['email']):
        return jsonify({"error": "Invalid email"}), 400

    session['email'] = data['email']

    image_url = None
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        image_url = f"/static/uploads/{filename}"

    report = Report(
        type=data['type'],
        description=data['description'],
        zip=data['zip'],
        email=data['email'],
        phone=data['phone'],
        lat=data.get('lat'),
        lng=data.get('lng'),
        image_url=image_url
    )

    db.session.add(report)
    db.session.commit()
    print(f"[DEBUG] Report saved with ID: {report.id}")
    # Notify users in the same ZIP code
    matching_users = User.query.filter_by(zip=data['zip']).all()
    for user in matching_users:
        try:
            msg = Message(
                subject=f"Alert: {data['type']} in your area!",
                sender="your_email@gmail.com",  # Same as configured above
                recipients=[user.email],
                body=f"""Hey {user.name},

    There is a {data['type']} reported in your area ({data['zip']}).

    Details:
    {data['description']}

    Stay safe,
    Your Community Safety Team
    """
            )
            mail.send(msg)
        except Exception as e:
            print(f"[ERROR] Failed to send email to {user.email}: {e}")
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


import os
from flask import current_app


@app.route('/api/reports/<int:id>', methods=['DELETE'])
def delete_report(id):
    if not session.get('admin'):
        return jsonify({"error": "Unauthorized"}), 401
    report = Report.query.get(id)
    if not report:
        return jsonify({"error": "Not found"}), 404
    if not report.resolved:
        return jsonify({"error": "Cannot delete unresolved report"}), 403

    # Remove image file if it exists
    if hasattr(report, 'image_path') and report.image_path:
        image_full_path = os.path.join(current_app.root_path, 'static', 'uploads', report.image_path)
        if os.path.exists(image_full_path):
            os.remove(image_full_path)

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
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get("email")
    user = User.query.filter_by(email=email).first()
    if user:
        session["user_email"] = email
        return jsonify({"message": "Logged in"}), 200
    return jsonify({"error": "User not found"}), 404
@app.route('/signup', methods=['GET', 'POST'])
def signup_page():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        zip_code = request.form.get('zip')

        if not name or not email or not zip_code:
            return "Missing fields", 400

        new_user = User(name=name, email=email, zip=zip_code)
        db.session.add(new_user)
        db.session.commit()

        return ('/')  # or redirect to login or dashboard

    return render_template('signup.html')  # GET method will render the form


@app.before_request
def create_tables():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
