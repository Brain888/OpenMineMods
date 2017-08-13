from PyQt5.QtWidgets import *
from CurseAPI import CurseAPI, CurseProject
from MultiMC import MultiMCInstance
from functools import partial
from Utils import clearLayout


class ModBrowseWindow(QWidget):
    def __init__(self, curse: CurseAPI, instance: MultiMCInstance):
        super().__init__()

        self.curse = curse
        self.instance = instance

        self.page = 0

        self.setWindowTitle("Browsing mods for {}")

        self.layout = QVBoxLayout()

        self.searchBox = QGroupBox("Search Mods")
        self.layout.addWidget(self.searchBox)

        self.searchGrid = QGridLayout()

        self.searchInp = QLineEdit(self)
        self.searchGrid.addWidget(self.searchInp, 0, 0)
        searchBut = QPushButton("Go")
        searchBut.clicked.connect(self.init_mods)
        self.searchGrid.addWidget(searchBut, 0, 1)

        self.searchBox.setLayout(self.searchGrid)

        self.modBox = QGroupBox("Available Mods")
        self.layout.addWidget(self.modBox)

        self.modTable = QGridLayout()

        self.init_mods()

        self.modBox.setLayout(self.modTable)
        self.setLayout(self.layout)

        self.show()

    def init_mods(self):
        clearLayout(self.modTable)

        if self.searchInp.text():
            mods = self.curse.search(self.searchInp.text())
        else:
            mods = self.curse.get_mod_list(self.instance.version, self.page)

        for x, mod in enumerate(mods):
            addButton = QPushButton("Install", self)
            addButton.clicked.connect(partial(self.add_clicked, mod=mod))
            self.modTable.addWidget(QLabel(mod.title), x, 0)
            self.modTable.addWidget(addButton, x, 1)

    def add_clicked(self, mod: CurseProject):
        print("Install {}".format(mod.title))
