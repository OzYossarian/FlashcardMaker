import os.path
from datetime import datetime

from main.anki.Connector import Connector
from main.anki.NoteTaker import NoteTaker
from main.logs.log import log
from main.translation.Translator import Translator


class FlashcardMaker:
    def __init__(self):
        self.translator = Translator()
        self.note_taker = NoteTaker()
        self.connector = Connector()

    def create(self, phrase: str, new_log_entry=True):
        translations = self.translator.translate(phrase, new_log_entry)
        notes = [
            self.note_taker.add_note(translation)
            for translation in translations]
        return translations, notes

    def update_anki(self):
        log(f'Updating Anki...')
        now = datetime.now().strftime('%Y%m%d_%H%M%S')
        deck_apkg = self.note_taker.output_deck(now)
        self.connector.request('importPackage', path=deck_apkg)
        self.connector.request('sync')
        # Tidy up by deleting the .apkg file immediately
        if os.path.exists(deck_apkg):
            os.remove(deck_apkg)

