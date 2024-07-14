from __future__ import unicode_literals, division, absolute_import, print_function

__license__   = 'GPL v3'
__copyright__ = '2011, Grant Drake'

from collections import OrderedDict

# calibre Python 3 compatibility.
from six import text_type as unicode

try:
    from qt.core import (Qt, QWidget, QGridLayout, QLabel, QLineEdit, QPushButton, QSpinBox,
                         QCheckBox, QHBoxLayout, QVBoxLayout, QTabWidget, QGroupBox, QStackedWidget, QUrl, QListWidget, QAbstractItemView)
except ImportError:
    from PyQt5.Qt import (Qt, QWidget, QGridLayout, QLabel, QLineEdit, QPushButton, QSpinBox,
                          QCheckBox, QHBoxLayout, QVBoxLayout, QTabWidget, QGroupBox, QStackedWidget, QUrl, QListWidget, QAbstractItemView)

from calibre.gui2 import open_url
from calibre.utils.config import JSONConfig

from calibre_plugins.extract_isbn.common_icons import get_icon
from calibre_plugins.extract_isbn.common_dialogs import KeyboardConfigDialog
from calibre_plugins.extract_isbn.common_widgets import KeyValueComboBox
from calibre_plugins.extract_isbn.identifier import IdentifierContext

try:
    load_translations()
except NameError:
    pass # load_translations() added in calibre 1.9

HELP_URL = 'https://github.com/kiwidude68/calibre_plugins/wiki/Extract-ISBN'

STORE_NAME = 'Options'
KEY_VALID_ISBN13_PREFIX = 'validISBN13Prefix'
KEY_POST_TASK = 'postTask'
KEY_RANKING_METHOD = 'rankingMethod'
KEY_WORKER_THRESHOLD = 'workerThreshold'
KEY_BATCH_SIZE = 'batchSize'
KEY_DISPLAY_FAILURES = 'displayFailures'
KEY_ASK_FOR_CONFIRMATION = 'askForConfirmation'
KEY_CONTEXT_RANKING_PRIORITY = 'contextRankingPriority'
KEY_CONTEXT_MATCHER_EBOOK = 'contextMatcherEbook'
KEY_CONTEXT_MATCHER_HARDBACK = 'contextMatcherHardback'
KEY_CONTEXT_MATCHER_PAPERBACK = 'contextMatcherPaperback'
KEY_CONTEXT_MATCHER_PRINT = 'contextMatcherPrint'
KEY_CONTEXT_MATCHER_SOURCE = 'contextMatcherSource'

SHOW_TASKS = OrderedDict([('none', _('Do not change my search')),
                        ('updated', _('Show the books that have new or updated ISBNs'))])

RANKING_METHODS = OrderedDict([('orderFound', _('Prefer first found')),
                        ('context', _('By context'))])
RANKING_METHOD_TOOLTIPS = [
    '(default) Use the first-found ISBN-13 and\nfallback to the first-found ISBN-10',
    'Classify found ISBNs as belonging to print\neditions, digital editions, etcetera based\non the surrounding context and select\nthe winning ISBN based on preference'
]

DEFAULT_STORE_VALUES = {
    KEY_POST_TASK: 'none',
    KEY_RANKING_METHOD: 'orderFound',
    KEY_VALID_ISBN13_PREFIX: ['977', '978', '979'],
    KEY_WORKER_THRESHOLD: 1,
    KEY_BATCH_SIZE: 100,
    KEY_DISPLAY_FAILURES: True,
    KEY_ASK_FOR_CONFIRMATION: True,
    KEY_CONTEXT_RANKING_PRIORITY: [e.value for e in [
        IdentifierContext.EBOOK,
        IdentifierContext.HARDBACK,
        IdentifierContext.PAPERBACK,
        IdentifierContext.PRINT,
        IdentifierContext.SOURCE,
        IdentifierContext.UNKNOWN
    ]],
    KEY_CONTEXT_MATCHER_EBOOK: '(ebook|digital|eisbn)',
    KEY_CONTEXT_MATCHER_HARDBACK: '(hardcover|hardback|hb)',
    KEY_CONTEXT_MATCHER_PAPERBACK: '(paperback|pb)',
    KEY_CONTEXT_MATCHER_PRINT: 'print',
    KEY_CONTEXT_MATCHER_SOURCE: 'source'
}

CONTEXT_TRANSLATIONS = {
    IdentifierContext.EBOOK.value: _('ebook'),
    IdentifierContext.HARDBACK.value: _('hardback'),
    IdentifierContext.PAPERBACK.value: _('paperback'),
    IdentifierContext.PRINT.value: _('print'),
    IdentifierContext.SOURCE.value: _('source'),
    IdentifierContext.UNKNOWN.value: _('unknown')
}

