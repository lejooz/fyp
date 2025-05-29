import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import datetime

def send_notification(conf):
    _user = conf.get('Mailer')['username']
    _pwd = conf.get('Mailer')['password']
    FROM = _user
    TO = [conf.get('Mailer')['to']]
    SUBJECT = "Figure Detected"
    date = str(datetime.datetime.utcnow())
    TEXT = f"A figure was detected at {date} ,image was sent via mail"

    msg = MIMEText(TEXT)
    msg['From'] = FROM
    msg['To'] = ", ".join(TO)
    msg['Subject'] = SUBJECT

    try:
        server = smtplib.SMTP_SSL(conf.get('Mailer')['smtp'], int(conf.get('Mailer')['port']))
        server.login(_user, _pwd)
        server.sendmail(FROM, TO, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Failed to send notification email: {e}")

def sendMessege(img_data, conf):
    _user = conf.get('Mailer')['username']
    _pwd = conf.get('Mailer')['password']

    msg = MIMEMultipart()
    msg['Subject'] = 'Figure Detected!'
    msg['From'] = _user
    toList = conf.get('Mailer')['to'].split(",")
    msg['To'] = ", ".join(toList)
    FROM = _user
    TO = toList

    text = MIMEText("Hi, This figure was captured by Cyber Camera")
    msg.attach(text)
    image = MIMEImage(img_data, _subtype="jpg")
    msg.attach(image)

    try:
        server = smtplib.SMTP_SSL(conf.get('Mailer')['smtp'], int(conf.get('Mailer')['port']))
        server.login(_user, _pwd)
        server.sendmail(FROM, TO, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Failed to send image email: {e}")

def send_email_address(data, conf):
    _user = conf.get('Mailer')['username']
    _pwd = conf.get('Mailer')['password']

    msg = MIMEMultipart()
    msg['Subject'] = 'IP address for cyber camera'
    msg['From'] = _user
    toList = conf.get('Mailer')['to'].split(",")
    msg['To'] = ", ".join(toList)
    FROM = _user
    TO = toList

    text = MIMEText(f"Your IP address has been changed to: {data}")
    msg.attach(text)

    try:
        server = smtplib.SMTP_SSL(conf.get('Mailer')['smtp'], int(conf.get('Mailer')['port']))
        server.login(_user, _pwd)
        server.sendmail(FROM, TO, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Failed to send IP address email: {e}")