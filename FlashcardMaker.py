from datetime import datetime

from anki.Connector import Connector
from anki.NoteTaker import NoteTaker
from logs.log import log
from translation.Translator import Translator


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
