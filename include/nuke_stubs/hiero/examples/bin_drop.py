# Class to show how to handle drop events in the bin view
from hiero.core.events import *

class BinViewDropHandler:
  kTextMimeType = "text/plain"
  
  def __init__(self):
    # Hiero doesn't deal with drag and drop for text/plain data, so tell it to allow it.
    hiero.ui.registerBinViewCustomMimeDataType(BinViewDropHandler.kTextMimeType)
    
    # Register interest in the drop event now.
    registerInterest((EventType.kDrop, EventType.kBin), self.dropHandler)

  def dropHandler(self, event):
    # Get the mime data.
    print('mimeData: {}'.format(event.mimeData))

    # Fast and easy way to get text data.
    if event.mimeData.hasText():
      print('mimeData as text: ', event.mimeData.text())
      
    # More complicated way of getting text data.
    if event.mimeData.hasFormat(BinViewDropHandler.kTextMimeType):
      byteArray = event.mimeData.data(BinViewDropHandler.kTextMimeType)
      print('mimeData data as a string: {}'.format(byteArray.data().decode('utf-8')))

      # Signal that we've handled the event here.
      event.dropEvent.accept()

    # Get custom Hiero objects if drag from one view to another.
    # Ths is only present if the drop was from one Hiero view to another.
    if hasattr(event, "items"):
      print('mimeData has items: {}'.format(event.items))
    
    # Figure out which item it was dropped onto.
    print('mimeData drop item: {}'.format(event.dropItem))
    
    # Get the widget that the drop happened in.
    print('mimeData drop widget: {}'.format(event.dropWidget))
    
    # Get the higher level container widget (for the Bin View, this will be the Bin View widget).
    print('mimeData container widget: {}'.format(event.containerWidget))
    
    # Can also get the sender.
    print('mimeData event sender: {}'.format(event.sender))
      
  def unregister(self):
    unregisterInterest((EventType.kDrop, EventType.kBin), self.dropHandler)
    hiero.ui.unregisterBinViewCustomMimeDataType(BinViewDropHandler.kTextMimeType)


# Instantiate the handler to get it to register itself.
dropHandler = BinViewDropHandler()