# This is where all preferences for this plugin will be stored
plugin_prefs = JSONConfig('plugins/Extract ISBN')

# Set defaults
plugin_prefs.defaults[STORE_NAME] = DEFAULT_STORE_VALUES

def show_help():
    open_url(QUrl(HELP_URL))

class ConfigWidget(QWidget):

    def __init__(self, plugin_action):
        QWidget.__init__(self)
        self.plugin_action = plugin_action
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        tab_widget = QTabWidget(self)
        layout.addWidget(tab_widget)

        self.general_tab = GeneralTab(self, plugin_action)
        self.identification_tab = IdentificationTab(self)
        self.ranking_tab = RankingTab(self)
        tab_widget.addTab(self.general_tab, _('General'))
        tab_widget.addTab(self.identification_tab, _('Identification'))
        tab_widget.addTab(self.ranking_tab, _('Ranking'))

    def save_settings(self):
        new_prefs = {}
        new_prefs[KEY_POST_TASK] = self.general_tab.showCombo.selected_key()
        prefixes = unicode(self.general_tab.isbn13_ledit.text()).replace(' ','')
        new_prefs[KEY_VALID_ISBN13_PREFIX] = prefixes.split(',')
        new_prefs[KEY_RANKING_METHOD] = self.ranking_tab.rankingMethodCombo.selected_key()
        new_prefs[KEY_CONTEXT_MATCHER_EBOOK] = self.identification_tab.context_identification_config.context_matcher_ebook_edit.text()
        new_prefs[KEY_CONTEXT_MATCHER_HARDBACK] = self.identification_tab.context_identification_config.context_matcher_hardback_edit.text()
        new_prefs[KEY_CONTEXT_MATCHER_PAPERBACK] = self.identification_tab.context_identification_config.context_matcher_paperback_edit.text()
        new_prefs[KEY_CONTEXT_MATCHER_PRINT] = self.identification_tab.context_identification_config.context_matcher_print_edit.text()
        new_prefs[KEY_CONTEXT_MATCHER_SOURCE] = self.identification_tab.context_identification_config.context_matcher_source_edit.text()
        new_prefs[KEY_CONTEXT_RANKING_PRIORITY] = self.ranking_tab.context_ranking_config.context_ranking_priority()
        new_prefs[KEY_WORKER_THRESHOLD] = int(unicode(self.general_tab.threshold_spin.value()))
        new_prefs[KEY_BATCH_SIZE] = int(unicode(self.general_tab.batch_spin.value()))
        new_prefs[KEY_DISPLAY_FAILURES] = self.general_tab.display_failures_checkbox.isChecked()
        new_prefs[KEY_ASK_FOR_CONFIRMATION] = self.general_tab.ask_for_confirmation_checkbox.isChecked()
        plugin_prefs[STORE_NAME] = new_prefs

