import argparse
from datetime import datetime

from main.FlashcardMaker import FlashcardMaker
from main.logs.log import log
from main.server.Phrase import Phrase
from main.server.Server import Server
from main.utils import open_anki


def main():
    log('Generating flashcards from file...')
    args = configure_args()
    log(f'File path is {args.filepath}')

    already_open = open_anki()
    log('Anki already open' if already_open else 'Opened Anki...')

    server = Server()
    flashcard_maker = FlashcardMaker()

    def translate(german: str):
        log(f'Translating and flashcarding \'{german}\'...')
        translations, _ = flashcard_maker.create(german, new_log_entry=False)
        phrase = Phrase(id=None, german=german)
        phrase.translations = translations
        now = datetime.now()
        phrase.share_date = now
        phrase.translation_date = now
        phrase.flashcard_date = now
        return phrase

    with open(args.filepath) as file:
        log('Reading file...')
        german_words = [line.rstrip() for line in file.readlines()]
        log('Creating phrases from lines...')
        phrases = [translate(german) for german in german_words]
        flashcard_maker.update_anki()
        server.post_phrases(phrases)


def configure_args():
    description = 'Generate Anki flashcards from a file of German words'
    parser = argparse.ArgumentParser(description=description)
    help = 'Relative path to the file containing the German words'
    parser.add_argument("filepath", help=help, type=str)
    args = parser.parse_args()
    return args


main()
