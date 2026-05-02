import { QueryInterface } from "@/components/QueryInterface";

export default function QueryPage() {
  return (
    <main className="min-h-screen p-8 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-brand-700 mb-8">Ask a Question</h1>
      <QueryInterface />
    </main>
  );
}
