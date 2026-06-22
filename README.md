# Analisis Performa E-Commerce \& Dashboard

Proyek ini merupakan analisis data *end-to-end* menggunakan Olist Brazilian E-Commerce Public Dataset. Di dalamnya mencakup tahap *data wrangling*, *exploratory data analysis* (EDA), segmentasi pelanggan dengan metode RFM (Recency, Frequency, Monetary), serta pembuatan dashboard interaktif menggunakan Streamlit.

## Pertanyaan Bisnis

1. **Performa Produk:** Kategori produk apa yang menghasilkan total pendapatan (*revenue*) tertinggi sepanjang tahun 2018?
2. **Segmentasi Pelanggan (RFM):** Bagaimana pembagian segmen pelanggan (seperti *Best Customers*, *Loyal*, *At Risk*, *Hibernating*) berdasarkan nilai *Recency*, *Frequency*, dan *Monetary* pada data 12 bulan terakhir?

## Struktur Proyek



├── data/                                   # Folder untuk menyimpan file CSV mentah
│   ├── customers\_dataset.csv
│   ├── orders\_dataset.csv
│   ├── order\_items\_dataset.csv
│   ├── order\_payments\_dataset.csv
│   ├── products\_dataset.csv
│   └── product\_category\_name\_translation.csv
├── dashboard/
│   ├── dashboard.py                        # Script utama dashboard Streamlit
│   └── main\_data.csv                       # Data bersih hasil ekspor dari notebook
├── ecommerce\_analysis.ipynb                # Notebook analisis utama (Tahap 1-3)
├── requirements.txt                        # Daftar library/dependencies proyek
└── README.md

