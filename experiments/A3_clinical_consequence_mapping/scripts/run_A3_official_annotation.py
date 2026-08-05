#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


A3_DIR = Path("experiments/A3_clinical_consequence_mapping")
INPUT_DIR = A3_DIR / "inputs"
ANNOTATION_DIR = A3_DIR / "annotations"
RESULTS_DIR = A3_DIR / "results"
MARKER_DIR = A3_DIR / "markers"

ENSEMBL_DIR = ANNOTATION_DIR / "ensembl_vep"
CLINVAR_DIR = ANNOTATION_DIR / "clinvar"

RESOLVED_FILE = INPUT_DIR / "A3_candidate_loci_resolved.tsv"
FIXED_VCF = INPUT_DIR / "A3_candidate_loci_GRCh38_header_fixed.vcf"

OUTPUT_TABLE = RESULTS_DIR / "A3_preliminary_official_annotation.tsv"
SUMMARY_FILE = RESULTS_DIR / "A3_official_annotation_summary.txt"

COMPLETE_MARKER = MARKER_DIR / "A3_OFFICIAL_ANNOTATION.COMPLETE"
FAILED_MARKER = MARKER_DIR / "A3_OFFICIAL_ANNOTATION.FAILED"

for directory in (
    ANNOTATION_DIR,
    RESULTS_DIR,
    MARKER_DIR,
    ENSEMBL_DIR,
    CLINVAR_DIR,
):
    directory.mkdir(parents=True, exist_ok=True)

COMPLETE_MARKER.unlink(missing_ok=True)
FAILED_MARKER.unlink(missing_ok=True)


REFSEQ_ACCESSIONS = {
    "chr1": "NC_000001.11",
    "chr4": "NC_000004.12",
    "chr20": "NC_000020.11",
}


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        raise FileNotFoundError(f"Missing or empty input table: {path}")

    lines = path.read_text(encoding="utf-8").splitlines()

    if not lines:
        raise ValueError(f"No data in {path}")

    header = lines[0].split("\t")
    rows: list[dict[str, str]] = []

    for line in lines[1:]:
        if not line.strip():
            continue

        values = line.split("\t")

        if len(values) != len(header):
            raise ValueError(
                f"Malformed TSV row in {path}: "
                f"expected {len(header)} values, found {len(values)}"
            )

        rows.append(dict(zip(header, values, strict=True)))

    return rows


def request_json(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    attempts: int = 4,
) -> Any:
    request_headers = {
        "Accept": "application/json",
        "User-Agent": "Project-GenoPhylax-A3/1.0",
    }

    if headers:
        request_headers.update(headers)

    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(
                url,
                headers=request_headers,
            )

            with urllib.request.urlopen(
                request,
                timeout=90,
            ) as response:
                text = response.read().decode("utf-8")

            return json.loads(text)

        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
        ) as exc:
            last_error = exc

            if attempt == attempts:
                break

            time.sleep(attempt * 3)

    raise RuntimeError(
        f"Request failed after {attempts} attempts: {url}: {last_error}"
    )


def save_json(path: Path, data: Any) -> None:
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def normalize_chromosome(chrom: str) -> str:
    return chrom.removeprefix("chr")


def create_fixed_vcf(rows: list[dict[str, str]]) -> None:
    contig_lengths = {
        "chr1": "248956422",
        "chr4": "190214555",
        "chr20": "64444167",
    }

    header = [
        "##fileformat=VCFv4.2",
        "##reference=GCA_000001405.15_GRCh38_no_alt_analysis_set",
        "##source=Project_GenoPhylax_A3",
        (
            '##INFO=<ID=SOURCE,Number=1,Type=String,'
            'Description="Source GenoPhylax experiment">'
        ),
    ]

    for chrom in ("chr1", "chr4", "chr20"):
        header.append(
            f"##contig=<ID={chrom},length={contig_lengths[chrom]}>"
        )

    header.append(
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO"
    )

    records = []

    for row in rows:
        records.append(
            "\t".join(
                [
                    row["chrom"],
                    row["position"],
                    row["locus_id"],
                    row["ref"],
                    row["alt"],
                    ".",
                    "PASS",
                    "SOURCE=A2",
                ]
            )
        )

    FIXED_VCF.write_text(
        "\n".join(header + records) + "\n",
        encoding="utf-8",
    )


