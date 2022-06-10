"""
Parse Apple dictionaries given as Body.data files.

The function that does the heavy lifting is _parse. Overview:

- The files are just ZIPs of XML entries concatenated with some headers
  inbetween
- We greedily try to find the ZIPs and extract the XML
- Some XML parsing is implemented to find interesting stuff (derivatives for
  example).

"""
import argparse
import contextlib
import itertools
import os
import pickle
import shutil
import zlib
from typing import Dict, List, Tuple, Set

import lxml.etree as etree

# Matches spans that give some meta info, like "literary", "informal", etc.
XPATH_INFO = '//span[@class="lg"]/span[@class="reg"]'

# This matches the bold words in the definitions. For an example,
# see "vital", which contains "noun (vitals)"
XPATH_OTHER_WORDS = '//span[@class="fg"]/span[@class="f"]'

# This matches the derivatives at the end of definition.
XPATH_DERIVATIVES = '//span[contains(@class, "t_derivatives")]//' \
                    'span[contains(@class, "x_xoh")]/' \
                    'span[@role="text"]'

GERMAN_ENGLISH = \
    '/System/Library/AssetsV2/' \
    'com_apple_MobileAsset_DictionaryServices_dictionaryOSX/' \
    '0c247d541a5a54cc5db9ec9986c030fad7ff8d68.asset/' \
    'AssetData/' \
    'German - English.dictionary/' \
    'Contents/Resources/Body.data'

# def save_definitions(dictionary_path, lookup_words):
#     word_dict = parse(dictionary_path)
#     entry = word_dict[target]
#     t = entry.get_xml_tree()


def parse(dictionary_path):
    print(f"Parsing {dictionary_path}...")
    entries_tuples = _parse(dictionary_path)
    print('Augmenting...')
    # Some definitions have multiple entries (for example foil in NOAD).
    # Merge them here.
    entries = merge_same_keys(entries_tuples)
    _get_links(entries)
    return {k: e.get_xml_tree_string() for k, e in entries.items()}


def merge_same_keys(entries_tuples: List[Tuple[str, str]]) -> Dict[str, 'Entry']:
    entries = {}
    for k, e in entries_tuples:
        if k in entries:
            entries[k].append_definition(e)
        else:
            entries[k] = Entry(k, e)
    return entries


def _get_links(entries):
    print('Getting links...')
    for i, (key, entry) in enumerate(entries.items()):
        if i % 1000 == 0:
            progress = i / len(entries)
            print(f'\rGetting links: {progress * 100:.1f}%', end='', flush=True)
        for w in entry.get_words_and_derivatives():
            if w not in entries:
                entries[w] = entry


def _parse(dictionary_path) -> List[Tuple[str, str]]:
    """Parse Body.data into a list of entries given as key, definition tuples."""
    with open(dictionary_path, 'rb') as f:
        content_bytes = f.read()
    total_bytes = len(content_bytes)

    # The first zip file starts at ~100 bytes:
    content_bytes = content_bytes[100:]

    first = True
    entries = []
    for i in itertools.count():
        if not content_bytes:  # Backup condition in case stop is never True.
            break
        try:
            d = zlib.decompressobj()
            res = d.decompress(content_bytes)
            new_entries, stop = _split(res, verbose=first)
            entries += new_entries
            if stop:
                break
            if i % 10 == 0:
                bytes_left = len(content_bytes)  # Approximately...
                progress = 1 - bytes_left / total_bytes
                print(f'{progress * 100:.1f}% // '
                      f'{len(entries)} entries parsed // '
                      f'Latest entry: {entries[-1][0]}')
            first = False

            # Set content_bytes to the unused data so we can start the search for the
            # next zip file.
            content_bytes = d.unused_data

        except zlib.error:  # Current content_bytes is not a zipfile -> skip a byte.
            content_bytes = content_bytes[1:]

    return entries


