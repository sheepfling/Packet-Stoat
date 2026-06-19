extends Node

@export var replay_path := "res://data/synthetic.fastdispkt"
@export var packets_per_frame := 64

var world: Node = null

func bind_world(bound_world: Node) -> void:
	world = bound_world

func load_replay() -> bool:
	if world == null:
		push_error("FastDIS replay loader has no FastDisWorld binding.")
		return false
	if not FileAccess.file_exists(replay_path):
		push_warning("FastDIS replay file is missing: %s" % replay_path)
		return false
	return world.load_replay_file(replay_path)

func step_replay() -> int:
	if world == null:
		return 0
	return world.ingest_replay_frame(packets_per_frame, true)
