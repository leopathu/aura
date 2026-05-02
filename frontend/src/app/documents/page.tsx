import { ProtectedLayout } from "@/components/ProtectedLayout";
import { DocumentList } from "@/components/DocumentList";

export default function DocumentsPage() {
  return (
    <ProtectedLayout>
      <main className="p-8 max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-brand-700 mb-8">Documents</h1>
        <DocumentList />
      </main>
    </ProtectedLayout>
  );
}
