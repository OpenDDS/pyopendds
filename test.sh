source .venv/bin/activate
pip install -e .
cd test
LD_LIBRARY_PATH="$LD_LIBRARY_PATH:build" python test.py &
sub=$!
sleep 5
cd build
./publisher -DCPSConfigFile ../rtps.ini &
pub=$!
wait $sub
kill $pub
