vertical-integration
-------
vertical-integration is a fake library that tricks travis into building the
outer product of the NSLS-II data stack for master and the latest point releases
for all of our libraries on python 2.7 and 3.4.  This includes:

- `bluesky`
- `metadatastore`
- `dataportal`
- `filestore`
- `scikit-xray`
- `replay`
- `suitcase`

Build matrix
------
It would be super cool to get a graphic here for what combinations of things
cause tests to fail.

In the mean time... Is anything failing? ----> [![Build Status](https://travis-ci.org/NSLS-II/vertical-integration.svg?branch=master)](https://travis-ci.org/NSLS-II/vertical-integration)
