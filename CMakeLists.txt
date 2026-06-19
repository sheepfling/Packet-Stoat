cmake_minimum_required(VERSION 3.16)

project(fastdis
    VERSION 0.13.0
    DESCRIPTION "Fast DIS packet scanning with a stable C ABI and C++ RAII wrappers"
    LANGUAGES C CXX)

include(GNUInstallDirs)

option(FASTDIS_BUILD_SHARED "Build the fastdis shared library" ON)
option(FASTDIS_BUILD_STATIC "Build the fastdis static library" OFF)
option(FASTDIS_BUILD_TESTS "Build native C ABI tests" ON)
option(FASTDIS_BUILD_EXAMPLES "Build native examples" ON)
option(FASTDIS_BUILD_BENCHMARKS "Build native benchmarks" ON)
option(FASTDIS_BUILD_FUZZERS "Build native fuzz harnesses" OFF)
option(FASTDIS_ENABLE_ASAN "Enable AddressSanitizer" OFF)
option(FASTDIS_ENABLE_UBSAN "Enable UndefinedBehaviorSanitizer" OFF)
option(FASTDIS_ENABLE_TSAN "Enable ThreadSanitizer" OFF)

if(FASTDIS_ENABLE_TSAN AND (FASTDIS_ENABLE_ASAN OR FASTDIS_ENABLE_UBSAN))
    message(FATAL_ERROR "FASTDIS_ENABLE_TSAN cannot be combined with ASAN or UBSAN")
endif()

function(fastdis_apply_sanitizers target_name)
    if(MSVC)
        return()
    endif()
    if(FASTDIS_ENABLE_ASAN)
        target_compile_options(${target_name} PRIVATE -fsanitize=address)
        target_link_options(${target_name} PRIVATE -fsanitize=address)
    endif()
    if(FASTDIS_ENABLE_UBSAN)
        target_compile_options(${target_name} PRIVATE -fsanitize=undefined)
        target_link_options(${target_name} PRIVATE -fsanitize=undefined)
    endif()
    if(FASTDIS_ENABLE_TSAN)
        target_compile_options(${target_name} PRIVATE -fsanitize=thread)
        target_link_options(${target_name} PRIVATE -fsanitize=thread)
    endif()
endfunction()

set(FASTDIS_PUBLIC_HEADERS
    ${CMAKE_CURRENT_SOURCE_DIR}/include/fastdis/fastdis.h
    ${CMAKE_CURRENT_SOURCE_DIR}/include/fastdis/fastdis.hpp
    ${CMAKE_CURRENT_SOURCE_DIR}/include/fastdis/fastdis_frames.hpp
    ${CMAKE_CURRENT_SOURCE_DIR}/include/fastdis/fastdis_orientation.hpp
    ${CMAKE_CURRENT_SOURCE_DIR}/include/fastdis/fastdis_pdu_catalog.h
    ${CMAKE_CURRENT_SOURCE_DIR}/include/fastdis/fastdis_pdu_catalog.hpp)
set(FASTDIS_NATIVE_SOURCES
    ${CMAKE_CURRENT_SOURCE_DIR}/src/native/fastdis_core.cpp)

add_library(fastdis_objects OBJECT ${FASTDIS_NATIVE_SOURCES} ${FASTDIS_PUBLIC_HEADERS})
target_include_directories(fastdis_objects PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>)
target_compile_features(fastdis_objects PUBLIC cxx_std_17)
target_compile_definitions(fastdis_objects PRIVATE FASTDIS_EXPORTS)
set_target_properties(fastdis_objects PROPERTIES POSITION_INDEPENDENT_CODE ON)
fastdis_apply_sanitizers(fastdis_objects)

if(MSVC)
    target_compile_options(fastdis_objects PRIVATE /W4 /permissive-)
else()
    target_compile_options(fastdis_objects PRIVATE -Wall -Wextra -Wpedantic)
    set_target_properties(fastdis_objects PROPERTIES
        CXX_VISIBILITY_PRESET hidden
        VISIBILITY_INLINES_HIDDEN YES)
endif()

