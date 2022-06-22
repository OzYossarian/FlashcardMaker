import unicodedata
import urllib.parse
import deepl
import requests

from typing import List
from bs4 import BeautifulSoup

from main.authorization.Authorizer import Authorizer
from main.logs.log import log
from main.translation.parse_dictionaries.parse_dict import unpickle_dict


# Possible word types: adjective, adverb, noun, verb, interjection. More?
# TODO - in future, could scrape sound too???
# TODO - in future, can keep linguee HTML and just format it with some
#  (their?) CSS
# TODO - in future, check for multiple entries with same english and add
#  hint? e.g. like how current Anki deck adds (H~) etc.
from main.translation.Translation import Translation
from main.utils import project_root


class Translator:
    def __init__(self, user_name: str):
        self.authorizer = Authorizer()
        deepl_authorization = self.authorizer.deepl_authorization(user_name)
        self.deepl = deepl.Translator(deepl_authorization)
        apple_dict_path = \
            f'{project_root()}/' \
            f'main/' \
            f'translation/' \
            f'parse_dictionaries/' \
            f'apple_german_english.pickle'
        self.apple_dict = unpickle_dict(apple_dict_path)

    def translate(self, german: str, new_log_entry=True):
        # The big boi top-level method
        try:
            log(f'Translating {german}...', new_log_entry)
            # TODO - someone has made a Linguee API - investigate?
            #  If it has pre-downloaded results that it exposes then maybe use
            #  this to stop pinging Linguee too much.
            # At first, try to translate with Linguee.
            translations = self.search_linguee(german)
            if translations:
                translations = self.remove_derivatives(translations)
                translations = self.add_noun_plurals(translations)
                verbs = [
                    translation for translation in translations
                    if translation.category == 'verb']
                self.conjugate_verbs(verbs)
                return translations
            else:
                # Search DeepL for this phrase instead
                translation = self.deepl_translate(german)
                return [translation]
        except Exception as e:
            text = \
                f'The following error occurred ' \
                f'translating \'{german}\': {str(e)}'
            log(text)
            return []

    def search_linguee(self, phrase: str):
        page = requests.get(self.linguee_url(phrase))
        soup = BeautifulSoup(page.content, "html.parser")
        search_results = soup.find(id='dictionary')
        translations = []
        if search_results is None:
            log(f'Linguee has no translation for \'{phrase}\'')
        else:
            search_results = search_results.find(class_='isForeignTerm')
            exact_results = search_results.find(class_='exact')
            if exact_results is not None:
                log('Found exact match(es)...')
                # Each result is in a class 'lemma', but might also be 'featured'
                # - what do with non-featured ones?
                for result in exact_results.find_all(class_='lemma featured'):
                    translations.append(Translation.from_result_tag(result))
                log('Got exact linguee results:')
                [log(str(translation)) for translation in translations]
            else:
                # What to do here?
                inexact_results = search_results.find(class_='inexact')
                if inexact_results is not None:
                    log('Only found inexact result(s)')
                    # for result in inexact_results.select('div[class*="lemma featured"]'):
                    #     german = result.find(class_='dictLink').text
                    #     translations.extend(self.translate(german, new_log_entry=False))
                else:
                    log('No results found! See HTML below:')
                    log(search_results.prettify())
            return translations

    def remove_derivatives(self, hits: List[Translation]):
        found_derivatives = False

        def is_likely_derived_adverb(hit: Translation):
            return hit.category == 'adverb' and any(
                hit.german == x.german and x.category == 'adjective'
                for x in hits)

        def is_likely_derived_noun(hit: Translation):
            return hit.category == 'noun, neuter' and any(
                hit.german == x.german.capitalize() and x.category == 'verb'
                for x in hits)

        filtered = hits.copy()
        for hit in hits:
            if is_likely_derived_adverb(hit) or is_likely_derived_noun(hit):
                found_derivatives = True
                filtered.remove(hit)

        if found_derivatives:
            log('Removed some duplicates - now we have:')
            [log(str(x)) for x in filtered]

        return filtered

    def add_noun_plurals(self, hits: List[Translation]):
        # Remove linguee's plurals - I don't trust them
        hits = [hit for hit in hits if hit.category != 'noun, plural']

        nouns = [hit for hit in hits if hit.category[:4] == 'noun']
        for noun in nouns:
            log(f'Pluralising {noun.german} ({noun.category})...')
            if noun.german in self.apple_dict:
                page = self.apple_dict[noun.german]
                soup = BeautifulSoup(page, "html.parser")
                noun.find_plural(soup)
            else:
                # Not hundy cent sure what to do here?
                log(f"'{noun.german}' not in Apple dictionary.")
                noun.plural = '?'

        log('Nouns pluralised!')
        return hits

    def conjugate_verbs(self, verbs: List[Translation]):
        for verb in verbs:
            log(f'Conjugating verb \'{verb.german}\'...')
            url = self.conjugator_url(verb.german)
            page = requests.get(url)
            soup = BeautifulSoup(page.content, "html.parser")
            verb.conjugation = soup.find(id='stammformen').text.strip()
        log('Verbs conjugated!')

    def deepl_translate(self, german: str):
        english = self.deepl.translate_text(
            german, source_lang='DE', target_lang='EN-GB').text
        translation = Translation(german, english=english)
        return translation

    def linguee_url(self, phrase: str):
        phrase = urllib.parse.quote(phrase)
        return \
            f'https://www.linguee.com' \
            f'/english-german' \
            f'/search' \
            f'?source=auto' \
            f'&query={phrase}'

    def conjugator_url(self, verb: str):
        verb = unicodedata.normalize('NFC', verb)
        return f'https://www.verbformen.de/?w={verb}'
