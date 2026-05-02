import { DocumentList } from "@/components/DocumentList";

export default function DocumentsPage() {
  return (
    <main className="min-h-screen p-8 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-brand-700 mb-8">Documents</h1>
      <DocumentList />
    </main>
  );
}
