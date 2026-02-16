import os

ALLOWED_EXTENSIONS = {"pdf"}


def allowed_file(filename):
    """
    Check file extension.
    """
    if "." not in filename:
        return False

    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def validate_pdf(file):
    """
    Validate uploaded file:
    - Must exist
    - Must be PDF extension
    - Must not be empty
    """
    if not file:
        return False, "No file selected."

    if file.filename == "":
        return False, "No file selected."

    if not allowed_file(file.filename):
        return False, "Only PDF files are allowed."

    # Optional: Check MIME type
    if file.mimetype != "application/pdf":
        return False, "Invalid file type. Only PDF allowed."

    return True, None
