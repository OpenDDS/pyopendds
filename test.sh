source .venv/bin/activate
pip install -e .
cd test
LD_LIBRARY_PATH="$LD_LIBRARY_PATH:build" python test.py
