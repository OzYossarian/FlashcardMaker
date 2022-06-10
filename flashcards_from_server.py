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
        phrases = server.get_phrases()
        if len(phrases) > 0:
            flashcard_maker = FlashcardMaker()
            translate_phrases(flashcard_maker, phrases)
            flashcard_maker.update_anki()
            server.post_phrases(phrases)
        log(f'Successfully checked for new flashcards!')
    except Exception as e:
        log(str(e))


def translate_phrases(flashcard_maker, phrases):
    # N.B. Unflashcarded phrases may already be translated (e.g. if
    # another user already shared this phrase and thus it was translated
    # then, or if making the flashcard just failed earlier for some
    # reason).
    for phrase in phrases:
        now = datetime.now()
        if phrase.translations:
            log(f'Translations exist for {phrase.german} - flashcarding...')
            # Has already been translated, so just needs flashcarding.
            for translation in phrase.translations:
                flashcard_maker.note_taker.add_note(translation)
            phrase.flashcard_date = now
        else:
            # Needs translating and flashcarding
            if phrase.english == '':
                log(f'Auto-translating {phrase.german} then flashcarding...')
                translations, _ = \
                    flashcard_maker.create(phrase.german, new_log_entry=False)
                phrase.translations = translations
            else:
                log(f'Translation given: {phrase.german} = {phrase.english}...')
                translation = Translation(
                    german=phrase.german,
                    english=phrase.english)
                log(f'Converting given translation to note...')
                flashcard_maker.note_taker.add_note(translation)
                phrase.translations = [translation]
            phrase.translation_date = now
            # Mark phrase as flashcarded - even if we didn't actually find any
            # translations. This ensures we don't keep redownloading this
            # phrase to try to translate it, knowing it won't work.
            phrase.flashcard_date = now


# main()
