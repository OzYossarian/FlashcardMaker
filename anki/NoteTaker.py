from pathlib import Path

import genanki
import os

from translation.Translation import Translation


class NoteTaker:
    def __init__(self):
        self.deck = self.default_deck()
        self.model = self.default_model()

    def add_note(self, translation: Translation):
        fields = self.get_fields(translation)
        note = genanki.Note(self.model, fields)
        self.deck.add_note(note)
        return note

    def output_deck(self, file_name):
        relative_path = f'anki/output/{file_name}.apkg'
        absolute_path = os.path.abspath(relative_path)
        Path(absolute_path).parent.mkdir(parents=True, exist_ok=True)
        genanki.Package(self.deck).write_to_file(relative_path)
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
            translation.conjugation]
        fields = [
            field if field is not None else ''
            for field in fields]
        return fields

    @staticmethod
    def default_model():
        return genanki.Model(
            1607392319,
            'Fluency Lube Auto',
            fields=[
                {'name': 'english'},
                {'name': 'german'},
                {'name': 'example'},
                {'name': 'plural'},
                {'name': 'conjugation'},
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
                        '{{conjugation}}',
                },
            ])

    @staticmethod
    def default_deck():
        return genanki.Deck(
            2059400110,
            'Fluency Lube Auto')
