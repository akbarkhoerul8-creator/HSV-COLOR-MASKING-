# Laporan Eksperimen & Uji Coba: Segmentasi HSV Color Masking
**Topik:** Penggantian Latar Belakang Citra Digital (Studi Kasus Pas Foto Formal Siswa Berdasi Merah)  
**Mata Kuliah / Bidang:** Pengolahan Citra Digital (PCD)  
**Lingkungan:** Python 3.10, OpenCV, NumPy, Matplotlib  
**File Citra Uji:** `foto_merah.jpg` (Resolusi: 736 x 1104 piksel)  
**Folder Hasil Eksperimen:** `hasil/laporan_uji_coba/`

---

## 1. Pendahuluan & Latar Belakang Masalah

Dalam pengolahan citra digital, manipulasi warna latar belakang (*background replacement*) pas foto formal studio sering kali menggunakan ruang warna **HSV (Hue, Saturation, Value)** karena komponen warna (*Hue*) terpisah dari intensitas pencahayaan (*Value*).

Namun, pada implementasi praktis pas foto resmi (seperti foto siswa sekolah), muncul tantangan kritis:
1. **Objek *foreground* memiliki warna yang sama dengan latar belakang**: Siswa mengenakan seragam putih dengan **dasi merah** dan **lencana bendera merah-putih**.
2. **Bagian tubuh memiliki rona kemerahan**: Bibir dan area tipis kulit memiliki nilai rona (*Hue*) kemerahan yang mendekati latar belakang.

Eksperimen ini mendokumentasikan proses pengujian berulang (*iterative testing*) dari metode awal yang cacat (*imperfect*) hingga perancangan metode penyempurnaan berbasis **Konektivitas Spasial (Connected Components Analysis)** dan **Alpha Blending (Feathering)** yang menghasilkan segmentasi sempurna.

---

## 2. Profil Data Citra & Analisis Nilai HSV Tiap Region

Pengujian dilakukan pada citra pas foto siswa berlatar belakang merah studio dengan resolusi **$736 \times 1104$ piksel**.

Berikut adalah data pengukuran spektrum warna HSV pada berbagai region citra asli:

| Region Objek | Hue ($H$) (0-179) | Saturation ($S$) (0-255) | Value ($V$) (0-255) | Karakteristik Spektrum |
| :--- | :---: | :---: | :---: | :--- |
| **Latar Belakang Merah Studio** | $177 - 178$ | $206 - 220$ (Rata-rata $213$) | $195 - 208$ (Rata-rata $201$) | Merah murni pekat, saturasi tinggi, terang merata |
| **Dasi Merah Siswa (SD)** | **$178 - 179$** | **$160 - 188$** (Rata-rata $171$) | **$175 - 206$** (Rata-rata $194$) | **Nilai HSV tumpang tindih (*overlap*) dengan latar belakang!** |
| **Lencana Bendera Merah Putih** | $175 - 179$ | $150 - 210$ | $160 - 210$ | Merah bendera, saturasi tinggi di atas saku putih |
| **Bibir Siswa** | $0 - 8$ | $100 - 145$ | $140 - 190$ | Merah jingga/pink, saturasi sedang hingga tinggi |
| **Kulit Wajah & Dahi** | $5 - 15$ | $30 - 100$ | $120 - 220$ | Rona kulit normal, saturasi rendah ke sedang |
| **Daun Telinga (Translusen)** | $4 - 10$ | $90 - 125$ | $45 - 180$ | Rona kemerahan akibat pencahayaan tembus |
| **Kemeja Putih** | $0 - 180$ | $0 - 25$ | $180 - 235$ | Netral (hampir tanpa saturasi), intensitas tinggi |

> **Temuan Kritis Penelitian:**  
> Dasi merah seragam memiliki nilai Hue ($H \approx 178$) dan Saturation ($S > 160$) yang berada **persis di dalam rentang latar belakang**. Oleh karena itu, **secara teoritis tidak ada kombinasi batas ambang warna (*threshold*) HSV murni yang mampu memisahkan dasi dari latar belakang tanpa memotong dasi tersebut.** Diperlukan pendekatan berbasis lokasi/spasial.

