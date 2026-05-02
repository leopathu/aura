"use client";

import { ProtectedLayout } from "@/components/ProtectedLayout";
import { BrainSidebar } from "@/components/BrainSidebar";
import { BrainPanel } from "@/components/BrainPanel";
import { useBrainStore } from "@/store/brain-store";

/**
 * Main Brains page — sidebar + brain panel.
 */
export default function BrainsPage() {
  return (
    <ProtectedLayout>
      <BrainsContent />
    </ProtectedLayout>
  );
}

function BrainsContent() {
  const selectedBrain = useBrainStore((s) => s.selectedBrain);

  return (
    <div className="flex h-[calc(100vh-57px)]">
      <BrainSidebar />
      <main className="flex-1 overflow-hidden bg-slate-50">
        {selectedBrain ? (
          <BrainPanel brain={selectedBrain} />
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 px-6">
            <span className="text-6xl mb-4">🧠</span>
            <h2 className="text-xl font-semibold text-slate-600">Select a Brain</h2>
            <p className="text-sm mt-2 max-w-xs">
              Choose a brain from the sidebar or create a new one to start chatting.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
