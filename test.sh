set -e

cd tests/basic_test
LD_LIBRARY_PATH="$LD_LIBRARY_PATH:build" python3 subscriber.py &
sub=$!

cd build
./publisher -DCPSConfigFile ../rtps.ini &
pub=$!

wait