---

## 3. Dokumentasi Hasil Uji Coba Berdasarkan Tahapan Iterasi

*Catatan: File citra visual uji coba tiap tahap tersimpan di folder `hasil/laporan_uji_coba/`:*
- `1_foto_asli.jpg`
- `2_iterasi_1_bocor_kulit.jpg`
- `3_iterasi_2_dasi_bibir_biru.jpg` (Hasil tangkapan layar awal)
- `4_iterasi_3_sempurna.jpg` (Hasil sempurna terkini)
- `komparasi_3_tahap.jpg` (Visualisasi perbandingan ketiga tahap)

---

### Tahap 1: Pengujian Ambang Batas Global Rendah ($S \ge 50$)
*Metode: Thresholding HSV Naif / Konvensional*

* **Parameter Kode:**
  ```python
  # Rentang 1 (Hue 0-10)
  batas1_bawah = np.array([0, 50, 50])
  batas1_atas  = np.array([10, 255, 255])
  # Rentang 2 (Hue 170-179)
  batas2_bawah = np.array([170, 50, 50])
  batas2_atas  = np.array([179, 255, 255])
  hasil[mask > 0] = [255, 0, 0] # Biru murni BGR
  ```
* **Hasil Pengamatan:**
  - Latar belakang berubah menjadi biru.
  - **Kegagalan Total (*Catastrophic Failure*):** Seluruh wajah siswa (dahi, pipi, hidung, dagu), bibir, seluruh dasi, dan lencana baju terdeteksi sebagai latar belakang dan berubah menjadi bercak-bercak biru besar.
* **Penyebab Kegagalan:**
  - Batas bawah saturasi $S = 50$ terlalu rendah. Kulit wajah manusia memiliki saturasi antara $30 - 100$, sehingga hampir separuh wajah ikut terdeteksi mask merah.

---

### Tahap 2: Peningkatan Batas Bawah Saturasi ($S \ge 130$) & Morfologi Kasar
*(Kondisi Program Sebelum Diperbaiki - Tangkapan Layar Pengguna)*

* **Parameter Kode:**
  ```python
  # Rentang 1 (Hue 0-10)
  batas1_bawah = np.array([0, 130, 50])
  batas1_atas  = np.array([10, 255, 255])
  # Rentang 2 (Hue 170-179)
  batas2_bawah = np.array([170, 130, 50])
  batas2_atas  = np.array([179, 255, 255])
  
  # Pembersihan morfologi kasar
  kernel = np.ones((7, 7), np.uint8)
  mask = cv2.erode(mask, kernel, iterations=1)
  mask = cv2.dilate(mask, kernel, iterations=2)
  
  hasil[mask > 0] = [255, 0, 0]
  ```
* **Hasil Pengamatan (Cacat yang Ditemukan):**
  1. **Dasi Merah berubah menjadi biru 100%:** Seluruh badan dasi SD berubah menjadi biru solid, hanya menyisakan lambang Tut Wuri Handayani di ujung bawah.
  2. **Bibir Berwarna Biru:** Area tengah bibir terdeteksi sebagai latar dan berubah warna menjadi biru karena saturasi bibir mencapai $140$.
  3. **Bercak Biru di Dahi & Alis:** Terdapat titik biru di pelipis/dahi sebelah kiri.
  4. **Lencana Saku Terpotong:** Bagian merah pada lencana bendera ikut berubah jadi biru.
  5. **Tepian Rambut & Bahu Kaku / Bergerigi:** Efek dilatasi $2\times$ dengan kernel persegi $7 \times 7$ memperlebar mask sebanyak 14 piksel ke dalam siluet orang, memakan rambut dan bahu.
  6. **Warna Biru Flat / Tidak Natural:** Penggunaan `[255, 0, 0]` (Biru 100%) menghasilkan kontras yang sangat kaku dan tidak realistis layaknya foto studio.

---

### Tahap 3: Penggabungan *Connected Components* + Pengetatan Rentang HSV + *Alpha Blending*
*(Metode Sempurna - Implementasi Terbaru)*

