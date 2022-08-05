from datetime import datetime
from pathlib import Path

import genanki

from main.translation.Translation import Translation
from main.utils import project_root, anki_id


class NoteTaker:
    def __init__(self):
        # Eventually server will need to log in to several people's Anki
        # accounts, so an Authorizer will be needed. For now, it isn't.
        # (Not sure if this comment applies to NoteTaker or Connector!)
        # (Nor sure if this is even possible! :((( Sad times)
        self.default_deck_name = 'Fluency Lube'
        default_deck_id = anki_id(self.default_deck_name)
        default_deck = genanki.Deck(default_deck_id, self.default_deck_name)
        self.decks = {
            self.default_deck_name: default_deck}

        self.model = self.default_model(self.default_deck_name)

    def add_note(self, translation: Translation, deck_name: str = None):
        fields = self.get_fields(translation)
        note = genanki.Note(self.model, fields)
        deck = self.get_deck(deck_name)
        deck.add_note(note)
        return note

    def output_deck(self, deck_name: str):
        now = datetime.now().strftime('%Y%m%d_%H%M%S')
        deck_file_name = deck_name.replace(' ', '_')
        relative_path = f'main/anki/output/{now}_{deck_file_name}.apkg'
        absolute_path = f'{project_root()}/{relative_path}'
        Path(absolute_path).parent.mkdir(parents=True, exist_ok=True)
        deck = self.get_deck(deck_name, create_if_needed=False)
        genanki.Package(deck).write_to_file(absolute_path)
        return absolute_path

    @staticmethod
    def get_fields(translation: Translation):
        german = translation.german
        if translation.article is not None:
            german = f'{translation.article} {german}'
        if translation.context is not None:
            german = f'{german} {translation.context}'
        fields = [
            translation.english,
            german,
            translation.example,
            translation.plural,
            translation.conjugation,
            translation.source]
        fields = [
            field if field is not None else ''
            for field in fields]
        return fields

    # TODO - figure out if adding 'source' will break everything!
    @staticmethod
    def default_model(name: str):
        return genanki.Model(
            anki_id(name),
            name,
            fields=[
                {'name': 'english'},
                {'name': 'german'},
                {'name': 'example'},
                {'name': 'plural'},
                {'name': 'conjugation'},
                {'name': 'source'},
            ],
            templates=[
                {
                    'name': 'Card 1',
                    'qfmt': '{{english}}',
                    'afmt':
                        '{{FrontSide}}<hr id=answer>'
                        '{{german}}<br><br>'
                        '{{example}}<br><br>'
                        '{{plural}}<br><br>'
                        '{{conjugation}}<br><br>'
                        '<i>{{source}}</i><br><br>',
                },
            ])

    def get_deck(self, deck_name: str, create_if_needed: bool = True):
        if deck_name in self.decks:
            return self.decks[deck_name]
        elif create_if_needed:
            deck = genanki.Deck(anki_id(deck_name), deck_name)
            self.decks[deck_name] = deck
            return deck
        else:
            return None
