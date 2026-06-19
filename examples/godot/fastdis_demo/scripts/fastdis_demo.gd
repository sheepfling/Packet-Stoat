extends Node3D

const ENTITY_BINDINGS := [
	{"id": Vector3i(100, 1, 0), "path": NodePath("EntityA")},
	{"id": Vector3i(100, 1, 1), "path": NodePath("EntityB")},
	{"id": Vector3i(100, 1, 2), "path": NodePath("EntityC")},
]

@onready var status_label: Label3D = $StatusLabel
@onready var replay_loader: Node = $ReplayLoader

var fastdis_world: Node = null

func _ready() -> void:
	if not ClassDB.class_exists("FastDisWorld"):
		_show_status("FastDisWorld extension not loaded. Build examples/godot/fastdis_gdextension and copy the wrapper plus libfastdis into addons/fastdis/bin/.")
		push_error(status_label.text)
		return

	fastdis_world = ClassDB.instantiate("FastDisWorld")
	if fastdis_world == null:
		_show_status("FastDisWorld is registered but could not be instantiated.")
		push_error(status_label.text)
		return
	fastdis_world.name = "FastDisWorld"
	add_child(fastdis_world)
	fastdis_world.set_georeference(29.5597, -95.0831, 0.0)
	fastdis_world.apply_orientation = false
	fastdis_world.transform_mode = 0
	fastdis_world.snapshot_slots = 3
	fastdis_world.stale_after_ticks = 120
	fastdis_world.auto_apply = true

	for binding in ENTITY_BINDINGS:
		fastdis_world.register_entity(binding.id.x, binding.id.y, binding.id.z, binding.path)

	replay_loader.bind_world(fastdis_world)
	if replay_loader.load_replay():
		_show_status("Replay loaded. Registered %d entities." % ENTITY_BINDINGS.size())
	else:
		var error_text := fastdis_world.get_last_error()
		if error_text.is_empty():
			error_text = "Replay file missing at res://data/synthetic.fastdispkt"
		_show_status(error_text)

func _process(_delta: float) -> void:
	if fastdis_world == null:
		return
	var consumed := replay_loader.step_replay()
	if consumed > 0:
		_show_status("Replay stepping: packets=%d known_entities=%d" % [fastdis_world.get_loaded_replay_packet_count(), fastdis_world.get_known_entity_count()])
	elif not fastdis_world.get_last_error().is_empty():
		_show_status(fastdis_world.get_last_error())

func _show_status(text: String) -> void:
	status_label.text = text
	print(text)