* **Inovasi & Formulasi Solusi:**
  1. **Analisis Konektivitas Spasial (`cv2.connectedComponentsWithStats`):**
     - Memisahkan pulau piksel (*pixel islands*).
     - Menetapkan aturan topologi: Latar belakang adalah komponen merah yang **terhubung ke tepi atas gambar ($y=0$) atau tepi samping atas**.
     - Dasi, bibir, dan lencana yang terisolasi di dalam kemeja putih secara otomatis **dikeluarkan dari mask latar belakang**.
  2. **Pengetatan Rentang Hue & Saturasi Kulit:**
     - Rentang utama fokus pada $H \in [165, 179]$ (merah background).
     - Rentang merah jingga dibatasi $H \in [0, 8]$ dengan syarat $S \ge 160$ dan $V \ge 70$. Rona bibir ($S \le 145$) tidak akan pernah terpicu.
  3. **Morfologi Presisi:**
     - Menggunakan kernel elips $3 \times 3$ untuk `cv2.MORPH_OPEN` (menghilangkan debu piksel) dan `cv2.MORPH_CLOSE` (menutup lubang mikro).
  4. **Alpha Blending / Feathering:**
     - Mengubah mask biner menjadi peta transparansi bergradasi halus menggunakan *Gaussian Blur* ($5 \times 5$):
       $$\text{Output}(x, y) = \text{FotoAsli}(x, y) \cdot (1 - \alpha) + \text{WarnaBiru} \cdot \alpha$$
  5. **Warna Standar Studio Pas Foto:**
     - Menggunakan BGR `[215, 80, 0]` (Biru Royal Pas Foto Formal) yang harmonis dan alami.

* **Hasil Pengamatan (Sempurna):**
  - **Dasi merah utuh 100%:** Tekstur kain merah dan bordir emas lambang Tut Wuri Handayani terjaga sempurna.
  - **Bibir alami 100%:** Rona bibir asli tetap utuh tanpa bercak biru.
  - **Lencana bendera merah putih utuh:** Warna merah bendera tetap merah cerah.
  - **Tepian rambut dan bahu sangat halus:** Bebas dari gerigi (*aliasing*) dan tidak ada garis merah (*color fringing*).

---

## 4. Tabel Matriks Perbandingan Uji Coba

| Parameter / Evaluasi | Iterasi 1 (Naif Global) | Iterasi 2 (Screenshot Awal) | Iterasi 3 (Hasil Sempurna) |
| :--- | :---: | :---: | :---: |
| **Batas Bawah Saturasi ($S_{min}$)** | $50$ | $130$ | Rentang 1: $160$, Rentang 2: $120$ |
| **Operasi Morfologi** | Tidak ada | Kernel Kotak $7 \times 7$ (Erode 1, Dilate 2) | Kernel Elips $3 \times 3$ (Open & Close) |
| **Metode Segmentasi** | *Pixel-wise threshold* | *Pixel-wise threshold* | **Spasial *Connected Components*** |
| **Teknik Pewarnaan** | Boolean indexing `mask > 0` | Boolean indexing `mask > 0` | **Soft Alpha Blending ($5 \times 5$)** |
| **Dasi Merah Siswa** | Berubah Biru (Cacat) | Berubah Biru (Cacat) | **Terlindungi 100% (Sempurna)** |
| **Bibir Siswa** | Berubah Biru (Cacat) | Berubah Biru Sebagian (Cacat) | **Terlindungi 100% (Sempurna)** |
| **Kulit Wajah & Dahi** | Bocor Parah (Cacat) | Bercak Biru di Dahi (Cacat) | **Bersih Total 100% (Sempurna)** |
| **Lencana Saku Baju** | Berubah Biru (Cacat) | Berubah Biru (Cacat) | **Terlindungi 100% (Sempurna)** |
| **Kerapian Tepi Rambut** | Kasar & Kotor | Kaku & Terpotong Kasar | **Sangat Halus & Alami** |
| **Karakter Warna Biru** | Biru Neon `[255, 0, 0]` | Biru Neon `[255, 0, 0]` | **Biru Royal Studio `[215, 80, 0]`** |

