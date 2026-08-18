const SIGNAL_LABELS = {
  attendance: "Attendance deviation",
  academic: "Academic score deviation",
  behavior: "Behavioural incidents",
  conversation_distress: "Conversation distress signal",
  trend_acceleration: "Worsening trend",
};

const ROUTING_LABELS = {
  no_routing_needed: { label: "No routing needed", classes: "bg-ink/8 text-ink-light" },
  normal_pathway: { label: "Normal pathway — counsellor reviews directly", classes: "bg-sage-100 text-sage-700" },
  safeguarding_pathway: {
    label: "⚠ Safeguarding pathway — caregiver may be part of the concern",
    classes: "bg-terracotta-100 text-terracotta-700",
  },
};

export default function RiskExplanation({ assessment }) {
  const breakdown = assessment.breakdown ?? {};
  const entries = Object.entries(breakdown).filter(([, v]) => v > 0);
  const maxValue = Math.max(1, ...entries.map(([, v]) => v));
  const routing = ROUTING_LABELS[assessment.routing] ?? ROUTING_LABELS.no_routing_needed;

  return (
    <div className="space-y-4">
      <p className="text-sm leading-relaxed text-ink-light">{assessment.explanation}</p>

      {entries.length > 0 && (
        <div className="space-y-2.5">
          {entries
            .sort((a, b) => b[1] - a[1])
            .map(([key, value]) => (
              <div key={key} className="flex items-center gap-3 text-xs">
                <span className="w-48 shrink-0 text-ink-light">{SIGNAL_LABELS[key] ?? key}</span>
                <div className="h-2 flex-1 overflow-hidden rounded-full bg-ink/8">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-sage-500 to-terracotta-500"
                    style={{ width: `${Math.min(100, (value / maxValue) * 100)}%` }}
                  />
                </div>
                <span className="w-10 shrink-0 text-right tabular-nums text-ink-faint">{value.toFixed(2)}</span>
              </div>
            ))}
        </div>
      )}

      <span className={`inline-block rounded-full px-3 py-1 text-xs font-semibold ${routing.classes}`}>
        {routing.label}
      </span>
    </div>
  );
}
