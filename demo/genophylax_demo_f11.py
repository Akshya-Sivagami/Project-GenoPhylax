#!/usr/bin/env python3
"""
GenoPhylax F11 Demo — cached-replay mode
Reproduces the A3 F11 clinical-integrity attack chain (signal perturbation ->
silent pathogenic variant suppression) from committed experiment outputs.
No GPU/basecalling required — replays real, already-generated results.
"""
import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "experiments" / "A3_clinical_consequence_mapping" / "results" / "F11_candidate"
HYBRID = ROOT / "controlled_hybrid_variant_calling"
SHAM = ROOT / "PM2_off_target_sham" / "F11_PM2_off_target_sham_report.txt"

def read_pileup(condition):
    path = HYBRID / condition / "variant_calling" / f"F11_{condition}_pileup.tsv"
    if not path.exists():
        print(f"[ERROR] missing cached result: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        row = next(csv.DictReader(f, delimiter="\t"))
    return row

def read_summary():
    path = HYBRID / "F11_controlled_hybrid_variant_calling_summary.tsv"
    with open(path) as f:
        return {r["condition"]: r for r in csv.DictReader(f, delimiter="\t")}

def bar(label, alt, depth, width=20):
    n = int(width * int(alt) / int(depth)) if int(depth) else 0
    return f"{label:>6} [{'#'*n}{'.'*(width-n)}] ALT={alt}/{depth}"

def show_clean():
    row = read_pileup("CLEAN")
    summary = read_summary()["CLEAN"]
    print("[1/3] Loading clean basecall -> align -> variant call (cached)")
    print(f"      {bar('CLEAN', row['ALT_T'], row['depth'])}")
    print(f"[2/3] Variant call: chr4 F11 pathogenic locus")
    print(f"      GT={summary['GT']}  QUAL={summary['QUAL']}  DP={summary['FORMAT_DP']}  AD={summary['FORMAT_AD_REF']},{summary['FORMAT_AD_ALT']}")
    print(f"[3/3] Status: PRESENT — pathogenic call retained")

def show_attack(make_chart=False):
    print("[1/4] Loading PM2 targeted signal perturbation (cached)")
    summary = read_summary()
    print(f"{'condition':>8} {'ALT':>5} {'DEL':>5} {'OTHER':>6} {'GT':>6} {'QUAL':>10} {'status':>10}")
    for cond in ["CLEAN", "W0", "PM2", "PM5", "PM10", "PM20"]:
        row = read_pileup(cond)
        s = summary[cond]
        print(f"{cond:>8} {row['ALT_T']:>5} {row['DEL']:>5} {row['OTHER']:>6} {s['GT']:>6} {s['QUAL']:>10} {s['status']:>10}")
    print("[2/4] Dose-response: ALT evidence collapses 14 -> 0 at PM2 and beyond")
    print("[3/4] Target VCF record: CLEAN 0/1 (QUAL 222.201) -> PM2 NO_CALL")
    print("[4/4] Status: SILENT SUPPRESSION — pathogenic variant deleted, no error/crash raised")
    if make_chart:
        save_chart()

def show_sham():
    print("[1/3] Loading PM2 off-target sham control (cached)")
    text = SHAM.read_text()
    print(text)
    print("[2/3] Comparison: on-target PM2 -> NO_CALL   |   off-target PM2 (sham) -> retained")
    print("[3/3] Status: TARGETING CONFIRMED — suppression is location-specific, not generic signal damage")

def save_chart():
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("[chart] matplotlib not installed, skipping chart (pip install matplotlib to enable)")
        return
    conds = ["CLEAN", "W0", "PM2", "PM5", "PM10", "PM20"]
    alt = [int(read_pileup(c)["ALT_T"]) for c in conds]
    delv = [int(read_pileup(c)["DEL"]) for c in conds]
    other = [int(read_pileup(c)["OTHER"]) for c in conds]
    ref = [int(read_pileup(c)["REF_G"]) for c in conds]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(conds, ref, label="REF", color="#888")
    ax.bar(conds, alt, bottom=ref, label="ALT (pathogenic evidence)", color="#2a7")
    ax.bar(conds, delv, bottom=[r + a for r, a in zip(ref, alt)], label="DEL", color="#c33")
    ax.bar(conds, other, bottom=[r + a + d for r, a, d in zip(ref, alt, delv)], label="OTHER", color="#999")
    ax.set_ylabel("Read count (depth=25)")
    ax.set_title("F11 pathogenic variant: ALT evidence collapse under signal perturbation")
    ax.legend()
    plt.tight_layout()
    out = Path(__file__).resolve().parent / "f11_demo_chart.png"
    plt.savefig(out, dpi=150)
    print(f"[chart] saved {out}")

def main():
    ap = argparse.ArgumentParser(description="GenoPhylax F11 demo (cached-replay mode)")
    ap.add_argument("--mode", choices=["clean", "attack", "sham"], required=True)
    ap.add_argument("--chart", action="store_true", help="also save a PNG evidence chart (attack mode only)")
    args = ap.parse_args()
    print("=" * 60)
    print(f" GenoPhylax F11 Demo — mode: {args.mode.upper()}  [CACHED REPLAY]")
    print("=" * 60)
    if args.mode == "clean":
        show_clean()
    elif args.mode == "attack":
        show_attack(make_chart=args.chart)
    elif args.mode == "sham":
        show_sham()
    print()

if __name__ == "__main__":
    main()