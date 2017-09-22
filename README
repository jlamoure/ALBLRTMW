# EXAMPLE install-and-run:

> $ python install.py ../backups/lblrtm/17.02.25/ aer
> $ python createModel.py
> $ python readTAPE5lblrtm.py models/maunakea/TAPE5_lblrtm
> $ python plot.py models/maunakea/TAPE30_maunakea 

# install.py: extract and compile AER's LNFL and LBLRTM

> $ python install.py AER-tars-dir source-dir build-dir, or
> $ python install.py AER-tars-dir source-and-build-dir

- where AER-tars-dir contains aer_lblrtm_v12.X_lnfl_v3.X.tar.gz and aer_v_3.X.tar.gz
- request AER tars from http://rtweb.aer.com/lblrtm_code.html

# run.py: run LNFL and/or LBLRTM, when there is a TAPE5_lnfl and TAPE5_lblrtm to use

> $ python run.py --lblrtm model-dir, run only LBLRTM to produce model
> $ python run.py --lnfl model-dir, run only LNFL to produce linefile for LBLRTM

### supported by:

- makeTAPE5lblrtm.py, cannot be run from command line
- makeTAPE5lnfl.py, cannot be run from command line

# readTAPE5lblrtm.py: prints LBLRTM TAPE5 records and entries to console

> $ python readTAPE5lblrtm.py path-to/TAPE5_lblrtm

# fitter.py: try to match input spectrum iteratively with LBLRTM models

- edit main function to enter parameters
- algorithms are NOT polished

> $ python fitter.py algorithm-int-0-to-3 path-to/input-spectrum-file

# createModel.py: create LNFL TAPE5, run LNFL, create LBLRTM TAPE5, run LBLRTM

- edit main function to enter parameters

> $ python createModel.py

# plotSpectrum.py: can parse LBLRTMs output spectrum TAPEs, (beta) ATRAN model file

> $ python plot.py path-to/TAPE30-or-29-28-27
