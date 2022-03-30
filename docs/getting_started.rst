###############
Getting Started
###############

Once :file:`$DDS_ROOT/setenv.sh` has been sourced or the equivalent, run the commands
below in this directory.

.. code-block:: shell

    # Build and Install PyOpenDDS
    pip install .

    # Build Basic Test
    cd tests/basic_test
    mkdir build
    cd build
    cmake ..
    make

    # Build and Install Basic Test Python Type Support
    itl2py -o basic_output basic_idl opendds_generated/basic.itl
    # If using OpenDDS 3.19 or before, then just specify basic.itl
    cd basic_output
    pip install .

    # Run Basic Test
    cd ../..
    bash run_test.sh