if(FASTDIS_BUILD_SHARED)
    add_library(fastdis_shared SHARED $<TARGET_OBJECTS:fastdis_objects>)
    add_library(fastdis::shared ALIAS fastdis_shared)
    target_include_directories(fastdis_shared PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>)
    set_target_properties(fastdis_shared PROPERTIES
        OUTPUT_NAME fastdis
        VERSION ${PROJECT_VERSION}
        SOVERSION 0)
    fastdis_apply_sanitizers(fastdis_shared)
endif()

if(FASTDIS_BUILD_STATIC)
    add_library(fastdis_static STATIC $<TARGET_OBJECTS:fastdis_objects>)
    add_library(fastdis::static ALIAS fastdis_static)
    target_include_directories(fastdis_static PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>)
    set_target_properties(fastdis_static PROPERTIES OUTPUT_NAME fastdis_static)
    fastdis_apply_sanitizers(fastdis_static)
endif()

if(FASTDIS_BUILD_TESTS)
    enable_testing()
    add_executable(fastdis_capi_tests tests/native/test_c_api.cpp)
    target_include_directories(fastdis_capi_tests PRIVATE include)
    target_compile_features(fastdis_capi_tests PRIVATE cxx_std_17)
    if(FASTDIS_BUILD_SHARED)
        target_link_libraries(fastdis_capi_tests PRIVATE fastdis_shared)
    elseif(FASTDIS_BUILD_STATIC)
        target_link_libraries(fastdis_capi_tests PRIVATE fastdis_static)
    else()
        target_link_libraries(fastdis_capi_tests PRIVATE fastdis_objects)
    endif()
    set_target_properties(fastdis_capi_tests PROPERTIES
        BUILD_RPATH "$ORIGIN"
        INSTALL_RPATH "$ORIGIN")
    fastdis_apply_sanitizers(fastdis_capi_tests)
    add_test(NAME fastdis_capi_tests COMMAND fastdis_capi_tests)

    add_executable(fastdis_cpp_raii_tests tests/native/test_cpp_raii.cpp)
    target_include_directories(fastdis_cpp_raii_tests PRIVATE include)
    target_compile_features(fastdis_cpp_raii_tests PRIVATE cxx_std_17)
    if(FASTDIS_BUILD_SHARED)
        target_link_libraries(fastdis_cpp_raii_tests PRIVATE fastdis_shared)
    elseif(FASTDIS_BUILD_STATIC)
        target_link_libraries(fastdis_cpp_raii_tests PRIVATE fastdis_static)
    else()
        target_link_libraries(fastdis_cpp_raii_tests PRIVATE fastdis_objects)
    endif()
    set_target_properties(fastdis_cpp_raii_tests PROPERTIES
        BUILD_RPATH "$ORIGIN"
        INSTALL_RPATH "$ORIGIN")
    fastdis_apply_sanitizers(fastdis_cpp_raii_tests)
    add_test(NAME fastdis_cpp_raii_tests COMMAND fastdis_cpp_raii_tests)

    add_executable(fastdis_cpp_raii_noexcept_tests tests/native/test_cpp_raii.cpp)
    target_include_directories(fastdis_cpp_raii_noexcept_tests PRIVATE include)
    target_compile_features(fastdis_cpp_raii_noexcept_tests PRIVATE cxx_std_17)
    target_compile_definitions(fastdis_cpp_raii_noexcept_tests PRIVATE FASTDIS_CPP_NO_EXCEPTIONS)
    if(NOT MSVC)
        target_compile_options(fastdis_cpp_raii_noexcept_tests PRIVATE -fno-exceptions)
    endif()
    if(FASTDIS_BUILD_SHARED)
        target_link_libraries(fastdis_cpp_raii_noexcept_tests PRIVATE fastdis_shared)
    elseif(FASTDIS_BUILD_STATIC)
        target_link_libraries(fastdis_cpp_raii_noexcept_tests PRIVATE fastdis_static)
    else()
        target_link_libraries(fastdis_cpp_raii_noexcept_tests PRIVATE fastdis_objects)
    endif()
    set_target_properties(fastdis_cpp_raii_noexcept_tests PROPERTIES
        BUILD_RPATH "$ORIGIN"
        INSTALL_RPATH "$ORIGIN")
    fastdis_apply_sanitizers(fastdis_cpp_raii_noexcept_tests)
    add_test(NAME fastdis_cpp_raii_noexcept_tests COMMAND fastdis_cpp_raii_noexcept_tests)

    add_executable(fastdis_frame_tests tests/native/test_frames.cpp)
    target_include_directories(fastdis_frame_tests PRIVATE include)
    target_compile_features(fastdis_frame_tests PRIVATE cxx_std_17)
    if(FASTDIS_BUILD_SHARED)
        target_link_libraries(fastdis_frame_tests PRIVATE fastdis_shared)
    elseif(FASTDIS_BUILD_STATIC)
        target_link_libraries(fastdis_frame_tests PRIVATE fastdis_static)
    else()
        target_link_libraries(fastdis_frame_tests PRIVATE fastdis_objects)
    endif()
    set_target_properties(fastdis_frame_tests PROPERTIES
        BUILD_RPATH "$ORIGIN"
        INSTALL_RPATH "$ORIGIN")
    fastdis_apply_sanitizers(fastdis_frame_tests)
    add_test(NAME fastdis_frame_tests COMMAND fastdis_frame_tests)

    add_executable(fastdis_orientation_convention_tests tests/native/test_orientation_conventions.cpp)
    target_include_directories(fastdis_orientation_convention_tests PRIVATE include)
    target_compile_features(fastdis_orientation_convention_tests PRIVATE cxx_std_17)
    if(FASTDIS_BUILD_SHARED)
        target_link_libraries(fastdis_orientation_convention_tests PRIVATE fastdis_shared)
    elseif(FASTDIS_BUILD_STATIC)
        target_link_libraries(fastdis_orientation_convention_tests PRIVATE fastdis_static)
    else()
        target_link_libraries(fastdis_orientation_convention_tests PRIVATE fastdis_objects)
    endif()
    set_target_properties(fastdis_orientation_convention_tests PROPERTIES
        BUILD_RPATH "$ORIGIN"
        INSTALL_RPATH "$ORIGIN")
    fastdis_apply_sanitizers(fastdis_orientation_convention_tests)
    add_test(NAME fastdis_orientation_convention_tests COMMAND fastdis_orientation_convention_tests)
