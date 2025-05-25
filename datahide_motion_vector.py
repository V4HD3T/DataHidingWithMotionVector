import os
import cv2

def read_data_bytes(filepath):
    with open(filepath, "rb") as f:
        return bytearray(f.read())

def embed_data_in_video(input_video_path, output_video_path, data):
    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        print("[-] Video could not be opened:", input_video_path)
        return False

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    fourcc = cv2.VideoWriter_fourcc(*'HFYU')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    # Veri + 4 byte uzunluk bilgisi
    data = len(data).to_bytes(4, 'big') + data
    total_bytes = len(data)
    max_bytes = frame_count * 16  # 2 satır x 8 byte = 16 byte/frame

    if total_bytes > max_bytes:
        print(f"[-] Data too large. Max capacity: {max_bytes} bytes.")
        return False

    byte_index = 0
    success, frame = cap.read()
    while success:
        if byte_index < total_bytes:
            for y in range(2):  # alt iki satır
                for x in range(8):
                    if byte_index >= total_bytes:
                        break
                    byte = data[byte_index]
                    for i in range(8):
                        px = x * 8 + i
                        py = height - 2 + y
                        frame[py, px, 0] = (frame[py, px, 0] & 0xFE) | ((byte >> (7 - i)) & 1)
                    byte_index += 1
        out.write(frame)
        success, frame = cap.read()

    cap.release()
    out.release()
    print(f"[+] Data successfully embedded. Output: {output_video_path}")
    return True

if __name__ == "__main__":
    secret_files = [f for f in os.listdir() if f.startswith("secret.")]
    if not secret_files:
        print("[-] No secret files found.")
        exit()

    print("Which file do you want to hide?")
    for i, f in enumerate(secret_files, 1):
        print(f"{i} - {f}")

    try:
        choice = int(input("Your choice (number): "))
        hidden_file = secret_files[choice - 1]
    except:
        print("[-] Invalid selection.")
        exit()

    input_video = "coastguard_cif.avi"
    ext = os.path.splitext(hidden_file)[1].replace(".", "")
    output_video = f"datahiden_{ext}.avi"

    data = read_data_bytes(hidden_file)
    print(f"[i] Data size: {len(data)} bytes")
    embed_data_in_video(input_video, output_video, data)