---

## 5. Perbandingan Kode Sumber (Diff Analysis)

### Kode Lama (Penyebab Cacat pada Iterasi 2):
```python
# HANYA mengandalkan batas warna (pasti gagal pada dasi merah)
batas1_bawah = np.array([0, 130, 50])
batas1_atas  = np.array([10, 255, 255])
batas2_bawah = np.array([170, 130, 50])
batas2_atas  = np.array([179, 255, 255])

mask = cv2.bitwise_or(cv2.inRange(hsv, batas1_bawah, batas1_atas),
                      cv2.inRange(hsv, batas2_bawah, batas2_atas))

# Morfologi kasar yang merusak tepi
kernel = np.ones((7, 7), np.uint8)
mask = cv2.erode(mask, kernel, iterations=1)
mask = cv2.dilate(mask, kernel, iterations=2)

# Pewarnaan keras (jagged edges)
hasil[mask > 0] = [255, 0, 0]
```

### Kode Baru (Solusi Sempurna pada Iterasi 3):
```python
# 1. Pengetatan HSV (Cegah bocor ke bibir & kulit)
batas1_bawah = np.array([0, 160, 70])
batas1_atas  = np.array([8, 255, 255])
batas2_bawah = np.array([165, 120, 50])
batas2_atas  = np.array([179, 255, 255])

mask_merah = cv2.bitwise_or(cv2.inRange(hsv, batas1_bawah, batas1_atas),
                            cv2.inRange(hsv, batas2_bawah, batas2_atas))

# 2. Morfologi halus
kernel_bersih = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
mask_clean = cv2.morphologyEx(mask_merah, cv2.MORPH_OPEN, kernel_bersih)
mask_clean = cv2.morphologyEx(mask_clean, cv2.MORPH_CLOSE, kernel_bersih)

# 3. Analisis Konektivitas Spasial (HANYA pilih yang menyentuh batas luar latar)
num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask_clean)
mask = np.zeros((h, w), dtype=np.uint8)
for i in range(1, num_labels):
    is_top   = np.any(labels[0, :] == i)
    is_left  = np.any(labels[:int(h * 0.6), 0] == i)
    is_right = np.any(labels[:int(h * 0.6), w - 1] == i)
    if (is_top or is_left or is_right) and stats[i, cv2.CC_STAT_AREA] > 1000:
        mask[labels == i] = 255

# 4. Alpha Blending (Transisi tepi halus bebas halo merah)
alpha = cv2.GaussianBlur(mask.astype(np.float32) / 255.0, (5, 5), 0)
alpha = np.expand_dims(alpha, axis=2)
warna_biru = np.array([215, 80, 0], dtype=np.float32) # Biru Studio Formal
hasil = (foto.astype(np.float32) * (1.0 - alpha) + warna_biru * alpha).astype(np.uint8)
```

---

## 6. Kesimpulan untuk Laporan Praktikum / Skripsi

1. **Keterbatasan Ruang Warna HSV:** Ruang warna HSV sangat baik untuk mendeteksi warna tertentu yang homogen, namun memiliki keterbatasan mendasar saat objek latar depan (*foreground*) dan latar belakang (*background*) memiliki kesamaan rona (*Hue*) dan saturasi (*Saturation*), seperti pada kasus seragam berdasi merah.
2. **Pentingnya Informasi Spasial:** Informasi warna piksel harus dikombinasikan dengan **informasi spasial/topologi** (*Connected Components Analysis*). Dengan memanfaatkan asumsi bahwa latar belakang pas foto terhubung dengan batas luar kanvas, objek merah yang berada di dalam siluet tubuh dapat diproteksi secara deterministik.
3. **Penyempurnaan Tepi Citra:** Penggantian warna latar belakang berbasis biner (*hard assignment*) selalu menimbulkan artefak tepi bergerigi dan *color bleeding*. Penerapan **Alpha Blending** dengan perataan Gaussian pada tepi mask terbukti secara signifikan meningkatkan kualitas visual dan realisme hasil akhir pas foto.
