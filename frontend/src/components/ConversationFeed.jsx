import ContextTags from "./ContextTags.jsx";

function distressColor(score) {
  if (score != null && score >= 0.5) return "bg-coral-50 border-coral-100";
  if (score != null && score >= 0.25) return "bg-terracotta-50 border-terracotta-100";
  return "bg-white border-cream-200";
}

export default function ConversationFeed({ conversations, maxItems = 8 }) {
  if (!conversations.length) {
    return <p className="text-sm text-ink-faint">No AI conversation snippets recorded yet.</p>;
  }

  const recent = [...conversations].reverse().slice(0, maxItems);

  return (
    <div className="space-y-2.5">
      {recent.map((c, i) => (
        <div key={i} className={`rounded-2xl border p-3.5 text-sm ${distressColor(c.distress_score)}`}>
          <div className="mb-1.5 flex items-center justify-between gap-2">
            <span className="text-xs font-semibold text-ink-faint">Week {c.week}</span>
            <div className="flex items-center gap-2">
              {c.distress_score != null && c.distress_score >= 0.25 && (
                <span className="text-xs font-semibold text-coral-600">distress {c.distress_score.toFixed(2)}</span>
              )}
              <ContextTags context={c.predicted_category === "none" ? null : c.predicted_category} />
            </div>
          </div>
          <p className="text-ink">&ldquo;{c.text}&rdquo;</p>
        </div>
      ))}
    </div>
  );
}
