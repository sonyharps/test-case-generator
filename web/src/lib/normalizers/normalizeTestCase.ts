const humanizeInput = (input: any): string => {
  if (!input) return "";
  const parts = Object.entries(input).map(
    ([k, v]) => `${k} "${v}"`
  );
  return `Masukkan ${parts.join(" dan ")}`;
};

const humanizeExpected = (exp: any): string[] => {
  if (!exp) return [];

  const results: string[] = [];

  if (exp.status_code) {
    results.push(`API merespons status code ${exp.status_code}`);
  }

  if (exp.response) {
    results.push(`Response berisi data sesuai spesifikasi`);
  }

  return results;
};

export function normalizeTestCase(raw: any, type: any) {
  const steps: string[] = [];
  const expected: string[] = [];

  // CASE: combined input + expected_result
  if (raw.input) {
    steps.push(humanizeInput(raw.input));
  }

  if (raw.expected_result) {
    expected.push(...humanizeExpected(raw.expected_result));
  }

  return {
    id: raw.tc_id,
    type,
    title:
      raw.title?.trim() ||
      `Validasi skenario ${type}`,
    preconditions:
      raw.preconditions?.length
        ? raw.preconditions
        : [
            "Sistem telah memiliki data pengguna palid",
            "Pengguna berada di halaman login",
          ],
    steps: steps.length ? steps : ["Lakukan aksi sesuai skenario"],
    expectedResult:
      expected.length
        ? expected
        : ["Sistem merespons sesuai ekspektasi"],
  };
}
