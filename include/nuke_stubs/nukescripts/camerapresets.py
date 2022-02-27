#
# Camera preset class for cameraTracker film backs
#

class CameraFilmBackPresets:
  """A simple container object for holding the label and film back data of a camera."""

  def __init__(self):
    """Initialise by adding all of our presets."""

    self.presets = []

    self.addPreset("Custom", {'filmBackSize': '36 24'})
    self.addPreset("Film/35mm/2 perf 1.78", {'filmBackSize': '15.6 8.76'})
    self.addPreset("Film/35mm/2 perf 2.40 v1", {'filmBackSize': '22.05 9.27'})
    self.addPreset("Film/35mm/2 perf 2.40 v2", {'filmBackSize': '20.96 8.76'})
    self.addPreset("Film/35mm/3 perf 1.78", {'filmBackSize': '24.92 13.87'})
    self.addPreset("Film/35mm/4 perf 1.33 TV Safe", {'filmBackSize': '20.12 15.09'})
    self.addPreset("Film/35mm/4 perf 1.33 Large TV Transmit", {'filmBackSize': '21.13 15.85'})
    self.addPreset("Film/35mm/4 perf 1.78", {'filmBackSize': '24 13.5'})
    self.addPreset("Film/35mm/4 perf 1.85 Extract", {'filmBackSize': '24 12.98'})
    self.addPreset("Film/35mm/4 perf 1.85 Projection", {'filmBackSize': '20.96 11.33'})
    self.addPreset("Film/35mm/4 perf 2.40 Anamorphic Projection", {'filmBackSize': '20.96 17.53'})
    self.addPreset("Film/35mm/4 perf 2.40 Extract", {'filmBackSize': '20.96 10.4'})
    self.addPreset("Film/16mm 1.37", {'filmBackSize': '10.26 7.49'})
    self.addPreset("Film/Super 16mm 1.66", {'filmBackSize': '12.52 7.41'})
    self.addPreset("Film/Super 16mm 1.85", {'filmBackSize': '12.52 7.77'})
    self.addPreset("Film/35mm Full Frame", {'filmBackSize': '36 18.3'})
    self.addPreset("Film/65mm 2.20", {'filmBackSize': '52.63 23.01'})
    self.addPreset("Film/Panavision Super 70mm", {'filmBackSize': '48.56 22.1'})
    self.addPreset("Film/70mm Extract 2.40", {'filmBackSize': '48.56 20.31'})
    self.addPreset("Film/70mm Imax", {'filmBackSize': '70 48.5'})
    self.addPreset("Film/Academy", {'filmBackSize': '21.95 16'})
    self.addPreset("Film/Super35", {'filmBackSize': '24.89 18.66'})
    self.addPreset("Arri/D21 1.33", {'filmBackSize': '23.76 17.82'})
    self.addPreset("Arri/D21 1.78", {'filmBackSize': '23.76 13.37'})
    self.addPreset("Arri/D21 1.85", {'filmBackSize': '23.76 12.84'})
    self.addPreset("Arri/D21 2.40", {'filmBackSize': '23.76 9.94'})
    self.addPreset("Arri/Alexa 16:9 1.78", {'filmBackSize': '23.76 13.37'})
    self.addPreset("Arri/Alexa 16:9 1.85", {'filmBackSize': '23.76 12.84'})
    self.addPreset("Arri/Alexa 16:9 2.39 Scope 2x", {'filmBackSize': '15.97 13.37'})
    self.addPreset("Arri/Alexa 16:9 2.39 Flat", {'filmBackSize': '23.76 9.95'})
    self.addPreset("Arri/Alexa 4:3 1.33", {'filmBackSize': '23.76 17.82'})
    self.addPreset("Arri/Alexa 4:3 1.78", {'filmBackSize': '23.76 13.37'})
    self.addPreset("Arri/Alexa 4:3 1.85", {'filmBackSize': '23.76 12.84'})
    self.addPreset("Arri/Alexa 4:3 2.39 Scope 2x", {'filmBackSize': '21.30 17.82'})
    self.addPreset("Arri/Alexa 4:3 2.39 Flat", {'filmBackSize': '23.76 9.95'})
    self.addPreset("Black Magic/Pocket Cinema Camera", {'filmBackSize': '12.48 7.02'})
    self.addPreset("Black Magic/Cinema Camera 2k", {'filmBackSize': '15.81 8.88'})
    self.addPreset("Black Magic/Production Camera 4k", {'filmBackSize': '21.12 11.88'})
    self.addPreset("Canon/DSLR/M Still", {'filmBackSize': '22.3 14.9'})
    self.addPreset("Canon/DSLR/M Video", {'filmBackSize': '22.3 12.54'})
    self.addPreset("Canon/DSLR/1D MKIV Still", {'filmBackSize': '27.9 18.6'})
    self.addPreset("Canon/DSLR/1D MKIV Video", {'filmBackSize': '27.9 15.69'})
    self.addPreset("Canon/DSLR/1DX Still", {'filmBackSize': '36 24'})
    self.addPreset("Canon/DSLR/1DX Video", {'filmBackSize': '35.8 20.14'})
    self.addPreset("Canon/DSLR/5D MKII+III Still", {'filmBackSize': '36 24'})
    self.addPreset("Canon/DSLR/5D MKII+III Video", {'filmBackSize': '35.8 20.14'})
    self.addPreset("Canon/DSLR/6D Still", {'filmBackSize': '36 24'})
    self.addPreset("Canon/DSLR/6D Video", {'filmBackSize': '35.8 20.14'})
    self.addPreset("Canon/DSLR/7D Still", {'filmBackSize': '22.3 14.9'})
    self.addPreset("Canon/DSLR/7D Video", {'filmBackSize': '22.3 12.54'})
    self.addPreset("Canon/DSLR/60D Still", {'filmBackSize': '22.3 14.9'})
    self.addPreset("Canon/DSLR/60D Video", {'filmBackSize': '22.3 12.54'})
    self.addPreset("Canon/DSLR/70D Still", {'filmBackSize': '22.5 15.0'})
    self.addPreset("Canon/DSLR/70D Video", {'filmBackSize': '22.5 12.7'})
    self.addPreset("Canon/DSLR/Rebel 550D 600D 650D T2i T3i T4i Still", {'filmBackSize': '22.3 14.9'})
    self.addPreset("Canon/DSLR/Rebel 550D 600D 650D T2i T3i T4i Video", {'filmBackSize': '22.3 12.54'})
    self.addPreset("Canon/1DC Still", {'filmBackSize': '36 24'})
    self.addPreset("Canon/1DC Video", {'filmBackSize': '35.8 20.14'})
    self.addPreset("Canon/C100", {'filmBackSize': '24.6 13.8'})
    self.addPreset("Canon/C300", {'filmBackSize': '24.6 13.8'})
    self.addPreset("Canon/C500", {'filmBackSize': '24.6 13.8'})
    self.addPreset("Canon/XL1 4:3", {'filmBackSize': '4.82 3.64'})
    self.addPreset("Canon/XL1 16:9", {'filmBackSize': '4.82 2.73'})
    self.addPreset("Canon/XL2 4:3", {'filmBackSize': '4.8 3.6'})
    self.addPreset("Canon/XL2 16:9", {'filmBackSize': '6.4 3.6'})
    self.addPreset("Nikon/DSLR/D4 FX Still", {'filmBackSize': '36 23.9'})
    self.addPreset("Nikon/DSLR/D4 1.2x Still", {'filmBackSize': '30 20'})
    self.addPreset("Nikon/DSLR/D4 DX Still", {'filmBackSize': '24 16'})
    self.addPreset("Nikon/DSLR/D4 5:4 Still", {'filmBackSize': '30 24'})
    self.addPreset("Nikon/DSLR/D90 Still", {'filmBackSize': '23.6 15.8'})
    self.addPreset("Nikon/DSLR/D300S Still", {'filmBackSize': '23.6 15.8'})
    self.addPreset("Nikon/DSLR/D600 FX Still", {'filmBackSize': '35.9 24'})
    self.addPreset("Nikon/DSLR/D600 DX Still", {'filmBackSize': '24 16'})
    self.addPreset("Nikon/DSLR/D700 FX Still", {'filmBackSize': '36 23.9'})
    self.addPreset("Nikon/DSLR/D700 DX Still", {'filmBackSize': '24 16'})
    self.addPreset("Nikon/DSLR/D800 FX Still", {'filmBackSize': '35.9 24'})
    self.addPreset("Nikon/DSLR/D800 1.2x Still", {'filmBackSize': '30 20'})
    self.addPreset("Nikon/DSLR/D800 DX Still", {'filmBackSize': '24 16'})
    self.addPreset("Nikon/DSLR/D800 5:4 Still", {'filmBackSize': '30 24'})
    self.addPreset("Nikon/DSLR/D3100 DX Still", {'filmBackSize': '23.1 15.4'})
    self.addPreset("Nikon/DSLR/D3200 DX Still", {'filmBackSize': '23.2 15.4'})
    self.addPreset("Nikon/DSLR/D5100 DX Still", {'filmBackSize': '23.6 15.6'})
    self.addPreset("Nikon/DSLR/D7000 DX Still", {'filmBackSize': '23.6 15.6'})
    self.addPreset("Phantom/65 4k", {'filmBackSize': '52.1 31.04'}) #4096x2440
    self.addPreset("Phantom/65 4k 16:9", {'filmBackSize': '52.1 29.31'}) #4096x2304
    self.addPreset("Phantom/65 UHD", {'filmBackSize': '48.84 27.47'}) #3840x2160
    self.addPreset("Phantom/65 2k Square", {'filmBackSize': '26.05 26.05'}) #2048x2048
    self.addPreset("Phantom/65 2k 1.85", {'filmBackSize': '26.05 14.04'}) #2048x1104
    self.addPreset("Phantom/65 2k 2.35", {'filmBackSize': '26.05 11.09'}) #2048x872
    self.addPreset("Phantom/65 1080p", {'filmBackSize': '24.42 13.74'})
    self.addPreset("Phantom/65 1632x1200", {'filmBackSize': '20.76 15.26'})
    self.addPreset("Phantom/65 720p", {'filmBackSize': '16.28 9.16'})
    self.addPreset("Phantom/65 1152x896", {'filmBackSize': '14.65 11.4'})
    self.addPreset("Phantom/65 800x600", {'filmBackSize': '10.18 7.63'})
    self.addPreset("Phantom/65 640x480", {'filmBackSize': '8.14 6.11'})
    self.addPreset("Phantom/65 512x512", {'filmBackSize': '6.51 6.51'})
    self.addPreset("Phantom/65 256x256", {'filmBackSize': '3.26 3.26'})
    self.addPreset("Phantom/Flex 2.5k", {'filmBackSize': '25.6 15.46'})
    self.addPreset("Phantom/Flex 1080p", {'filmBackSize': '18.55 10.43'})
    self.addPreset("Phantom/Flex 720p", {'filmBackSize': '12.37 6.96'})
    self.addPreset("Phantom/Flex 640x480", {'filmBackSize': '6.18 4.64'})
    self.addPreset("Phantom/HD Gold 2k Square", {'filmBackSize': '25.6 25.6'})
    self.addPreset("Phantom/HD Gold 2k 1.85", {'filmBackSize': '25.6 13.8'})
    self.addPreset("Phantom/HD Gold 2k 2.35", {'filmBackSize': '25.6 10.9'})
    self.addPreset("Phantom/HD Gold 1080p", {'filmBackSize': '24 13.5'})
    self.addPreset("Phantom/HD Gold 720p", {'filmBackSize': '16 9'})
    self.addPreset("Phantom/HD Gold 1152x896", {'filmBackSize': '14.4 11.2'})
    self.addPreset("Phantom/HD Gold 800x600", {'filmBackSize': '10 7.5'})
    self.addPreset("Phantom/HD Gold 640x480", {'filmBackSize': '8 6'})
    self.addPreset("Phantom/HD Gold 512x512", {'filmBackSize': '6.4 6.4'})
    self.addPreset("Red/One/4.5k", {'filmBackSize': '24.19 10.37'})
    self.addPreset("Red/One/4k 16:9", {'filmBackSize': '22.12 12.44'})
    self.addPreset("Red/One/4k 2:1", {'filmBackSize': '22.12 11.06'})
    self.addPreset("Red/One/4k HD", {'filmBackSize': '20.74 11.66'})
    self.addPreset("Red/One/4k Anamorphic", {'filmBackSize': '14.93 12.44'})
    self.addPreset("Red/One/3k 16:9", {'filmBackSize': '16.59 9.33'})
    self.addPreset("Red/One/3k 2:1", {'filmBackSize': '16.65 8.29'})
    self.addPreset("Red/One/2k 16:9", {'filmBackSize': '11.06 6.22'})
    self.addPreset("Red/One/2k 2:1", {'filmBackSize': '11.06 5.53'})
    self.addPreset("Red/Epic/5k", {'filmBackSize': '27.648 14.58'})
    self.addPreset("Red/Epic/5k 2:1", {'filmBackSize': '27.648 13.824'})
    self.addPreset("Red/Epic/5k HD", {'filmBackSize': '25.920 14.58'})
    self.addPreset("Red/Epic/5k ANA", {'filmBackSize': '17.798 14.58'})
    self.addPreset("Red/Epic/5k WS", {'filmBackSize': '27.648 11.664'})
    self.addPreset("Red/Epic/4k", {'filmBackSize': '22.118 11.664'})
    self.addPreset("Red/Epic/4k HD", {'filmBackSize': '20.736 11.664'})
    self.addPreset("Red/Epic/3k", {'filmBackSize': '16.589 8.748'})
    self.addPreset("Red/Epic/3k HD", {'filmBackSize': '15.552 8.748'})
    self.addPreset("Red/Epic/2k", {'filmBackSize': '11.059 5.832'})
    self.addPreset("Red/Epic/2k HD", {'filmBackSize': '10.368 5.832'})
    self.addPreset("Red/Epic/2k WS", {'filmBackSize': '11.059 4.612'})
    self.addPreset("Red/Epic/1k HD", {'filmBackSize': '6.912 3.888'})
    self.addPreset("Red/Epic/1k WS", {'filmBackSize': '6.912 2.592'})
    self.addPreset("Red/Epic Dragon/6k Full", {'filmBackSize': '30.7 15.8'})
    self.addPreset("Red/Epic Dragon/6k FF3", {'filmBackSize': '36 18.56'})
    self.addPreset("Red/Epic Dragon/5.5k Full", {'filmBackSize': '27.7 14.6'})
    self.addPreset("Red/Epic Dragon/5k Full", {'filmBackSize': '25.58 13.49'})
    self.addPreset("Red/Epic Dragon/4k Full", {'filmBackSize': '20.47 10.79'})
    self.addPreset("Red/Epic Dragon/3k Full", {'filmBackSize': '15.35 8.09'})
    self.addPreset("Red/Epic Dragon/2k Full", {'filmBackSize': '10.25 5.4'})
    self.addPreset("Red/Epic Dragon/1k Full", {'filmBackSize': '6.4 3.6'})
    self.addPreset("Sony/DSLR/APS-C A37", {'filmBackSize': '23.5 15.6'})
    self.addPreset("Sony/DSLR/APS-C A57", {'filmBackSize': '23.5 15.6'})
    self.addPreset("Sony/DSLR/APS-C A58", {'filmBackSize': '23.5 15.6'})
    self.addPreset("Sony/DSLR/APS-C A65", {'filmBackSize': '23.5 15.6'})
    self.addPreset("Sony/DSLR/APS-C A77", {'filmBackSize': '23.5 15.6'})
    self.addPreset("Sony/DSLR/APS-C A3000", {'filmBackSize': '23.5 15.6'})
    self.addPreset("Sony/DSLR/Full Frame A99", {'filmBackSize': '35.8 23.9'})
    self.addPreset("Sony/DSLR/Mirrorless A7", {'filmBackSize': '35.8 23.9'})
    self.addPreset("Sony/DSLR/NEX-6", {'filmBackSize': '23.5 15.6'})
    self.addPreset("Sony/DSLR/SLT-A37", {'filmBackSize': '23.5 15.6'})
    self.addPreset("Sony/DSLR/SLT-A57", {'filmBackSize': '23.5 15.6'})
    self.addPreset("Sony/DSLR/SLT-A99", {'filmBackSize': '35.8 23.8'})
    self.addPreset("Sony/DSR-400", {'filmBackSize': '8.8 6.6'})
    self.addPreset("Sony/EX1", {'filmBackSize': '6.97 3.92'})
    self.addPreset("Sony/F3", {'filmBackSize': '24.7 13.1'})
    self.addPreset("Sony/FS100U", {'filmBackSize': '23.6 13.3'})#Exmor Super35 CMOS Sensor
    self.addPreset("Sony/FS700", {'filmBackSize': '23.6 13.3'})#Exmor Super35 CMOS Sensor
    self.addPreset("Sony/F35 1.78", {'filmBackSize': '23.62 13.28'})
    self.addPreset("Sony/F35 1.85", {'filmBackSize': '22.45 12.14'})
    self.addPreset("Sony/F35 2.39", {'filmBackSize': '22.45 9.4'})
    self.addPreset("Sony/F55", {'filmBackSize': '24 12.7'})
    self.addPreset("Sony/F5", {'filmBackSize': '24 12.7'})
    self.addPreset("Sony/F65", {'filmBackSize': '24.7 13.1'})

  def addPreset(self, label, filmBackDict):
    """Parse a dict for the camera aperture size and add to the list."""

    haperture, vaperture = [float(x) for x in filmBackDict['filmBackSize'].split()]
    self.presets.append( (label, haperture, vaperture) )

#
# Global preset object initialisation
#

_gFilmBackPresets = CameraFilmBackPresets()

#
# Utility functions for accessing global CameraFilmBackPreset member variables.
#

def getLabels():
  """Returns the list of preset labels for display in the knob."""
  return [preset[0] for preset in _gFilmBackPresets.presets]

def getFilmBackSize(index):
  """Returns the film back size for the given index."""
  return [_gFilmBackPresets.presets[index][1], _gFilmBackPresets.presets[index][2]];

def addPreset(label, haperture, vaperture):
  """Adds a preset to the global list of presets."""
  _gFilmBackPresets.addPreset(label, {'filmBackSize': str(haperture)+' '+str(vaperture)})
