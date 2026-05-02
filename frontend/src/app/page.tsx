import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-8 p-8 bg-slate-50">
      <div className="text-center">
        <h1 className="text-5xl font-bold text-brand-700 mb-4">Aura</h1>
        <p className="text-xl text-slate-500 max-w-md">
          A Retrieval-Augmented Generation system powered by pgvector and OpenAI.
        </p>
      </div>
      <div className="flex gap-4">
        <Link
          href="/login"
          className="px-6 py-3 bg-brand-600 text-white rounded-lg font-medium hover:bg-brand-700 transition-colors"
        >
          Sign In
        </Link>
        <Link
          href="/register"
          className="px-6 py-3 border border-brand-600 text-brand-600 rounded-lg font-medium hover:bg-brand-50 transition-colors"
        >
          Create Account
        </Link>
        <Link
          href="/brains"
          className="px-6 py-3 border border-slate-300 text-slate-600 rounded-lg font-medium hover:bg-slate-100 transition-colors"
        >
          My Brains
        </Link>
      </div>
    </main>
  );
}