def _split(input_bytes, verbose) -> Tuple[List[Tuple[str, str]], bool]:
    """Split `input_bytes` into a list of tuples (name, definition)."""
    printv = print if verbose else lambda *a, **k: ...

    # The first four bytes are always not UTF-8 (not sure why?)
    input_bytes = input_bytes[4:]

    printv('Splitting...')
    printv(f'{"index": <10}', f'{"bytes": <30}', f'{"as chars"}',
           '-' * 50, sep='\n')

    entries = []
    total_offset = 0
    stop_further_parsing = False

    while True:
        # Find the next newline, which delimits the current entry.
        try:
            next_offset = input_bytes.index('\n'.encode('utf-8'))
        except ValueError:  # No more new-lines -> no more entries!
            break

        entry_text = input_bytes[:next_offset].decode('utf-8')

        # The final part of the dictionary contains some meta info, which we skip.
        # TODO: might only be for the NOAD, so check other dictionaries.
        if 'fbm_AdvisoryBoard' in entry_text[:1000]:
            print('fbm_AdvisoryBoard detected, stopping...')
            stop_further_parsing = True
            break

        # Make sure we have a valid entry.
        assert (entry_text.startswith('<d:entry') and
                entry_text.endswith('</d:entry>')), \
            f'ENTRY: {entry_text} \n REM: {input_bytes}'

        # The name of the definition is stored in the "d:title" attribute,
        # where "d" is the current domain, which we get from the nsmap - the
        # actual attribute will be "{com.apple.blabla}title" (including the
        # curly brackets).
        xml_entry = etree.fromstring(entry_text)
        domain = xml_entry.nsmap['d']
        key = '{%s}title' % domain
        name = xml_entry.get(key)  # Lookup the attribute in the tree.

        entries.append((name, entry_text))

        printv(f'{next_offset + total_offset: 10d}',
               f'{str(input_bytes[next_offset + 1:next_offset + 5]): <30}',
               xml_entry.get(key))

        # There is always 4 bytes of chibberish between entries. Skip them
        # and the new lines (for a total of 5 bytes).
        input_bytes = input_bytes[next_offset + 5:]
        total_offset += next_offset
    return entries, stop_further_parsing


class Entry:
    def __init__(self, key, content):
        self.key = key
        self.content = content

        # Set to true on the first call to `append_definition`.
        # Used in get_xml_tree.
        self._multi_definition = False

        # These are lazily populated as they take a while.
        self._xml = None
        self._info = None
        self._words_and_derivatives = None

    def append_definition(self, content):
        """Extend self.content with more XML.

        The key here is to make sure the overall content is still valid XML
        by wrapping the whole thing in a <div>, which is handled in `get_xml_tree`,
        here we just set _multi_definition.
        """
        self._multi_definition = True
        self.content += content

    def get_xml_tree(self):
        content = self.content
        if self._multi_definition:
            content = '<div>' + self.content + '</div>'
        return etree.fromstring(content)

    def get_xml_tree_string(self):
        tree = self.get_xml_tree()
        return etree.tostring(tree, pretty_print=True).decode()

    def get_special(self, xpath, replace=None):
        matches = self.get_xml().xpath(xpath)
        if not matches:
            return []
        # Note: May be empty.
        texts = [el.text for el in matches if el.text]
        if replace:
            for r_in, r_out in replace:
                texts = [t.replace(r_in, r_out) for t in texts]
        texts = [t.strip() for t in texts]
        return texts

    def get_xml(self):
        if self._xml is None:
            self._xml = self.get_xml_tree()
        return self._xml

    def get_words_and_derivatives(self):
        derivatives = set(self.get_special(XPATH_DERIVATIVES))
        other_words = set(self.get_special(XPATH_OTHER_WORDS, [("the", "")]))
        return (derivatives | other_words) - {self.key}

    def get_info(self):
        return _lazy(self, "_info", lambda: set(self.get_special(XPATH_INFO)))

    def __str__(self):
        return f'Entry({self.key})'


def _lazy(obj, ivar, creator):
    if getattr(obj, ivar) is None:
        setattr(obj, ivar, creator())
    return getattr(obj, ivar)


def pickle_dict(pickle_path: str, dict_path: str):
    dictionary = parse(dict_path)
    with open(pickle_path, 'wb') as file:
        pickle.dump(dictionary, file)


def unpickle_dict(pickle_path: str):
    with open(pickle_path, 'rb') as file:
        dictionary = pickle.load(file)
    return dictionary

