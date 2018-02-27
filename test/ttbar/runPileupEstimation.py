import optparse
import os,sys
import json
import commands
import ROOT
from SimGeneral.MixingModule.mix_2017_25ns_WinterMC_PUScenarioV1_PoissonOOTPU_cfi import *

"""
steer the script
"""
def main():

    #configuration
    usage = 'usage: %prog [options]'
    parser = optparse.OptionParser(usage)
    parser.add_option('--certJson',  dest='certJson',      help='json file with processed runs',          default=None,    type='string')
    parser.add_option('--dataRange', dest='dataRange'  ,   help='name of data range for pileup file name',                  default="",    type='string')
    #parser.add_option('--MCName',    dest='MCName'  ,      help='name of MC sample for reweighting histogram name',         default="",    type='string')
    parser.add_option('--mbXsec',    dest='mbXsec'  ,      help='minimum bias cross section to use',      default=69200,   type=float)
    parser.add_option('--mbXsecUnc', dest='mbXsecUnc'  ,   help='minimum bias cross section uncertainty', default=0.046,   type=float)
    parser.add_option('--mcDirs',    dest='mcDirs'  ,      help='directories of MC to build PU',          default="",      type='string')
    parser.add_option('--puJson',    dest='puJson'  ,      help='pileup json file',      
                      default='/afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions17/13TeV/PileUp/pileup_latest.txt',    type='string')
    (opt, args) = parser.parse_args()
   
    MCDirs=opt.mcDirs.split(",")

    MCName=MCDirs[0].split("crab_")[1].split("/")[0]
 
    #simulated pileup
    if len(MCDirs)==0:    
        NPUBINS=len(mix.input.nbPileupEvents.probValue)
        simPuH=ROOT.TH1F('simPuH','',NPUBINS,float(0),float(NPUBINS))
        for xbin in xrange(0,NPUBINS):
            probVal=mix.input.nbPileupEvents.probValue[xbin]
            simPuH.SetBinContent(xbin,probVal)
    else:
        NPUBINS=100
        simPuH=ROOT.TH1F('simPuH','',NPUBINS,float(0),float(NPUBINS))
        print "N dirs",len(MCDirs)
        for directory in MCDirs:
            fileNames=os.listdir(directory)
            print "N files",len(fileNames)
            iFile=0
            for fileName in fileNames:
                if iFile%50==0:
                    print "iFile",iFile
                iFile=iFile+1
                if fileName.find(".root")!=-1:
                    tfile=ROOT.TFile.Open(directory+"/"+fileName)
                    puPlus=tfile.Get("allEvents/hPUPlusCount")
                    simPuH.Add(puPlus)
                    puNeg=tfile.Get("allEvents/hPUNegCount")
                    simPuH.Add(puNeg,-1)
                    tfile.Close()
        
    simPuH.Scale(1./simPuH.Integral())
    #simPuH.Draw("hist")
    #raw_input()

    #compute pileup in data assuming different xsec
    puDist=[]
    puWgts=[]
    MINBIASXSEC={'nom':opt.mbXsec,'up':opt.mbXsec*(1.+opt.mbXsecUnc),'down':opt.mbXsec*(1.-opt.mbXsecUnc)}
    for scenario in MINBIASXSEC:
        oFileName="Pileup_"+scenario+"_"+opt.dataRange+".root"
        if os.path.isfile(oFileName):
            print "pile up target exists"
            continue
        print scenario, 'xsec=',MINBIASXSEC[scenario]
        cmd='pileupCalc.py -i %s --inputLumiJSON %s --calcMode true --minBiasXsec %f --maxPileupBin %d --numPileupBins %s %s'%(opt.certJson,opt.puJson,MINBIASXSEC[scenario],NPUBINS,NPUBINS,oFileName)
        print cmd
        commands.getstatusoutput(cmd)

    for scenario in MINBIASXSEC:
        oFileName="Pileup_"+scenario+"_"+opt.dataRange+".root"
        fIn=ROOT.TFile.Open(oFileName)
        pileupH=fIn.Get('pileup')
        pileupH.Scale(1./pileupH.Integral())
        puDist.append( ROOT.TGraph(pileupH) )
        puDist[-1].SetName('pu_'+scenario+'_'+MCName)

        pileupH.Divide(simPuH)
        puWgts.append( ROOT.TGraph(pileupH) )
        puWgts[-1].SetName('puwgts_'+scenario+'_'+MCName)
        fIn.Close()
    #commands.getstatusoutput('mv Pileup.root Pileup'+str(opt.append)+'.root')

    #save pileup weights to file
    #fOut=ROOT.TFile.Open('$CMSSW_BASE/src/RecoBTag/PerformanceMeasurements/test/ttbar/data/pileupWgts'+str(opt.dataRange)+'.root','RECREATE')
    fOut=ROOT.TFile.Open('$CMSSW_BASE/src/RecoBTag/PerformanceMeasurements/test/ttbar/data/pileupWgts'+str(opt.dataRange)+'.root','UPDATE')
    for gr in puWgts: gr.Write()
    for gr in puDist: gr.Write()
    fOut.Close()

"""
for execution from another script
"""
if __name__ == "__main__":
    sys.exit(main())