endif()

if(FASTDIS_BUILD_EXAMPLES)
    add_executable(fastdis_scan_file_c examples/c/scan_file.c)
    target_include_directories(fastdis_scan_file_c PRIVATE include)
    if(FASTDIS_BUILD_SHARED)
        target_link_libraries(fastdis_scan_file_c PRIVATE fastdis_shared)
    elseif(FASTDIS_BUILD_STATIC)
        target_link_libraries(fastdis_scan_file_c PRIVATE fastdis_static)
    else()
        target_link_libraries(fastdis_scan_file_c PRIVATE fastdis_objects)
    endif()
    set_target_properties(fastdis_scan_file_c PROPERTIES BUILD_RPATH "$ORIGIN")
    fastdis_apply_sanitizers(fastdis_scan_file_c)


    add_executable(fastdis_entity_state_scan_c examples/c/entity_state_scan.c)
    target_include_directories(fastdis_entity_state_scan_c PRIVATE include)
    if(FASTDIS_BUILD_SHARED)
        target_link_libraries(fastdis_entity_state_scan_c PRIVATE fastdis_shared)
    elseif(FASTDIS_BUILD_STATIC)
        target_link_libraries(fastdis_entity_state_scan_c PRIVATE fastdis_static)
    else()
        target_link_libraries(fastdis_entity_state_scan_c PRIVATE fastdis_objects)
    endif()
    set_target_properties(fastdis_entity_state_scan_c PROPERTIES BUILD_RPATH "$ORIGIN")
    fastdis_apply_sanitizers(fastdis_entity_state_scan_c)

    add_executable(fastdis_transform_batch_c examples/c/transform_batch.c)
    target_include_directories(fastdis_transform_batch_c PRIVATE include)
    if(FASTDIS_BUILD_SHARED)
        target_link_libraries(fastdis_transform_batch_c PRIVATE fastdis_shared)
    elseif(FASTDIS_BUILD_STATIC)
        target_link_libraries(fastdis_transform_batch_c PRIVATE fastdis_static)
    else()
        target_link_libraries(fastdis_transform_batch_c PRIVATE fastdis_objects)
    endif()
    set_target_properties(fastdis_transform_batch_c PROPERTIES BUILD_RPATH "$ORIGIN")
    fastdis_apply_sanitizers(fastdis_transform_batch_c)

    add_executable(fastdis_entity_table_c examples/c/entity_table.c)
    target_include_directories(fastdis_entity_table_c PRIVATE include)
    if(FASTDIS_BUILD_SHARED)
        target_link_libraries(fastdis_entity_table_c PRIVATE fastdis_shared)
    elseif(FASTDIS_BUILD_STATIC)
        target_link_libraries(fastdis_entity_table_c PRIVATE fastdis_static)
    else()
        target_link_libraries(fastdis_entity_table_c PRIVATE fastdis_objects)
    endif()
    set_target_properties(fastdis_entity_table_c PROPERTIES BUILD_RPATH "$ORIGIN")
    fastdis_apply_sanitizers(fastdis_entity_table_c)

    add_executable(fastdis_snapshot_buffer_c examples/c/snapshot_buffer.c)
    target_include_directories(fastdis_snapshot_buffer_c PRIVATE include)
    if(FASTDIS_BUILD_SHARED)
        target_link_libraries(fastdis_snapshot_buffer_c PRIVATE fastdis_shared)
    elseif(FASTDIS_BUILD_STATIC)
        target_link_libraries(fastdis_snapshot_buffer_c PRIVATE fastdis_static)
    else()
        target_link_libraries(fastdis_snapshot_buffer_c PRIVATE fastdis_objects)
    endif()
    set_target_properties(fastdis_snapshot_buffer_c PROPERTIES BUILD_RPATH "$ORIGIN")
    fastdis_apply_sanitizers(fastdis_snapshot_buffer_c)

    add_executable(fastdis_scan_file_cpp examples/cpp/scan_file.cpp)
    target_include_directories(fastdis_scan_file_cpp PRIVATE include)
    target_compile_features(fastdis_scan_file_cpp PRIVATE cxx_std_17)
    if(FASTDIS_BUILD_SHARED)
        target_link_libraries(fastdis_scan_file_cpp PRIVATE fastdis_shared)
    elseif(FASTDIS_BUILD_STATIC)
        target_link_libraries(fastdis_scan_file_cpp PRIVATE fastdis_static)
    else()
        target_link_libraries(fastdis_scan_file_cpp PRIVATE fastdis_objects)
    endif()
    set_target_properties(fastdis_scan_file_cpp PROPERTIES BUILD_RPATH "$ORIGIN")
    fastdis_apply_sanitizers(fastdis_scan_file_cpp)

    add_executable(fastdis_raii_snapshot_buffer_cpp examples/cpp/raii_snapshot_buffer.cpp)
    target_include_directories(fastdis_raii_snapshot_buffer_cpp PRIVATE include)
    target_compile_features(fastdis_raii_snapshot_buffer_cpp PRIVATE cxx_std_17)
    if(FASTDIS_BUILD_SHARED)
        target_link_libraries(fastdis_raii_snapshot_buffer_cpp PRIVATE fastdis_shared)
    elseif(FASTDIS_BUILD_STATIC)
        target_link_libraries(fastdis_raii_snapshot_buffer_cpp PRIVATE fastdis_static)
    else()
        target_link_libraries(fastdis_raii_snapshot_buffer_cpp PRIVATE fastdis_objects)
    endif()
    set_target_properties(fastdis_raii_snapshot_buffer_cpp PROPERTIES BUILD_RPATH "$ORIGIN")
    fastdis_apply_sanitizers(fastdis_raii_snapshot_buffer_cpp)

    add_executable(fastdis_udp_burst_cpp examples/cpp/udp_burst.cpp)
    target_include_directories(fastdis_udp_burst_cpp PRIVATE include)
    target_compile_features(fastdis_udp_burst_cpp PRIVATE cxx_std_17)
    if(FASTDIS_BUILD_SHARED)
        target_link_libraries(fastdis_udp_burst_cpp PRIVATE fastdis_shared)
    elseif(FASTDIS_BUILD_STATIC)
        target_link_libraries(fastdis_udp_burst_cpp PRIVATE fastdis_static)
    else()
        target_link_libraries(fastdis_udp_burst_cpp PRIVATE fastdis_objects)
    endif()
    set_target_properties(fastdis_udp_burst_cpp PROPERTIES BUILD_RPATH "$ORIGIN")
    fastdis_apply_sanitizers(fastdis_udp_burst_cpp)
