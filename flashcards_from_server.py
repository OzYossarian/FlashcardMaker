from datetime import datetime

from main.FlashcardMaker import FlashcardMaker
from main.server.Server import Server
from main.logs.log import log
from main.translation.Translation import Translation
from main.utils import open_anki

# Temporary design: have a python script that we set the OS to run every x
# minutes. In this script, get unflashcarded phrases from crunchy nut server,
# translate them, then create flashcards for them and import into Anki.
# Should check Anki running and if not open it.


def main():
    try:
        log('Flashcard maker booting up...', new_entry=True)
        already_open = open_anki()
        log('Anki already open' if already_open else 'Opened Anki...')
        server = Server()
        for user_name in server.authorizer.users:
            phrases = server.get_phrases(owner=user_name)
            if len(phrases) > 0:
                flashcard_maker = FlashcardMaker(user_name)
                translated = translate_phrases(flashcard_maker, phrases)
                flashcard_maker.update_anki()
                server.post_phrases(translated)
            log(f'Successfully checked for new flashcards!')
    except Exception as e:
        log(str(e))


def translate_phrases(flashcard_maker, phrases):
    # N.B. Unflashcarded phrases may already be translated (e.g. if
    # another user already shared this phrase and thus it was translated
    # then, or if making the flashcard just failed earlier for some
    # reason).
    translated = []
    for phrase in phrases:
        try:
            translate_phrase(phrase, flashcard_maker)
            translated.append(phrase)
        except Exception as exception:
            log(
                f"An error occurred translating {phrase}.\n"
                f"As a result, it won't be posted back to the database.\n"
                f"The error was {exception}")
    return translated


def translate_phrase(phrase, flashcard_maker):
    now = datetime.now()
    if phrase.translations:
        log(f'Translations exist for {phrase.german} - flashcarding...')
        # Has already been translated, so just needs flashcarding.
        for translation in phrase.translations:
            flashcard_maker.note_taker.add_note(
                translation, phrase.deck_name)
        phrase.flashcard_date = now
    else:
        # Needs translating and flashcarding
        if phrase.english == '':
            log(f'Auto-translating {phrase.german} then flashcarding...')
            flashcard_maker.create(phrase, new_log_entry=False)
        else:
            log(f'Translation given: {phrase.german} = {phrase.english}...')
            translation = Translation(
                german=phrase.german,
                english=phrase.english)
            log(f'Converting given translation to note...')
            flashcard_maker.note_taker.add_note(
                translation, phrase.deck_name)
            phrase.translations = [translation]
        phrase.translation_date = now
        # Mark phrase as flashcarded - even if we didn't actually find any
        # translations. This ensures we don't keep redownloading this
        # phrase to try to translate it, knowing it won't work.
        phrase.flashcard_date = now


main()
