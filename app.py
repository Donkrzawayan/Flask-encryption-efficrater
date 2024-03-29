import os
import secrets
import time

from flask import Flask, render_template, request, flash, redirect, send_from_directory, send_file, session, Response
from flask_session import Session
from werkzeug.utils import secure_filename

import model
from model import UploadManager, DownloadManager

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads/'
if not os.path.exists(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)
ALLOWED_EXTENSIONS = {'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = secrets.token_hex(24)


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _get_key(redirect_path):
    if 'key' not in request.files:
        flash('No file part')
        return redirect(redirect_path)
    key = request.files['key']
    if key.filename == '':
        flash('No selected file')
        return redirect(redirect_path)
    if not key:
        flash('Corrupted file')
        return redirect(redirect_path)
    return key


def _get_file():
    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    # If the user does not select a file, the browser submits an empty file without a filename.
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    # Check if the user selected a file with allowed extension
    if not file or not _allowed_file(file.filename):
        flash('Not an allowed file extension')
        return redirect(request.url)
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return filename


@app.route('/generate_key', methods=['POST'])
def generate_key():
    key = os.urandom(32)
    return Response(
        key,
        mimetype='text/plain',
        headers={'Content-disposition': 'attachment; filename=aes.key'}
    )


@app.route('/generate_keys', methods=['POST'])
def generate_keys():
    zip = model.generate_keys()
    return send_file(
        zip,
        mimetype='application/zip',
        as_attachment=True,
        download_name='keys.zip'
    )


@app.route('/upload_file', methods=['POST'])
def upload_file():
    select = session['select']
    key = session['key']
    file = _get_file()
    start = time.perf_counter()
    filename = UploadManager(app.config['UPLOAD_FOLDER']).caller(select, file, key)
    end = time.perf_counter()
    flash(f'{file} processing time: {end - start}\n')
    return redirect(f'/file/{filename}')


@app.route('/upload', methods=['POST'])
def upload():
    session['select'] = request.form['encrypt_types']
    session['key'] = _get_key('/').read()

    return render_template('upload.html')


@app.route('/file/<name>')
def uploaded_file(name):
    return render_template('file.html', filename=name)


@app.route('/file/<name>/download')
def download_file(name):
    start = time.perf_counter()
    send = send_from_directory(app.config['UPLOAD_FOLDER'], name)
    end = time.perf_counter()
    flash(f'{name} downloading time: {end - start}')
    return send


@app.route('/file/<name>', methods=['POST'])
def download(name):
    key = _get_key(f'/file/{name}').read()
    select = request.form['encrypt_types']
    start = time.perf_counter()
    file = DownloadManager(app.config['UPLOAD_FOLDER']).caller(select, name, key)
    end = time.perf_counter()
    flash(f'{name} processing time: {end - start}\n')
    return file


@app.route('/', methods=['GET', 'POST'])
def index():
    upload_folder = app.config['UPLOAD_FOLDER']
    if request.method == 'POST':
        start = time.perf_counter()
        filename = _get_file()
        end = time.perf_counter()
        flash(f'{filename} uploading time: {end - start}')
    filenames = [f for f in os.listdir(upload_folder) if os.path.isfile(os.path.join(upload_folder, f))]
    return render_template('uploaded.html', filenames=filenames) if filenames else render_template('index.html')


if __name__ == '__main__':
    app.config['SESSION_TYPE'] = 'filesystem'
    Session(app)
    app.run(debug=True)
