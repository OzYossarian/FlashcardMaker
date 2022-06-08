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
            translations = translate_phrases(flashcard_maker, phrases)
            flashcard_maker.update_anki()

            full_phrases = add_translations_to_phrases(phrases, translations)
            post_back_to_database(full_phrases)
        log(f'Successfully checked for new flashcards!')
    except Exception as e:
        log(str(e))


def post_back_to_database(phrases):
    log(f'Posting results back to database...')
    for phrase in phrases:
        if phrase.id is not None:
            # Add translation to existing record
            url = phrase_url + phrase.id
            pass
        else:
            # Save new copy of existing record with translation attached.
            # TODO - change this design! Just about works for now with the
            #  current server implementation.
            url = phrase_url
            pass
        body = json.dumps(phrase, cls=RecursiveJsonEncoder)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': get_authorization('Teague')}
        requests.post(url, data=body, headers=headers)


def add_translations_to_phrases(phrases, translations):
    # TODO - bad design to convert one initial phrase in database into several
    #  records with translations. Better to have two collections in database?
    #  One for phrases and the other for translations. OR just allow phrase
    #  to have multiple translation documents in database - duh.
    log(f'Adding translations to phrases...')
    now = datetime.now()
    full_phrases = []
    for phrase, phrase_translations in zip(phrases, translations):
        # Mark as flashcarded
        # TODO - check actually has been flashcarded, and come up with better
        #  design for marking something as untranslatable.
        phrase.flashcard_date = now
        full_phrases.append(phrase)
        if len(phrase_translations) > 0:
            phrase.translation = phrase_translations[0]
            remainder = phrase_translations[1:]
            for translation in remainder:
                log(f'Multiple translations found for {phrase.german}...')
                copied = copy(phrase)
                copied.id = None
                copied.translation = translation
                full_phrases.append(copied)
    return full_phrases


def translate_phrases(flashcard_maker, phrases):
    translations = []
    for phrase in phrases:
        if phrase.english == '':
            log(f'Auto-translating {phrase.german}...')
            phrase_translations, _ = \
                flashcard_maker.create(phrase.german, new_log_entry=False)
            translations.append(phrase_translations)
        else:
            log(f'Translation given: {phrase.german} = {phrase.english}...')
            phrase_translation = Translation(
                german=phrase.german,
                english=phrase.english)
            log(f'Converting given translation to note...')
            flashcard_maker.note_taker.add_note(phrase_translation)
            translations.append([phrase_translation])
    return translations


def get_unflashcarded_phrases():
    log('Checking database for unflashcarded phrases...')
    headers = {'Authorization': get_authorization('Teague')}
    # By default, we only get unflashcarded phrases
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
    running_processes = [process.name() for process in psutil.process_iter()]
    # Anki has different name depending on what version, OS, etc.
    anki_open = 'AnkiMac' in running_processes or 'anki' in running_processes
    if not anki_open:
        log('Opening anki...')
        # Apparently this is best done in a subprocess. But this design is
        # temporary so I don't give a fook. Is also Mac specific.
        os.system("open /Applications/Anki.app")
        # Give it a few seconds to open
        time.sleep(5)
    else:
        log('Anki already open...')


main()
