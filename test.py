import os
import time
import csv
import cv2
import numpy as np
import matplotlib.pyplot as plt
from skimage.metrics import structural_similarity as ssim

DATA = [
    {
        "type": "jpg",
        "original": r"secret.jpg",
        "extracted": r"extracted_jpg_data.jpg",
        "video": r"datahidden_jpg.avi"
    },
    {
        "type": "json",
        "original": r"secret.json",
        "extracted": r"extracted_json_data.json",
        "video": r"datahidden_json.avi"
    },
    {
        "type": "txt",
        "original": r"secret.txt",
        "extracted": r"extracted_txt_data.txt",
        "video": r"datahidden_txt.avi"
    }
]

def read_binary(path):
    with open(path, "rb") as f:
        return f.read()

def bit_error_rate(original, extracted):
    length = min(len(original), len(extracted))
    errors = sum(bin(o ^ e).count('1') for o, e in zip(original[:length], extracted[:length]))
    return errors / (length * 8) if length > 0 else 0.0

def calculate_psnr(img1, img2):
    mse = np.mean((img1.astype("float32") - img2.astype("float32")) ** 2)
    if mse == 0: return 100
    return 20 * np.log10(255.0 / np.sqrt(mse))

def is_image_file(path):
    return path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))

results = []
os.chdir(r"C:\Users\v4hd3\Desktop\MotionVector")

for entry in DATA:
    print(f"\n[{entry['type'].upper()}] Değerlendiriliyor...")

    t0 = time.time()
    original = read_binary(entry["original"])
    t1 = time.time()
    extracted = read_binary(entry["extracted"])
    t2 = time.time()

    ber = bit_error_rate(original, extracted)

    psnr_val, ssim_val = None, None
    if is_image_file(entry["original"]):
        img1 = cv2.imread(entry["original"])
        img2 = cv2.imread(entry["extracted"])
        if img1.shape != img2.shape:
            h, w = min(img1.shape[0], img2.shape[0]), min(img1.shape[1], img2.shape[1])
            img1 = img1[:h, :w]
            img2 = img2[:h, :w]
        psnr_val = calculate_psnr(img1, img2)
        win = min(img1.shape[0], img1.shape[1], 7)
        ssim_val = ssim(img1, img2, channel_axis=-1, win_size=win)

    cap = cv2.VideoCapture(entry["video"])
    ret1, frame1 = cap.read()
    ret2, frame2 = cap.read()
    cap.release()

    psnr_vid, ssim_vid = None, None
    if ret1 and ret2:
        win = min(frame1.shape[0], frame1.shape[1], 7)
        psnr_vid = calculate_psnr(frame1, frame2)
        ssim_vid = ssim(frame1, frame2, channel_axis=-1, win_size=win)

    results.append({
        "type": entry["type"],
        "embed_time": round(t1 - t0, 4),
        "extract_time": round(t2 - t1, 4),
        "BER": round(ber, 6),
        "PSNR_File": round(psnr_val, 2) if psnr_val else "",
        "SSIM_File": round(ssim_val, 4) if ssim_val else "",
        "PSNR_Video": round(psnr_vid, 2) if psnr_vid else "",
        "SSIM_Video": round(ssim_vid, 4) if ssim_vid else ""
    })

csv_path = "motion_vector_results.csv"
with open(csv_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)

print(f"\nSonuçlar CSV dosyasına yazıldı: {csv_path}")

try:
    labels = [r["type"].upper() for r in results]

    def safe_vals(key): return [r[key] if r[key] != "" else 0 for r in results]

    fig, axs = plt.subplots(3, 2, figsize=(12, 12))

    axs[0, 0].bar(labels, safe_vals("PSNR_File"), color='skyblue')
    axs[0, 0].set_title("PSNR (Dosya)")
    axs[0, 0].set_ylabel("dB")

    axs[0, 1].bar(labels, safe_vals("SSIM_File"), color='lightcoral')
    axs[0, 1].set_title("SSIM (Dosya)")
    axs[0, 1].set_ylabel("Benzerlik")

    axs[1, 0].bar(labels, safe_vals("PSNR_Video"), color='lightgreen')
    axs[1, 0].set_title("PSNR (Video)")
    axs[1, 0].set_ylabel("dB")

    axs[1, 1].bar(labels, safe_vals("SSIM_Video"), color='orange')
    axs[1, 1].set_title("SSIM (Video)")
    axs[1, 1].set_ylabel("Benzerlik")

    axs[2, 0].bar(labels, safe_vals("BER"), color='gray')
    axs[2, 0].set_title("Bit Error Rate (BER)")
    axs[2, 0].set_ylabel("Oran")

    axs[2, 1].bar(labels, safe_vals("extract_time"), color='mediumpurple', label="Çıkarma")
    axs[2, 1].bar(labels, safe_vals("embed_time"), color='gold', alpha=0.7, label="Gömme")
    axs[2, 1].set_title("Süreler (saniye)")
    axs[2, 1].legend()

    for ax in axs.flat:
        ax.set_ylim(bottom=0)
        ax.grid(True, axis='y', linestyle='--', linewidth=0.5)

    plt.tight_layout()
    plt.savefig("test_results.png")
    print("Grafik kaydedildi: test_results.png")
except Exception as e:
    print(f"Grafik oluşturulamadı: {e}")
