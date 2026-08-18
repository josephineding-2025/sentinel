const STYLES = {
  no_concern: { emoji: "🟢", label: "No significant concern", classes: "bg-sage-100 text-sage-700" },
  insufficient_evidence: { emoji: "🔵", label: "Insufficient evidence", classes: "bg-lavender-100 text-lavender-600" },
  potential_concern: { emoji: "🟠", label: "Potential concern", classes: "bg-terracotta-100 text-terracotta-700" },
  high_priority: { emoji: "🔴", label: "High-priority", classes: "bg-coral-100 text-coral-700" },
};

export default function RiskBadge({ state }) {
  const style = STYLES[state] ?? { emoji: "⚪", label: state, classes: "bg-ink/10 text-ink-light" };
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-semibold ${style.classes}`}>
      <span>{style.emoji}</span>
      {style.label}
    </span>
  );
}
