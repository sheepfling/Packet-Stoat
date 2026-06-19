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
        push_error("FastDisWorld extension is not loaded. Build examples/godot/fastdis_gdextension and install the wrapper plus libfastdis before running headless orientation verification.")
        failures += 1
        quit(failures)
        return

    var tolerances: Dictionary = fixture["tolerances"] as Dictionary
    var tolerance: float = float(tolerances["engine_axis_angular_error_deg"])
    var cases: Array = fixture["cases"] as Array
    for item: Dictionary in cases:
        _run_case(item, tolerance)

    if failures == 0:
        print("FastDIS Godot orientation verification passed")
    else:
        push_error("FastDIS Godot orientation verification failed: %d case checks" % failures)
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

func _run_case(item: Dictionary, tolerance_degrees: float) -> void:
    var name: String = str(item["name"])
    var expected: Dictionary = item["expected"] as Dictionary
    if not expected.has("godot_forward"):
        print("SKIP %s: no Godot fixture axes" % name)
        return

    var world: Object = ClassDB.instantiate("FastDisWorld")
    if world == null:
        failures += 1
        push_error("%s could not instantiate FastDisWorld" % name)
        return
    world.set_georeference(float(item["lat_deg"]), float(item["lon_deg"]), float(item["height_m"]))
    world.set_apply_orientation(true)

    var attitude: Dictionary = item["local_ned_attitude_deg"] as Dictionary
    var expected_forward: Vector3 = _vec3(expected["godot_forward"] as Array)
    var expected_right: Vector3 = _vec3(expected["godot_right"] as Array)
    var expected_up: Vector3 = _vec3(expected["godot_up"] as Array)
    var transform: Transform3D = world.call(
        "build_debug_transform",
        float(attitude["heading"]),
        float(attitude["pitch"]),
        float(attitude["roll"])
    )
    var basis: Basis = transform.basis
    var actual_right: Vector3 = basis.x.normalized()
    var actual_up: Vector3 = basis.y.normalized()
    var actual_forward: Vector3 = (-basis.z).normalized()

    _expect_angle(name, "forward", actual_forward, expected_forward, tolerance_degrees)
    _expect_angle(name, "right", actual_right, expected_right, tolerance_degrees)
    _expect_angle(name, "up", actual_up, expected_up, tolerance_degrees)
    _expect_angle(name, "model_front", basis.z.normalized(), -expected_forward.normalized(), tolerance_degrees)
    world.free()

func _vec3(values: Array) -> Vector3:
    return Vector3(float(values[0]), float(values[1]), float(values[2]))

func _expect_angle(case_name: String, axis_name: String, actual: Vector3, expected: Vector3, tolerance_degrees: float) -> void:
    var angle: float = rad_to_deg(actual.normalized().angle_to(expected.normalized()))
    if angle > tolerance_degrees:
        failures += 1
        push_error("%s %s angle %.8f > %.8f" % [case_name, axis_name, angle, tolerance_degrees])
    else:
        print("PASS %s %s angle %.8f" % [case_name, axis_name, angle])
