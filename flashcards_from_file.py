import argparse
from datetime import datetime

from main.FlashcardMaker import FlashcardMaker
from main.logs.log import log
from main.server.Phrase import Phrase
from main.server.Server import Server
from main.utils import open_anki


def main():
    log('Generating flashcards from file...')
    server = Server()
    user_name = server.authorizer.me
    flashcard_maker = FlashcardMaker(user_name)

    args = configure_args(flashcard_maker.note_taker.default_deck_name)
    log(f'File path is {args.filepath}')
    log(f'Deck name is {args.deck_name}')

    already_open = open_anki()
    log('Anki already open...' if already_open else 'Opened Anki...')

    def translate(german: str):
        log(f'Translating and flashcarding \'{german}\'...')
        phrase = Phrase(
            id=None, german=german, owner=user_name, deck_name=args.deck_name)
        flashcard_maker.create(phrase, new_log_entry=False)
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


def configure_args(default_deck_name: str):
    description = 'Generate Anki flashcards from a file of German words'
    parser = argparse.ArgumentParser(description=description)
    filepath_help = 'Relative path to the file containing the German words'
    parser.add_argument('filepath', help=filepath_help, type=str)
    deck_name_help = 'Name of the Anki deck to store the flashcards in'
    parser.add_argument(
        'deck_name', help=deck_name_help, type=str, nargs='?',
        default=default_deck_name)
    args = parser.parse_args()
    return args


main()