endif()

if(FASTDIS_BUILD_BENCHMARKS)
    add_executable(fastdis_native_bench benchmarks/native_bench.cpp)
    target_include_directories(fastdis_native_bench PRIVATE include)
    target_compile_features(fastdis_native_bench PRIVATE cxx_std_17)
    if(FASTDIS_BUILD_SHARED)
        target_link_libraries(fastdis_native_bench PRIVATE fastdis_shared)
    elseif(FASTDIS_BUILD_STATIC)
        target_link_libraries(fastdis_native_bench PRIVATE fastdis_static)
    else()
        target_link_libraries(fastdis_native_bench PRIVATE fastdis_objects)
    endif()
    set_target_properties(fastdis_native_bench PROPERTIES
        BUILD_RPATH "$ORIGIN"
        INSTALL_RPATH "$ORIGIN")
    fastdis_apply_sanitizers(fastdis_native_bench)
endif()

if(FASTDIS_BUILD_FUZZERS)
    foreach(fuzz_name
            fastdis_fuzz_header
            fastdis_fuzz_scan_many
            fastdis_fuzz_catalog_dispatch
            fastdis_fuzz_min_lengths
            fastdis_fuzz_unknown_pdu
            fastdis_fuzz_entity_transform
            fastdis_fuzz_snapshot_buffer
            fastdis_fuzz_frame_orientation
            fastdis_fuzz_entity_table_ingest)
        if(fuzz_name STREQUAL "fastdis_fuzz_header")
            set(fuzz_source fuzz/fuzz_header.cpp)
        elseif(fuzz_name STREQUAL "fastdis_fuzz_scan_many")
            set(fuzz_source fuzz/fuzz_scan_many.cpp)
        elseif(fuzz_name STREQUAL "fastdis_fuzz_catalog_dispatch")
            set(fuzz_source fuzz/fuzz_catalog_dispatch.cpp)
        elseif(fuzz_name STREQUAL "fastdis_fuzz_min_lengths")
            set(fuzz_source fuzz/fuzz_min_lengths.cpp)
        elseif(fuzz_name STREQUAL "fastdis_fuzz_unknown_pdu")
            set(fuzz_source fuzz/fuzz_unknown_pdu.cpp)
        elseif(fuzz_name STREQUAL "fastdis_fuzz_entity_transform")
            set(fuzz_source fuzz/fuzz_entity_transform.cpp)
        elseif(fuzz_name STREQUAL "fastdis_fuzz_snapshot_buffer")
            set(fuzz_source fuzz/fuzz_snapshot_buffer.cpp)
        elseif(fuzz_name STREQUAL "fastdis_fuzz_frame_orientation")
            set(fuzz_source fuzz/fuzz_frame_orientation.cpp)
        else()
            set(fuzz_source fuzz/fuzz_entity_table_ingest.cpp)
        endif()

        add_executable(${fuzz_name} ${fuzz_source})
        target_include_directories(${fuzz_name} PRIVATE include)
        target_compile_features(${fuzz_name} PRIVATE cxx_std_17)
        if(FASTDIS_BUILD_SHARED)
            target_link_libraries(${fuzz_name} PRIVATE fastdis_shared)
        elseif(FASTDIS_BUILD_STATIC)
            target_link_libraries(${fuzz_name} PRIVATE fastdis_static)
        else()
            target_link_libraries(${fuzz_name} PRIVATE fastdis_objects)
        endif()
        set_target_properties(${fuzz_name} PROPERTIES BUILD_RPATH "$ORIGIN")
        fastdis_apply_sanitizers(${fuzz_name})
    endforeach()
endif()


install(FILES ${FASTDIS_PUBLIC_HEADERS}
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/fastdis)

if(FASTDIS_BUILD_SHARED)
    install(TARGETS fastdis_shared
        EXPORT fastdisTargets
        RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
        LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
        ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR})
endif()

if(FASTDIS_BUILD_STATIC)
    install(TARGETS fastdis_static
        EXPORT fastdisTargets
        RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
        LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
        ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR})
endif()

install(EXPORT fastdisTargets
    NAMESPACE fastdis::
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/fastdis)