def query_ensembl(row: dict[str, str]) -> Any:
    chrom = normalize_chromosome(row["chrom"])
    position = row["position"]
    alt = row["alt"]

    region = f"{chrom}:{position}-{position}:1"

    encoded_region = urllib.parse.quote(region, safe=":-")
    encoded_alt = urllib.parse.quote(alt, safe="")

    url = (
        "https://rest.ensembl.org/"
        f"vep/human/region/{encoded_region}/{encoded_alt}"
        "?hgvs=1"
        "&mane=1"
        "&canonical=1"
        "&numbers=1"
        "&protein=1"
        "&symbol=1"
        "&variant_class=1"
    )

    return request_json(
        url,
        headers={"Content-Type": "application/json"},
    )


def canonical_spdi(row: dict[str, str]) -> str:
    accession = REFSEQ_ACCESSIONS[row["chrom"]]

    zero_based_position = int(row["position"]) - 1

    return (
        f"{accession}:"
        f"{zero_based_position}:"
        f"{row['ref']}:"
        f"{row['alt']}"
    )


def query_clinvar(row: dict[str, str]) -> tuple[str, Any, Any]:
    spdi = canonical_spdi(row)

    search_term = f'"{spdi}"[cspdi]'

    params = urllib.parse.urlencode(
        {
            "db": "clinvar",
            "term": search_term,
            "retmode": "json",
            "retmax": "20",
        }
    )

    search_url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        f"esearch.fcgi?{params}"
    )

    search_json = request_json(search_url)

    id_list = (
        search_json
        .get("esearchresult", {})
        .get("idlist", [])
    )

    if not id_list:
        return spdi, search_json, {}

    summary_params = urllib.parse.urlencode(
        {
            "db": "clinvar",
            "id": ",".join(id_list),
            "retmode": "json",
        }
    )

    summary_url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        f"esummary.fcgi?{summary_params}"
    )

    summary_json = request_json(summary_url)

    return spdi, search_json, summary_json


def select_transcript_consequence(
    vep_record: dict[str, Any],
) -> dict[str, Any]:
    transcripts = vep_record.get(
        "transcript_consequences",
        [],
    )

    if not transcripts:
        return {}

    def rank(item: dict[str, Any]) -> tuple[int, int, int]:
        mane = 0 if item.get("mane_select") else 1
        canonical = 0 if item.get("canonical") else 1
        protein_coding = (
            0 if item.get("biotype") == "protein_coding" else 1
        )

        return mane, canonical, protein_coding

    return sorted(transcripts, key=rank)[0]


def parse_clinvar_summary(
    summary_json: Any,
) -> dict[str, str]:
    if not summary_json:
        return {
            "clinvar_record_count": "0",
            "clinvar_variation_ids": "",
            "clinvar_titles": "",
            "clinvar_significance": "",
            "clinvar_review_status": "",
        }

    result = summary_json.get("result", {})
    uids = result.get("uids", [])

    titles: list[str] = []
    significance_values: list[str] = []
    review_values: list[str] = []

    for uid in uids:
        record = result.get(uid, {})

        title = record.get("title")

        if title:
            titles.append(str(title))

        germline = record.get(
            "germline_classification",
            {},
        )

        description = germline.get("description")
        review_status = germline.get("review_status")

        if description:
            significance_values.append(str(description))

        if review_status:
            review_values.append(str(review_status))

    return {
        "clinvar_record_count": str(len(uids)),
        "clinvar_variation_ids": ";".join(uids),
        "clinvar_titles": ";".join(sorted(set(titles))),
        "clinvar_significance": ";".join(
            sorted(set(significance_values))
        ),
        "clinvar_review_status": ";".join(
            sorted(set(review_values))
        ),
    }


