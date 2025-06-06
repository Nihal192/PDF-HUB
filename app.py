from flask import Flask, request, send_file, render_template, redirect, url_for, session
from functools import wraps
from werkzeug.utils import secure_filename
import os
from PyPDF2 import PdfReader, PdfWriter
from pdf2docx import Converter
from PIL import Image

app = Flask(__name__)
app.secret_key = 'change-this-secret-key'

USERS = {
    'admin': 'password'
}

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in USERS and USERS[username] == password:
            session['username'] = username
            return redirect(url_for('home'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    return render_template('index.html')

@app.route('/pdf-to-word', methods=['GET'])
@login_required
def pdf_to_word():
    return render_template('pdf_to_word_form.html')

@app.route('/convert-pdf-to-word', methods=['POST'])
@login_required
def convert_pdf_to_word():
    if 'file' not in request.files:
        return 'No file part', 400
    
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        docx_filename = f"{os.path.splitext(filename)[0]}.docx"
        docx_filepath = os.path.join(app.config['UPLOAD_FOLDER'], docx_filename)
        
        cv = Converter(filepath)
        cv.convert(docx_filepath)
        cv.close()
        
        return render_template('download.html', filename=docx_filename)
    
    return 'Invalid file type', 400

@app.route('/split-pdf', methods=['GET'])
@login_required
def split_pdf_form():
    return render_template('split_pdf_form.html')

@app.route('/split-pdf', methods=['POST'])
@login_required
def split_pdf_upload():
    if 'file' not in request.files:
        return 'No file part', 400
    
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            start_page = int(request.form['start_page'])
            end_page = int(request.form['end_page'])
            
            pdf_reader = PdfReader(filepath)
            pdf_writer = PdfWriter()
            
            if start_page < 1 or end_page > len(pdf_reader.pages) or start_page > end_page:
                return 'Invalid page range', 400
            
            for page_num in range(start_page - 1, end_page):
                pdf_writer.add_page(pdf_reader.pages[page_num])
            
            split_filename = f"{os.path.splitext(filename)[0]}_pages_{start_page}_to_{end_page}.pdf"
            split_filepath = os.path.join(app.config['UPLOAD_FOLDER'], split_filename)
            
            with open(split_filepath, 'wb') as output_pdf:
                pdf_writer.write(output_pdf)
            
            return render_template('split_pdf_download.html', split_filename=split_filename)
        
        except Exception as e:
            return f"An error occurred during PDF processing: {str(e)}", 500
    
    return 'Invalid file type', 400

@app.route('/merge-pdf', methods=['GET'])
@login_required
def merge_pdf_form():
    return render_template('merge_pdf_form.html')

@app.route('/merge-pdf', methods=['POST'])
@login_required
def merge_pdf():
    if 'file1' not in request.files or 'file2' not in request.files:
        return 'No file part', 400
    
    file1 = request.files['file1']
    file2 = request.files['file2']

    if file1.filename == '' or file2.filename == '':
        return 'No selected file', 400

    if file1 and allowed_file(file1.filename) and file2 and allowed_file(file2.filename):
        try:
            filename1 = secure_filename(file1.filename)
            filename2 = secure_filename(file2.filename)
            
            filepath1 = os.path.join(app.config['UPLOAD_FOLDER'], filename1)
            filepath2 = os.path.join(app.config['UPLOAD_FOLDER'], filename2)

            file1.save(filepath1)
            file2.save(filepath2)
            
            pdf_writer = PdfWriter()

            pdf_reader1 = PdfReader(filepath1)
            pdf_reader2 = PdfReader(filepath2)
            
            for page in pdf_reader1.pages:
                pdf_writer.add_page(page)
            
            for page in pdf_reader2.pages:
                pdf_writer.add_page(page)
            
            merged_filename = f"merged_{filename1.rsplit('.', 1)[0]}_{filename2.rsplit('.', 1)[0]}.pdf"
            merged_filepath = os.path.join(app.config['UPLOAD_FOLDER'], merged_filename)
            
            with open(merged_filepath, 'wb') as merged_pdf:
                pdf_writer.write(merged_pdf)
            
            return render_template('merge_pdf_download.html', filename=merged_filename)

        except Exception as e:
            return f"An error occurred during PDF processing: {str(e)}", 500

    return 'Invalid file type', 400

@app.route('/image-to-pdf', methods=['GET'])
@login_required
def image_to_pdf_form():
    return render_template('image_to_pdf_form.html')

@app.route('/image-to-pdf', methods=['POST'])
@login_required
def convert_images_to_pdf():
    if 'images' not in request.files:
        return 'No file part', 400

    files = request.files.getlist('images')
    if not files:
        return 'No selected file', 400

    images = []
    for file in files:
        if file.filename == '' or not allowed_image(file.filename):
            return 'Invalid file type', 400
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        img = Image.open(filepath).convert('RGB')
        images.append(img)

    if not images:
        return 'No valid images', 400

    pdf_filename = 'images_combined.pdf'
    pdf_filepath = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
    first_image, *rest = images
    first_image.save(pdf_filepath, save_all=True, append_images=rest)

    return render_template('image_to_pdf_download.html', filename=pdf_filename)

@app.route('/download/<filename>', methods=['GET'])
@login_required
def download_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
