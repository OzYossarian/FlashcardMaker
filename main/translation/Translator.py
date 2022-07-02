import unicodedata
import urllib.parse
import deepl
import requests

from typing import List
from bs4 import BeautifulSoup
from requests import Response

from main.authorization.Authorizer import Authorizer
from main.logs.log import log
from main.translation.parse_dictionaries.parse_dict import unpickle_dict
from main.translation.Translation import Translation
from main.utils import project_root


# Possible word types: adjective, adverb, noun, verb, interjection. More?
# TODO - in future, could scrape sound too???
# TODO - in future, can keep linguee HTML and just format it with some
#  (their?) CSS
# TODO - in future, check for multiple entries with same english and add
#  hint? e.g. like how current Anki deck adds (H~) etc.
# TODO - someone has made a Linguee API - investigate?
#  If it has pre-downloaded results that it exposes then maybe use
#  this to stop pinging Linguee too much.


class Translator:
    def __init__(self, user_name: str, comprehensive: bool = False):
        # If comprehensive is True, we return all translations, at the risk
        # of adding more unnecessary ones.
        self.comprehensive = comprehensive
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
        try:
            log(f'Translating {german}...', new_log_entry)
            # At first, try to translate with Linguee.
            translations = self.search_linguee(german)
            # If we get a None back, Linguee server rejected us - don't
            # fall through to just using DeepL!
            if translations is not None:
                if len(translations) > 0:
                    # Remove verbs-as-nouns, adverbs of adjectives, etc.
                    return self.clean_linguee_translations(translations)
                else:
                    # Search DeepL for this phrase instead
                    translation = self.deepl_translate(german)
                    return [translation]
            else:
                return []
        except Exception as e:
            text = \
                f'The following error occurred ' \
                f'translating \'{german}\': {str(e)}'
            log(text)
            return []

    def clean_linguee_translations(self, translations):
        translations = self.remove_derivatives(translations)
        translations = self.add_noun_plurals(translations)
        verbs = [
            translation for translation in translations
            if translation.category == 'verb']
        self.conjugate_verbs(verbs)
        return translations

    def search_linguee(self, german: str):
        response = requests.get(self.linguee_url(german))
        if response.status_code >= 500:
            error = \
                'Linguee server error - probably from sending too many ' \
                'requests. Either wait an hour or so, or change your IP ' \
                '(e.g. with a VPN) and retry.'
            log(error)
            # Return None so that we don't just try and use DeepL instead.
            return None
        else:
            return self.linguee_translate(german, response)

    def linguee_translate(self, german: str, response: Response):
        log('Trying to translate with Linguee...')
        translations = []
        soup = BeautifulSoup(response.content, "html.parser")
        search_results = soup.find(id='dictionary')
        if search_results is None:
            log(f'Linguee has no translation for \'{german}\'')
        else:
            classes = ['lemma featured']
            if self.comprehensive:
                classes.append('lemma')
            search_results = search_results.find(class_='isForeignTerm')
            exact_results = search_results.find(class_='exact')
            if exact_results is not None:
                translations = \
                    self.exact_linguee_translate(exact_results, classes)
            else:
                translations = \
                    self.inexact_linguee_translate(search_results, classes)
            for translation in translations:
                translation.source = f'Linguee - \'{german}\''
        return translations

    def inexact_linguee_translate(self, search_results, classes):
        # What to do here?
        translations = []
        inexact_results = search_results.find(class_='inexact')
        if inexact_results is not None:
            log('Only found inexact result(s)')
        else:
            log('No results found! See HTML below:')
            log(search_results.prettify())
        return translations

    def exact_linguee_translate(self, exact_results, classes):
        log('Found exact match(es)...')
        translations = []
        for class_ in classes:
            for result in exact_results.select(f'div[class="{class_}"]'):
                translations.append(Translation.from_linguee_result_tag(result))
        log('Got exact linguee results:')
        [log(str(translation)) for translation in translations]
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
        nouns = [
            hit for hit in hits
            if hit.category is not None and hit.category[:4] == 'noun']

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
        log('Translating with DeepL...')
        english = self.deepl.translate_text(
            german, source_lang='DE', target_lang='EN-GB').text
        translation = Translation(
            german, english=english, source=f'DeepL = \'{german}\'')
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
