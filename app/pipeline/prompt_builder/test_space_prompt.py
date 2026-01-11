def build_test_space_prompt(pre):
    req = pre["clean_requirement"]
    domain = pre.get("domain", "system")

    return f"""
Anda adalah QA Engineer senior.

TUGAS:
Berdasarkan requirement berikut, hasilkan TEST SPACE dalam format JSON MURNI.

REQUIREMENT:
{req}

ATURAN KERAS (WAJIB):
- Output HARUS JSON
- TIDAK BOLEH ada teks di luar JSON
- TIDAK BOLEH markdown
- TIDAK BOLEH penjelasan

FORMAT WAJIB:

{{
  "success": [
    {{
      "scenario": "string",
      "goal": "string"
    }}
  ],
  "failure": [
    {{
      "scenario": "string",
      "goal": "string"
    }}
  ],
  "boundary": [
    {{
      "scenario": "string",
      "goal": "string"
    }}
  ]
}}

MINIMAL:
- success: 5 item
- failure: 5 item
- boundary: 8 item

OUTPUT JSON SAJA.
"""
