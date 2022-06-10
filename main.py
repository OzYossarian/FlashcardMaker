import json
from copy import copy
from datetime import datetime
import os
import time

import psutil
import requests

from FlashcardMaker import FlashcardMaker
from server.Phrase import Phrase
from server.authorization import tokens
from logs.log import log
from translation.Translation import Translation
from utils import RecursiveJsonEncoder

base_url = 'https://crunchy-nut-server.herokuapp.com'
phrase_url = base_url + '/phrase/'

# Temporary design: have a python script that we set the OS to run every x
# minutes. In this script, get unflashcarded phrases from crunchy nut server,
# translate them, then create flashcards for them and import into Anki.
# Should check Anki running and if not open it.


def main():
    try:
        log('Flashcard maker booting up...', new_entry=True)
        openAnki()
        phrases = get_unflashcarded_phrases()
        if len(phrases) > 0:
            flashcard_maker = FlashcardMaker()
            translate_phrases(flashcard_maker, phrases)
            flashcard_maker.update_anki()
            post_back_to_database(phrases)
        log(f'Successfully checked for new flashcards!')
    except Exception as e:
        log(str(e))


def post_back_to_database(phrases):
    log(f'Posting results back to database...')
    for phrase in phrases:
        url = phrase_url + phrase.id
        # TODO - check JSON encoder works on list of translations.
        body = json.dumps(phrase, cls=RecursiveJsonEncoder)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': get_authorization('Teague')}
        requests.post(url, data=body, headers=headers)


def translate_phrases(flashcard_maker, phrases):
    for phrase in phrases:
        now = datetime.now()
        if phrase.translations:
            log(f'Translations exist for {phrase.german} - flashcarding...')
            # Has already been translated, so just needs flashcarding.
            for translation in phrase.translations:
                flashcard_maker.note_taker.add_note(translation)
            phrase.flashcard_date = now
        else:
            # Needs translating and flashcarding
            if phrase.english == '':
                log(f'Auto-translating {phrase.german} then flashcarding...')
                translations, _ = \
                    flashcard_maker.create(phrase.german, new_log_entry=False)
                phrase.translations = translations
            else:
                log(f'Translation given: {phrase.german} = {phrase.english}...')
                translation = Translation(
                    german=phrase.german,
                    english=phrase.english)
                log(f'Converting given translation to note...')
                flashcard_maker.note_taker.add_note(translation)
                phrase.translations = [translation]
            phrase.translation_date = now
            # Mark phrase as flashcarded - even if we didn't actually find any
            # translations. This ensures we don't keep redownloading this
            # phrase to try to translate it, knowing it won't work.
            phrase.flashcard_date = now


def get_unflashcarded_phrases():
    # We get all unflashcarded phrases. These may already be translated (e.g.
    # if another user already shared this phrase and thus it was translated
    # then, or if making the flashcard just failed earlier for some reason).
    log('Checking database for unflashcarded phrases...')
    headers = {'Authorization': get_authorization('Teague')}
    response = requests.get(phrase_url, headers=headers)
    phrases = [Phrase.from_data(data) for data in response.json()]
    log(f'Got {len(phrases)} phrases...')
    return phrases


def get_authorization(owner: str):
    authorization = '{' \
        f'"name": "{owner}", ' \
        f'"token": "{tokens[owner]}"}}'
    return authorization


def openAnki():
    # Open Anki if it isn't open already.
    processes = [process.name() for process in psutil.process_iter()]
    # Anki has different name depending on what version, OS, etc.
    anki_open = any(['anki' in process.lower() for process in processes])
    if not anki_open:
        log('Opening Anki...')
        # Apparently this is best done in a subprocess. But this design is
        # temporary so I don't give a fook. Is also Mac specific.
        os.system("open /Applications/Anki.app")
        # Give it a few seconds to open
        time.sleep(5)
    else:
        log('Anki already open...')


main()