class GeneralTab(QWidget):

    def __init__(self, parent_dialog, plugin_action):
        QWidget.__init__(self)
        self.parent_dialog = parent_dialog
        self.plugin_action = plugin_action
        layout = QGridLayout(self)
        self.setLayout(layout)

        c = plugin_prefs[STORE_NAME]

        layout.addWidget(QLabel(_('When the scan completes:'), self), 0, 0, 1, 2)
        post_show = c.get(KEY_POST_TASK, DEFAULT_STORE_VALUES[KEY_POST_TASK])
        self.showCombo = KeyValueComboBox(self, SHOW_TASKS, post_show)
        layout.addWidget(self.showCombo, 1, 0, 1, 2)

        layout.addWidget(QLabel(_('Valid prefixes for ISBN-13 (comma separated):'), self), 2, 0, 1, 2)
        prefixes = c.get(KEY_VALID_ISBN13_PREFIX, DEFAULT_STORE_VALUES[KEY_VALID_ISBN13_PREFIX])
        self.isbn13_ledit = QLineEdit(','.join(prefixes), self)
        layout.addWidget(self.isbn13_ledit, 3, 0, 1, 2)

        lbl = QLabel(_('Selected books before running as a background job:'), self)
        lbl.setToolTip(_('Running as a background job is slower but is the only way to avoid\n') +
                       _('memory leaks and will keep the UI more responsive.'))
        layout.addWidget(lbl, 4, 0, 1, 1)
        worker_threshold = c.get(KEY_WORKER_THRESHOLD, DEFAULT_STORE_VALUES[KEY_WORKER_THRESHOLD])
        self.threshold_spin = QSpinBox(self)
        self.threshold_spin.setMinimum(0)
        self.threshold_spin.setMaximum(20)
        self.threshold_spin.setProperty('value', worker_threshold)
        layout.addWidget(self.threshold_spin, 4, 1, 1, 1)

        batch_lbl = QLabel(_('Batch size running as a background job:'), self)
        batch_lbl.setToolTip(_('Books will be broken into batches to ensure that if you run\n'
                       'extract for a large group you can cancel/close calibre without\n'
                       'losing all of your results as you can cancel the pending groups.'))
        layout.addWidget(batch_lbl, 5, 0, 1, 1)
        batch_size = c.get(KEY_BATCH_SIZE, DEFAULT_STORE_VALUES[KEY_BATCH_SIZE])
        self.batch_spin = QSpinBox(self)
        self.batch_spin.setMinimum(1)
        self.batch_spin.setMaximum(10000)
        self.batch_spin.setProperty('value', batch_size)
        layout.addWidget(self.batch_spin, 5, 1, 1, 1)

        display_failures = c.get(KEY_DISPLAY_FAILURES, DEFAULT_STORE_VALUES[KEY_DISPLAY_FAILURES])
        self.display_failures_checkbox = QCheckBox(_('Display failure dialog if ISBN not found or identical'), self)
        self.display_failures_checkbox.setToolTip(_('Uncheck this option if you want do not want to be prompted\n'
                                                        'about no ISBN being found in the book or it is the same as\n'
                                                        'your current value.'))
        self.display_failures_checkbox.setChecked(display_failures)
        layout.addWidget(self.display_failures_checkbox, 6, 0, 1, 2)

        ask_for_confirmation = c.get(KEY_ASK_FOR_CONFIRMATION, DEFAULT_STORE_VALUES[KEY_ASK_FOR_CONFIRMATION])
        self.ask_for_confirmation_checkbox = QCheckBox(_('Prompt to apply ISBN changes'), self)
        self.ask_for_confirmation_checkbox.setToolTip(_('Uncheck this option if you want changes applied without\n'
                                                        'a confirmation dialog. There is a small risk with this\n'
                                                        'option unchecked that if you are making other changes to\n'
                                                        'this book record at the same time they will be lost.'))
        self.ask_for_confirmation_checkbox.setChecked(ask_for_confirmation)
        layout.addWidget(self.ask_for_confirmation_checkbox,7, 0, 1, 2)

        button_layout = QHBoxLayout()
        keyboard_shortcuts_button = QPushButton(' '+_('Keyboard shortcuts')+'... ', self)
        keyboard_shortcuts_button.setToolTip(_('Edit the keyboard shortcuts associated with this plugin'))
        keyboard_shortcuts_button.clicked.connect(self.edit_shortcuts)
        button_layout.addWidget(keyboard_shortcuts_button)

        help_button = QPushButton(' '+_('Help'), self)
        help_button.setIcon(get_icon('help.png'))
        help_button.clicked.connect(show_help)
        button_layout.addWidget(help_button)
        layout.addLayout(button_layout, 9, 0, 1, 2)

    def edit_shortcuts(self):
        d = KeyboardConfigDialog(self.plugin_action.gui, self.plugin_action.action_spec[0])
        if d.exec_() == d.Accepted:
            self.plugin_action.gui.keyboard.finalize()

class IdentificationTab(QWidget):

    def __init__(self, parent_dialog):
        QWidget.__init__(self)
        self.parent_dialog = parent_dialog
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.context_identification_config = ContextIdentificationConfig(self)
        layout.addWidget(self.context_identification_config)

class RankingTab(QWidget):

    def __init__(self, parent_dialog):
        QWidget.__init__(self)
        self.parent_dialog = parent_dialog
        layout = QGridLayout(self)
        self.setLayout(layout)

        c = plugin_prefs[STORE_NAME]

        ranking_method_lbl = QLabel(_('ISBN ranking method:'), self)
        ranking_method_lbl.setToolTip(_('Determines which ISBN will be selected out of the ones which are found.'))
        layout.addWidget(ranking_method_lbl, 0, 0, 1, 2)
        ranking_method = c.get(KEY_RANKING_METHOD, DEFAULT_STORE_VALUES[KEY_RANKING_METHOD])
        self.rankingMethodCombo = KeyValueComboBox(self, RANKING_METHODS, ranking_method)
        for index, tooltip in enumerate(RANKING_METHOD_TOOLTIPS):
            self.rankingMethodCombo.setItemData(index, tooltip, Qt.ItemDataRole.ToolTipRole)
        layout.addWidget(self.rankingMethodCombo, 1, 0, 1, 2)

        self.context_ranking_config = ContextRankingConfig(self)

        stacked_widget = QStackedWidget()
        stacked_widget.addWidget(QWidget())
        stacked_widget.addWidget(self.context_ranking_config)
        layout.addWidget(stacked_widget, 2, 0, 1, 2)

        self.rankingMethodCombo.activated[int].connect(stacked_widget.setCurrentIndex)
        stacked_widget.setCurrentIndex(self.rankingMethodCombo.currentIndex())

