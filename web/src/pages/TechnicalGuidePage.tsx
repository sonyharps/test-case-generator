// src/pages/TechnicalGuidePage.tsx
import { BookOpen, Zap, Database, Cpu, FileText, Layers, AlertCircle, CheckCircle } from "lucide-react";

export default function TechnicalGuidePage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="border-b border-slate-200 pb-4">
        <h1 className="text-2xl font-semibold text-slate-900 flex items-center gap-2">
          <BookOpen className="w-6 h-6 text-blue-600" />
          Petunjuk Teknis / README
        </h1>
        <p className="text-slate-600 mt-1">
          Dokumentasi lengkap penggunaan AI QA Orchestrator
        </p>
      </div>

      {/* Overview */}
      <section className="bg-white rounded-xl border border-slate-200 p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-3 flex items-center gap-2">
          <Zap className="w-5 h-5 text-amber-500" />
          Tentang Aplikasi
        </h2>
        <div className="prose prose-slate max-w-none text-sm">
          <p className="text-slate-600 mb-3">
            <strong>AI QA Orchestrator</strong> adalah platform pembuatan test case otomatis
            berbasis AI yang membantu QA Engineer dan Software Tester menghasilkan test case
            berkualitas dari requirement dalam waktu singkat.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
            <div className="bg-blue-50 rounded-lg p-4 border border-blue-100">
              <div className="font-medium text-blue-700 mb-1">Functional Testing</div>
              <div className="text-xs text-blue-600">Test case untuk validasi fitur sesuai requirement</div>
            </div>
            <div className="bg-red-50 rounded-lg p-4 border border-red-100">
              <div className="font-medium text-red-700 mb-1">Negative Testing</div>
              <div className="text-xs text-red-600">Test case untuk skenario invalid dan error handling</div>
            </div>
            <div className="bg-green-50 rounded-lg p-4 border border-green-100">
              <div className="font-medium text-green-700 mb-1">Boundary Testing</div>
              <div className="text-xs text-green-600">Test case untuk batas minimum dan maximum</div>
            </div>
          </div>
        </div>
      </section>

      {/* Quick Start */}
      <section className="bg-white rounded-xl border border-slate-200 p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-3 flex items-center gap-2">
          <CheckCircle className="w-5 h-5 text-green-500" />
          Memulai Cepat
        </h2>
        <div className="space-y-4">
          <Step
            num={1}
            title="Login ke Aplikasi"
            description="Gunakan email dan password untuk login. Jika belum punya akun, daftar terlebih dahulu."
          />
          <Step
            num={2}
            title="Pilih Halaman Orchestrator"
            description="Buka menu Orchestrator untuk memulai pembuatan test case."
          />
          <Step
            num={3}
            title="Masukkan Requirement"
            description="Ketik atau paste requirement yang akan diuji. Contoh: 'User dapat login dengan email dan password'"
          />
          <Step
            num={4}
            title="Pilih Konfigurasi LLM"
            description="Pilih provider (Local, Groq, Gemini) dan model yang akan digunakan."
          />
          <Step
            num={5}
            title="Generate Test Case"
            description="Klik tombol Generate dan tunggu proses pembuatan test case selesai."
          />
          <Step
            num={6}
            title="Review & Export"
            description="Review hasil test case, edit jika diperlukan, lalu export ke PDF."
          />
        </div>
      </section>

      {/* Features */}
      <section className="bg-white rounded-xl border border-slate-200 p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-3 flex items-center gap-2">
          <Layers className="w-5 h-5 text-purple-500" />
          Fitur Utama
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FeatureCard
            icon={<Cpu className="w-5 h-5" />}
            title="Multi-LLM Support"
            description="Dukungan berbagai provider LLM: Ollama (local), Groq, Gemini, dan GLM."
          />
          <FeatureCard
            icon={<FileText className="w-5 h-5" />}
            title="RAG Documents"
            description="Upload dokumen (PRD, User Story) untuk konteks test case yang lebih relevan."
          />
          <FeatureCard
            icon={<Database className="w-5 h-5" />}
            title="Requirements Library"
            description="Simpan dan kelola requirement untuk digunakan kembali di lain waktu."
          />
          <FeatureCard
            icon={<Layers className="w-5 h-5" />}
            title="Test Repository"
            description="Simpan test case ke repository dan buat test run untuk eksekusi."
          />
        </div>
      </section>

      {/* LLM Configuration */}
      <section className="bg-white rounded-xl border border-slate-200 p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-3 flex items-center gap-2">
          <Cpu className="w-5 h-5 text-indigo-500" />
          Konfigurasi LLM
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="text-left py-2 px-3 font-medium text-slate-700">Provider</th>
                <th className="text-left py-2 px-3 font-medium text-slate-700">Model</th>
                <th className="text-left py-2 px-3 font-medium text-slate-700">Kelebihan</th>
                <th className="text-left py-2 px-3 font-medium text-slate-700">Keterangan</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              <tr>
                <td className="py-2 px-3 font-medium">Local (Ollama)</td>
                <td className="py-2 px-3 text-slate-600">llama3.1, mistral, phi</td>
                <td className="py-2 px-3 text-slate-600">Gratis, privasi terjaga</td>
                <td className="py-2 px-3 text-slate-600">Butuh resource komputer tinggi</td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-medium">Groq</td>
                <td className="py-2 px-3 text-slate-600">llama-3.1-8b, mixtral</td>
                <td className="py-2 px-3 text-slate-600">Sangat cepat</td>
                <td className="py-2 px-3 text-slate-600">Perlu API key, ada rate limit</td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-medium">Gemini</td>
                <td className="py-2 px-3 text-slate-600">gemini-2.0-flash</td>
                <td className="py-2 px-3 text-slate-600">Free tier murah hati</td>
                <td className="py-2 px-3 text-slate-600">Perlu API key Google</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* RAG Feature */}
      <section className="bg-white rounded-xl border border-slate-200 p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-3 flex items-center gap-2">
          <Database className="w-5 h-5 text-cyan-500" />
          RAG (Retrieval-Augmented Generation)
        </h2>
        <div className="prose prose-slate max-w-none text-sm text-slate-600 space-y-3">
          <p>
            RAG memungkinkan test case yang dihasilkan lebih relevan dengan konteks aplikasi
            Anda dengan mengupload dokumen referensi:
          </p>
          <ul className="list-disc pl-5 space-y-1">
            <li><strong>PRD (Product Requirement Document)</strong> - Dokumentasi requirement produk</li>
            <li><strong>User Stories</strong> - Cerita pengguna untuk fitur tertentu</li>
            <li><strong>Technical Specification</strong> - Spesifikasi teknis aplikasi</li>
            <li><strong>Test Plan</strong> - Rencana testing yang sudah ada</li>
          </ul>
          <p className="text-xs text-slate-500 mt-3">
            Format yang didukung: PDF, DOCX, TXT, MD
          </p>
        </div>
      </section>

      {/* Tips & Best Practices */}
      <section className="bg-amber-50 rounded-xl border border-amber-200 p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-3 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-amber-600" />
          Tips & Best Practices
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <Tip
            title="Requirement yang Jelas"
            description="Tuliskan requirement dengan spesifik: input, expected output, dan business logic."
          />
          <Tip
            title="Gunakan Boundary Testing"
            description="Aktifkan opsi Boundary Testing untuk menemukan edge case yang sering terlewat."
          />
          <Tip
            title="Review Hasil Generate"
            description="Selalu review test case yang dihasilkan AI sebelum disimpan atau dieksekusi."
          />
          <Tip
            title="Simpan ke Repository"
            description="Gunakan Test Repository untuk menyimpan test case berkualitas untuk penggunaan kembali."
          />
        </div>
      </section>

      {/* Keyboard Shortcuts */}
      <section className="bg-white rounded-xl border border-slate-200 p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-3 flex items-center gap-2">
          <Zap className="w-5 h-5 text-yellow-500" />
          Keyboard Shortcuts
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
          <Shortcut keyCombo="Ctrl + Enter" description="Generate test case" />
          <Shortcut keyCombo="Ctrl + S" description="Simpan session" />
          <Shortcut keyCombo="Ctrl + E" description="Export PDF" />
          <Shortcut keyCombo="Esc" description="Tutup dialog" />
        </div>
      </section>

      {/* Footer */}
      <div className="text-center text-xs text-slate-500 py-4 border-t border-slate-200">
        <p>AI QA Orchestrator v0.1 • Enterprise Test Case Engine</p>
        <p className="mt-1">© 2024 Internal QA Team</p>
      </div>
    </div>
  );
}

