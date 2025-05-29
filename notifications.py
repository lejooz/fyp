import requests
import time

class Notification(object):
    def __init__(self, conf):
        # Store your Telegram bot token and chat ID from config.
        self.telegram_token = conf.get('Notifications').get('telegram_token', '')
        self.telegram_chat_id = conf.get('Notifications').get('telegram_chat_id', '')

    def send_notification(self, message=None):
        if message is None:
            # Default message if none is provided
            message = (
                "🚨 Suspicious activity detected!\n"
                f"{time.strftime('%c')}\n"
                "For more information, please check your Cyber-cam web interface."
            )

        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        data = {
            "chat_id": self.telegram_chat_id,
            "text": message
        }

        try:
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to send Telegram notification: {e}")