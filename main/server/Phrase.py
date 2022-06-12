from typing import Dict, Any, List

from main.translation.Translation import Translation


class Phrase:
    def __init__(
            self, id: int, german: str, english: str = None,
            owner: str = None, share_date: str = None,
            database_date: str = None, translation_date: str = None,
            flashcard_date: str = None,
            translations: List[Translation] = None):
        self.id = id
        self.german = german
        self.english = english
        self.owner = owner
        self.share_date = share_date
        self.database_date = database_date
        self.translation_date = translation_date
        self.flashcard_date = flashcard_date
        self.translations = translations if translations is not None else []

    @classmethod
    def from_data(cls, data: Dict[str, Any]):
        translations_data = data.get('translations', None)
        if translations_data is not None:
            translations = [
                Translation.from_data(translation_data)
                for translation_data in translations_data]
        else:
            translations = []
        return cls(
            data.get('_id', None),
            data.get('german', None),
            data.get('english', None),
            data.get('owner', None),
            data.get('share_date', None),
            data.get('database_date', None),
            data.get('translation_date', None),
            data.get('flashcard_date', None),
            translations)
