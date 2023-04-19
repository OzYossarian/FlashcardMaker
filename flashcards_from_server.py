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
            success = translate_phrase(phrase, flashcard_maker)
            if success:
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
        # Always translates successfully.
        return True
    else:
        # Needs translating and flashcarding
        if phrase.english == '':
            log(f'Auto-translating {phrase.german} then flashcarding...')
            notes = flashcard_maker.create(phrase, new_log_entry=False)
            # If `notes` is not None, this was successfully translated
            translated = notes is not None
        else:
            log(f'Translation given: {phrase.german} = {phrase.english}...')
            translation = Translation(
                german=phrase.german,
                english=phrase.english)
            log(f'Converting given translation to note...')
            flashcard_maker.note_taker.add_note(
                translation, phrase.deck_name)
            translated = True
            phrase.translations = [translation]
        # If we actually did translate this phrase, note this down.
        # Sometimes we fail - right now this is almost always because we
        # sent too many Linguee requests in the last few minutes. In this
        # case, we want to try again with this phrase next time. So don't
        # mark it as flashcarded.
        if translated:
            phrase.translation_date = now
            phrase.flashcard_date = now
        return translated


main()
