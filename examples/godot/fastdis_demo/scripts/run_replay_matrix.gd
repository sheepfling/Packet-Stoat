extends SceneTree

var failures: int = 0

func _init() -> void:
	call_deferred("_run")

func _run() -> void:
	var extension_resource: Resource = load("res://addons/fastdis/fastdis.gdextension")
	if extension_resource == null:
		push_error("Could not load res://addons/fastdis/fastdis.gdextension")
		failures += 1
		quit(failures)
		return

	if not ClassDB.class_exists("FastDisWorld"):
		push_error("FastDisWorld extension is not loaded. Build examples/godot/fastdis_gdextension and install the wrapper plus libfastdis before running the replay matrix smoke test.")
		failures += 1
		quit(failures)
		return

	var replay_path := OS.get_environment("FASTDIS_GODOT_REPLAY_PATH")
	var expected_packets := int(OS.get_environment("FASTDIS_GODOT_EXPECTED_PACKETS"))
	var expected_entities := int(OS.get_environment("FASTDIS_GODOT_EXPECTED_ENTITIES"))
	var packet_budget := int(OS.get_environment("FASTDIS_GODOT_REPLAY_PACKET_BUDGET"))
	if packet_budget <= 0:
		packet_budget = 128
	if replay_path.is_empty():
		push_error("FASTDIS_GODOT_REPLAY_PATH is required.")
		failures += 1
		quit(failures)
		return
	if expected_packets <= 0 or expected_entities <= 0:
		push_error("FASTDIS_GODOT_EXPECTED_PACKETS and FASTDIS_GODOT_EXPECTED_ENTITIES are required.")
		failures += 1
		quit(failures)
		return

	var world: Node = ClassDB.instantiate("FastDisWorld")
	if world == null:
		push_error("Could not instantiate FastDisWorld")
		failures += 1
		quit(failures)
		return
	root.add_child(world)
	world.call("set_auto_apply", false)
	world.call("set_apply_orientation", false)
	world.call("set_georeference", 29.5597, -95.0831, 0.0)

	var entity_names: Array[String] = []
	var initial_positions: Dictionary = {}
	for index: int in range(expected_entities):
		var marker := Node3D.new()
		marker.name = "ReplayEntity%d" % index
		root.add_child(marker)
		entity_names.append(marker.name)
		initial_positions[marker.name] = marker.global_position
		world.call("register_entity", 100, 1, index, marker.get_path())

	if not world.call("load_replay_file", replay_path):
		push_error("FastDisWorld.load_replay_file failed for %s" % replay_path)
		failures += 1
		quit(failures)
		return

	var loaded_packets: int = int(world.call("get_loaded_replay_packet_count"))
	if loaded_packets != expected_packets:
		push_error("Expected replay to load %d packets, got %d" % [expected_packets, loaded_packets])
		failures += 1

	var replay_steps := int(ceili(float(expected_packets) / float(packet_budget)))
	for _step: int in range(replay_steps):
		var rc: int = int(world.call("ingest_replay_frame", packet_budget, true))
		if rc != 0:
			push_error("FastDisWorld.ingest_replay_frame failed with status %d" % rc)
			failures += 1
			break
		world.call("apply_latest_snapshots")
		await process_frame

	var known_entities: int = int(world.call("get_known_entity_count"))
	if known_entities < expected_entities:
		push_error("Expected at least %d known entities, got %d" % [expected_entities, known_entities])
		failures += 1

	var moved_entities: Array = []
	for name: String in entity_names:
		var marker: Node3D = root.get_node_or_null(name)
		if marker == null:
			continue
		var start_position: Vector3 = initial_positions[name]
		var distance: float = marker.global_position.distance_to(start_position)
		if distance > 0.001:
			moved_entities.append({
				"name": name,
				"distance": distance,
				"position": [marker.global_position.x, marker.global_position.y, marker.global_position.z]
			})

	if moved_entities.size() < expected_entities:
		push_error("Expected at least %d moved entities, got %d" % [expected_entities, moved_entities.size()])
		failures += 1

	var report := {
		"schema": "fastdis.godot_replay_smoke_report.v1",
		"surface": "godot",
		"mode": "replay",
		"loaded_packets": loaded_packets,
		"replay_steps": replay_steps,
		"known_entities": known_entities,
		"moved_entity_count": moved_entities.size(),
		"moved_entities": moved_entities,
		"errors": failures
	}
	print(JSON.stringify(report))

	if failures == 0:
		print("FastDIS Godot replay matrix smoke passed")
	else:
		push_error("FastDIS Godot replay matrix smoke failed: %d checks" % failures)
	quit(failures)
