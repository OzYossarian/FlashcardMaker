import os.path
from datetime import datetime

from main.anki.Connector import Connector
from main.anki.NoteTaker import NoteTaker
from main.logs.log import log
from main.server.Phrase import Phrase
from main.translation.Translator import Translator


class FlashcardMaker:
    def __init__(self):
        self.translator = Translator()
        self.note_taker = NoteTaker()
        self.connector = Connector()

    def create(self, phrase: Phrase, new_log_entry=True):
        phrase.translations = \
            self.translator.translate(phrase.german, new_log_entry)
        notes = [
            self.note_taker.add_note(translation, phrase.deck_name)
            for translation in phrase.translations]
        return notes

    def update_anki(self):
        log(f'Updating Anki...')
        now = datetime.now().strftime('%Y%m%d_%H%M%S')
        for deck_name in self.note_taker.decks:
            deck_apkg = self.note_taker.output_deck(now, deck_name)
            self.connector.request('importPackage', path=deck_apkg)
            # Tidy up by deleting the .apkg file immediately
            if os.path.exists(deck_apkg):
                os.remove(deck_apkg)
        self.connector.request('sync')

