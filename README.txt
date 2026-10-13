# Replikasi Parsial Eksperimen PostgreSQL dan MongoDB

## 1. Deskripsi Proyek

Repository ini berisi implementasi eksperimen untuk melakukan replikasi parsial terhadap penelitian berjudul **“Comparative Read Performance Analysis of PostgreSQL and MongoDB in E-Commerce: An Empirical Study of Filtering and Analytical Queries”** oleh Urnikienė et al. (2026).

Eksperimen dilakukan untuk membandingkan performa pembacaan data (*read performance*) pada PostgreSQL dan MongoDB dalam konteks data e-commerce. Pengujian lokal berfokus pada dua query, yaitu `select_test2` dan `select_test4`, sebagai bagian dari adaptasi Stage I penelitian asli.

Eksperimen ini tidak dimaksudkan untuk mereplikasi seluruh penelitian asli. Hasil yang diperoleh menggambarkan performa kedua sistem pada dataset, konfigurasi, dan lingkungan lokal yang digunakan.

## 2. Tujuan

- Membandingkan waktu eksekusi query pembacaan data pada PostgreSQL dan MongoDB.
- Mengukur waktu eksekusi melalui beberapa pengulangan.
- Menganalisis hasil menggunakan statistik deskriptif dan paired t-test.
- Mengamati signifikansi statistik dari perbedaan waktu eksekusi pada eksperimen lokal.

## 3. Lingkup Eksperimen

Eksperimen lokal menggunakan dua query pengujian:

| Query | Hasil PostgreSQL | Hasil MongoDB |
|---|---:|---:|
| `select_test2` | 36 baris | 36 dokumen |
| `select_test4` | 3.149 baris | 3.149 dokumen |

Setiap query dijalankan sebanyak 15 kali. Dua eksekusi pertama digunakan sebagai *warm-up* dan tidak dimasukkan ke dalam analisis, sehingga terdapat 13 pengukuran untuk setiap query pada masing-masing sistem.

Jumlah baris atau dokumen pada eksperimen lokal dapat berbeda dari penelitian asli karena dataset dan proses pembentukan data yang digunakan tidak sepenuhnya identik.

## 4. Kebutuhan Sistem

Perangkat lunak yang diperlukan:

- Windows
- Python 3
- PostgreSQL
- MongoDB
- Library Python yang tercantum dalam `requirements.txt`

Spesifikasi perangkat keras serta versi perangkat lunak yang digunakan untuk eksperimen dicatat dalam laporan penelitian.

## 5. Struktur Repository

```text
mahadata-postgresql-mongodb/
├── .gitignore
├── README.md
├── requirements.txt
└── scripts/
    ├── ecommerceDB_postgre.sql
    ├── generate_data_v4.py
    ├── benchmark.py
    ├── analyze_results.py
    └── results/
        ├── figures/
        │   └── mean_query_times.png
        └── raw/
            ├── benchmark_results.csv
            ├── descriptive_statistics.csv
            ├── paired_ttest_results.csv
            └── row_count_check.csv
```

## 6. Instalasi

### 6.1. Clone Repository

```bash
git clone https://github.com/157-Fadina/mahadata-postgresql-mongodb.git
cd mahadata-postgresql-mongodb
```

### 6.2. Buat Virtual Environment

```bash
python -m venv .venv
```

Aktifkan virtual environment pada Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 6.3. Instal Dependensi

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 7. Persiapan Basis Data

Sebelum menjalankan eksperimen:

1. Pastikan server PostgreSQL dan MongoDB telah berjalan.
2. Siapkan skema serta data PostgreSQL menggunakan berkas SQL dan/atau skrip yang tersedia, sesuai prosedur yang digunakan oleh eksperimen.
3. Siapkan data MongoDB melalui skrip pembentukan data apabila memang diperlukan.
4. Periksa konfigurasi koneksi database pada skrip sebelum menjalankan pengujian.
5. Pastikan data dan struktur kedua database sudah sesuai dengan kebutuhan query.

Sesuaikan konfigurasi koneksi berdasarkan lingkungan lokal. Jangan mengunggah kata sandi, kredensial, atau informasi rahasia ke repository publik.

## 8. Menjalankan Eksperimen

Setelah virtual environment aktif dan database siap, masuk ke direktori `scripts`:

```bash
cd scripts
```

Jalankan skrip sesuai dengan urutan yang diperlukan oleh implementasi:

```bash
python generate_data_v4.py
python benchmark.py
python analyze_results.py
```

Urutan di atas mengasumsikan `generate_data_v4.py` merupakan skrip persiapan data. Periksa isi skrip sebelum menjalankannya kembali, khususnya jika proses pembentukan data dapat menambahkan data duplikat atau mengubah data yang sudah tersedia.

Jika data telah disiapkan dan tidak perlu dibuat ulang, lanjutkan ke skrip benchmark sesuai prosedur eksperimen.

## 9. Hasil Eksperimen

Hasil benchmark, statistik deskriptif, hasil paired t-test, serta pemeriksaan jumlah data disimpan dalam folder `scripts/results/raw/`. Visualisasi hasil disimpan dalam folder `scripts/results/figures/`.

Berdasarkan hasil pengukuran lokal:

| Query | Rata-rata PostgreSQL | Rata-rata MongoDB |
|---|---:|---:|
| `select_test2` | 1,1674 ms | 4,3024 ms |
| `select_test4` | 18,9131 ms | 39,0006 ms |

Pada kedua query, rata-rata waktu eksekusi PostgreSQL lebih rendah daripada MongoDB dalam lingkungan pengujian lokal ini. Interpretasi hasil dibatasi pada query, dataset, konfigurasi, dan perangkat yang digunakan, sehingga tidak dapat langsung digeneralisasi untuk seluruh beban kerja basis data.

## 10. Referensi

Urnikienė, et al. (2026). *Comparative Read Performance Analysis of PostgreSQL and MongoDB in E-Commerce: An Empirical Study of Filtering and Analytical Queries*. Big Data and Cognitive Computing, 10(2), Article 66.

DOI: https://doi.org/10.3390/bdcc10020066
