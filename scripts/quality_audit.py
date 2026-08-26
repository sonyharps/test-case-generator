#!/usr/bin/env python
"""Quality audit for a generated test-case xlsx.

Checks per TC (ISO/IEC/IEEE 29119-3):
  1. Field fill rate (priority, module, test_data, postconditions)
  2. Language — Indonesian vs English heuristic
  3. Duplicate titles (normalized)
  4. Steps actionability — starts with action verb, avg count
  5. Expected result measurability — length & specificity heuristics
  6. Test data concreteness — contains digits/specific values

Usage: python scripts/quality_audit.py <file.xlsx>
"""
import re
import sys
from collections import Counter
from openpyxl import load_workbook

# Common Indonesian action words / markers
ID_MARKERS = {
    "verifikasi", "validasi", "klik", "input", "isi", "masukkan", "pilih",
    "buka", " navigasi", "cek", "periksa", "sistem", "menampilkan", "tampil",
    "muncul", "pengguna", "harus", "tidak", "dengan", "pada", "yang", "dan",
    "ke", "dari", "untuk", "saat", "ketika", "jika", "maka", "gagal", "berhasil",
}
EN_MARKERS = {
    "verify", "click", "enter", "input the", "navigate", "check that",
    "system should", "the user", "should display", "must be", "when the",
    "then the", "and the", "is displayed", "successfully", "invalid",
}

VERBS = re.compile(
    r"^(klik|buka|input|isi|masuk|pilih|navigasi|cek|periksa|verifikasi|validasi|"
    r"tekan|tap|scroll|upload|download|kirim|submit|aktif|nonaktif|login|logout|"
    r"tambah|hapus|edit|ubah|set|jalankan|amati|pastikan|lakukan|wait|tunggu)",
    re.IGNORECASE,
)


def lang_ratio(text: str) -> float:
    """Return Indonesian score 0..1 (fraction of matched markers)."""
    t = " " + text.lower() + " "
    id_hits = sum(1 for m in ID_MARKERS if m in t)
    en_hits = sum(1 for m in EN_MARKERS if m in t)
    total = id_hits + en_hits
    if total == 0:
        return 0.5
    return id_hits / total


def main(path: str):
    wb = load_workbook(path)
    print("=" * 64)
    print(f"QUALITY AUDIT: {path}")
    print("=" * 64)

    total_tc = 0
    all_titles = []
    grand = Counter()

    for sheet in ["Functional", "Negative", "Boundary"]:
        ws = wb[sheet]
        n = ws.max_row - 1
        if n <= 0:
            print(f"\n[{sheet}] EMPTY")
            continue
        total_tc += n
        print(f"\n[{sheet}] — {n} TC")

        stats = Counter()
        prio = Counter()
        lang_scores = []
        step_counts = []
        dup_check = {}

        for r in range(2, ws.max_row + 1):
            tc_id = ws.cell(r, 1).value or ""
            priority = (ws.cell(r, 2).value or "").strip()
            module = (ws.cell(r, 3).value or "").strip()
            title = (ws.cell(r, 4).value or "").strip()
            precond = ws.cell(r, 5).value or ""
            test_data = ws.cell(r, 6).value or ""
            steps = ws.cell(r, 7).value or ""
            expected = ws.cell(r, 8).value or ""
            postcond = ws.cell(r, 9).value or ""

            if priority: stats["priority_filled"] += 1
            if module and module.lower() not in ("general", "-"): stats["module_filled"] += 1
            if test_data.strip(): stats["test_data_filled"] += 1
            if postcond.strip(): stats["postcond_filled"] += 1

            if priority: prio[priority] += 1

            # Language on title+steps
            blob = f"{title} {steps}"
            lang_scores.append(lang_ratio(blob))
            ind = lang_ratio(blob) >= 0.6
            stats["indonesian" if ind else "english_leaning"] += 1

            # Steps actionability
            step_list = [s.strip() for s in str(steps).split("\n") if s.strip()]
            step_counts.append(len(step_list))
            actionable = sum(1 for s in step_list if VERBS.match(s))
            if step_list and actionable / len(step_list) >= 0.5:
                stats["steps_actionable"] += 1

            # Expected measurability: has specifics (digits, quotes, UI refs)
            if re.search(r"\d|\"|'|warna|merah|hijau|toast|button|tombol|halaman|popup|error|berhasil", str(expected), re.IGNORECASE):
                stats["expected_measurable"] += 1

            # Test data concreteness: contains digits
            if re.search(r"\d", str(test_data)):
                stats["test_data_concrete"] += 1

            # Duplicate detection (normalized title)
            key = re.sub(r"\W+", " ", title.lower()).strip()
            if key in dup_check:
                stats["duplicate_title"] += 1
            dup_check[key] = tc_id
            all_titles.append((sheet, tc_id, title))

        print(f"  Priority filled   : {stats['priority_filled']}/{n}")
        print(f"  Module filled     : {stats['module_filled']}/{n}")
        print(f"  Test data filled  : {stats['test_data_filled']}/{n}")
        print(f"  Test data konkret : {stats['test_data_concrete']}/{n}")
        print(f"  Postcond filled   : {stats['postcond_filled']}/{n}")
        print(f"  Steps actionable  : {stats['steps_actionable']}/{n}")
        print(f"  Expected measurable: {stats['expected_measurable']}/{n}")
        print(f"  Bahasa Indonesia  : {stats['indonesian']}/{n} (english-leaning: {stats['english_leaning']})")
        print(f"  Duplikat judul    : {stats['duplicate_title']}/{n}")
        print(f"  Prioritas distribs: {dict(prio)}")
        print(f"  Rata-rata steps/TC: {sum(step_counts)/len(step_counts):.1f}")

        for k in stats:
            grand[k] += stats[k]

    print("\n" + "=" * 64)
    print(f"TOTAL: {total_tc} TC | overall quality:")
    for k in ["priority_filled", "module_filled", "test_data_filled", "test_data_concrete",
              "postcond_filled", "steps_actionable", "expected_measurable",
              "indonesian", "duplicate_title"]:
        print(f"  {k:20s}: {grand[k]}/{total_tc} ({100*grand[k]/total_tc:.0f}%)")


if __name__ == "__main__":
    main(sys.argv[1])
