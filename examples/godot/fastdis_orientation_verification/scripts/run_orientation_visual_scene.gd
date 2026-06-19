extends SceneTree

var failures: int = 0

func _init() -> void:
    call_deferred("_run")

func _run() -> void:
    var fixture: Dictionary = _load_fixture()
    if fixture.is_empty():
        failures += 1
        quit(failures)
        return

    var extension_resource: Resource = load("res://addons/fastdis/fastdis.gdextension")
    if extension_resource == null:
        push_error("Could not load res://addons/fastdis/fastdis.gdextension")
        failures += 1
        quit(failures)
        return

    if not ClassDB.class_exists("FastDisWorld"):
        push_error("FastDisWorld extension is not loaded. Build examples/godot/fastdis_gdextension and install the wrapper plus libfastdis before running visual orientation verification.")
        failures += 1
        quit(failures)
        return

    var scene_resource: PackedScene = load("res://scenes/orientation_verification.tscn")
    if scene_resource == null:
        push_error("Could not load res://scenes/orientation_verification.tscn")
        failures += 1
        quit(failures)
        return

    var cases: Array = fixture["cases"] as Array
    for item: Dictionary in cases:
        var node: Node = scene_resource.instantiate()
        node.set("case_name", str(item["name"]))
        root.add_child(node)
        await process_frame
        await process_frame
        if not node.has_method("scene_summary"):
            failures += 1
            push_error("%s scene is missing scene_summary()" % str(item["name"]))
        else:
            var summary: Dictionary = node.call("scene_summary")
            if summary.is_empty() or not bool(summary.get("passed", false)):
                failures += 1
                push_error("%s visual scene reported failure" % str(item["name"]))
        root.remove_child(node)
        node.queue_free()
        await process_frame

    if failures == 0:
        print("FastDIS Godot orientation visual scene verification passed")
    else:
        push_error("FastDIS Godot orientation visual scene verification failed: %d case checks" % failures)
    quit(failures)

func _load_fixture() -> Dictionary:
    var candidates: Array[String] = [
        "res://tests/orientation_engine_cases.json",
        "res://../../../tests/data/orientation_engine_cases.json",
    ]
    for candidate: String in candidates:
        var path: String = ProjectSettings.globalize_path(candidate)
        if FileAccess.file_exists(path):
            var text: String = FileAccess.get_file_as_string(path)
            var parsed: Variant = JSON.parse_string(text)
            if typeof(parsed) == TYPE_DICTIONARY:
                return parsed as Dictionary
            push_error("Could not parse fixture JSON: %s" % path)
            return {}
    push_error("Could not find orientation_engine_cases.json")
    return {}
