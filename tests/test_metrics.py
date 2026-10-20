"""Tes metrik dengan deret sintetis, tanpa jaringan."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from idx_analytics import metrics


def seri(nilai: list[float]) -> pd.Series:
    idx = pd.date_range("2024-01-01", periods=len(nilai), freq="D")
    return pd.Series(nilai, index=idx, dtype=float)


def test_imbal_hasil_harian_dan_kumulatif():
    harga = seri([100, 110, 99, 108.9])
    ret = metrics.imbal_hasil_harian(harga)
    assert len(ret) == 3
    assert ret.iloc[0] == pytest.approx(0.10)
    assert metrics.kurva_ekuitas(ret).iloc[-1] == pytest.approx(1.10 * 0.90 * 1.10)


def test_imbal_hasil_tahunan_geometrik():
    # naik 1% setiap hari selama 252 hari bursa -> (1,01^252) - 1
    harian = [1.01 ** i for i in range(253)]
    ret = metrics.imbal_hasil_harian(pd.Series(harian, dtype=float))
    assert metrics.imbal_hasil_tahunan(ret) == pytest.approx(1.01 ** 252 - 1.0, rel=1e-6)


def test_max_drawdown_negatif():
    harga = seri([100, 120, 90, 110])
    ret = metrics.imbal_hasil_harian(harga)
    assert metrics.max_drawdown(ret) == pytest.approx(90 / 120 - 1.0)


def test_volatilitas_nol_saat_konstan():
    ret = pd.Series([0.0] * 30)
    assert metrics.volatilitas_tahunan(ret) == pytest.approx(0.0)
    assert np.isnan(metrics.sharpe(ret))


def test_beta_terhadap_dirinya_sendiri_satu():
    rng = np.random.default_rng(7)
    ret = pd.Series(rng.normal(0.0004, 0.012, 300))
    assert metrics.beta(ret, ret) == pytest.approx(1.0)


def test_beta_setengah_jika_bergerak_separuh():
    rng = np.random.default_rng(11)
    bench = pd.Series(rng.normal(0.0003, 0.01, 400))
    aset = bench * 0.5
    assert metrics.beta(aset, bench) == pytest.approx(0.5, rel=1e-6)


def test_var95_historis_positif():
    rng = np.random.default_rng(3)
    ret = pd.Series(rng.normal(0.0, 0.02, 2000))
    var = metrics.var_historis(ret, 0.95)
    assert 0.02 < var < 0.06


def test_sortino_tak_terdefinisi_tanpa_kerugian():
    ret = pd.Series([0.01] * 40)
    assert np.isnan(metrics.sortino(ret))


def test_sortino_positif_untuk_deret_menguntungkan():
    rng = np.random.default_rng(5)
    ret = pd.Series(rng.normal(0.002, 0.01, 500))
    assert metrics.sortino(ret) > 0


def test_kurva_drawdown_mulai_dari_nol():
    harga = seri([100, 101, 102])
    kurva = metrics.kurva_drawdown(harga)
    assert kurva.iloc[0] == pytest.approx(0.0)
    assert kurva.max() == pytest.approx(0.0)


def test_musiman_bulanan_menghitung_jumlah_bulan():
    idx = pd.bdate_range("2023-01-02", "2023-12-29")
    ret = pd.Series(0.001, index=idx)
    tabel = metrics.musiman_bulanan(ret)
    assert len(tabel) == 12
    assert tabel["rata_rata"].iloc[0] > 0
