import os
import time
import csv
import cv2
import numpy as np
import matplotlib.pyplot as plt
from skimage.metrics import structural_similarity as ssim
from Levenshtein import ratio as levenshtein_ratio

def read_binary(path):
    try:
        with open(path, "rb") as f:
            return f.read()
    except FileNotFoundError:
        print(f"[HATA] Dosya bulunamadı: {path}")
        return None

def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except FileNotFoundError:
        print(f"[HATA] Dosya bulunamadı: {path}")
        return None

def bit_error_rate(original, extracted):
    if original is None or extracted is None:
        return None
    length = min(len(original), len(extracted))
    errors = sum(bin(o ^ e).count('1') for o, e in zip(original[:length], extracted[:length]))
    return errors / (length * 8) if length > 0 else None

def calculate_psnr(img1, img2):
    mse = np.mean((img1.astype("float32") - img2.astype("float32")) ** 2)
    return 100 if mse == 0 else 20 * np.log10(255.0 / np.sqrt(mse))

def calculate_mse(img1, img2):
    return np.mean((img1.astype("float32") - img2.astype("float32")) ** 2)

def calculate_mae(img1, img2):
    return np.mean(np.abs(img1.astype("float32") - img2.astype("float32")))

def histogram_difference(img1, img2):
    diff_sum = 0
    for i in range(3):
        hist1 = cv2.calcHist([img1], [i], None, [256], [0, 256])
        hist2 = cv2.calcHist([img2], [i], None, [256], [0, 256])
        hist1 = cv2.normalize(hist1, hist1).flatten()
        hist2 = cv2.normalize(hist2, hist2).flatten()
        diff_sum += np.sum(np.abs(hist1 - hist2))
    return diff_sum

def detailed_image_metrics(img1, img2):
    if img1.shape != img2.shape:
        h, w = min(img1.shape[0], img2.shape[0]), min(img1.shape[1], img2.shape[1])
        img1, img2 = img1[:h, :w], img2[:h, :w]

    mse_val = calculate_mse(img1, img2)
    psnr_val = 100 if mse_val == 0 else 20 * np.log10(255.0 / np.sqrt(mse_val))
    win = min(img1.shape[0], img1.shape[1], 7)
    ssim_val = ssim(img1, img2, channel_axis=-1, win_size=win)
    mae_val = calculate_mae(img1, img2)
    hist_diff = histogram_difference(img1, img2)
    diff_img = cv2.absdiff(img1, img2)
    diff_gray = cv2.cvtColor(diff_img, cv2.COLOR_BGR2GRAY)
    mean_diff_pixel = np.mean(diff_gray)

    return {
        "PSNR_File": round(psnr_val, 2),
        "SSIM_File": round(ssim_val, 4),
        "MSE": round(mse_val, 4),
        "MAE": round(mae_val, 4),
        "Histogram_Diff": round(hist_diff, 4),
        "Mean_Diff_Pixel": round(mean_diff_pixel, 4)
    }

def average_video_metrics(video_path):
    cap = cv2.VideoCapture(video_path)
    psnrs, ssims = [], []
    ret, prev = cap.read()
    while True:
        ret, frame = cap.read()
        if not ret or prev is None:
            break
        win = min(prev.shape[0], prev.shape[1], 7)
        psnrs.append(calculate_psnr(prev, frame))
        ssims.append(ssim(prev, frame, channel_axis=-1, win_size=win))
        prev = frame
    cap.release()
    return (
        round(np.mean(psnrs), 2) if psnrs else None,
        round(np.mean(ssims), 4) if ssims else None
    )

def is_image_file(path):
    return path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))

def calculate_text_similarity(orig_path, extr_path):
    text1, text2 = read_text(orig_path), read_text(extr_path)
    if text1 and text2:
        return round(levenshtein_ratio(text1, text2), 4)
    return None

# Ana dizin ve sonuç klasörü
base_dir = r"C:\Users\v4hd3\Desktop\MotionVector"
result_dir = os.path.join(base_dir, "testresults")
os.makedirs(result_dir, exist_ok=True)
os.chdir(base_dir)

DATA = [
    {"type": "jpg", "original": "secret.jpg", "extracted": "extracted_jpg_data.jpg", "video": "datahiden_jpg.avi"},
    {"type": "json", "original": "secret.json", "extracted": "extracted_json_data.json", "video": "datahiden_json.avi"},
    {"type": "txt", "original": "secret.txt", "extracted": "extracted_txt_data.txt", "video": "datahiden_txt.avi"}
]

results = []

