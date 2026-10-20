"""Unduh harga saham IDX dari Yahoo Finance, dengan cache untuk mode offline."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

BENCHMARK = "^JKSE"

# Ticker likuid yang mewakili sektor utama IDX. ^JKSE dipakai sebagai benchmark.
UNIVERSE: dict[str, str] = {
    "^JKSE": "IHSG (indeks gabungan)",
    "BBCA.JK": "Bank Central Asia",
    "BBRI.JK": "Bank Rakyat Indonesia",
    "BMRI.JK": "Bank Mandiri",
    "BBNI.JK": "Bank Negara Indonesia",
    "TLKM.JK": "Telkom Indonesia",
    "ASII.JK": "Astra International",
    "UNTR.JK": "United Tractors",
    "UNVR.JK": "Unilever Indonesia",
    "ICBP.JK": "Indofood CBP",
    "INDF.JK": "Indofood Sukses Makmur",
    "AMRT.JK": "Sumber Alfaria Trijaya",
    "CPIN.JK": "Charoen Pokphand Indonesia",
    "KLBF.JK": "Kalbe Farma",
    "SMGR.JK": "Semen Indonesia",
    "ANTM.JK": "Aneka Tambang",
    "MDKA.JK": "Merdeka Copper Gold",
    "ADRO.JK": "Adaro Energy",
    "PTBA.JK": "Bukit Asam",
    "EXCL.JK": "XL Axiata",
    "ISAT.JK": "Indosat",
    "GOTO.JK": "GoTo Gojek Tokopedia",
    "ARTO.JK": "Bank Jago",
}


def unduh(tickers: list[str], periode: str = "5y") -> pd.DataFrame:
    """Ambil harga penutupan yang sudah disesuaikan (auto_adjust=True)."""
    import yfinance as yf

    data = yf.download(
        tickers, period=periode, interval="1d",
        auto_adjust=True, progress=False, threads=True,
    )
    if data.empty:
        raise RuntimeError("Yahoo Finance tidak mengembalikan data")

    if isinstance(data.columns, pd.MultiIndex):
        close = data["Close"]
    else:  # satu ticker saja
        close = data[["Close"]].rename(columns={"Close": tickers[0]})
    close = close.dropna(how="all").sort_index()
    close.index = pd.to_datetime(close.index).tz_localize(None)
    return close


def ambil_harga(
    periode: str = "5y",
    cache: Path | None = None,
    segarkan: bool = False,
) -> tuple[pd.DataFrame, str]:
    """Coba jaringan dulu, jatuh ke cache kalau gagal. Kembalikan (data, sumber)."""
    if cache is not None and cache.exists() and not segarkan:
        harga = pd.read_csv(cache, index_col=0, parse_dates=True)
        return harga, "cache"

    try:
        harga = unduh(list(UNIVERSE), periode=periode)
        if cache is not None:
            cache.parent.mkdir(parents=True, exist_ok=True)
            harga.to_csv(cache)
        return harga, "yahoo"
    except Exception as exc:  # noqa: BLE001
        if cache is not None and cache.exists():
            harga = pd.read_csv(cache, index_col=0, parse_dates=True)
            print(f"[peringatan] unduh gagal ({exc}), memakai cache {cache.name}")
            return harga, "cache"
        raise
