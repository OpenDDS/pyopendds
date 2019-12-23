source .venv/bin/activate
pip install -e .
cd tests/basic_test
LD_LIBRARY_PATH="$LD_LIBRARY_PATH:build" python subscriber.py &
sub=$!
sleep 5
cd build
./publisher -DCPSConfigFile ../rtps.ini &
pub=$!
wait $sub
kill $pub
