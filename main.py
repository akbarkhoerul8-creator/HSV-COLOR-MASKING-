# =====================================================================
# Implementasi HSV Color Masking untuk Mengubah Warna Latar Belakang
# pada Citra Digital Menggunakan Python dan OpenCV
# (Versi lokal: dijalankan di laptop, tanpa Google Colab)
#
# Persiapan:
# 1. Buat folder, misalnya Tugas_PCD_HSV, lalu simpan file ini
#    (hsv_color_masking_lokal.py) di dalamnya.
# 2. Simpan foto berlatar merah di folder yang sama dan beri nama
#    foto_merah.jpg. Jika nama foto berbeda, ubah NAMA_FILE di Cell 2,
#    atau biarkan saja: program akan membuka jendela pilih file.
# 3. Instal library (satu kali), ketik di terminal:
#       python -m pip install opencv-python numpy matplotlib
# 4. Jalankan program:
#       python hsv_color_masking_lokal.py
#
# Catatan: setiap jendela gambar harus ditutup agar program lanjut
# ke cell berikutnya.
# =====================================================================


# %% Cell 1 - Import Library
# Fungsi : Memanggil library yang dibutuhkan untuk pengolahan citra.
# os         -> mengatur lokasi file dan folder (TAMBAHAN untuk versi lokal)
# cv2        -> mengolah gambar (OpenCV)
# numpy      -> mengolah data piksel dalam bentuk array
# matplotlib -> menampilkan gambar di layar
import os
import cv2
import numpy as np
import matplotlib.pyplot as plt

print("OpenCV:", cv2.__version__)
print("Library berhasil dimuat!")


# %% Cell 2 - Membaca Foto
# Fungsi : Memasukkan foto yang akan diproses, lalu menampilkannya.
# Foto yang dipilih sebaiknya memiliki latar belakang berwarna merah.
# (Pengganti files.upload() milik Colab: foto dibaca dari folder program.)

# --- Menentukan lokasi foto (TAMBAHAN untuk versi lokal) ---

# Folder tempat file program ini berada
try:
    folder_program = os.path.dirname(os.path.abspath(__file__))
except NameError:
    folder_program = os.getcwd()

# Nama foto yang disimpan di folder program. Ubah jika namanya berbeda.
NAMA_FILE = "foto_merah.jpg"
lokasi_foto = os.path.join(folder_program, NAMA_FILE)

# Jika foto tidak ditemukan, buka jendela untuk memilih foto secara manual
if not os.path.exists(lokasi_foto):
    print("Foto", NAMA_FILE, "tidak ditemukan di folder program.")
    print("Silakan pilih foto pada jendela yang muncul...")
    try:
        import tkinter as tk
        from tkinter import filedialog

        jendela = tk.Tk()
        jendela.withdraw()
        jendela.attributes("-topmost", True)
        lokasi_foto = filedialog.askopenfilename(
            title="Pilih foto berlatar merah",
            filetypes=[("Gambar", "*.jpg *.jpeg *.png *.bmp")]
        )
        jendela.destroy()
    except Exception:
        lokasi_foto = ""

# Menghentikan program jika foto tetap tidak ditemukan
if not lokasi_foto or not os.path.exists(lokasi_foto):
    raise FileNotFoundError(
        "Foto tidak ditemukan. Simpan foto di folder yang sama "
        "dengan program ini dan periksa nama file-nya."
    )

print("Foto yang digunakan:", lokasi_foto)

# --- Membaca foto ---

# Membaca file foto menjadi gambar yang dapat diolah OpenCV (format BGR)
foto = cv2.imdecode(
    np.fromfile(lokasi_foto, np.uint8),
    cv2.IMREAD_COLOR
)

# Memeriksa apakah foto berhasil dibaca
if foto is None:
    raise ValueError("Foto gagal dibaca!")

# Mengubah BGR ke RGB agar warna tampil benar di Matplotlib
foto_rgb = cv2.cvtColor(foto, cv2.COLOR_BGR2RGB)

