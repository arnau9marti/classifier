DIR=/usr/local

# paths for compilation commands below
PATHS=-L$(DIR)/lib -I$(DIR)/include
LIBS=-lpugixml

all:	classifier

classifier: classifier.cc
	g++  -o classifier classifier.cc $(LIBS)

clean:
	rm -f classifier

