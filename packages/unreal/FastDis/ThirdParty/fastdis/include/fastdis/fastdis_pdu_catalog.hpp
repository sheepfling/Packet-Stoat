/* Generated wrapper for the source-level PDU catalog. */
#ifndef FASTDIS_PDU_CATALOG_HPP
#define FASTDIS_PDU_CATALOG_HPP

#include <fastdis/fastdis_pdu_catalog.h>

#include <cstddef>
#include <cstdint>

namespace fastdis {

using PduCatalogEntry = fastdis_pdu_catalog_entry_t;

inline constexpr std::size_t pdu_catalog_count = FASTDIS_PDU_CATALOG_COUNT;

inline const PduCatalogEntry* pdu_catalog() noexcept {
    return FASTDIS_PDU_CATALOG;
}

inline const PduCatalogEntry* find_pdu(std::uint8_t protocol_version, std::uint8_t pdu_type) noexcept {
    return fastdis_pdu_catalog_find(protocol_version, pdu_type);
}

inline bool has_body_decoder(std::uint8_t protocol_version, std::uint8_t pdu_type) noexcept {
    const PduCatalogEntry* entry = find_pdu(protocol_version, pdu_type);
    return entry != nullptr && entry->has_body_decoder != 0u;
}

} // namespace fastdis

#endif /* FASTDIS_PDU_CATALOG_HPP */
