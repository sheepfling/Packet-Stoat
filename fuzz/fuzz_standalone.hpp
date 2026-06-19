#pragma once

#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <vector>

extern "C" int LLVMFuzzerTestOneInput(const std::uint8_t* data, std::size_t size);

#if !defined(FASTDIS_LIBFUZZER)
int main(int argc, char** argv) {
    std::vector<std::uint8_t> bytes;
    if (argc > 1) {
        std::ifstream in(argv[1], std::ios::binary);
        if (!in) {
            std::cerr << "could not open " << argv[1] << '\n';
            return 2;
        }
        bytes.assign(std::istreambuf_iterator<char>(in), std::istreambuf_iterator<char>());
    } else {
        bytes.assign(std::istreambuf_iterator<char>(std::cin), std::istreambuf_iterator<char>());
    }

    if (bytes.empty()) {
        return 0;
    }
    return LLVMFuzzerTestOneInput(bytes.data(), bytes.size());
}
#endif
