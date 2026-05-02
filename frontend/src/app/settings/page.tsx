import { ProtectedLayout } from "@/components/ProtectedLayout";
import { SettingsPage } from "@/components/SettingsPage";

export default function Settings() {
  return (
    <ProtectedLayout>
      <div className="overflow-y-auto h-full">
        <SettingsPage />
      </div>
    </ProtectedLayout>
  );
}
