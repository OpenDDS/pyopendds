#!/bin/bash

printf 'Compiling TypesSupport .idl files...\n'
pyidl TypeSupport_test.idl TypeSupport_to_include.idl -p TypeSupportTest

printf '\nRunning test:\n'
python main.py
