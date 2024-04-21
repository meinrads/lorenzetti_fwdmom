#!/usr/bin/env python3

from GaugiKernel          import LoggingLevel, Logger
from GaugiKernel          import GeV
from G4Kernel             import *
import argparse
import sys,os, traceback


mainLogger = Logger.getModuleLogger("job")
parser = argparse.ArgumentParser(description = '', add_help = False)
parser = argparse.ArgumentParser()


parser.add_argument('-i','--inputFile', action='store', dest='inputFile', required = False,
                    help = "The event input file generated by the Pythia event generator.")

parser.add_argument('-o','--outputFile', action='store', dest='outputFile', required = False,
                    help = "The reconstructed event file generated by lzt/geant4 framework.")

parser.add_argument('--nov','--numberOfEvents', action='store', dest='numberOfEvents', required = False, type=int, default=-1,
                    help = "The number of events to apply the reconstruction.")

parser.add_argument('-l', '--outputLevel', action='store', dest='outputLevel', required = False, type=str, default='INFO',
                    help = "The output level messenger.")

parser.add_argument('-c','--command', action='store', dest='command', required = False, default="''",
                    help = "The preexec command")
                  
parser.add_argument('-f', '--doForward', action='store', dest='doForward', required = False, type=bool, default=False,
                    help = "Build forward rings?")


if len(sys.argv)==1:
  parser.print_help()
  sys.exit(1)

args = parser.parse_args()

doForward = args.doForward

outputLevel = LoggingLevel.toC(args.outputLevel)

try:

  exec(args.command)

  from GaugiKernel import ComponentAccumulator
  acc = ComponentAccumulator("ComponentAccumulator", args.outputFile)


  from RootStreamBuilder import RootStreamESDReader, recordable
  ESD = RootStreamESDReader("ESDReader", 
                            InputFile       = args.inputFile,
                            OutputCellsKey  = recordable("Cells"),
                            OutputEventKey  = recordable("Events"),
                            OutputTruthKey  = recordable("Particles"),
                            OutputSeedsKey  = recordable("Seeds"),
                            OutputLevel     = outputLevel
                            )
  ESD.merge(acc)


  # build cluster for all seeds
  from CaloClusterBuilder import CaloClusterMaker
  cluster = CaloClusterMaker( "CaloClusterMaker",
                              InputCellsKey        = recordable("Cells"),
                              InputSeedsKey        = recordable("Seeds"),
                              # output as
                              OutputClusterKey     = recordable("Clusters"),
                              # other configs
                              HistogramPath        = "Expert/Clusters",
                              OutputLevel          = outputLevel )

  # build rings for forward electron candidates (2.5<|eta|<3.2) only if -f True
  if(doForward == True):
    from CaloRingsBuilder import CaloRingsMakerCfg
    rings   = CaloRingsMakerCfg(   "CaloRingsMaker",
                                InputClusterKey    = recordable("Clusters"),  
                                OutputRingerKey    = recordable("Rings"),
                                HistogramPath      = "Expert/Rings",
                                OutputLevel        = outputLevel)
  else:
    from CaloRingsBuilder import CaloRingsMakerCfg
    rings   = CaloRingsMakerCfg(   "CaloRingsMaker",
                                InputClusterKey    = recordable("Clusters"),  
                                OutputRingerKey    = recordable("Rings"),
                                HistogramPath      = "Expert/Rings",
                                OutputLevel        = outputLevel)



  from RootStreamBuilder import RootStreamAODMaker
  AOD = RootStreamAODMaker( "RootStreamAODMaker",
                            InputEventKey    = recordable("Events"),
                            InputSeedsKey    = recordable("Seeds"),
                            InputTruthKey    = recordable("Particles"),
                            InputCellsKey    = recordable("Cells"),
                            InputClusterKey  = recordable("Clusters"),
                            InputRingerKey   = recordable("Rings"),
                            OutputLevel      = outputLevel)

  # sequence
  acc+= cluster
  acc+= rings
  acc+= AOD

  acc.run(args.numberOfEvents)

  del acc
  sys.exit(0)
  
except  Exception as e:
  traceback.print_exc()
  mainLogger.error(e)
  sys.exit(1)

