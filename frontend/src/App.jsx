import { NavLink, Route, Routes } from "react-router-dom";

import Dashboard from "./pages/Dashboard.jsx";
import ReviewQueue from "./pages/ReviewQueue.jsx";
import StudentChat from "./pages/StudentChat.jsx";
import StudentProfile from "./pages/StudentProfile.jsx";

const NAV_ITEMS = [
  { to: "/", end: true, label: "Overview", icon: "🏠" },
  { to: "/review", end: false, label: "Review Queue", icon: "🔔" },
  { to: "/chat", end: false, label: "Student Chat", icon: "💬" },
];

function navPillClass({ isActive }) {
  return [
    "flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-semibold transition-colors",
    isActive ? "bg-sage-500 text-white shadow-soft" : "text-cream-200/80 hover:bg-white/10 hover:text-white",
  ].join(" ");
}

export default function App() {
  return (
    <div className="min-h-screen bg-cream">
      <header className="rounded-b-3xl bg-ink px-6 py-5 shadow-card">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-sage-500 text-lg">🌱</span>
            <div>
              <p className="text-base font-extrabold leading-tight tracking-wide text-white">SENTINEL</p>
              <p className="text-xs font-medium text-cream-200/70">Counsellor dashboard · prototype</p>
            </div>
          </div>
          <nav className="flex gap-1 rounded-full bg-white/5 p-1">
            {NAV_ITEMS.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.end} className={navPillClass}>
                <span>{item.icon}</span>
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-6 py-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/review" element={<ReviewQueue />} />
          <Route path="/chat" element={<StudentChat />} />
          <Route path="/students/:studentId" element={<StudentProfile />} />
        </Routes>
      </main>
    </div>
  );
}
