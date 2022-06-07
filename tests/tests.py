import random
from FlashcardMaker import FlashcardMaker
from translation.Translation import Translation

flashcardMaker = FlashcardMaker()


def lookup_word(word: str):
    flashcardMaker.translator.translate(word)


def lookup_random_word():
    line_number = random.randint(0, 1000000)
    with open('german_words.txt') as words:
        for i, word in enumerate(words):
            if i == line_number:
                word = word.strip()
                flashcardMaker.translator.translate(word.strip())


def create_note(translation: Translation):
    return flashcardMaker.note_taker.add_note(translation)


def output_deck():
    flashcardMaker.note_taker.add_note(example_translation)
    flashcardMaker.note_taker.output_deck('abc')


def swift_test():
    return 'Hello, Swift!'


example_translation = Translation(
    'Deutsch',
    'some type',
    'some context',
    'English',
    'some example',
    'some plural',
    'some conjugation'
)

# print('Hello world!')
notes = flashcardMaker.create('Schmetterling`')
flashcardMaker.update_anki()
