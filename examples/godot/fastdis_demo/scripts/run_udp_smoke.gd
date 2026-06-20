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
		push_error("FastDisWorld extension is not loaded. Build examples/godot/fastdis_gdextension and install the wrapper plus libfastdis before running the UDP smoke test.")
		failures += 1
		quit(failures)
		return

	var port := int(OS.get_environment("FASTDIS_GODOT_UDP_PORT"))
	var expected_packets := int(OS.get_environment("FASTDIS_GODOT_EXPECTED_PACKETS"))
	var expected_entities := int(OS.get_environment("FASTDIS_GODOT_EXPECTED_ENTITIES"))
	if port <= 0:
		push_error("FASTDIS_GODOT_UDP_PORT is required.")
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

	var entity_names: Array[String] = ["EntityA", "EntityB", "EntityC"]
	var initial_positions: Dictionary = {}
	for index: int in range(entity_names.size()):
		var marker := Node3D.new()
		marker.name = entity_names[index]
		root.add_child(marker)
		initial_positions[entity_names[index]] = marker.global_position
		world.call("register_entity", 100, 1, index, marker.get_path())

	var peer := PacketPeerUDP.new()
	var bind_error: int = peer.bind(port, "127.0.0.1")
	if bind_error != OK:
		push_error("Could not bind PacketPeerUDP on 127.0.0.1:%d (error %d)" % [port, bind_error])
		failures += 1
		quit(failures)
		return

	var packets_received := 0
	var guard_frames := 0
	while packets_received < expected_packets and guard_frames < 600:
		while peer.get_available_packet_count() > 0:
			var packet: PackedByteArray = peer.get_packet()
			if packet.is_empty():
				continue
			var rc: int = int(world.call("ingest_packet", packet, true))
			if rc != 0:
				push_error("FastDisWorld.ingest_packet failed with status %d" % rc)
				failures += 1
				break
			packets_received += 1
		world.call("apply_latest_snapshots")
		await process_frame
		guard_frames += 1

	if packets_received != expected_packets:
		push_error("Expected %d packets, received %d" % [expected_packets, packets_received])
		failures += 1

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

	var report := {
		"schema": "fastdis.godot_udp_smoke_report.v1",
		"surface": "godot",
		"mode": "live_udp",
		"packets_received": packets_received,
		"known_entities": known_entities,
		"moved_entity_count": moved_entities.size(),
		"moved_entities": moved_entities,
		"errors": failures
	}
	print(JSON.stringify(report))

	if failures == 0:
		print("FastDIS Godot UDP smoke passed")
	else:
		push_error("FastDIS Godot UDP smoke failed: %d checks" % failures)
	quit(failures)
