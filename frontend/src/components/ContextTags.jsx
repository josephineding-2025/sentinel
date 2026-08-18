const LABELS = {
  academic: "Academic",
  peer_social: "Peer / social",
  bullying: "Bullying",
  family_conflict: "Family",
  isolation_distress: "Social isolation",
};

export default function ContextTags({ context }) {
  if (!context) {
    return <span className="text-sm text-ink-faint">No dominant context yet</span>;
  }
  return (
    <span className="inline-block rounded-full bg-ink/8 px-2.5 py-0.5 text-xs font-semibold text-ink-light">
      {LABELS[context] ?? context}
    </span>
  );
}
