from flask import  render_template, request, jsonify, redirect, url_for, session
from app import app
from .minio_client import upload_video, get_url_video, get_url_thumb
import pyclamd, uuid
from data.orm import SyncORM
import bcrypt


def hash_password(password):
    salt = bcrypt.gensalt(rounds=10)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


@app.route("/")
def main():
    videos = SyncORM.get_all_video_uids()
    links = []
    for video in videos:
        thumb_url = get_url_thumb(video['uid'])
        links.append({
            "title": video["title"], 
            "thumb_url": thumb_url,
            "uid": video['uid']})
    return render_template('index.html', videos=links)

@app.route('/<string:uid>', methods=['GET', 'POST'])
def view_video(uid):
    if request.method == "POST":
        action = request.form.get('action')
        login = session.get('user_id')
        # video_uid = request.form.get('video_uid')
        if action == 'like':
            vote_type = request.form.get('vote_type')
            increase = request.form.get('increase') == 'true'

            SyncORM.vote(uid, vote_type, increase)

            return redirect(url_for('view_video', uid=uid))
        
        elif action == 'comment':
            if not login:
                return redirect(url_for('login'))
            
            text = request.form.get('text')

            SyncORM.add_comment(text, login, uid)

            return redirect(url_for('view_video', uid=uid))
    else:
        video = SyncORM.get_video_meta(uid)
        url = get_url_video(uid)
        comments = SyncORM.get_all_comments_video(uid)
        return render_template('video_page.html', video=video, video_url=url, comments=comments)

@app.route("/liking")
def liking():
    return render_template('liking.html')

@app.route("/settings")
def setting():
    return render_template('settings.html')

@app.route("/info")
def info():
    return render_template('info.html')

@app.route("/help")
def help():
    return render_template('help.html')

@app.route("/complaints")
def complaints():
    return render_template('complaints.html')

@app.route("/channel")
def channel():
    return render_template('channel.html')

@app.route('/upload')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        try:
            # Получаем файл из формы (multipart/form-data)
            title = request.form.get('title')
            description = request.form.get('description')
            file = request.files.get('video')
            if not file:
                return jsonify({'error': 'No video uploaded'}), 400

            # Подключение к clamd
            cd = pyclamd.ClamdNetworkSocket(host='26.48.28.173', port=3310)

            if not cd.ping():
                return jsonify({'error': 'ClamAV daemon is not available'}), 500
            
            # Перемещаем указатель в начало и скармливаем байты
            file.seek(0)
            result = cd.scan_stream(file.read())
            if result is not None:
                return jsonify({'error': 'File is infected', 'details': result}), 400

            file.seek(0)
            # Генерим уникальный ID
            uid = uuid.uuid4().hex
            upload_video(file, file.filename, uid)
            SyncORM.insert_meta_video(uid, title, description) # type: ignore

            # Возвращаем ID видео
            return jsonify({'message': 'Upload successful'}), 200
        except Exception as e:
            print('Ошибка регистрации:{e}')
            return jsonify({'message': 'Ошибка сервера'}), 500
    else:
        return render_template('upload.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            login = request.form.get('login')
            password = request.form.get('password')
            selected = request.form.get('option') == 'true'
            if not login:
                return "Логин обязателен"
            if not selected:
                #Проверка на существование пользователя
                user_password = SyncORM.get_user_password(login)
                if not user_password:
                    return jsonify({'message': 'User not found'})
                if not verify_password(password, user_password):
                    return jsonify({'message': 'Invalid password'}), 401

                session['user_id'] = login

                return redirect(url_for('main'))
            else:
                admin_password = SyncORM.get_admin_password(login)
                if not admin_password:
                    return jsonify({'message': 'Admin not found'})
                if not verify_password(password, admin_password):
                    return jsonify({'message': 'Invalid password'}), 401

                session['admin_id'] = login

                return redirect(url_for('admin'))
        except Exception as e:
            print(f"Ошибка авторизации: {e}")
            return jsonify({'message': 'Server error'}), 500
    else:
        return render_template("login.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            login = request.form.get('login')
            password = request.form.get('password')
            password2 = request.form.get('password2')

            if not login:
                return "Логин обязателен"

            #Проверка совпадения паролей
            if password != password2:
                return "Пароли не совпадают"
            
            #Проверка наличия пользователя
            if SyncORM.get_user_password(login):
                return 'Этот пользователь уже существует'
            
            #Хэширование пароля
            hashed_password = hash_password(password)

            #Записывание пользователя в БД
            SyncORM.add_user(login, hashed_password)

            return render_template('index.html')
        except Exception as e:
            return jsonify({'message': 'Ошибка сервера'}), 500
    else:
        return render_template('register.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')