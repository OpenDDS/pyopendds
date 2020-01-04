set -e
cd tests/basic_test
rm -fr build
mkdir build
cd build
cmake ..
make
rm -fr basic_output
itl2py -o basic_output basic.itl
cd basic_output
basic_idl_DIR=$(realpath ..) pip install -e .
