dir="build$1"
LD_LIBRARY_PATH="$LD_LIBRARY_PATH:$dir" python3 subscriber.py &
sub=$!

cd $dir
./publisher -DCPSConfigFile ../rtps.ini &
pub=$!
cd -

exit_status=0
wait $pub
pub_status=$?
if [ $pub_status -ne 0 ]
then
  echo "Cpp publisher exited with status $pub_status" 1>&2
  exit_status=1
fi
wait $sub
sub_status=$?
if [ $sub_status -ne 0 ]
then
  echo "Python subscriber exited with status $sub_status" 1>&2
  exit_status=1
fi

cd $dir
./subscriber -DCPSConfigFile ../rtps.ini &
sub=$!
cd -

LD_LIBRARY_PATH="$LD_LIBRARY_PATH:$dir" python3 publisher.py &
pub=$!

exit_status=0
wait $pub
pub_status=$?
if [ $pub_status -ne 0 ]
then
  echo "Python publisher exited with status $pub_status" 1>&2
  exit_status=1
fi
wait $sub
sub_status=$?
if [ $sub_status -ne 0 ]
then
  echo "Cpp subscriber exited with status $sub_status" 1>&2
  exit_status=1
fi
exit $exit_status
