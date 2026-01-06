buffer = bytearray()
start_marker = bytes.fromhex('AA55')
buffer = bytearray(b'\xAA\x55\x02\xAA\x55\x04\x05')

start_idx = buffer.find(start_marker)

print(start_idx)  # Output: -1 since start_marker is not in buffer
print(buffer[len(start_marker):].find(start_marker))  # Output: 2

