from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import ttest_rel


input_file = Path("results/raw/benchmark_results.csv")

output_dir = Path("results")
figure_dir = output_dir / "figures"

figure_dir.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(input_file)

df["is_warmup"] = (
    df["is_warmup"]
    .astype(str)
    .str.lower()
    .map({"true": True, "false": False})
)

# Tahap 1: keluarkan dua percobaan pemanasan.
measured = df[df["is_warmup"] == False].copy()

if measured.empty:
    raise ValueError("Tidak ada data pengukuran setelah warm-up dihapus.")

# Tahap 2: cek jumlah baris hasil kedua database.
row_check = measured.pivot_table(
    index=["query_type", "attempt"],
    columns="db",
    values="rows",
    aggfunc="first",
)

if "PostgreSQL" in row_check.columns and "MongoDB" in row_check.columns:
    row_check["same_rows"] = (
        row_check["PostgreSQL"] == row_check["MongoDB"]
    )
    row_check.to_csv(output_dir / "row_count_check.csv")

    print("\n=== Pemeriksaan jumlah baris ===")
    print(row_check)

# Tahap 3: statistik deskriptif.
summary = (
    measured.groupby(["query_type", "db"])["time_ms"]
    .agg(
        mean_ms="mean",
        median_ms="median",
        std_ms="std",
        count="count",
    )
    .reset_index()
)

summary.to_csv(
    output_dir / "descriptive_statistics.csv",
    index=False,
)

print("\n=== Statistik deskriptif ===")
print(summary.to_string(index=False))

# Tahap 4: buat grafik rata-rata waktu eksekusi.
mean_table = summary.pivot(
    index="query_type",
    columns="db",
    values="mean_ms",
)

ax = mean_table.plot(kind="bar")

ax.set_title("Rata-rata Waktu Eksekusi Query")
ax.set_xlabel("Jenis query")
ax.set_ylabel("Waktu eksekusi (ms)")
ax.legend(title="Database")

plt.tight_layout()
plt.savefig(
    figure_dir / "mean_query_times.png",
    dpi=200,
    bbox_inches="tight",
)
plt.close()

# Tahap 5: paired t-test dan Cohen's dz.
test_results = []

for query_type in sorted(measured["query_type"].unique()):
    subset = measured[
        measured["query_type"] == query_type
    ]

    paired = subset.pivot(
        index="attempt",
        columns="db",
        values="time_ms",
    ).dropna()

    if not {"PostgreSQL", "MongoDB"}.issubset(paired.columns):
        continue

    pg = paired["PostgreSQL"]
    mongo = paired["MongoDB"]

    differences = pg - mongo

    t_stat, p_value = ttest_rel(pg, mongo)

    diff_std = differences.std(ddof=1)
    if diff_std == 0 or pd.isna(diff_std):
        cohen_dz = None
    else:
        cohen_dz = differences.mean() / diff_std

    pg_mean = pg.mean()
    mongo_mean = mongo.mean()

    speed_ratio = (
        mongo_mean / pg_mean
        if pg_mean > 0
        else None
    )

    test_results.append({
        "query_type": query_type,
        "n_pairs": len(paired),
        "mean_postgresql_ms": pg_mean,
        "mean_mongodb_ms": mongo_mean,
        "mongodb_divided_by_postgresql": speed_ratio,
        "t_statistic": t_stat,
        "p_value": p_value,
        "cohen_dz": cohen_dz,
    })

tests = pd.DataFrame(test_results)

tests.to_csv(
    output_dir / "paired_ttest_results.csv",
    index=False,
)

print("\n=== Hasil pengujian statistik ===")
print(tests.to_string(index=False))

print("\nAnalisis selesai.")
print("Tabel dan grafik tersimpan di folder results.")