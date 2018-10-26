cd test
rm -fr build
mkdir build
cd build
cmake ..
make
cd ../..
source .venv/bin/activate
pip install -e .
