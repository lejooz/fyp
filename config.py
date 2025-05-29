import configparser
import hashlib

class Configuration(object):
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read("conf.ini")

    def write(self, section, attr, value):
        self.config.set(section, attr, value)
        with open("conf.ini", 'w') as cfgfile:
            self.config.write(cfgfile)

    def get(self, section):
        dict1 = {}
        options = self.config.options(section)
        for option in options:
            try:
                dict1[option] = self.config.get(section, option)
                if dict1[option] == -1:
                    print("skip: %s" % option)
            except Exception as e:
                print("exception on %s! %s" % (option, e))
                dict1[option] = None
        return dict1

    def boolean(self, section, attr):
        return self.config.getboolean(section, attr)

    def is_exist(self, category, option):
        return self.config.has_option(category, option)

    def hash(self, string):
        return hashlib.sha224(string.encode("utf-8")).hexdigest()

    # Encryption/Decryption methods can be implemented if needed,
    # but for now, only config file management and hashing are included.