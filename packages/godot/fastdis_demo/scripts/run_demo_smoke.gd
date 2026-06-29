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
		push_error("FastDisWorld extension is not loaded. Build packages/godot/fastdis_gdextension and install the wrapper plus libfastdis before running the demo smoke test.")
		failures += 1
		quit(failures)
		return

	var replay_path := ProjectSettings.globalize_path("res://data/synthetic.fastdispkt")
	if not FileAccess.file_exists(replay_path):
		push_error("Missing replay fixture at %s" % replay_path)
		failures += 1
		quit(failures)
		return

	var packed_scene: PackedScene = load("res://scenes/fastdis_demo.tscn")
	if packed_scene == null:
		push_error("Could not load res://scenes/fastdis_demo.tscn")
		failures += 1
		quit(failures)
		return

	var scene: Node = packed_scene.instantiate()
	root.add_child(scene)
	await process_frame

	var world: Node = scene.get_node_or_null("FastDisWorld")
	if world == null:
		push_error("Demo scene did not instantiate FastDisWorld")
		failures += 1
		quit(failures)
		return

	var entity_names: Array[String] = ["EntityA", "EntityB", "EntityC"]
	var initial_positions: Dictionary = {}
	for name: String in entity_names:
		var marker: Node3D = scene.get_node_or_null(name)
		if marker == null:
			push_error("Missing demo marker: %s" % name)
			failures += 1
			continue
		initial_positions[name] = marker.global_position

	for _step: int in range(6):
		scene.call("_process", 1.0 / 60.0)
		world.call("apply_latest_snapshots")
		await process_frame

	var known_entities: int = int(world.call("get_known_entity_count"))
	if known_entities < 3:
		push_error("Expected at least 3 known entities, got %d" % known_entities)
		failures += 1

	for name: String in entity_names:
		var marker: Node3D = scene.get_node_or_null(name)
		if marker == null:
			continue
		var start_position: Vector3 = initial_positions[name]
		var distance: float = marker.global_position.distance_to(start_position)
		if distance <= 0.001:
			push_error("%s did not move; distance %.6f" % [name, distance])
			failures += 1
		else:
			print("PASS %s moved %.6f" % [name, distance])

	var status_label: Label3D = scene.get_node_or_null("StatusLabel")
	if status_label == null:
		push_error("Demo scene is missing StatusLabel")
		failures += 1
	elif "Replay stepping:" not in status_label.text:
		push_error("Demo status label did not report replay stepping: %s" % status_label.text)
		failures += 1

	if failures == 0:
		print("FastDIS Godot demo smoke passed")
	else:
		push_error("FastDIS Godot demo smoke failed: %d checks" % failures)
	quit(failures)
