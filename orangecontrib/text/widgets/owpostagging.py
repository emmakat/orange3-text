from PyQt4 import QtGui

from Orange.widgets import gui
from Orange.widgets import settings
from Orange.widgets.widget import OWWidget, Msg
from orangecontrib.text.corpus import Corpus
from orangecontrib.text.tag.pos import taggers, StanfordPOSTagger
from orangecontrib.text.widgets.utils import ResourceLoader


class Input:
    CORPUS = 'Corpus'


class Output:
    CORPUS = 'Corpus'


class OWPOSTagger(OWWidget):
    """Marks up words with corresponding part of speech."""
    name = 'POS Tagging'
    icon = 'icons/POSTagging.svg'
    priority = 50

    inputs = [
        (Input.CORPUS, Corpus, 'set_data'),
    ]
    outputs = [
        (Output.CORPUS, Corpus)
    ]

    want_main_area = False
    resizing_enabled = False

    # Settings
    autocommit = settings.Setting(True)
    tagger_index = settings.Setting(0)

    STANFORD = len(taggers)
    stanford = settings.SettingProvider(ResourceLoader)

    class Error(OWWidget.Error):
        not_configured = Msg("Tagger wasn't configured")
        stanford = Msg("Problem while loading Stanford POS Tagger {}")

    def __init__(self):
        super().__init__()
        self.corpus = None
        self.tagger = None
        self.stanford_tagger = None


        button_group = QtGui.QButtonGroup(self, exclusive=True)
        button_group.buttonClicked[int].connect(self.change_tagger)

        layout = QtGui.QVBoxLayout()
        layout.setSpacing(15)
        self.controlArea.layout().addLayout(layout)

        for i, tagger in enumerate(taggers + [StanfordPOSTagger]):
            rb = QtGui.QRadioButton(text=tagger.name)
            rb.setChecked(i == self.tagger_index)
            button_group.addButton(rb, i)
            layout.addWidget(rb)

        box = QtGui.QGroupBox('Stanford')
        layout = QtGui.QVBoxLayout(box)
        layout.setMargin(0)
        self.stanford = ResourceLoader(widget=self, model_format='Stanford model (*.model *.tagger)',
                                       provider_format='Java file (*.jar)',
                                       model_button_label='Model', provider_button_label='Tagger')
        self.set_stanford_tagger(self.stanford.model_path, self.stanford.resource_path)

        self.stanford.valueChanged.connect(self.set_stanford_tagger)
        layout.addWidget(self.stanford)
        self.controlArea.layout().addWidget(box)

        buttons_layout = QtGui.QHBoxLayout()
        buttons_layout.addWidget(self.report_button)
        buttons_layout.addSpacing(15)
        buttons_layout.addWidget(
            gui.auto_commit(None, self, 'autocommit', 'Commit', box=False)
        )
        self.controlArea.layout().addLayout(buttons_layout)

    def change_tagger(self, i):
        if i != self.tagger_index:
            self.tagger_index = i
            self.on_change()

    def set_data(self, data):
        self.corpus = data
        self.on_change()

    def commit(self):
        if self.tagger_index == self.STANFORD:
            self.tagger = self.stanford_tagger
        else:
            self.tagger = taggers[self.tagger_index]

        self.apply()

    def apply(self):
        if self.corpus is not None:
            if not self.tagger:
                if self.tagger_index == self.STANFORD:
                    self.Error.stanford('')
                else:
                    self.Error.not_configured()
            else:
                self.Error.clear()
                new_corpus = self.tagger.tag_corpus(self.corpus.copy())
                self.send(Output.CORPUS, new_corpus)

    def on_change(self):
        self.Error.clear()
        self.commit()

    def set_stanford_tagger(self, model_path, stanford_path):
        self.stanford_tagger = None
        if model_path and stanford_path:
            try:
                StanfordPOSTagger.check(model_path, stanford_path)
                self.stanford_tagger = StanfordPOSTagger(model_path, stanford_path)
            except ValueError as e:
                self.Error.stanford(str(e))

        self.on_change()

    def send_report(self):
        self.report_items('Tagger', (('Name', self.tagger.name),))


if __name__ == '__main__':
    app = QtGui.QApplication([])
    widget = OWPOSTagger()
    widget.set_data(Corpus.from_file('deerwester'))
    widget.show()
    app.exec()
    widget.saveSettings()
