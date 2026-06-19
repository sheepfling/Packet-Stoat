# Alpha 3 Sanitizer Smoke Report

- generated_at: `2026-06-19T17:40:37.115524+00:00`
- status: `passed`
- build_dir: `build-alpha3-sanitizers`
- config: `Debug`
- sanitizers: `asan,ubsan`

## Command

```text
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 /Users/rick/Library/Mobile Documents/com~apple~CloudDocs/GIT/fastdis/tools/run_sanitizers.py --build-dir build-alpha3-sanitizers --config Debug --sanitizers asan,ubsan
```

## Summary

- return_code: `0`
- note: Alpha 3 release smoke requires at least one ASAN/UBSAN sanitizer-backed native test pass artifact.

## Output

```text
+ cmake -S /Users/rick/Library/Mobile Documents/com~apple~CloudDocs/GIT/fastdis -B /Users/rick/Library/Mobile Documents/com~apple~CloudDocs/GIT/fastdis/build-alpha3-sanitizers -DCMAKE_BUILD_TYPE=Debug -DFASTDIS_BUILD_SHARED=ON -DFASTDIS_BUILD_TESTS=ON -DFASTDIS_BUILD_EXAMPLES=OFF -DFASTDIS_BUILD_BENCHMARKS=OFF -DFASTDIS_BUILD_FUZZERS=ON -DFASTDIS_ENABLE_ASAN=ON -DFASTDIS_ENABLE_UBSAN=ON -DFASTDIS_ENABLE_TSAN=OFF
-- Configuring done (0.1s)
-- Generating done (0.1s)
-- Build files have been written to: /Users/rick/Library/Mobile Documents/com~apple~CloudDocs/GIT/fastdis/build-alpha3-sanitizers
+ cmake --build /Users/rick/Library/Mobile Documents/com~apple~CloudDocs/GIT/fastdis/build-alpha3-sanitizers --config Debug
[  3%] Built target fastdis_objects
[  6%] Built target fastdis_shared
[ 10%] Building CXX object CMakeFiles/fastdis_capi_tests.dir/tests/native/test_c_api.cpp.o
[ 13%] Linking CXX executable fastdis_capi_tests
[ 13%] Built target fastdis_capi_tests
[ 16%] Building CXX object CMakeFiles/fastdis_cpp_raii_tests.dir/tests/native/test_cpp_raii.cpp.o
[ 20%] Linking CXX executable fastdis_cpp_raii_tests
[ 20%] Built target fastdis_cpp_raii_tests
[ 23%] Building CXX object CMakeFiles/fastdis_cpp_raii_noexcept_tests.dir/tests/native/test_cpp_raii.cpp.o
[ 26%] Linking CXX executable fastdis_cpp_raii_noexcept_tests
[ 26%] Built target fastdis_cpp_raii_noexcept_tests
[ 33%] Built target fastdis_frame_tests
[ 40%] Built target fastdis_orientation_convention_tests
[ 46%] Built target fastdis_fuzz_header
[ 53%] Built target fastdis_fuzz_scan_many
[ 56%] Building CXX object CMakeFiles/fastdis_fuzz_catalog_dispatch.dir/fuzz/fuzz_catalog_dispatch.cpp.o
[ 60%] Linking CXX executable fastdis_fuzz_catalog_dispatch
[ 60%] Built target fastdis_fuzz_catalog_dispatch
[ 66%] Built target fastdis_fuzz_min_lengths
[ 70%] Building CXX object CMakeFiles/fastdis_fuzz_unknown_pdu.dir/fuzz/fuzz_unknown_pdu.cpp.o
[ 73%] Linking CXX executable fastdis_fuzz_unknown_pdu
[ 73%] Built target fastdis_fuzz_unknown_pdu
[ 80%] Built target fastdis_fuzz_entity_transform
[ 86%] Built target fastdis_fuzz_snapshot_buffer
[ 93%] Built target fastdis_fuzz_frame_orientation
[100%] Built target fastdis_fuzz_entity_table_ingest
+ ctest --test-dir /Users/rick/Library/Mobile Documents/com~apple~CloudDocs/GIT/fastdis/build-alpha3-sanitizers --build-config Debug --output-on-failure
Test project /Users/rick/Library/Mobile Documents/com~apple~CloudDocs/GIT/fastdis/build-alpha3-sanitizers
    Start 1: fastdis_capi_tests
1/5 Test #1: fastdis_capi_tests .....................   Passed    0.33 sec
    Start 2: fastdis_cpp_raii_tests
2/5 Test #2: fastdis_cpp_raii_tests .................   Passed    0.21 sec
    Start 3: fastdis_cpp_raii_noexcept_tests
3/5 Test #3: fastdis_cpp_raii_noexcept_tests ........   Passed    0.21 sec
    Start 4: fastdis_frame_tests
4/5 Test #4: fastdis_frame_tests ....................   Passed    0.11 sec
    Start 5: fastdis_orientation_convention_tests
5/5 Test #5: fastdis_orientation_convention_tests ...   Passed    0.10 sec

100% tests passed, 0 tests failed out of 5

Total Test time (real) =   0.97 sec
```
