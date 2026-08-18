import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client.js";
import RiskBadge from "../components/RiskBadge.jsx";

export default function StudentChat() {
  const [students, setStudents] = useState([]);
  const [studentId, setStudentId] = useState("");
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [lastAssessment, setLastAssessment] = useState(null);
  const [error, setError] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    api.listStudents().then((list) => {
      setStudents(list);
      if (list.length) setStudentId(list[0].student_id);
    });
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function switchStudent(id) {
    setStudentId(id);
    setMessages([]);
    setLastAssessment(null);
    setError(null);
  }

  async function handleSend(e) {
    e.preventDefault();
    if (!input.trim() || !studentId || sending) return;

    const text = input.trim();
    setInput("");
    setError(null);
    setMessages((prev) => [...prev, { role: "student", text }]);
    setSending(true);

    try {
      const result = await api.sendMessage(studentId, text);
      setMessages((prev) => [...prev, { role: "assistant", text: result.reply }]);
      setLastAssessment(result.risk_assessment);
    } catch (err) {
      setError(err.message);
    } finally {
      setSending(false);
    }
  }

  return (
    <div>
      <h1 className="mb-1 text-2xl font-extrabold text-ink">Student AI Account (demo)</h1>
      <p className="mb-6 text-sm text-ink-light">
        Simulates the student-facing side of the architecture: whatever is typed here is stored and classified
        immediately, and the fused risk score updates live — check the Overview or Review Queue in another tab after
        sending a message.
      </p>

      <div className="mb-4 flex items-center gap-3">
        <label className="text-sm font-semibold text-ink-light">Signed in as</label>
        <select
          value={studentId}
          onChange={(e) => switchStudent(e.target.value)}
          className="rounded-full border border-cream-200 bg-white px-4 py-1.5 text-sm font-semibold text-ink shadow-soft"
        >
          {students.map((s) => (
            <option key={s.student_id} value={s.student_id}>
              {s.student_id}
            </option>
          ))}
        </select>
      </div>

      {lastAssessment && (
        <div className="mb-4 flex flex-wrap items-center gap-3 rounded-2xl bg-white p-3.5 text-sm shadow-soft">
          <span className="font-semibold text-ink-light">Risk updated:</span>
          <RiskBadge state={lastAssessment.risk_state} />
          <span className="font-semibold text-ink-faint">score {lastAssessment.risk_score.toFixed(2)}</span>
          <Link className="ml-auto font-semibold text-sage-700 hover:underline" to={`/students/${studentId}`}>
            View on admin dashboard &rarr;
          </Link>
        </div>
      )}

      <div className="mb-3 flex h-96 flex-col overflow-y-auto rounded-3xl bg-ink p-4 shadow-card">
        {messages.length === 0 && (
          <div className="m-auto text-center text-cream-200/60">
            <p className="text-3xl">🤖</p>
            <p className="mt-2 text-sm font-semibold">No messages yet — say something below.</p>
          </div>
        )}
        <div className="space-y-3">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "student" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                  m.role === "student"
                    ? "rounded-br-md bg-terracotta-500 text-white"
                    : "rounded-bl-md bg-white/10 text-cream-100"
                }`}
              >
                {m.text}
              </div>
            </div>
          ))}
        </div>
        <div ref={bottomRef} />
      </div>

      {error && (
        <p className="mb-2 rounded-2xl bg-coral-50 px-4 py-2 text-sm text-coral-700">
          {error} — the live chat requires GEMINI_API_KEY to be set in the backend's .env (see README).
        </p>
      )}

      <form onSubmit={handleSend} className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
          className="flex-1 rounded-full border border-cream-200 bg-white px-4 py-2.5 text-sm shadow-soft placeholder:text-ink-faint focus:outline-none focus:ring-2 focus:ring-sage-500"
          disabled={!studentId}
        />
        <button
          type="submit"
          disabled={sending || !studentId}
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-sage-500 text-lg text-white shadow-soft transition-colors hover:bg-sage-600 disabled:opacity-50"
          aria-label="Send"
        >
          {sending ? "…" : "➤"}
        </button>
      </form>
    </div>
  );
}
