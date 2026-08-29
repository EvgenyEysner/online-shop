import { Info } from "lucide-react";

interface DemoDataBadgeProps {
  label?: string;
}

export function DemoDataBadge({ label = "Demo-Daten" }: DemoDataBadgeProps) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold border bg-amber-50 text-amber-700 border-amber-200">
      <Info size={11} />
      {label}
    </span>
  );
}
