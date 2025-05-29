import cv2
import mailer
import logging
import time
import datetime
import pygame
import notifications

logging.basicConfig(filename='app.log', level=logging.DEBUG)
pygame.mixer.init()

class VideoCamera(object):
    binary = True

    def __init__(self, config):
        self.config = config
        self.video = cv2.VideoCapture(int(self.config.get('Video')['camera']))
        self.videoWriter = None
        self.online = False
        self.recording = False
        self.first_captured = None
        # Notification now uses Telegram config
        self.notification = notifications.Notification(config)

    def __del__(self):
        self.video.release()

    def finished(self):
        self.video.release()
        if self.notification:
            self.notification.release()

    def start(self, sens, method, mail, sound, notif):
        self.online = False
        logging.info('Active security started at ' + str(datetime.datetime.now()))
        iterator = 0
        repeated = 0
        sequence_capture = False
        self.first_captured = None
        while True:
            success, image = self.video.read()
            if not success:
                continue
            iterator += 1
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Select detection method
            if method == 'face':
                faceCascade = cv2.CascadeClassifier("haarcascade/faceDetect.xml")
            elif method == 'ubody':
                faceCascade = cv2.CascadeClassifier("haarcascade/haarcascade_upperbody.xml")
            elif method == 'fbody':
                faceCascade = cv2.CascadeClassifier("haarcascade/haarcascade_fullbody.xml")
            elif method == 'move':
                if self.first_captured is None:
                    self.first_captured = gray
                frameDelta = cv2.absdiff(self.first_captured, gray)
                self.first_captured = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
                thresh = cv2.dilate(thresh, None, iterations=2)
                (cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for c in cnts:
                    if cv2.contourArea(c) < int(self.config.get('Video')['min_movement_object']):
                        continue
                    repeated += 1
                    break

            if method in ['ubody', 'fbody', 'face']:
                faces = faceCascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    flags=0)
                if type(faces) is not tuple:
                    if sequence_capture:
                        repeated += 1
                    sequence_capture = True
                else:
                    sequence_capture = False
                    repeated = 0

            if self.online:
                logging.info('Active security Stopped by user at ' + str(datetime.datetime.now()))
                self.first_captured = None
                return

            if repeated == (6 - sens):
                logging.info('Figure has been Detected at ' + str(datetime.datetime.now()))
                ret, jpeg = cv2.imencode('.jpg', image)
                img = jpeg.tobytes()
                if notif:
                    try:
                        logging.info('Sending notification  ' + str(datetime.datetime.now()))
                        # Send Telegram notification
                        if self.notification:
                            self.notification.send_notification(
                                message="🚨 Suspicious activity detected!\n"
                                        f"{time.strftime('%c')}\n"
                                        "For more information, please check your Cyber-cam web interface."
                            )
                    except Exception as e:
                        logging.warning(f'Error sending notification at {str(datetime.datetime.now())}: {e}')
                if sound:
                    pygame.mixer.music.load(self.config.get('Sound')['alarm'])
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        continue
                if mail:
                    try:
                        logging.info('Sending email ' + str(datetime.datetime.now()))
                        mailer.sendMessege(img, self.config)
                    except Exception as e:
                        logging.info(f'Error Sending Mail at {str(datetime.datetime.now())}: {e}')
                self.first_captured = None
                return

            if iterator == 10:
                iterator = 0
                repeated = 0

    def record(self, upload, cloud):
        self.recording = True
        logging.info('Video recording started at ' + str(datetime.datetime.now()))
        timestr = time.strftime("%Y%m%d-%H%M%S")
        video_path = self.config.get('File')['videos'] + 'video' + timestr + ".avi"
        # Get frame size from camera properties
        frame_width = int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
        videoWriter = cv2.VideoWriter(
            video_path,
            fourcc,
            int(self.config.get('Video')['fps']),
            (frame_width, frame_height)
        )
        while self.recording:
            while True:
                success, image = self.video.read()
                if not success:
                    continue
                else:
                    break
            if self.recording:
                videoWriter.write(image)
                time.sleep(0.08)
        videoWriter.release()
        if upload:
            with open(video_path, 'rb') as f:
                data = f.read()
                cloud.upload_file(data, '/video' + timestr + ".avi")

    def playAudio(self, audio_time):
        audio_file = "audio" + audio_time + ".wav"
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            continue

    def endVideo(self):
        self.recording = False

    def get_frame(self, faced, saved=False, video=False, videoStop=False):
        while True:
            success, image = self.video.read()
            if not success:
                continue
            else:
                break
        if video:
            cv2.circle(image, (100, 20), 15, (0, 0, 255), -1)
        if faced:
            faceCascade = cv2.CascadeClassifier("haarcascade/faceDetect.xml")
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = faceCascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                flags=0)
            for (x, y, w, h) in faces:
                cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            ret, jpeg = cv2.imencode('.jpg', image)
            return jpeg.tobytes()
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()