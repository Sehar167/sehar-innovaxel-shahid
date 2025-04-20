from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import random
import string
import time
import re
import logging

logging.basicConfig(level=logging.INFO)

@app.before_request
def log_request_info():
    logging.info(f"Request Method: {request.method} | Request URL: {request.url}")


def is_valid_url(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.))' # domain...
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

# Initialize Flask and SQLite database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///urls.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# URL shortening model
class URL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    short_code = db.Column(db.String(6), unique=True, nullable=False)
    created_at = db.Column(db.String(20), default=str(time.time()))
    updated_at = db.Column(db.String(20), default=str(time.time()))
    access_count = db.Column(db.Integer, default=0)

# Create the database if it doesn't exist
with app.app_context():
    db.create_all()

# Utility function to generate short code
def generate_short_code(length=6):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

# 3.1 Create Short URL
@app.route('/shorten', methods=['POST'])
def create_short_url():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "URL is required"}), 400

    original_url = data['url']
    
    # Function to generate a unique short code
    def get_unique_short_code():
        short_code = generate_short_code()
        while URL.query.filter_by(short_code=short_code).first():
            short_code = generate_short_code()  # Ensure uniqueness
        return short_code

    short_code = get_unique_short_code()

    new_url = URL(url=original_url, short_code=short_code)
    db.session.add(new_url)
    db.session.commit()

    return jsonify({
        "id": new_url.id,
        "url": original_url,
        "shortCode": short_code,
        "createdAt": new_url.created_at,
        "updatedAt": new_url.updated_at
    }), 201

# 3.2 Retrieve Original URL
@app.route('/shorten/<short_code>', methods=['GET'])
def retrieve_original_url(short_code):
    url_entry = URL.query.filter_by(short_code=short_code).first()
    if not url_entry:
        return jsonify({"error": "Short URL not found"}), 404

    url_entry.access_count += 1
    db.session.commit()

    return jsonify({
        "id": url_entry.id,
        "url": url_entry.url,
        "shortCode": url_entry.short_code,
        "createdAt": url_entry.created_at,
        "updatedAt": url_entry.updated_at
    }), 200

# 3.3 Update Short URL
@app.route('/shorten/<short_code>', methods=['PUT'])
def update_short_url(short_code):
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "URL is required"}), 400

    url_entry = URL.query.filter_by(short_code=short_code).first()
    if not url_entry:
        return jsonify({"error": "Short URL not found"}), 404

    url_entry.url = data['url']
    url_entry.updated_at = str(time.time())
    db.session.commit()

    return jsonify({
        "id": url_entry.id,
        "url": url_entry.url,
        "shortCode": url_entry.short_code,
        "createdAt": url_entry.created_at,
        "updatedAt": url_entry.updated_at
    }), 200

# 3.4 Delete Short URL
@app.route('/shorten/<short_code>', methods=['DELETE'])
def delete_short_url(short_code):
    url_entry = URL.query.filter_by(short_code=short_code).first()
    if not url_entry:
        return jsonify({"error": "Short URL not found"}), 404

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    db.session.delete(url_entry)
    db.session.commit()

    return '', 204

# 3.5 Get URL Statistics
@app.route('/shorten/stats/<short_code>', methods=['GET'])
def get_url_statistics(short_code):
    url_entry = URL.query.filter_by(short_code=short_code).first()
    if not url_entry:
        return jsonify({"error": "Short URL not found"}), 404

    return jsonify({
        "id": url_entry.id,
        "url": url_entry.url,
        "shortCode": url_entry.short_code,
        "createdAt": url_entry.created_at,
        "updatedAt": url_entry.updated_at,
        "accessCount": url_entry.access_count
    }), 200

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
