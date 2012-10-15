"""
Scheme Info editor widget.

"""

from PyQt4.QtGui import (
    QWidget, QDialog, QLabel, QLineEdit, QTextEdit, QCheckBox, QFormLayout,
    QVBoxLayout, QHBoxLayout, QDialogButtonBox, QSizePolicy
)

from PyQt4.QtCore import Qt

from ..gui.utils import StyledWidget_paintEvent, StyledWidget
from .. import config


class SchemeInfoEdit(QWidget):
    """Scheme info editor widget.
    """
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        self.scheme = None
        self.__setupUi()

    def __setupUi(self):
        layout = QFormLayout()
        layout.setRowWrapPolicy(QFormLayout.WrapAllRows)
        layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        self.name_edit = QLineEdit(self)
        self.name_edit.setPlaceholderText(self.tr("untitled"))
        self.name_edit.setSizePolicy(QSizePolicy.Expanding,
                                     QSizePolicy.Fixed)
        self.desc_edit = QTextEdit(self)

        layout.addRow(self.tr("Name"), self.name_edit)
        layout.addRow(self.tr("Description"), self.desc_edit)

        self.setLayout(layout)

    def setScheme(self, scheme):
        """Set the scheme to display/edit

        """
        self.scheme = scheme
        self.name_edit.setText(scheme.title or "")
        self.desc_edit.setPlainText(scheme.description or "")

    def commit(self):
        """Commit the current contents of the editor widgets
        back to the scheme.

        """
        name = unicode(self.name_edit.text()).strip()
        description = unicode(self.desc_edit.toPlainText()).strip()
        self.scheme.title = name
        self.scheme.description = description

    def paintEvent(self, event):
        return StyledWidget_paintEvent(self, event)


class SchemeInfoDialog(QDialog):
    def __init__(self, *args, **kwargs):
        QDialog.__init__(self, *args, **kwargs)
        self.scheme = None
        self.__setupUi()

    def __setupUi(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.editor = SchemeInfoEdit(self)
        self.editor.layout().setContentsMargins(20, 20, 20, 20)
        self.editor.layout().setSpacing(15)
        self.editor.setSizePolicy(QSizePolicy.MinimumExpanding,
                                  QSizePolicy.MinimumExpanding)

        heading = self.tr("Scheme Info")
        heading = "<h3>{0}</h3>".format(heading)
        self.heading = QLabel(heading, self, objectName="heading")

        # Insert heading
        self.editor.layout().insertRow(0, self.heading)

        self.buttonbox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal,
            self
            )

        # Insert button box
        self.editor.layout().addRow(self.buttonbox)

        widget = StyledWidget(self, objectName="auto-show-container")
        check_layout = QHBoxLayout()
        check_layout.setContentsMargins(20, 10, 20, 10)
        self.auto_show_check = \
            QCheckBox(self.tr("Don't show again when I make a New Scheme."),
                      self,
                      objectName="auto-show-check",
                      checked=not config.rc.get(
                            "mainwindow.show-properties-on-new-scheme", True
                            )
                      )

        check_layout.addWidget(self.auto_show_check)
        check_layout.addWidget(
               QLabel(self.tr("You can edit and add Scheme Info later at the "
                              "bottom of the menu"),
                      self,
                      objectName="auto-show-info"),
               alignment=Qt.AlignRight)
        widget.setLayout(check_layout)
        widget.setSizePolicy(QSizePolicy.MinimumExpanding,
                             QSizePolicy.Fixed)

        self.buttonbox.accepted.connect(self.editor.commit)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        layout.addWidget(self.editor, stretch=10)
        layout.addWidget(widget)

        self.setLayout(layout)

    def setScheme(self, scheme):
        """Set the scheme to display/edit.
        """
        self.scheme = scheme
        self.editor.setScheme(scheme)

    def accept(self):
        checked = self.auto_show_check.isChecked()
        config.rc["mainwindow.show-properties-on-new-scheme"] = not checked
        return QDialog.accept(self)
