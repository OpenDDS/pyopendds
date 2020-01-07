LD_LIBRARY_PATH="$LD_LIBRARY_PATH:build" python3 subscriber.py &
sub=$!

cd build
./publisher -DCPSConfigFile ../rtps.ini &
pub=$!

exit_status=0
wait $pub
pub_status=$?
if [ $pub_status -ne 0 ]
then
  echo "Publisher exited with status $pub_status" 1>&2
  exit_status=1
fi
wait $sub
sub_status=$?
if [ $sub_status -ne 0 ]
then
  echo "Subscriber exited with status $sub_status" 1>&2
  exit_status=1
fi
exit $exit_status
