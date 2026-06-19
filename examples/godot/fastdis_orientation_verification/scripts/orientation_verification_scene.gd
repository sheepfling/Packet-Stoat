extends Node3D

@export var case_name := "level_north"
@export var max_axis_angle_degrees := 0.01

var expected_forward := Vector3.FORWARD
var expected_right := Vector3.RIGHT
var expected_up := Vector3.UP

func _ready() -> void:
    print("FastDIS orientation verification scene loaded: ", case_name)
    print("Actual forward is -global_transform.basis.z")
    print("Actual right is global_transform.basis.x")
    print("Actual up is global_transform.basis.y")

func basis_error_degrees(node: Node3D) -> Dictionary:
    var basis := node.global_transform.basis
    return {
        "forward": rad_to_deg((-basis.z).normalized().angle_to(expected_forward.normalized())),
        "right": rad_to_deg(basis.x.normalized().angle_to(expected_right.normalized())),
        "up": rad_to_deg(basis.y.normalized().angle_to(expected_up.normalized())),
    }
