"""Error dialog widget that shows when app had an exception at launch."""
# coding: utf-8
from __future__ import print_function

import logging
import traceback

from collections import namedtuple

from PySide2.QtWidgets import QMessageBox
from PySide2.QtGui import QClipboard, QDesktopServices

from ..about import get_about_key, about_to_string


LOGGER = logging.getLogger('__projectSlug__.error_dialog')


def _get_critical_logger():
    """Search the logger named Critical.

    Returns:
        (Handler|None): the logger handler if found or None if not found.
    """
    for logger in LOGGER.parent.handlers:
        if logger.name == 'Critical':
            return logger

    return None


def _prepare_report():
    """Prepare report when user wants to report bug.

    Will also insert the 'about' information inside the errors.log file.

    Returns:
        (str): a string contaning the about information with the traceback err.
    """
    critical_logger = _get_critical_logger()

    if not critical_logger:
        return None

    with open(critical_logger.baseFilename, 'r+') as file:
        content = file.read()
        file.seek(0, 0)

        about_traceback = about_to_string() + '\n' + content
        file.write(about_traceback)

    return about_traceback


class ErrorDialog(QMessageBox):
    """Error dialog widget."""

    def __init__(self, msg, parent=None):
        """Init method for the ErrorDialog class.

        Create a custom QMessageBox widget to be shown when an error happens.
        Widget will have link to the github issues and the path to the logs.

        Traceback will be shown in the "see more details" section.

        Args:
            msg (str): message to be shown
            parent (QWidget, optional): QWidget to be set as a parent. This is
            needed when launch the widget in non modal mode. Defaults to None.
        """
        QMessageBox.__init__(self, parent)
        self.setWindowTitle('__projectSlug__')
        self.setIcon(QMessageBox.Warning)

        self.setText('__projectSlug__ error...')
        self.setInformativeText(str(msg))

        self.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        self.addButton('Report bug', QMessageBox.ActionRole)
        self.addButton('Open logs', QMessageBox.ActionRole)

        self.buttonClicked.connect(self.click_event)

        self._traceback = traceback.format_exc()
        self.setDetailedText(
            'Traceback will be copied to clipboard when clicking Report Bug.'
            '\n---\n' + self._traceback
        )

    def prepare_report(self):  # type() -> Report
        """Prepare the error report and copies it to the clipboard.

        Returns:
            Report: a namedtuple with the link and the port attributes.
        """
        report = _prepare_report() or self._traceback

        clipboard = QClipboard()
        clipboard.setText(report)

        Report = namedtuple('Report', 'report link')
        return Report(report, get_about_key('Issues'))

    def click_event(self, button):
        """After the click event, get the link to open."""
        if button.text() == 'Report bug':
            to_open = self.prepare_report().link

        elif button.text() == 'Open logs':
            to_open = get_about_key('Logs')

        elif button.text() in ['OK', 'Cancel']:
            return

        QDesktopServices.openUrl(to_open)
