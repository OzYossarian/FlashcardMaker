import json
from typing import Iterable

import requests

from main.logs.log import log
from main.server.Phrase import Phrase
from main.utils import RecursiveJsonEncoder
from main.server import authorization


class Server:
    def __init__(self):
        self.base_url = 'https://crunchy-nut-server.herokuapp.com'
        self.phrase_url = self.base_url + '/phrase/'

    def get_phrases(self, include_flashcarded=False):
        log('Checking database for phrases...')
        if include_flashcarded:
            log('Including already flashcarded phrases...')
        headers = {'Authorization': self.authorise()}
        params = {'flashcarded': str(include_flashcarded).lower()}
        response = requests.get(
            self.phrase_url, params=params, headers=headers)
        phrases = [Phrase.from_data(data) for data in response.json()]
        log(f'Got {len(phrases)} phrases...')
        return phrases

    def post_phrases(self, phrases: Iterable[Phrase]):
        log(f'Posting results back to database...')
        for phrase in phrases:
            id = phrase.id if phrase.id is not None else ''
            url = self.phrase_url + id
            # TODO - check JSON encoder works on list of translations.
            body = json.dumps(phrase, cls=RecursiveJsonEncoder)
            headers = {
                'Content-Type': 'application/json',
                'Authorization': self.authorise()}
            requests.post(url, data=body, headers=headers)

    @staticmethod
    def authorise():
        credentials = '{' \
            f'"name": "{authorization.name}", ' \
            f'"token": "{authorization.token}"}}'
        return credentials