for entry in DATA:
    print(f"\n[{entry['type'].upper()}] Değerlendiriliyor...")

    t0 = time.time()
    orig_bin = read_binary(entry["original"])
    t1 = time.time()
    extr_bin = read_binary(entry["extracted"])
    t2 = time.time()

    ber = bit_error_rate(orig_bin, extr_bin)
    psnr_file, ssim_file, mse, mae, hist_diff, mean_diff_pixel, text_sim = None, None, None, None, None, None, None

    if is_image_file(entry["original"]) and entry["type"] == "jpg":
        img1 = cv2.imread(entry["original"])
        img2 = cv2.imread(entry["extracted"])
        if img1 is not None and img2 is not None:
            metrics = detailed_image_metrics(img1, img2)
            psnr_file = metrics["PSNR_File"]
            ssim_file = metrics["SSIM_File"]
            mse = metrics["MSE"]
            mae = metrics["MAE"]
            hist_diff = metrics["Histogram_Diff"]
            mean_diff_pixel = metrics["Mean_Diff_Pixel"]
    elif entry["type"] != "jpg":
        text_sim = calculate_text_similarity(entry["original"], entry["extracted"])

    psnr_vid, ssim_vid = average_video_metrics(entry["video"])

    results.append({
        "type": entry["type"],
        "embed_time": round(t1 - t0, 4),
        "extract_time": round(t2 - t1, 4),
        "BER": round(ber, 6) if ber is not None else "",
        "PSNR_File": psnr_file if psnr_file is not None else "",
        "SSIM_File": ssim_file if ssim_file is not None else "",
        "MSE": mse if mse is not None else "",
        "MAE": mae if mae is not None else "",
        "Histogram_Diff": hist_diff if hist_diff is not None else "",
        "Mean_Diff_Pixel": mean_diff_pixel if mean_diff_pixel is not None else "",
        "Text_Similarity": text_sim if text_sim else "",
        "PSNR_Video": psnr_vid if psnr_vid else "",
        "SSIM_Video": ssim_vid if ssim_vid else ""
    })

csv_path = os.path.join(result_dir, "motion_vector_results.csv")
fieldnames = ["type", "embed_time", "extract_time", "BER", "PSNR_File", "SSIM_File", "MSE", "MAE", "Histogram_Diff", "Mean_Diff_Pixel", "Text_Similarity", "PSNR_Video", "SSIM_Video"]

with open(csv_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

print(f"\nSonuçlar CSV dosyasına yazıldı: {csv_path}")

# Grafikler
try:
    import matplotlib.ticker as mtick
    from matplotlib import rcParams

    rcParams.update({
        "axes.titlesize": 14,
        "axes.labelsize": 12,
        "xtick.labelsize": 11,
        "ytick.labelsize": 11,
        "legend.fontsize": 11
    })

    labels = [r["type"].upper() for r in results]

    def safe_vals(key): 
        return [r[key] if isinstance(r[key], (int, float)) else 0 for r in results]

    metrics = [
        ("PSNR_File", "PSNR (Dosya Kalitesi)", "#4C72B0"),
        ("SSIM_File", "Yapısal Benzerlik (Dosya)", "#DD8452"),
        ("MSE", "Ortalama Kare Hata (MSE)", "#55A868"),
        ("MAE", "Ortalama Mutlak Hata (MAE)", "#C44E52"),
        ("Histogram_Diff", "Histogram Farkı", "#8172B2"),
        ("Mean_Diff_Pixel", "Ortalama Piksel Farkı", "#937860"),
        ("BER", "Bit Hata Oranı (BER)", "#DA8BC3"),
        ("PSNR_Video", "PSNR (Video)", "#8C8C8C"),
        ("SSIM_Video", "Yapısal Benzerlik (Video)", "#CCB974"),
        ("Text_Similarity", "Metin Benzerliği", "#64B5CD")
    ]

    for key, title, color in metrics:
        values = safe_vals(key)
        if any(v > 0 for v in values):
            fig, ax = plt.subplots(figsize=(7, 4), dpi=100)
            bars = ax.bar(labels, values, color=color)
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.set_ylabel("Değer", fontsize=12)
            ax.set_ylim(bottom=0)
            ax.grid(True, axis='y', linestyle='--', linewidth=0.5, alpha=0.7)
            for bar, val in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                        f"{val:.2f}", ha='center', va='bottom', fontsize=10)
            if "SSIM" in key or "Similarity" in key:
                ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
            fig.tight_layout()
            fig.savefig(os.path.join(result_dir, f"{key}.png"))
            plt.close(fig)

    # Embed/Extract zaman grafiği
    fig2, ax2 = plt.subplots(figsize=(10, 4), dpi=120)
    embed_times = safe_vals("embed_time")
    extract_times = safe_vals("extract_time")
    width = 0.35
    x = np.arange(len(labels))
    bar1 = ax2.bar(x - width/2, embed_times, width, label="Gömme Süresi", color="#1f77b4")
    bar2 = ax2.bar(x + width/2, extract_times, width, label="Çıkarma Süresi", color="#ff7f0e")
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels)
    ax2.set_title("Gömme ve Çıkarma Süreleri", fontsize=14, fontweight="bold")
    ax2.set_ylabel("Süre (saniye)")
    ax2.grid(True, axis='y', linestyle='--', linewidth=0.5)
    ax2.legend()
    for bar in bar1 + bar2:
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2, yval + 0.002,
                 f"{yval:.4f}", ha='center', va='bottom', fontsize=9)
    fig2.tight_layout()
    fig2.savefig(os.path.join(result_dir, "embed_extract_times.png"))
    plt.close(fig2)

    print(f"Grafikler '{result_dir}' klasörüne kaydedildi.")

except Exception as e:
    print(f"Grafik oluşturulamadı: {e}")
