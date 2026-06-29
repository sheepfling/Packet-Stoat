extends Node

# FastDIS dead reckoning runtime verification scene contract.
# The scene uses tests/data/dead_reckoning_engine_cases.json and must compare
# Godot Node3D results against transforms produced by the shared native
# fastdis_extrapolate_entity_transform_dead_reckoning evaluator.

const REPORT_SCHEMA := "fastdis.godot.dead_reckoning_runtime.v1"
const FIXTURE_CANDIDATES := [
    "res://tests/dead_reckoning_engine_cases.json",
    "res://../../../tests/data/dead_reckoning_engine_cases.json",
]


func _ready() -> void:
    print("FastDIS dead reckoning runtime scene contract loaded: %s" % REPORT_SCHEMA)
