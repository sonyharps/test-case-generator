export interface SummaryVM {
  id: string;
  nama: string;
  deskripsi: string;
  prioritas: string;
  kategori: string;
  fiturKunci: string[];
}

export function normalizeSummary(raw: any): SummaryVM {
  if (!raw) {
    return {
      id: "—",
      nama: "",
      deskripsi: "",
      prioritas: "",
      kategori: "",
      fiturKunci: [],
    };
  }

  return {
    id: raw.id ?? "REQ-001",
    nama: raw.nama ?? raw.judul ?? "",
    deskripsi: raw.deskripsi ?? "",
    prioritas: raw.prioritas ?? "",
    kategori: raw.kategori ?? "",
    fiturKunci: Array.isArray(raw.fitur_kunci) ? raw.fitur_kunci : [],
  };
}
