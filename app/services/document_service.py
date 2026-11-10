"""
Rydeon - Customer Document Processing Service
----------------------------------------------
Validates and safely stores customer identification documents (driving licenses,
passports) and records verification states in MySQL.
"""

import os
import time
from werkzeug.utils import secure_filename
from flask import current_app
from app.database.db import execute_query

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 Megabytes

def allowed_file(filename):
    """Checks whether the file has an approved extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_and_save_document(user_id, booking_id, document_type, file_storage):
    """
    Validates file format, size, saves to uploads/documents, and records in MySQL.
    Returns (True, document_dict) on success, or (False, error_string) on failure.
    """
    if not file_storage or file_storage.filename == '':
        return False, "No file was selected for upload."

    if not allowed_file(file_storage.filename):
        return False, f"Invalid file format. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS).upper()}."

    # Validate file size by reading chunk or checking content length
    file_storage.seek(0, os.SEEK_END)
    file_size = file_storage.tell()
    file_storage.seek(0)

    if file_size > MAX_FILE_SIZE:
        return False, f"File exceeds maximum permissible size of 5 MB ({file_size / (1024*1024):.1f} MB uploaded)."

    # Determine upload directory
    base_upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads') if current_app else 'uploads'
    docs_dir = os.path.join(base_upload_dir, 'documents')
    os.makedirs(docs_dir, exist_ok=True)

    # Generate secure, collision-free filename
    ext = file_storage.filename.rsplit('.', 1)[1].lower()
    clean_original = secure_filename(file_storage.filename.rsplit('.', 1)[0])[:20]
    timestamp = int(time.time())
    b_id = booking_id if booking_id else 'profile'
    unique_filename = f"doc_u{user_id}_b{b_id}_{clean_original}_{timestamp}.{ext}"
    relative_path = os.path.join('uploads', 'documents', unique_filename).replace('\\', '/')
    absolute_dest = os.path.join(docs_dir, unique_filename)

    file_storage.save(absolute_dest)

    # Record in MySQL
    sql = """
        INSERT INTO documents (user_id, booking_id, document_type, file_path, verification_status)
        VALUES (%s, %s, %s, %s, 'pending')
    """
    result = execute_query(sql, (user_id, booking_id, document_type, relative_path), commit=True)
    doc_id = result['lastrowid']

    doc_row = execute_query("SELECT id, user_id, booking_id, document_type, file_path, verification_status, uploaded_at FROM documents WHERE id = %s", (doc_id,), fetch_one=True)
    return True, doc_row

def get_booking_documents(booking_id, user_id=None):
    """Retrieves all documents associated with a specific booking."""
    sql = """
        SELECT id, user_id, booking_id, document_type, file_path, verification_status, uploaded_at
        FROM documents
        WHERE booking_id = %s
    """
    params = [booking_id]
    if user_id:
        sql += " AND user_id = %s"
        params.append(user_id)
    sql += " ORDER BY uploaded_at DESC"
    return execute_query(sql, tuple(params), fetch_all=True)
