set -e

cd tests/basic_test
LD_LIBRARY_PATH="$LD_LIBRARY_PATH:build" python3 subscriber.py &
sub=$!
sleep 5
cd build
./publisher -DCPSConfigFile ../rtps.ini &
pub=$!
wait $sub
kill $pub
wait
