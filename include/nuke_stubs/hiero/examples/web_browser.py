# An example of creating a dockable panel from Python.
# This script creates a simple PySide2 Qt web browser.

import hiero.ui
from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtWebEngineWidgets import *

class WebBrowserWidget(QWidget):
  def changeLocation(self):
    self.webView.load( QUrl(self.locationEdit.text()) )

  def __init__(self):
    QWidget.__init__( self )

    self.setObjectName( "uk.co.thefoundry.webwidget.1" )
    self.setWindowTitle( "Web Browser" )

    # If we set WA_DeleteOnClose, the widget will be destroyed when closed. If not, it'll remain in the Windows menu and can be shown again.
    #self.setAttribute( Qt.WA_DeleteOnClose, True )

    self.webView = QWebEngineView();
   
    self.setLayout( QVBoxLayout() )  
    
    self.locationEdit = QLineEdit( 'http://www.foundry.com' )
    self.locationEdit.setSizePolicy( QSizePolicy.Expanding, self.locationEdit.sizePolicy().verticalPolicy() )
    
    QObject.connect( self.locationEdit, SIGNAL('returnPressed()'),  self.changeLocation )
    
    self.layout().addWidget( self.locationEdit )
  
    bar = QToolBar()
    bar.addAction( self.webView.pageAction(QWebEnginePage.Back))
    bar.addAction( self.webView.pageAction(QWebEnginePage.Forward))
    bar.addAction( self.webView.pageAction(QWebEnginePage.Stop))
    bar.addAction( self.webView.pageAction(QWebEnginePage.Reload))
    bar.addSeparator()

    self.layout().addWidget( bar )
    self.layout().addWidget( self.webView )

    self.webView.load( QUrl( self.locationEdit.text() ) )

webBrowser = WebBrowserWidget()
wm = hiero.ui.windowManager()
wm.addWindow( webBrowser )

