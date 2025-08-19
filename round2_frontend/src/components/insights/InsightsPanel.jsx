import { useState } from "react";
import { insightsBulb } from "../../lib/api";

export default function InsightsPanel({ seedText, docIds = [] }) {
  const [busy, setBusy] = useState(false);
  const [text, setText] = useState("");

  async function run() {
    if (!seedText?.trim()) return;
    setBusy(true);
    setText("");
    try {
      const res = await insightsBulb({ query: seedText, docIds, k: 5 });
      setText(res?.answer || "No insights.");
    } catch (e) {
      setText(`${e?.message || "Failed to get insights."}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ display: "grid", gap: 8 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <button className="btnGhost" onClick={run} disabled={busy}>
          {busy ? "Thinking…" : "💡 Insights"}
        </button>
        <div style={{ opacity: .6, fontSize: 13 }}>
          Produces quick takeaways grounded in your docs.
        </div>
      </div>
      {text && (
        <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.5, opacity: .92 }}>
          {text}
        </div>
      )}
    </div>
  );
}
