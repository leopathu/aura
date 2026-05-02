import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-8 p-8">
      <div className="text-center">
        <h1 className="text-5xl font-bold text-brand-700 mb-4">Aura</h1>
        <p className="text-xl text-slate-500 max-w-md">
          A Retrieval-Augmented Generation system powered by pgvector and OpenAI.
        </p>
      </div>
      <div className="flex gap-4">
        <Link
          href="/query"
          className="px-6 py-3 bg-brand-600 text-white rounded-lg font-medium hover:bg-brand-700 transition-colors"
        >
          Ask a Question
        </Link>
        <Link
          href="/documents"
          className="px-6 py-3 border border-brand-600 text-brand-600 rounded-lg font-medium hover:bg-brand-50 transition-colors"
        >
          Manage Documents
        </Link>
      </div>
    </main>
  );
}
