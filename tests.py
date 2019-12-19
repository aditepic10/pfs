#!/usr/bin/env python

MODULES = {}
# Try to import test cases, ignore modules on fail
try:
    from submodules.antenna_deploy.test import run_tests as run_antenna_tests
    MODULES["antenna"] = run_antenna_tests
except:
    MODULES["antenna"] = False
try:
    from submodules.command_ingest.test import run_tests as run_command_tests
    MODULES["command"] = run_command_tests
except:
    MODULES["command"] = False
try:
    from submodules.eps.test import run_tests as run_eps_tests
    MODULES["eps"] = run_eps_tests
except:
    MODULES["eps"] = False
try:
    from submodules.radios.aprs_test import run_tests as run_aprs_tests
    MODULES["radio.aprs"] = run_aprs_tests
    APRS_PORT = "FAKE"
except:
    MODULES["radios.aprs"] = False
try:
    from submodules.radios.iridium_test import run_tests as run_iridium_tests
    MODULES["radios.iridium"] = run_iridium_tests
except:
    MODULES["radios.iridium"] = False
try:
    from submodules.telemetry.test.run_tests import run_tests as run_telemetry_tests
    MODULES["telemetry"] = run_telemetry_tests
except:
    MODULES["telemetry"] = False

if __name__ == '__main__':
    for module, func in MODULES.items():
        print()
        if func and not input(f"Run test cases for module {module}? [y]/N ") == 'N':
            func()
        else:
            print(f"run_tests not found for module {module}")
        print()
