from flask import Flask, render_template, Response, send_file, request, session, redirect, url_for
import camera
import flask_httpauth
import config
import os
import io
import threading
import time
import hashlib
import logging
import datetime
import ssl
import cloud
import sys

# Initialize Flask app and configuration
app = Flask(__name__)
conf = config.Configuration()
logging.basicConfig(filename='app.log', level=logging.DEBUG)
auth = flask_httpauth.HTTPBasicAuth()
app.secret_key = os.urandom(24)

# Global user and online status
user = None
online = None

# Initialize camera and cloud objects
cmra = camera.VideoCamera(conf)
drop = cloud.DropObj(conf)

@auth.get_password
def get_pw(username):
    global user
    user = username
    try:
        return conf.get('User')[username]
    except KeyError:
        return None

@auth.hash_password
def hash_pw(password):
    # Ensure bytes for hashing
    return hashlib.sha224(password.encode('utf-8')).hexdigest()

@app.route('/', methods=['GET', 'POST'])
@auth.login_required
def index():
    global online
    cloud_upload = False
    error = ''
    if request.method == 'POST':
        key = request.form.get('code')
        drop.auth(key)
        dropbox = '#'
    else:
        dropbox = drop.get_website()
        if conf.get('Cloud').get('token', 'none') == 'none':
            error = "You need to register your Dropbox account first, go to settings tab."
        if request.args.get('options') == 'record':
            if 'cloud' in request.args:
                cloud_upload = True
            recording = threading.Thread(target=cmra.record, args=[cloud_upload, drop])
            recording.start()
            session['options'] = 'record'
            return '<img id="bg" src="/video_feed_record" width="320" height="240" >'
        # for images
        if request.args.get('options') == 'image':
            if 'cloud' in request.args:
                cloud_upload = True
            image_capture = threading.Thread(target=capture_and_upload_image, args=[cloud_upload, drop])
            image_capture.start()
            return '', 204

    return render_template('index.html', online=online, dropbox=dropbox, error=error)

def gen(camera_obj, save=False, vstart=False):
    while True:
        frame = camera_obj.get_frame(False, save, vstart)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

def capture_and_upload_image(cloud_upload, drop):
    # capture image and upload to dropbox if required
    timestr = time.strftime("%Y%m%d-%H%M%S")
    image_path = conf.get('File').get('photos', './')  # Default to current directory if not set
    filename = os.path.join(image_path, 'image' + timestr + '.jpg')
    frame = cmra.get_frame(False)
    with open(filename, 'wb') as f:
        f.write(frame)
    logging.info('Image captured at  ' + str(datetime.datetime.now()))
    if cloud_upload:
        try:
            dropbox_path = '/image' + timestr + '.jpg'
            drop.upload_file(frame, dropbox_path)
            logging.info(f"Image uploaded to Dropbox: {dropbox_path}")
        except Exception as e:
            logging.error(f"Dropbox upload failed: {e}")

@app.route('/audio', methods=['POST'])
@auth.login_required
def audio():
    file = request.files.get('edition[audio]')
    if file:
        timestamp = str(time.time())
        filename = "audio" + timestamp + ".wav"
        file.save(filename)
        cmra.playAudio(timestamp)
        return ('', 204)
    return ('No audio uploaded', 400)

@app.route('/video_feed')
@auth.login_required
def video_feed():
    if 'options' in session:
        if session['options'] == 'record':
            return Response(gen(cmra, False, True),
                            mimetype='multipart/x-mixed-replace; boundary=frame')
    return Response(gen(cmra),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_record')
@auth.login_required
def video_feed_record():
    return Response(gen(cmra, False, True),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_frame')
@auth.login_required
def get_frame():
    frame = cmra.get_frame(False)
    if request.args.get('options') == 'save':
        timestr = time.strftime("%Y%m%d-%H%M%S")
        image_path = conf.get('File').get('photos', './')  # Default to current directory if not set
        filename = os.path.join(image_path, 'image' + timestr + '.jpg')
        with open(filename, 'wb') as f:
            f.write(frame)
        logging.info('Image captured at  ' + str(datetime.datetime.now()))

        # Cloud upload logic for images
        if 'cloud' in request.args:
            try:
                dropbox_path = '/image' + timestr + '.jpg'
                drop.upload_file(frame, dropbox_path)
                logging.info(f"Image uploaded to Dropbox: {dropbox_path}")
            except Exception as e:
                logging.error(f"Dropbox upload failed: {e}")

        return ('', 204)
    return send_file(io.BytesIO(frame), mimetype='image/jpeg')

@app.route('/stopV')
@auth.login_required
def stopV():
    session.pop('options', None)
    cmra.endVideo()
    return '<img id="bg" src="/video_feed" width="320" height="240" >'

@app.route('/toggle_online', methods=['POST'])
@auth.login_required
def toggle_online():
    global online
    if 'submit' in request.form:
        cmra.online = True
        return redirect(url_for('index'))
    sens = int(request.form.get('sensitive', '1'))
    method = request.form.get('method', '')
    sound = 'chk-sound' in request.form
    mail = 'chk-mail' in request.form
    notify = 'chk-not' in request.form
    online = threading.Thread(target=cmra.start, args=[sens, method, mail, sound, notify])
    online.start()
    return redirect(url_for('index'))

if __name__ == "__main__":
    debug_mode = True
    # Force http for LAN/hotspot streaming
    force_plain_http = True

    # Read host/port from config or use defaults
    host = conf.get('Connection').get('ip', '0.0.0.0')
    port = int(conf.get('Connection').get('port', '8080'))

    print(f"\n[INFO] Starting server on http://{host}:{port}/", flush=True)
    if host != '0.0.0.0':
        print("[WARNING] You are not binding to 0.0.0.0. LAN access may not work.", flush=True)

    if not force_plain_http and conf.boolean('Connection', 'https'):
        # Only use SSL if you know what you are doing!
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.load_cert_chain(conf.get('Connection')['certificate'], conf.get('Connection')['key'])
        print(f"[INFO] SSL enabled. Access via https://{host}:{port}/", flush=True)
        app.run(debug=debug_mode,
                threaded=True,
                host=host,
                port=port,
                ssl_context=context)
    else:
        app.run(debug=debug_mode,
                threaded=True,
                host=host,
                port=port)