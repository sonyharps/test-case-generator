def build_summary_prompt(requirement, domain):
    return f"""
Anda adalah Senior QA Analyst.

Buatkan RINGKASAN REQUIREMENT dalam FORMAT JSON SAJA.

Requirement:
{requirement}

Domain:
{domain}

WAJIB output JSON OBJECT (bukan array):

{{
  "id": "REQ-001",
  "nama": "Nama fitur",
  "deskripsi": "Ringkasan singkat apa yang dilakukan sistem",
  "prioritas": "High | Medium | Low",
  "kategori": "{domain}"
}}

DILARANG:
- list
- array
- bullet
- penjelasan tambahan
"""
