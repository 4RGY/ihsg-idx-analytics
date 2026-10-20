"""CLI analitik IDX."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import analysis, charts, fetch, report

AKAR = Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analitik risiko dan imbal hasil IHSG / saham IDX")
    parser.add_argument("--periode", default="5y", help="periode Yahoo Finance, mis. 3y, 5y, 10y")
    parser.add_argument("--rf", type=float, default=0.0575, help="aset bebas risiko tahunan")
    parser.add_argument("--outdir", type=Path, default=AKAR / "outputs")
    parser.add_argument("--cache", type=Path, default=AKAR / "data" / "harga.csv")
    parser.add_argument("--segarkan", action="store_true", help="paksa unduh ulang dari Yahoo")
    args = parser.parse_args(argv)

    print(f"[1/4] ambil harga {len(fetch.UNIVERSE)} ticker ({args.periode}) ...")
    harga, sumber = fetch.ambil_harga(args.periode, cache=args.cache, segarkan=args.segarkan)
    print(f"      sumber: {sumber}, {harga.shape[0]} baris x {harga.shape[1]} ticker")

    print("[2/4] hitung metrik ...")
    tabel = analysis.tabel_metrik(harga, rf=args.rf)
    pasar = analysis.ringkasan_pasar(harga)
    musiman = analysis.musiman(harga)
    matriks = analysis.korelasi(harga, n=10, berdasarkan=tabel)

    args.outdir.mkdir(parents=True, exist_ok=True)
    tabel.to_csv(args.outdir / "metrik.csv", index=False)
    matriks.to_csv(args.outdir / "korelasi.csv")
    musiman.to_csv(args.outdir / "musiman.csv", index=False)

    print("[3/4] gambar ...")
    for path in charts.buat_semua(harga, tabel, musiman, args.outdir / "figures"):
        print(f"      {path.relative_to(args.outdir)}")

    print("[4/4] tulis laporan ...")
    report.tulis_laporan(tabel, musiman, pasar, matriks, sumber, args.outdir / "laporan.md", args.rf)
    (args.outdir / "ringkasan.json").write_text(
        json.dumps({
            "sumber": sumber,
            "rf": args.rf,
            "periode": f"{pasar['tanggal_mulai']:%Y-%m-%d}..{pasar['tanggal_terakhir']:%Y-%m-%d}",
            "ihsg": {k: (str(v) if not isinstance(v, (int, float)) else v)
                     for k, v in pasar.items()},
            "saham_dianalisis": int(len(tabel) - 1),
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    teratas = tabel[tabel["ticker"] != "JKSE"].head(3)
    print("\n== ringkas ==")
    print(f"IHSG        : {pasar['level_terakhir']:,.2f} | CAGR {pasar['ret_tahunan']:.1%} "
          f"| vol {pasar['volatilitas']:.1%} | maxDD {pasar['max_drawdown']:.1%}")
    print("Sharpe top  : " + ", ".join(
        f"{r['ticker']} {r['sharpe']:.2f}" for _, r in teratas.iterrows()))
    print(f"laporan     : {args.outdir / 'laporan.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
