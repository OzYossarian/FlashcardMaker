import unicodedata
import bs4.element

from main.logs.log import log


class Translation:
    def __init__(
            self, german: str, category: str = None, context: str = None,
            english: str = None, example: str = None, plural: str = None,
            conjugation: str = None, article: str = None):
        self.german = german
        self.category = category
        self.context = context
        self.english = english
        self.example = example
        # Applicable only for nouns
        self.plural = plural
        # Applicable only for verbs
        self.conjugation = conjugation

        if article is None:
            articles = {
                'noun, masculine': 'der',
                'noun, neuter': 'das',
                'noun, feminine': 'die',
                'noun, plural': 'die',
            }
            self.article = articles.get(category, None)
        else:
            self.article = article

    def find_plural(self, soup: bs4.BeautifulSoup):
        # Find all nouns with same gender as this phrase.
        matches = [
            x for x in soup.find_all(class_='gramb x_xd0')
            if x.find(class_='ps').text.startswith(self.category[6:])]
        plural_starts = [
            match.find('span', text='Pl. ')
            for match in matches
        ]
        plurals = [
            plural_start.findNext().text.strip()
            for plural_start in plural_starts
            if plural_start is not None
        ]
        self.plural = '/'.join(plurals) if plurals else '?'

    @classmethod
    def from_data(cls, data):
        return cls(
            data.get('german', None),
            data.get('category', None),
            data.get('context', None),
            data.get('english', None),
            data.get('example', None),
            data.get('plural', None),
            data.get('conjugation', None),
            data.get('article', None))

    @classmethod
    def from_result_tag(cls, result):
        log('Trying to extract German-English phrase...')
        german_tag = result.find(class_='line lemma_desc')
        translation = cls.extract_german(german_tag)
        top_three_translations = \
            result.find(class_='lemma_content') \
                .find_all(class_='translation sortablemg featured')[:3]
        translation.english = ', '.join(
            x.find(class_='dictLink').text for x in top_three_translations)
        if translation.category == 'verb':
            translation.english = f'to {translation.english}'
        examples = top_three_translations[0].find(class_='example_lines')
        if examples is not None:
            translation.example = examples.find(class_='tag_s').text
        log(f'Extracted German-English phrase! {translation}')
        return translation

    @classmethod
    def extract_german(cls, german: bs4.element.Tag):
        log('Trying to extract German...')
        main = cls.format_contents(german.find(class_='dictLink'))
        context = german.find(class_='tag_lemma_context')
        if context is not None:
            context = cls.format_contents(context)
        word_type = cls.format_contents(german.find(class_='tag_wordtype'))
        translation = cls(main, word_type, context)
        log(f'Extracted German! {translation}')
        return translation

    @classmethod
    def format_contents(cls, tag: bs4.element.Tag) -> str:
        result = []
        contents = tag.contents
        for item in contents:
            if isinstance(item, str):
                result.append(item)
            if isinstance(item, bs4.element.Tag):
                class_ = item.get('class')
                if 'grammar_info' in class_:
                    result.append(f'[{cls.format_contents(item)}]')
                elif 'placeholder' in class_:
                    result.append(cls.format_contents(item))
                elif class_ is not None:
                    log(f'New tag class found!')
                    log(item.prettify())
                    result.append(cls.format_contents(item))
        return ''.join(unicodedata.normalize("NFKD", x) for x in result)

    def __str__(self):
        return str([
            self.english,
            self.article,
            self.german,
            self.context,
            self.category,
            self.example,
            self.plural,
            self.conjugation])
