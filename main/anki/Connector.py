import requests

from main.logs.log import log


class Connector:
    def __init__(self):
        # Eventually server will need to log in to several people's Anki
        # accounts, so an Authorizer will be needed. For now, it isn't.
        # (Not sure if this comment applies to NoteTaker or Connector!)
        # (Nor sure if this is even possible! :((( Sad times)
        self.version = 4  # Minimum possible - will update in a sec hopefully.
        self.initialised = False
        try:
            version = self.initialise()
            if version is not None:
                self.version = version
        except Exception as e:
            log(f'Error initialising AnkiConnect: {str(e)}')

    def initialise(self):
        permission = self.request('requestPermission')
        if permission['permission'] == 'granted':
            version = permission['version']
            log(f'Initialised AnkiConnect version {version}')
            return version
        else:
            log(f'Permission to connect to Anki denied.')
            return None

    def request(self, action: str, **params):
        data = {'action': action, 'params': params, 'version': self.version}
        response = requests.post('http://localhost:8765', json=data)
        return response.json()