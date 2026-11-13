const STYLES = {
  high: "bg-green-100 text-green-800 border-green-300",
  medium: "bg-yellow-100 text-yellow-800 border-yellow-300",
  low: "bg-red-100 text-red-800 border-red-300",
};

export function confidenceBand(score: number): "high" | "medium" | "low" {
  if (score >= 0.7) return "high";
  if (score >= 0.4) return "medium";
  return "low";
}

export default function ConfidenceBadge({ score }: { score: number }) {
  const band = confidenceBand(score);
  const label = band === "high" ? "high" : band === "medium" ? "medium" : "low";

  return (
    <span
      className={`inline-block rounded border px-2 py-0.5 text-xs font-medium ${STYLES[band]}`}
      title={`confidence ${score.toFixed(2)}`}
    >
      {label} {score.toFixed(2)}
    </span>
  );
}
