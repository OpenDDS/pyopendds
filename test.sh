source $DDS_ROOT/setenv.sh
source .venv/bin/activate
pip install -e .
DCPSInfoRepo &
repo=$!
sleep 5
python test.py
kill $repo