class ContextRankingConfig(QGroupBox):

    def __init__(self, parent_dialog):
        QGroupBox.__init__(self, _('Context Ranking'))
        self.parent_dialog = parent_dialog
        c = plugin_prefs[STORE_NAME]

        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.list_widget = QListWidget()
        self.list_widget.addItems(CONTEXT_TRANSLATIONS[i] for i in c.get(KEY_CONTEXT_RANKING_PRIORITY, DEFAULT_STORE_VALUES[KEY_CONTEXT_RANKING_PRIORITY]))
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setToolTip(_('The identifier matching the top-most context in this list\nwill be preferred over those below'))

        layout.addWidget(self.list_widget)

    def context_ranking_priority(self):
        return [self._reverse_context_translation(self.list_widget.item(i).text()) for i in range(self.list_widget.count())]

    def _reverse_context_translation(self, translation):
        return next(original for original, t in CONTEXT_TRANSLATIONS.items() if t == translation)

class TranslatableQListWidget(QListWidget):
    def __init__(self):
        QListWidget.__init__(self)

    def addItems(self, items):
        super(map(self._translate_item, items))


class ContextIdentificationConfig(QGroupBox):

    def __init__(self, parent_dialog):
        super().__init__(_('Context Identification'))
        self.parent_dialog = parent_dialog
        c = plugin_prefs[STORE_NAME]

        layout = QVBoxLayout(self)
        self.setLayout(layout)

        ebook_matcher_label = QLabel(_('eBook matcher:'), self)
        ebook_matcher_label.setToolTip(_('A regular expression which matches the context\nsurrounding an identifier when it is an ebook'))
        layout.addWidget(ebook_matcher_label)
        ebook_matcher = c.get(KEY_CONTEXT_MATCHER_EBOOK, DEFAULT_STORE_VALUES[KEY_CONTEXT_MATCHER_EBOOK])
        self.context_matcher_ebook_edit = QLineEdit(ebook_matcher, self)
        layout.addWidget(self.context_matcher_ebook_edit)

        hardback_matcher_label = QLabel(_('Hardback matcher:'), self)
        hardback_matcher_label.setToolTip(_('A regular expression which matches the context\nsurrounding an identifier when it is a hardback'))
        layout.addWidget(hardback_matcher_label)
        hardback_matcher = c.get(KEY_CONTEXT_MATCHER_HARDBACK, DEFAULT_STORE_VALUES[KEY_CONTEXT_MATCHER_HARDBACK])
        self.context_matcher_hardback_edit = QLineEdit(hardback_matcher, self)
        layout.addWidget(self.context_matcher_hardback_edit)

        paperback_matcher_label = QLabel(_('Paperback matcher:'), self)
        paperback_matcher_label.setToolTip(_('A regular expression which matches the context\nsurrounding an identifier when it is a paperback'))
        layout.addWidget(paperback_matcher_label)
        paperback_matcher = c.get(KEY_CONTEXT_MATCHER_PAPERBACK, DEFAULT_STORE_VALUES[KEY_CONTEXT_MATCHER_PAPERBACK])
        self.context_matcher_paperback_edit = QLineEdit(paperback_matcher, self)
        layout.addWidget(self.context_matcher_paperback_edit)

        print_matcher_label = QLabel(_('Print matcher:'), self)
        print_matcher_label.setToolTip(_('A regular expression which matches the context\nsurrounding an identifier when it is a printed text'))
        layout.addWidget(print_matcher_label)
        print_matcher = c.get(KEY_CONTEXT_MATCHER_PRINT, DEFAULT_STORE_VALUES[KEY_CONTEXT_MATCHER_PRINT])
        self.context_matcher_print_edit = QLineEdit(print_matcher, self)
        layout.addWidget(self.context_matcher_print_edit)

        source_matcher_label = QLabel(_('Source matcher:'), self)
        source_matcher_label.setToolTip(_('A regular expression which matches the context\nsurrounding an identifier when it is a source text'))
        layout.addWidget(source_matcher_label)
        source_matcher = c.get(KEY_CONTEXT_MATCHER_SOURCE, DEFAULT_STORE_VALUES[KEY_CONTEXT_MATCHER_SOURCE])
        self.context_matcher_source_edit = QLineEdit(source_matcher, self)
        layout.addWidget(self.context_matcher_source_edit)
