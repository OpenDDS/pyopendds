source $DDS_BUILDS/master/OpenDDS/setenv.sh
DCPSInfoRepo &
repo=$!
sleep 5
source .venv/bin/activate
python test.py
kill $repo
