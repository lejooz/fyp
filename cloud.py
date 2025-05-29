import dropbox

class DropObj(object):
    def __init__(self, conf):
        self.app_key = 'ck2ifx3agl50908'
        self.app_secret = 'w95xtn3ouucj6ru'
        self.token = conf.get('Cloud')['token']
        self.client = None
        self.flow = None
        self.conf = conf

        if self.token != 'none':
            try:
                self.client = dropbox.Dropbox(self.token)
            except Exception as e:
                print("Dropbox client initialization failed:", e)
                self.client = None

    def get_website(self):
        # This returns the Dropbox OAuth2 URL to start the authentication flow if not already authenticated
        if self.client is None:
            self.flow = dropbox.DropboxOAuth2FlowNoRedirect(self.app_key, self.app_secret)
            return self.flow.start()
        return 'http://#'  # Already authenticated; button should be disabled in the UI

    def auth(self, key):
        # This exchanges the user-provided code for an access token and stores it
        if self.token != 'none':
            self.client = dropbox.Dropbox(self.token)
        else:
            key = key.strip()
            try:
                access_token, user_id = self.flow.finish(key)
                self.conf.write('Cloud', 'token', access_token)
                self.token = access_token
                self.client = dropbox.Dropbox(access_token)
            except Exception as e:
                print("Dropbox authentication failed:", e)
                self.client = None

    def upload_file(self, file, name):
        # file should be a bytes object, name is the Dropbox path (e.g. '/photo.jpg')
        if self.client:
            try:
                self.client.files_upload(file, name)
            except Exception as e:
                print("Dropbox upload failed:", e)