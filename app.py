import numpy as np
import pandas as pd
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

 # Mengubah angka format Indonesia "6.241,89" menjadi float.
def _angka(teks):
    return float(str(teks).replace(".", "").replace(",", "."))

# Mengubah volume "23,85B" menjadi angka dalam miliar.
def _volume(teks):
    if pd.isna(teks): # Volume kosong dikembalikan sebagai NaN.
        return np.nan
    teks = str(teks).strip().upper()
    kali = {"B": 1.0, "M": 1e-3, "K": 1e-6} # Faktor pengali satuan volume.
    return _angka(teks[:-1]) * kali.get(teks[-1], 1.0)


# Mengubah persen "-0,90%" menjadi float -0.9.
def _persen(teks):
    return float(str(teks).replace("%", "").replace(",", "."))

# Membaca CSV dan mengubah semua kolom menjadi angka.
def muat_data():
    data = pd.read_csv("data/ihsg_daily.csv")
    data.columns = ["tanggal", "close", "open", "high", "low", "volume", "perubahan"]  # Menyamakan nama kolom.
    for kolom in ["close", "open", "high", "low"]:  # Mengubah empat kolom harga menjadi float.
        data[kolom] = data[kolom].map(_angka)
    data["perubahan"] = data["perubahan"].map(_persen)  # Mengubah kolom persen menjadi float.
    data["volume"] = data["volume"].map(_volume)  # Mengubah kolom volume menjadi miliar.
    data["tanggal"] = pd.to_datetime(data["tanggal"], format="%d/%m/%Y")  # Mengubah tanggal menjadi datetime.
    data = data.sort_values("tanggal").reset_index(drop=True)  # Mengurutkan data dari terlama ke terbaru.
    data["ma20"] = data["close"].rolling(20).mean()  # Menghitung rata-rata bergerak 20 hari.
    data["ma50"] = data["close"].rolling(50).mean()  # Menghitung rata-rata bergerak 50 hari.
    return data

# Memuat data sekali saat aplikasi dijalankan.
df = muat_data() 

# Peta pilihan periode ke jumlah tahun.
periode_tahun = {"1y": 1, "3y": 3, "5y": 5, "all": None}

# Memfilter data sesuai query ?periode=.
def filter_data():
    periode = request.args.get("periode", "5y") # Mengambil periode dengan default 5 tahun.
    if periode not in periode_tahun: # Periode tidak dikenal dikembalikan ke default.
        periode = "5y"
    tahun = periode_tahun[periode]
    if tahun is None: # Nilai "all" berarti tanpa filter.
        return df
    batas = df["tanggal"].max() - pd.DateOffset(years=tahun) # Menghitung batas awal periode.
    return df[df["tanggal"] >= batas]

# Mengubah Series menjadi list JSON dengan NaN sebagai null.
def _list(nilai, desimal=2):
    hasil = []
    for v in nilai:
        if pd.isna(v): # Nilai kosong seperti MA di awal data menjadi None.
            hasil.append(None)
        else:
            hasil.append(round(float(v), desimal)) # Angka dibulatkan sesuai jumlah desimal.
    return hasil

# Menampilkan halaman dashboard.
@app.route("/")
def dashboard():
    return render_template("dashboard.html")

# Mengirim angka ringkasan untuk kartu statistik.
@app.route("/api/ringkasan")
def ringkasan():
    data = filter_data()
    return jsonify(
        hari=int(len(data)), # Jumlah hari bursa dalam periode.
        close=round(float(data["close"].iloc[-1]), 2), # Harga penutupan terakhir.
        perubahan_harian=round(float(data["perubahan"].iloc[-1]), 2), # Perubahan harian terakhir.
        return_periode=round( # Return dari awal sampai akhir periode.
            float((data["close"].iloc[-1] / data["close"].iloc[0] - 1) * 100), 2
        ),
        volume_rata=round(float(data["volume"].mean()), 2), # Rata-rata volume dalam miliar.
    )

# Mengirim deret close, MA20, dan MA50.
@app.route("/api/tren-harga")
def tren_harga():
    data = filter_data()
    return jsonify(
        labels=data["tanggal"].dt.strftime("%Y-%m-%d").tolist(), # Label tanggal untuk sumbu X.
        close=_list(data["close"]),
        ma20=_list(data["ma20"]),
        ma50=_list(data["ma50"]),
    )

@app.route("/api/distribusi-arah")
def distribusi_arah(): # Menghitung jumlah hari naik, turun, dan stagnan.
    data = filter_data()["perubahan"]
    hasil = pd.Series(
        {
            "Naik": int((data > 0).sum()),
            "Turun": int((data < 0).sum()),
            "Stagnan": int((data == 0).sum()),
        }
    )
    return jsonify(labels=hasil.index.tolist(), data=hasil.tolist())

@app.route("/api/return-tahunan")
def return_tahunan(): # Menghitung return penutupan setiap tahun.
    penutupan = df.set_index("tanggal")["close"].resample("YE").last() # Close terakhir setiap tahun.
    hasil = (penutupan / penutupan.shift(1) - 1) * 100 # Return dibanding tahun sebelumnya.
    hasil.iloc[0] = (penutupan.iloc[0] / df["close"].iloc[0] - 1) * 100 # Tahun pertama dibanding close awal data.
    hasil.index = hasil.index.year # Index diubah menjadi tahun.
    tahun_awal = filter_data()["tanggal"].min().year # Tahun awal mengikuti filter periode.
    hasil = hasil[hasil.index >= tahun_awal]
    return jsonify(labels=[str(t) for t in hasil.index], data=_list(hasil))


if __name__ == "__main__":
    app.run(debug=True)
