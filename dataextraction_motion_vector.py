import os
import cv2

def extract_data_from_video(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("[-] Video could not be opened:", video_path)
        return None

    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    data = bytearray()
    data_len = None
    success, frame = cap.read()

    while success:
        for y in range(2):  # alt iki satır
            for x in range(8):
                byte = 0
                for i in range(8):
                    px = x * 8 + i
                    py = height - 2 + y
                    bit = frame[py, px, 0] & 1
                    byte = (byte << 1) | bit
                data.append(byte)

                if data_len is None and len(data) >= 4:
                    data_len = int.from_bytes(data[:4], 'big')
                    data = bytearray()  # başlıktan sonra sadece veri
                elif data_len is not None and len(data) >= data_len:
                    cap.release()
                    return data

        success, frame = cap.read()

    cap.release()
    print("[-] Data could not be extracted or is incomplete.")
    return None

def detect_extension_from_filename(name):
    name = name.lower()
    if "txt" in name:
        return "txt"
    elif "json" in name:
        return "json"
    elif "jpg" in name or "jpeg" in name:
        return "jpg"
    elif "png" in name:
        return "png"
    else:
        return "bin"

if __name__ == "__main__":
    print("Available AVI files:")
    files = [f for f in os.listdir() if f.endswith(".avi")]

    # Dosya adlarını format + data adı şeklinde dönüştür
    renamed_files = []
    for f in files:
        name, ext = os.path.splitext(f)
        filetype = detect_extension_from_filename(name)
        core_name = name.replace(filetype, "").rstrip("_-") or "datahidden"
        new_name = f"{core_name}_{filetype}{ext}"
        renamed_files.append(new_name)

    for i, f in enumerate(renamed_files, 1):
        print(f"{i} - {f}")

    try:
        choice = int(input("From which video to extract data? (Enter number): "))
        filename = files[choice - 1]
    except:
        print("[-] Invalid selection.")
        exit()

    print(f"[i] Selected video: {filename}")
    data = extract_data_from_video(filename)
    if data is None:
        print("Data extraction failed.")
        exit()

    ext = detect_extension_from_filename(filename)
    output_file = f"extracted_{ext}_data.{ext}"
    with open(output_file, "wb") as f:
        f.write(data)

    print(f"[+] Data extracted: {output_file}")
