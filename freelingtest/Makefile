
# Makefile to build the simple examples of FreeLing usage.
# If your installation paths are not /usr/local, call make with:
#
# make FREELINGDIR=/my/freeling/dir BOOSTINCLUDEDIR=/my/boost/include BOOSTLIBDIR=/my/boost/lib KALDIDIR=/my/kaldi-root/dir

# directories where freeling and boost are installed
FREELINGDIR=/usr/local
BOOSTINCLUDEDIR=/usr/local/include
BOOSTLIBDIR=/usr/local/lib
ICUINCLUDEDIR=/usr/local/opt/icu4c/include
ICULIBDIR=/usr/local/opt/icu4c/lib
# paths for compilation commands below
PATHS=-L$(FREELINGDIR)/lib -I$(FREELINGDIR)/include -I$(FREELINGDIR)/include/foma -L$(BOOSTLIBDIR) -I$(BOOSTINCLUDEDIR) -L$(ICULIBDIR) -I$(ICUINCLUDEDIR)
LIBS=-lfreeling -lboost_system

# paths for "asr.cc" example (requires kaldi installed and FreeLing compiled with --with-kaldi-asr option)
KALDIDIR=none
KALDI=-I$(KALDIDIR)/src -I$(KALDIDIR)/tools/ATLAS/include -I$(KALDIDIR)/tools/openfst/include -L$(KALDIDIR)/src/lib -L$(KALDIDIR)/tools/openfst/lib -lfst -lkaldi-base -lkaldi-online2 -lkaldi-chain -lkaldi-kws -lkaldi-sgmm2 -lkaldi-cudamatrix -lkaldi-lat -lkaldi-decoder -lkaldi-lm -lkaldi-thread -lkaldi-feat -lkaldi-matrix -lkaldi-transform -lkaldi-fstext -lkaldi-nnet2 -lkaldi-tree -lkaldi-gmm -lkaldi-nnet3 -lkaldi-util -lkaldi-hmm -lkaldi-nnet -lkaldi-ivector -DKALDI_DOUBLEPRECISION=0 -DHAVE_OPENFST_GE_10400 -DHAVE_ATLAS -DHAVE_CXXABI_H


all: coreferences

coreferences: coreferences.cc 
	g++ -std=c++0x -o coreferences coreferences.cc $(PATHS) $(LIBS)

clean:
	rm -f coreferences