def main() -> int:
    rows = read_tsv(RESOLVED_FILE)

    expected_loci = {"L1", "L2", "L3"}
    observed_loci = {row["locus_id"] for row in rows}

    if observed_loci != expected_loci:
        raise ValueError(
            f"Expected loci {expected_loci}; observed {observed_loci}"
        )

    create_fixed_vcf(rows)

    output_rows: list[dict[str, str]] = []

    summary_lines = [
        "A3 OFFICIAL ANNOTATION SUMMARY",
        f"Input loci: {len(rows)}",
        "",
    ]

    for row in rows:
        locus_id = row["locus_id"]

        print(f"Annotating {locus_id}: "
              f"{row['chrom']}:{row['position']} "
              f"{row['ref']}>{row['alt']}")

        vep_json = query_ensembl(row)

        save_json(
            ENSEMBL_DIR / f"{locus_id}_ensembl_vep.json",
            vep_json,
        )

        if isinstance(vep_json, list) and vep_json:
            vep_record = vep_json[0]
        else:
            vep_record = {}

        transcript = select_transcript_consequence(vep_record)

        spdi, clinvar_search, clinvar_summary = query_clinvar(row)

        save_json(
            CLINVAR_DIR / f"{locus_id}_clinvar_esearch.json",
            clinvar_search,
        )

        save_json(
            CLINVAR_DIR / f"{locus_id}_clinvar_esummary.json",
            clinvar_summary,
        )

        clinvar_fields = parse_clinvar_summary(
            clinvar_summary
        )

        consequence_terms = transcript.get(
            "consequence_terms",
            [],
        )

        output = {
            "locus_id": locus_id,
            "chrom": row["chrom"],
            "position": row["position"],
            "ref": row["ref"],
            "alt": row["alt"],
            "assembly": row["assembly"],
            "canonical_spdi": spdi,
            "ensembl_most_severe_consequence": str(
                vep_record.get(
                    "most_severe_consequence",
                    "",
                )
            ),
            "gene_symbol": str(
                transcript.get("gene_symbol", "")
            ),
            "gene_id": str(
                transcript.get("gene_id", "")
            ),
            "transcript_id": str(
                transcript.get("transcript_id", "")
            ),
            "transcript_biotype": str(
                transcript.get("biotype", "")
            ),
            "selected_consequence_terms": ";".join(
                consequence_terms
            ),
            "impact": str(
                transcript.get("impact", "")
            ),
            "mane_select": str(
                transcript.get("mane_select", "")
            ),
            "canonical_transcript": str(
                transcript.get("canonical", "")
            ),
            "hgvsc": str(
                transcript.get("hgvsc", "")
            ),
            "hgvsp": str(
                transcript.get("hgvsp", "")
            ),
            "variant_class": str(
                vep_record.get("variant_class", "")
            ),
            **clinvar_fields,
        }

        output_rows.append(output)

        summary_lines.extend(
            [
                (
                    f"{locus_id}: "
                    f"{row['chrom']}:{row['position']} "
                    f"{row['ref']}>{row['alt']}"
                ),
                (
                    "  Most severe consequence: "
                    f"{output['ensembl_most_severe_consequence']}"
                ),
                (
                    "  Selected gene: "
                    f"{output['gene_symbol'] or 'NONE'}"
                ),
                (
                    "  Selected transcript: "
                    f"{output['transcript_id'] or 'NONE'}"
                ),
                (
                    "  ClinVar exact-SPDI records: "
                    f"{output['clinvar_record_count']}"
                ),
                (
                    "  ClinVar significance: "
                    f"{output['clinvar_significance'] or 'NONE'}"
                ),
                "",
            ]
        )

        time.sleep(1)

    columns = list(output_rows[0].keys())

    with OUTPUT_TABLE.open(
        "w",
        encoding="utf-8",
    ) as handle:
        handle.write("\t".join(columns) + "\n")

        for output in output_rows:
            handle.write(
                "\t".join(
                    str(output[column]).replace(
                        "\t",
                        " ",
                    ).replace(
                        "\n",
                        " ",
                    )
                    for column in columns
                )
                + "\n"
            )

    SUMMARY_FILE.write_text(
        "\n".join(summary_lines),
        encoding="utf-8",
    )

    COMPLETE_MARKER.touch()

    print()
    print("=" * 80)
    print("A3 OFFICIAL ANNOTATION: COMPLETE")
    print("=" * 80)
    print(f"Fixed VCF: {FIXED_VCF}")
    print(f"Output table: {OUTPUT_TABLE}")
    print(f"Summary: {SUMMARY_FILE}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        FAILED_MARKER.touch()

        print(
            "A3 OFFICIAL ANNOTATION FAILED: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )

        raise
