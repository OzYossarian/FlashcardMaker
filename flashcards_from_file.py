import argparse
from datetime import datetime

from main.FlashcardMaker import FlashcardMaker
from main.logs.log import log
from main.server.Phrase import Phrase
from main.server.Server import Server
from main.utils import open_anki


def main():
    log('Generating flashcards from file...', new_entry=True)

    already_open = open_anki()
    log('Anki already open...' if already_open else 'Opened Anki...')

    server = Server()
    user_name = server.authorizer.me
    flashcard_maker = FlashcardMaker(user_name)

    args = configure_args(flashcard_maker.note_taker.default_deck_name)
    log(f'File path is \'{args.filepath}\'...')
    log(f'Deck name is \'{args.deck_name}\'...')

    def translate(german: str):
        log(f'\nTranslating and flashcarding \'{german}\'...')
        phrase = Phrase(
            id=None, german=german, owner=user_name, deck_name=args.deck_name)
        notes = flashcard_maker.create(phrase, new_log_entry=False)
        if notes is not None:
            now = datetime.now()
            phrase.share_date = now
            phrase.translation_date = now
            phrase.flashcard_date = now
            return phrase
        else:
            # Something went wrong while trying to translate this.
            return None

    with open(args.filepath) as file:
        log('Reading file...')
        german_lines = [line.strip() for line in file.readlines()]
        german_lines = [line for line in german_lines if line != '']
        log('Creating phrases from lines...')
        phrases = [translate(german) for german in german_lines]
        translated = [phrase for phrase in phrases if phrase is not None]
        log('\nPhrases translated and flashcarded!')
        flashcard_maker.update_anki()
        server.post_phrases(translated)


def configure_args(default_deck_name: str):
    description = 'Generate Anki flashcards from a file of German words'
    parser = argparse.ArgumentParser(description=description)
    filepath_help = 'Relative path to the file containing the German words.'
    parser.add_argument('filepath', help=filepath_help, type=str)
    deck_name_help = 'Name of the Anki deck to store the flashcards in. '
    deck_name_help += 'If left blank, defaults to "Fluency Lube".'
    parser.add_argument(
        'deck_name', help=deck_name_help, type=str, nargs='?',
        default=default_deck_name)
    args = parser.parse_args()
    return args


main()
