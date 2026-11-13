"use client";

export default function PrintButton() {
  return (
    <button
      type="button"
      onClick={() => window.print()}
      className="rounded border border-gray-300 px-3 py-1 text-sm text-gray-700"
    >
      Export PDF (print)
    </button>
  );
}