# Menampilkan foto asli
plt.figure(figsize=(6, 5))
plt.imshow(foto_rgb)
plt.title("Foto Asli")
plt.axis("off")
plt.show()


# %% Cell 3 - Konversi Warna ke HSV
# Fungsi : Mengubah format warna gambar dari BGR menjadi HSV.
# H (Hue)        -> jenis warna (merah, kuning, hijau, dst.)
# S (Saturation) -> kepekatan warna
# V (Value)      -> tingkat terang atau gelap
# Format HSV mempermudah pemilihan warna tertentu.
hsv = cv2.cvtColor(foto, cv2.COLOR_BGR2HSV)

print("Foto berhasil dikonversi ke HSV")
print("Ukuran gambar:", foto.shape)
print("Ukuran data HSV:", hsv.shape)


# %% Cell 4 - Deteksi Warna Merah & Isolasi Latar Belakang
# Fungsi : Memilih piksel latar belakang merah secara presisi.
#
# MASALAH PADA METODE SEBELUMNYA:
# 1. Dasi merah, bibir, dan badge bendera di baju memiliki warna merah yang
#    identik dengan latar belakang merah studio (sama-sama Hue ~178, Saturation tinggi).
#    Thresholding warna saja TIDAK BISA membedakannya hanya dari nilai warnanya.
# 2. Bibir memiliki rona kemerahan (Hue 0-10) sehingga ikut terwarnai biru.
#
# SOLUSI PENGOLAHAN CITRA DIGITAL (PCD):
# 1. Pengetatan Rentang HSV:
#    - Rentang merah studio utama: Hue 165-179.
#    - Rentang merah jingga: Hue 0-8 dengan syarat Saturation & Value tinggi (>160)
#      agar bibir, kulit, dan noda wajah (yang Saturation-nya lebih rendah) tidak ikut masuk.
# 2. Analisis Spasial / Konektivitas (Connected Components):
#    - Latar belakang (Background) adalah area merah luas yang terhubung ke batas
#      luar foto (tepi atas, sudut kiri atas, sudut kanan atas).
#    - Dasi, bibir, dan atribut baju berada di DALAM siluet tubuh (foreground) dan
#      terkelilingi oleh kain putih/kulit, sehingga terisolasi secara spasial.
#    - Dengan hanya memilih komponen merah yang menyentuh batas luar latar, dasi,
#      bibir, dan badge 100% AMAN dan tidak akan ikut berubah warna!

h, w = foto.shape[:2]

# Rentang 1: Merah jingga (Hue 0-8) dengan batas Saturation tinggi (>160)
# agar bibir & kulit tidak ikut terdeteksi
batas1_bawah = np.array([0, 160, 70])
batas1_atas  = np.array([8, 255, 255])

# Rentang 2: Merah studio utama (Hue 165-179)
batas2_bawah = np.array([165, 120, 50])
batas2_atas  = np.array([179, 255, 255])

# Membuat mask warna merah
mask1 = cv2.inRange(hsv, batas1_bawah, batas1_atas)
mask2 = cv2.inRange(hsv, batas2_bawah, batas2_atas)
mask_merah = cv2.bitwise_or(mask1, mask2)

# --- Operasi Morfologi untuk Membersihkan Noise ---
# MORPH_OPEN  : menghapus bintik-bintik kecil (noise)
# MORPH_CLOSE : menutup celah-celah kecil pada latar
kernel_bersih = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
mask_clean = cv2.morphologyEx(mask_merah, cv2.MORPH_OPEN, kernel_bersih, iterations=1)
mask_clean = cv2.morphologyEx(mask_clean, cv2.MORPH_CLOSE, kernel_bersih, iterations=1)

# --- Isolasi Latar Belakang Menggunakan Connected Components ---
# Memberi label unik untuk setiap pulau/area warna merah yang terpisah
num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask_clean)

# Menyiapkan mask khusus latar belakang
mask = np.zeros((h, w), dtype=np.uint8)

