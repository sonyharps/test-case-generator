def build_testcase_plan_prompt(req, domain):
    return f"""
Anda adalah Senior QA Engineer Level Expert.

Tugas Anda: buat rencana Test Scenario LENGKAP berbasis requirement berikut:

Requirement:
{req}

Domain: {domain}

OUTPUT HARUS FORMAT JSON:

{{
  "scenarios": [
    {{
      "name": "",
      "description": "",
      "functional_expansion": [],
      "negative_expansion": [],
      "boundary_expansion": []
    }}
  ]
}}

ATURAN:
- functional_expansion minimal 12 skenario.
- negative_expansion minimal 10 skenario invalid.
- boundary_expansion minimal 8 skenario boundary: min, max, empty, extreme, special chars, rate-limit, overflow.
- Tidak boleh ada text di luar JSON.
- Tidak boleh markdown.
- Tidak boleh ```.

HASILKAN JSON VALID SAJA.
"""
