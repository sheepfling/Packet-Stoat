extends Node3D

@export var case_name := "level_north"
@export var max_axis_angle_degrees := 0.01
@export var axis_length := 2.0
@export var root_separation := 3.0

var expected_forward := Vector3.FORWARD
var expected_right := Vector3.RIGHT
var expected_up := Vector3.UP
var show_model_front := true

@onready var expected_axes_root: Node3D = $ExpectedAxes
@onready var actual_axes_root: Node3D = $ActualAxes
@onready var status_label: Label3D = $StatusLabel

func _ready() -> void:
    _ensure_axis_gizmo(expected_axes_root, false)
    _ensure_axis_gizmo(actual_axes_root, true)
    _refresh_visualization()

func basis_error_degrees(node: Node3D) -> Dictionary:
    var basis := node.transform.basis
    var result := {
        "forward": rad_to_deg((-basis.z).normalized().angle_to(expected_forward.normalized())),
        "right": rad_to_deg(basis.x.normalized().angle_to(expected_right.normalized())),
        "up": rad_to_deg(basis.y.normalized().angle_to(expected_up.normalized())),
    }
    if show_model_front:
        result["model_front"] = rad_to_deg(basis.z.normalized().angle_to((-expected_forward).normalized()))
    return result

func basis_dot_products(node: Node3D) -> Dictionary:
    var basis := node.transform.basis
    var forward := (-basis.z).normalized()
    var right := basis.x.normalized()
    var up := basis.y.normalized()
    var result := {
        "forward": forward.dot(expected_forward.normalized()),
        "right": right.dot(expected_right.normalized()),
        "up": up.dot(expected_up.normalized()),
    }
    if show_model_front:
        result["model_front"] = basis.z.normalized().dot((-expected_forward).normalized())
    return result

func _refresh_visualization() -> void:
    var fixture := _load_fixture()
    if fixture.is_empty():
        _report_error("Could not load orientation fixture JSON.")
        return

    var item := _find_case(fixture)
    if item.is_empty():
        _report_error("Unknown case: %s" % case_name)
        return

    var expected: Dictionary = item["expected"] as Dictionary
    expected_forward = _vec3(expected["godot_forward"] as Array)
    expected_right = _vec3(expected["godot_right"] as Array)
    expected_up = _vec3(expected["godot_up"] as Array)

    expected_axes_root.transform = Transform3D(
        _basis_from_axes(expected_forward, expected_right, expected_up),
        Vector3(-root_separation * 0.5, 0.0, 0.0)
    )

    if not ClassDB.class_exists("FastDisWorld"):
        _report_error("FastDisWorld extension is not loaded.")
        return

    var world: Object = ClassDB.instantiate("FastDisWorld")
    if world == null:
        _report_error("Could not instantiate FastDisWorld.")
        return

    world.set_georeference(float(item["lat_deg"]), float(item["lon_deg"]), float(item["height_m"]))
    world.set_apply_orientation(true)
    if not world.has_method("set_orientation_mode") or not world.has_method("build_debug_transform_from_dis"):
        world.free()
        _report_error("FastDisWorld wrapper is missing the validated DIS orientation API. Rebuild/stage the current GDExtension.")
        return
    world.set_orientation_mode(2)

    var dis_deg: Dictionary = expected["dis_deg"] as Dictionary
    var actual_transform: Transform3D = world.call(
        "build_debug_transform_from_dis",
        float(dis_deg["psi"]),
        float(dis_deg["theta"]),
        float(dis_deg["phi"])
    )
    world.free()

    actual_axes_root.transform = Transform3D(actual_transform.basis.orthonormalized(), Vector3(root_separation * 0.5, 0.0, 0.0))

    var errors := basis_error_degrees(actual_axes_root)
    var dots := basis_dot_products(actual_axes_root)
    var passed := _max_error(errors) <= max_axis_angle_degrees
    _update_label(item["name"], errors, dots, passed)

func _update_label(name: String, errors: Dictionary, dots: Dictionary, passed: bool) -> void:
    var lines := PackedStringArray()
    lines.append("%s %s" % ["PASS" if passed else "FAIL", name])
    lines.append("forward angle=%.6f dot=%.6f" % [float(errors["forward"]), float(dots["forward"])])
    lines.append("right   angle=%.6f dot=%.6f" % [float(errors["right"]), float(dots["right"])])
    lines.append("up      angle=%.6f dot=%.6f" % [float(errors["up"]), float(dots["up"])])
    if show_model_front:
        lines.append("model_front angle=%.6f dot=%.6f" % [float(errors["model_front"]), float(dots["model_front"])])
    lines.append("threshold=%.6f deg" % max_axis_angle_degrees)
    status_label.text = "\n".join(lines)
    print(status_label.text)

func _report_error(message: String) -> void:
    status_label.text = "FAIL %s" % message
    push_error(message)

func _max_error(errors: Dictionary) -> float:
    var value := 0.0
    for error_value in errors.values():
        value = max(value, float(error_value))
    return value

func _find_case(fixture: Dictionary) -> Dictionary:
    var cases: Array = fixture.get("cases", []) as Array
    for item: Dictionary in cases:
        if str(item.get("name", "")) == case_name:
            return item
    if not cases.is_empty():
        return cases[0] as Dictionary
    return {}

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
    return {}

func _vec3(values: Array) -> Vector3:
    return Vector3(float(values[0]), float(values[1]), float(values[2]))

func _basis_from_axes(forward: Vector3, right: Vector3, up: Vector3) -> Basis:
    return Basis(right.normalized(), up.normalized(), (-forward).normalized()).orthonormalized()

func _ensure_axis_gizmo(root: Node3D, actual: bool) -> void:
    if root.has_node("ForwardBar"):
        return

    var colors := {
        "forward": Color(1.0, 0.15, 0.15) if actual else Color(0.55, 0.2, 0.2),
        "right": Color(0.15, 0.95, 0.25) if actual else Color(0.2, 0.45, 0.2),
        "up": Color(0.2, 0.45, 1.0) if actual else Color(0.2, 0.2, 0.55),
    }

    _add_axis_bar(root, "ForwardBar", Vector3(0.08, 0.08, axis_length), Vector3(0.0, 0.0, -axis_length * 0.5), colors["forward"])
    _add_axis_bar(root, "RightBar", Vector3(axis_length, 0.08, 0.08), Vector3(axis_length * 0.5, 0.0, 0.0), colors["right"])
    _add_axis_bar(root, "UpBar", Vector3(0.08, axis_length, 0.08), Vector3(0.0, axis_length * 0.5, 0.0), colors["up"])

func _add_axis_bar(root: Node3D, name: String, size: Vector3, origin: Vector3, color: Color) -> void:
    var mesh_instance := MeshInstance3D.new()
    mesh_instance.name = name
    var mesh := BoxMesh.new()
    mesh.size = size
    mesh_instance.mesh = mesh
    var material := StandardMaterial3D.new()
    material.albedo_color = color
    material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
    mesh_instance.set_surface_override_material(0, material)
    mesh_instance.position = origin
    root.add_child(mesh_instance)
