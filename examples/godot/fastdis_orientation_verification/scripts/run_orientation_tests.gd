extends SceneTree

var failures := 0

func _init() -> void:
    call_deferred("_run")

func _run() -> void:
    var fixture := _load_fixture()
    if fixture.is_empty():
        failures += 1
        quit(failures)
        return

    var tolerance := float(fixture["tolerances"]["engine_axis_angular_error_deg"])
    for item in fixture["cases"]:
        _run_case(item, tolerance)

    if failures == 0:
        print("FastDIS Godot orientation verification passed")
    else:
        push_error("FastDIS Godot orientation verification failed: %d case checks" % failures)
    quit(failures)

func _load_fixture() -> Dictionary:
    var candidates := [
        "res://tests/orientation_engine_cases.json",
        "res://../../../tests/data/orientation_engine_cases.json",
    ]
    for candidate in candidates:
        var path := ProjectSettings.globalize_path(candidate)
        if FileAccess.file_exists(path):
            var text := FileAccess.get_file_as_string(path)
            var parsed = JSON.parse_string(text)
            if typeof(parsed) == TYPE_DICTIONARY:
                return parsed
            push_error("Could not parse fixture JSON: %s" % path)
            return {}
    push_error("Could not find orientation_engine_cases.json")
    return {}

func _run_case(item: Dictionary, tolerance_degrees: float) -> void:
    var name := str(item["name"])
    var expected := item["expected"]
    if not expected.has("godot_forward"):
        print("SKIP %s: no Godot fixture axes" % name)
        return

    var expected_forward := _vec3(expected["godot_forward"])
    var expected_right := _vec3(expected["godot_right"])
    var expected_up := _vec3(expected["godot_up"])

    var basis := Basis(
        expected_right.normalized(),
        expected_up.normalized(),
        (-expected_forward).normalized()
    )

    # This validates Godot's basis-column interpretation. The next
    # implementation step is to replace this basis with the adapter-produced
    # Transform3D after applying a fastdis snapshot.
    var actual_right := basis.x.normalized()
    var actual_up := basis.y.normalized()
    var actual_forward := (-basis.z).normalized()

    _expect_angle(name, "forward", actual_forward, expected_forward, tolerance_degrees)
    _expect_angle(name, "right", actual_right, expected_right, tolerance_degrees)
    _expect_angle(name, "up", actual_up, expected_up, tolerance_degrees)
    _expect_angle(name, "model_front", basis.z.normalized(), -expected_forward.normalized(), tolerance_degrees)

func _vec3(values: Array) -> Vector3:
    return Vector3(float(values[0]), float(values[1]), float(values[2]))

func _expect_angle(case_name: String, axis_name: String, actual: Vector3, expected: Vector3, tolerance_degrees: float) -> void:
    var angle := rad_to_deg(actual.normalized().angle_to(expected.normalized()))
    if angle > tolerance_degrees:
        failures += 1
        push_error("%s %s angle %.8f > %.8f" % [case_name, axis_name, angle, tolerance_degrees])
    else:
        print("PASS %s %s angle %.8f" % [case_name, axis_name, angle])