function Step({ num, title, description }: { num: number; title: string; description: string }) {
  return (
    <div className="flex gap-4">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-semibold text-sm">
        {num}
      </div>
      <div>
        <h4 className="font-medium text-slate-900">{title}</h4>
        <p className="text-sm text-slate-600">{description}</p>
      </div>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="border border-slate-200 rounded-lg p-4 hover:border-blue-200 hover:bg-blue-50/30 transition-colors">
      <div className="flex items-center gap-2 mb-2">
        <div className="text-blue-600">{icon}</div>
        <h4 className="font-medium text-slate-900">{title}</h4>
      </div>
      <p className="text-sm text-slate-600">{description}</p>
    </div>
  );
}

function Tip({ title, description }: { title: string; description: string }) {
  return (
    <div className="flex gap-3">
      <div className="text-amber-600 mt-0.5">💡</div>
      <div>
        <h4 className="font-medium text-slate-900">{title}</h4>
        <p className="text-sm text-slate-600">{description}</p>
      </div>
    </div>
  );
}

function Shortcut({ keyCombo, description }: { keyCombo: string; description: string }) {
  return (
    <div className="flex items-center justify-between border border-slate-200 rounded-lg px-3 py-2">
      <span className="text-slate-600">{description}</span>
      <kbd className="px-2 py-1 text-xs font-medium text-slate-700 bg-slate-100 border border-slate-300 rounded">
        {keyCombo}
      </kbd>
    </div>
  );
}
