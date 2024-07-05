from __future__ import unicode_literals, division, absolute_import, print_function

__license__   = 'GPL v3'
__copyright__ = '2011, Grant Drake'

import re

# calibre Python 3 compatibility.
from six import text_type as unicode
from queue import PriorityQueue

from calibre.ebooks.metadata import check_isbn

import calibre_plugins.extract_isbn.config as cfg
from calibre_plugins.extract_isbn.identifier import Identifier, IdentifierContext, IdentifierType

RE_ISBN = u'(?P<number>[0-9\-\.–­―—\^ ]{9,18}[0-9xX])'
RE_PARENTHETICAL = u'(?P<parenthetical>\([\w\s]+\))'
RE_PREFIX = u'(?P<prefix>[\w\s©]*(?:ISBN|LCCN):?)'
RE_IDENTIFIER = re.compile(u"%s?\s*%s\s*%s?" % (RE_PREFIX, RE_ISBN, RE_PARENTHETICAL), re.UNICODE)

RE_STRIP_STYLE = re.compile(u'<style[^<]+</style>', re.MULTILINE | re.UNICODE)
RE_STRIP_MARKUP = re.compile(u'<[^>]+>', re.UNICODE)

DEFAULT_PRIORITY = [
    IdentifierContext.EBOOK,
    IdentifierContext.HARDBACK,
    IdentifierContext.PAPERBACK,
    IdentifierContext.PRINT,
    IdentifierContext.SOURCE,
    IdentifierContext.UNKNOWN
]

def rank_isbn_by_len(identifier, order, forward):
    return (
        1 if identifier.id_len == 13 else 2,
        order if forward else order * -1
    )

def rank_isbn_by_context(identifier, order, forward):
    return (
        DEFAULT_PRIORITY.index(identifier.context),
        1 if identifier.id_len == 13 else 2,
        order if forward else order * -1
    )

class BookScanner(object):

    def __init__(self, log):
        self.log = log
        self.identifiers = PriorityQueue()
        c = cfg.plugin_prefs[cfg.STORE_NAME]
        self.valid_isbn13s = c.get(cfg.KEY_VALID_ISBN13_PREFIX,
                                   cfg.DEFAULT_STORE_VALUES[cfg.KEY_VALID_ISBN13_PREFIX])
        if c.get(cfg.KEY_RANKING_METHOD, cfg.DEFAULT_STORE_VALUES[cfg.KEY_RANKING_METHOD]) == 'context':
            self.ranker = rank_isbn_by_context
        else:
            self.ranker = rank_isbn_by_len

    def get_isbn_result(self):
        if not self.identifiers.empty():
            return self.identifiers.get()[1]
        return None

    def has_identifier(self):
        return not self.identifiers.empty()

    def look_for_identifiers_in_text(self, book_files, forward=True):
        '''
        Scans text (string) for identifiers, returns one if found
        '''
        if not forward:
            book_files = reversed(book_files)
        for book_file in book_files:
            # Strip all the html markup tags out in case we get clashes with svg covers
            book_file = unicode(RE_STRIP_STYLE.sub('', book_file))
            book_file = unicode(RE_STRIP_MARKUP.sub('!', book_file))
            #open('E:\\isbn.html', 'wb').write(book_file)

            order = 0
            for match in RE_IDENTIFIER.finditer(book_file):
                self.log.debug('Possible identifier found:', match.groupdict())
                identifier = self._build_identifier(match.group('prefix'), match.group('number'), match.group('parenthetical'))
                if self._are_digits_identical(identifier.id):
                    self.log.debug('Identifier rejected due to repeating digits:', digits)
                elif identifier.type is not IdentifierType.ISBN and identifier.type is not IdentifierType.UNKNOWN:
                    self.log.debug('Identifier rejected due to incorrect type:', identifier.type)
                elif not (identifier.id_len == 13 or identifier.id_len == 10):
                    self.log.debug('Identifier rejected due to incorrect length:', identifier.id_len)
                elif identifier.id_len == 13 and not self._valid_isbn13(identifier.id):
                    self.log.debug('Identifier rejected due to invalid isbn13:', identifier.id)
                elif not check_isbn(identifier.id):
                    self.log.debug('Identifier rejected as it failed the calibre isbn check:', identifier.id)
                else:
                    order += 1
                    self.log.warn('      Valid ISBN:', identifier.id)
                    self._rank_identifier(identifier, order, forward)

            if self.has_identifier():
                break

    def _rank_identifier(self, identifier, order, forward):
        rank = self.ranker(identifier, order, forward)
        self.identifiers.put((rank, identifier.id))

    def _are_digits_identical(self, digits):
        '''
        Grant - next check for repeating digits like 1111111111
        is redundant as of Calibre 0.8, but not exactly
        sure which version Kovid changed so rather than dragging
        extract isbn dependency forward will repeat here.
        '''
        return re.match(r'(\d)\1{9,12}$', digits) is not None

    def _build_identifier(self, prefix, number, parenthetical):
        digits = self._extract_digits(number)
        id_type = self._determine_type(prefix, parenthetical)
        id_context = self._determine_context(prefix, parenthetical)
        return Identifier(digits, id_type, id_context)

    def _determine_type(self, prefix, parenthetical):
        glob = ' '.join([prefix or '', parenthetical or ''])
        if re.search('isbn', glob, re.IGNORECASE) is not None:
            return IdentifierType.ISBN
        elif re.search('lccn', glob, re.IGNORECASE) is not None:
            return IdentifierType.LCCN
        else:
            return IdentifierType.UNKNOWN

    def _determine_context(self, prefix, parenthetical):
        glob = ' '.join([prefix or '', parenthetical or ''])
        if re.search('(ebook|digital|eisbn)', glob, re.IGNORECASE) is not None:
            return IdentifierContext.EBOOK
        elif re.search('(hardcover|hardback|hb)', glob, re.IGNORECASE) is not None:
            return IdentifierContext.HARDBACK
        elif re.search('(paperback|pb)', glob, re.IGNORECASE) is not None:
            return IdentifierContext.PAPERBACK
        elif re.search('print', glob, re.IGNORECASE) is not None:
            return IdentifierContext.PRINT
        elif re.search('source', glob, re.IGNORECASE) is not None:
            return IdentifierContext.SOURCE
        else:
            return IdentifierContext.UNKNOWN

    def _extract_digits(self, original_text):
        return re.sub('[^0-9X]','', original_text)

    def _valid_isbn13(self, digits):
        return digits[:3] in self.valid_isbn13s
