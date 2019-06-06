# AOD_Lattice

## Dependencies:
### UHD library:
can be installed with the following commands. 
```
git clone https://github.com/EttusResearch/uhd.git
cd uhd/host && mkdir build
cmake ../
make test
make install
```

### Watchdog library:
can be installed with the following commands. 
```
pip install watchdog
```

## Getting started:
This repository has 2 folders a usercode folder and a servercode folder.
The usercode folder can be run without being connected to the SDR.
The servercode folder is intended to be run on the server that is connected to the SDR.
To get start
```
git clone --recursive git://github.com/QuantumQuadrate/AOD_Lattice.git
cd AOD_lattice
```
