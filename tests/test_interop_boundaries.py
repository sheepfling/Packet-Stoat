from __future__ import annotations

from fastdis.interop import CanonicalEntity, CanonicalEntityId, canonical_entity_to_dict


def test_canonical_entity_lives_in_vendor_neutral_interop() -> None:
    entity = CanonicalEntity(entity_id=CanonicalEntityId(site=1, application=2, entity=3))

    assert entity.key == "1:2:3"
    assert canonical_entity_to_dict(entity)["entity_id"] == {"site": 1, "application": 2, "entity": 3}


def test_lattice_module_keeps_compatibility_imports() -> None:
    from fastdis.lattice import CanonicalEntity as LatticeCanonicalEntity

    assert LatticeCanonicalEntity is CanonicalEntity
