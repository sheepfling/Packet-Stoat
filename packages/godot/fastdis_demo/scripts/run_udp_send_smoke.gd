extends SceneTree

var failures: int = 0


func _init() -> void:
	call_deferred("_run")


func _read_replay_packets(path: String) -> Array[PackedByteArray]:
	var packets: Array[PackedByteArray] = []
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_error("Could not open replay file: %s" % path)
		failures += 1
		return packets

	while file.get_position() < file.get_length():
		var header: PackedByteArray = file.get_buffer(4)
		if header.size() != 4:
			push_error("Replay file is truncated before a packet length prefix")
			failures += 1
			return []
		var length: int = (int(header[0]) << 24) | (int(header[1]) << 16) | (int(header[2]) << 8) | int(header[3])
		if length <= 0:
			push_error("Replay file contains an invalid packet length: %d" % length)
			failures += 1
			return []
		var packet: PackedByteArray = file.get_buffer(length)
		if packet.size() != length:
			push_error("Replay file is truncated within a packet body")
			failures += 1
			return []
		packets.append(packet)
	return packets


func _run() -> void:
	var host := OS.get_environment("FASTDIS_GODOT_SEND_HOST")
	var port := int(OS.get_environment("FASTDIS_GODOT_SEND_PORT"))
	var replay_path := OS.get_environment("FASTDIS_GODOT_SEND_REPLAY_PATH")
	var expected_packets := int(OS.get_environment("FASTDIS_GODOT_SEND_EXPECTED_PACKETS"))

	if host.is_empty():
		push_error("FASTDIS_GODOT_SEND_HOST is required.")
		failures += 1
		quit(failures)
		return
	if port <= 0:
		push_error("FASTDIS_GODOT_SEND_PORT is required.")
		failures += 1
		quit(failures)
		return
	if replay_path.is_empty():
		push_error("FASTDIS_GODOT_SEND_REPLAY_PATH is required.")
		failures += 1
		quit(failures)
		return

	var packets := _read_replay_packets(replay_path)
	if failures != 0:
		quit(failures)
		return

	var peer := PacketPeerUDP.new()
	peer.set_dest_address(host, port)

	var bytes_sent := 0
	for packet: PackedByteArray in packets:
		var rc := peer.put_packet(packet)
		if rc != OK:
			push_error("PacketPeerUDP.put_packet failed with %d" % rc)
			failures += 1
			break
		bytes_sent += packet.size()

	var report := {
		"schema": "fastdis.godot_udp_send_report.v1",
		"surface": "godot",
		"mode": "live_udp_send",
		"packets_sent": packets.size(),
		"expected_packets": expected_packets,
		"bytes_sent": bytes_sent,
		"errors": failures
	}
	print(JSON.stringify(report))

	if packets.size() != expected_packets:
		push_error("Expected to send %d packets, sent %d" % [expected_packets, packets.size()])
		failures += 1

	quit(failures)
