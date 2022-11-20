import hiero.core.log
hiero.core.log.info( "Loading Python hiero.importers package" )

import FnCyclone
from . import FnEdlImporter

#Register importers
FnCyclone.registerImporter(importer=FnEdlImporter.EdlImporter())
