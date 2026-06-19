extends SceneTree

var failures: int = 0

func _init() -> void:
	call_deferred("_run")

func _run() -> void:
	var extension_resource: Resource = load("res://addons/fastdis/fastdis.gdextension")
	if extension_resource == null:
		print("PASS FastDIS GDExtension manifest failed to load while the host native library was hidden.")

	var packed_scene: PackedScene = load("res://scenes/fastdis_demo.tscn")
	if packed_scene == null:
		push_error("Could not load res://scenes/fastdis_demo.tscn")
		failures += 1
		quit(failures)
		return

	var scene: Node = packed_scene.instantiate()
	root.add_child(scene)
	await process_frame

	if ClassDB.class_exists("FastDisWorld"):
		push_error("FastDisWorld unexpectedly loaded while the host native library was hidden.")
		failures += 1

	var status_label: Label3D = scene.get_node_or_null("StatusLabel")
	if status_label == null:
		push_error("Demo scene is missing StatusLabel")
		failures += 1
	elif "extension not loaded" not in status_label.text.to_lower():
		push_error("Demo scene did not surface a clear extension-missing message: %s" % status_label.text)
		failures += 1
	else:
		print("PASS missing native library status: %s" % status_label.text)

	if failures == 0:
		print("FastDIS Godot missing-library check passed")
	else:
		push_error("FastDIS Godot missing-library check failed: %d checks" % failures)
	quit(failures)
