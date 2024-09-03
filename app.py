from flask import Flask, request, send_file, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import os
from PyPDF2 import PdfReader, PdfWriter
from pdf2docx import Converter

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/pdf-to-word', methods=['GET'])
def pdf_to_word():
    return render_template('pdf_to_word_form.html')

@app.route('/convert-pdf-to-word', methods=['POST'])
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
def split_pdf_form():
    return render_template('split_pdf_form.html')

@app.route('/split-pdf', methods=['POST'])
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
def merge_pdf_form():
    return render_template('merge_pdf_form.html')

@app.route('/merge-pdf', methods=['POST'])
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

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