for i in range(1, num_labels):
    # Komponen latar belakang selalu menyentuh tepi atas atau samping atas foto
    menyentuh_tepi_atas  = np.any(labels[0, :] == i)
    menyentuh_tepi_kiri  = np.any(labels[:int(h * 0.6), 0] == i)
    menyentuh_tepi_kanan = np.any(labels[:int(h * 0.6), w - 1] == i)
    area = stats[i, cv2.CC_STAT_AREA]

    # Hanya ambil area yang terhubung ke tepi luar dan berukuran besar
    if (menyentuh_tepi_atas or menyentuh_tepi_kiri or menyentuh_tepi_kanan) and area > 1000:
        mask[labels == i] = 255

# Menutup lubang kecil pada latar belakang jika ada
kernel_tutup = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_tutup)

# Menampilkan mask (putih = latar belakang merah, hitam = orang & objek yang dilindungi)
plt.figure(figsize=(6, 5))
plt.imshow(mask, cmap="gray")
plt.title("Mask Latar Belakang (Dasi & Bibir Terlindungi)")
plt.axis("off")
plt.show()


# %% Cell 5 - Mengganti Warna Latar Belakang Menjadi Biru
# Fungsi : Mengubah latar belakang menjadi biru dengan transisi tepi halus (Alpha Blending).

# Warna latar belakang baru:
# Pilihan 1: Biru Pas Foto Studio Standar Indonesia (Elegan & Natural: BGR [215, 80, 0])
# Pilihan 2: Biru Solid murni (BGR [255, 0, 0])
warna_biru = np.array([215, 80, 0], dtype=np.float32)

# --- Alpha Blending / Feathering Tepi ---
# Memberikan sedikit efek kehalusan (Gaussian Blur) pada tepian mask
# agar batas rambut dan bahu tidak bergerigi / tidak meninggalkan garis merah kaku
alpha = cv2.GaussianBlur(mask.astype(np.float32) / 255.0, (5, 5), 0)
alpha = np.expand_dims(alpha, axis=2)

# Proses pencampuran warna (blending):
# Area latar (alpha=1)   -> menjadi warna biru
# Area orang (alpha=0)   -> tetap gambar asli (baju, dasi, wajah, rambut)
# Area batas (0<alpha<1) -> transisi halus natural tanpa artefak
hasil = (foto.astype(np.float32) * (1.0 - alpha) + warna_biru * alpha).astype(np.uint8)

# Mengubah BGR ke RGB agar warna tampil benar di Matplotlib
hasil_rgb = cv2.cvtColor(hasil, cv2.COLOR_BGR2RGB)

# Menampilkan foto sebelum dan sesudah secara berdampingan
plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.imshow(foto_rgb)
plt.title("Sebelum (Latar Merah)")
plt.axis("off")

plt.subplot(1, 2, 2)
plt.imshow(hasil_rgb)
plt.title("Sesudah (Latar Biru Sempurna)")
plt.axis("off")

plt.tight_layout()
plt.show()


# %% Cell 6 - Menyimpan Hasil
# Fungsi : Menyimpan hasil pengolahan sebagai bukti untuk laporan.
# (Pengganti files.download() milik Colab: hasil disimpan ke folder
# "hasil" di dalam folder program.)

# Membuat folder "hasil" jika belum ada
folder_hasil = os.path.join(folder_program, "hasil")
os.makedirs(folder_hasil, exist_ok=True)

lokasi_mask = os.path.join(folder_hasil, "hasil_mask.png")
lokasi_hasil = os.path.join(folder_hasil, "hasil_latar_biru.jpg")

# Menyimpan gambar mask dan gambar hasil
berhasil_mask = cv2.imwrite(lokasi_mask, mask)
berhasil_hasil = cv2.imwrite(lokasi_hasil, hasil)

if berhasil_mask and berhasil_hasil:
    print("Hasil berhasil disimpan di folder:", folder_hasil)
else:
    print("Hasil gagal disimpan. Periksa lokasi folder program.")