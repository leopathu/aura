import { ProtectedLayout } from "@/components/ProtectedLayout";
import { QueryInterface } from "@/components/QueryInterface";

export default function QueryPage() {
  return (
    <ProtectedLayout>
      <main className="p-8 max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-brand-700 mb-8">Ask a Question</h1>
        <QueryInterface />
      </main>
    </ProtectedLayout>
  );
}
