#include "fastdis/fastdis.h"

#include <cstddef>
#include <cstdint>

extern "C" int LLVMFuzzerTestOneInput(const std::uint8_t* data, std::size_t size) {
    if (data == nullptr) {
        return 0;
    }
    fastdis_header_t header{};
    (void)fastdis_parse_header(data, size, 0, &header);
    (void)fastdis_parse_header(data, size, FASTDIS_FLAG_ALLOW_TRUNCATED, &header);
    return 0;
}

#include "fuzz_standalone.hpp"
