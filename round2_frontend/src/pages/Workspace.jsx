import { useEffect, useMemo, useRef, useState } from "react";
import styles from "./Workspace.module.css";
import PdfViewer from "../components/pdf/PdfViewer.jsx";
import { answerSmart, listVoices, buildAudioUrl, related, getInsights } from "../lib/api.js";
import VoiceSelect from "../components/voiceControl/voiceControl.jsx";
import GlassLoading from "../components/glassLoading/glassLoading.jsx";

function Chip({ active, onClick, children, title }) {
  return (
    <div
      className={`${styles.chip} ${active ? styles.chipActive : ""}`}
      onClick={onClick}
      role="button"
      tabIndex={0}
      title={title}
    >
      {children}
    </div>
  );
}

function pickDefaultVoiceShortName(voices) {
  if (!Array.isArray(voices) || voices.length === 0) return "";
  const jenny = voices.find((v) =>
    (v.shortName || v.name || "").toLowerCase().includes("jenny")
  );
  return jenny?.shortName || voices[0]?.shortName || voices[0]?.name || "";
}

export default function Workspace() {
  const [pdfUrl, setPdfUrl] = useState(null);
  const [pdfName, setPdfName] = useState("Document.pdf");
  const [isOpening, setIsOpening] = useState(false);

  const [deep, setDeep] = useState(false);
  const [narrate, setNarrate] = useState(false);
  const [voices, setVoices] = useState([]);
  const [voice, setVoice] = useState("");
  const [query, setQuery] = useState("");
  const [busy, setBusy] = useState(false);

  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [audioUrl, setAudioUrl] = useState(null);

  const [hlOn, setHlOn] = useState(false);
  const [relBusy, setRelBusy] = useState(false);
  const [onlyThisDoc, setOnlyThisDoc] = useState(false);

  const pdfRef = useRef(null);

  useEffect(() => {
    const savedUrl = sessionStorage.getItem("prism.lastFreshUrl");
    const savedName = sessionStorage.getItem("prism.lastFreshName");
    if (savedUrl) {
      setPdfUrl(savedUrl);
      setPdfName(savedName || "Document.pdf");
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const raw = await listVoices("en");
        const vs = Array.isArray(raw) ? raw : raw?.voices || [];
        if (cancelled) return;
        setVoices(vs);
        setVoice((prev) => prev || pickDefaultVoiceShortName(vs));
      } catch {
        if (!cancelled) {
          setVoices([]);
          setVoice("");
        }
      }
    })();
    return () => { cancelled = true; };
  }, []);

  function selectedDocIdsOrNull() {
    if (!onlyThisDoc) return undefined; 
    const id = sessionStorage.getItem("prism.lastFreshDocId");
    return id ? [id] : undefined;
  }

  function handleTextSelected(text) {
    const trimmed = text.trim();
    if (!trimmed) return;
    const short = trimmed.length > 600 ? `${trimmed.slice(0, 600)}…` : trimmed;
    setQuery(short);
  }

  async function onAsk() {
    const q = query.trim();
    if (!q) return;
    setBusy(true);
    setAnswer("");
    setSources([]);
    setAudioUrl(null);
    try {
      const chosenVoice = narrate ? voice || pickDefaultVoiceShortName(voices) || undefined : undefined;
      const res = await answerSmart({
        query: q,
        k: 5,
        deep,
        tts: narrate,
        voice: chosenVoice,
        docIds: selectedDocIdsOrNull(),
      });
      setAnswer(res?.answer || "");
      setSources(Array.isArray(res?.sources) ? res.sources : []);
      setAudioUrl(buildAudioUrl(res?.audio?.url));
    } catch (e) {
      setAnswer(`⚠️ ${e?.message || "Failed to get answer."}`);
    } finally {
      setBusy(false);
    }
  }

  async function onInsights() {
    const q = (query || answer).trim();
    if (!q) return;
    setBusy(true);
    try {
      const res = await getInsights({
        query: q,
        k: 5,
        deep: true,
        docIds: selectedDocIdsOrNull(),
      });
      const bullet = "💡 Insights";
      const txt = res?.answer || "";
      setAnswer((prev) => (prev ? `${prev}\n\n${bullet}\n${txt}` : `${bullet}\n${txt}`));
      if (Array.isArray(res?.sources)) setSources(res.sources);
    } finally {
      setBusy(false);
    }
  }

  async function toggleHighlights() {
    const want = !hlOn;
    setHlOn(want);
    if (!want) {
      await pdfRef.current?.clearHighlights?.();
      return;
    }
    const q = (query || answer).trim();
    if (!q) return;
    setRelBusy(true);
    try {
      const rr = await related({ query: q, k: 6, deep: false, docIds: selectedDocIdsOrNull() });
      const hits = Array.isArray(rr?.hits) ? rr.hits : [];
      setSources(hits);
      const bands = hits.map((h, i) => ({
        page: Math.max(1, Number(h.page || 1)),
        y: typeof h.y === "number" ? h.y : (0.2 + i * 0.08),
        color: i % 2 ? "rgba(0,255,170,.35)" : "rgba(255,215,0,.45)",
      }));
      await pdfRef.current?.highlightHits?.(bands);
    } catch (e) {
      console.error(e);
    } finally {
      setRelBusy(false);
    }
  }

  function clearAll() {
    setSources([]);
    setAnswer("");
    setAudioUrl(null);
    setHlOn(false);
    pdfRef.current?.clearHighlights?.();
  }

  function openLocalPdf() {
    const inp = document.createElement("input");
    inp.type = "file";
    inp.accept = "application/pdf";
    inp.onchange = () => {
      const file = inp.files?.[0];
      if (!file) return;
      const blobUrl = URL.createObjectURL(file);
      setPdfUrl(blobUrl);
      setPdfName(file.name || "Document.pdf");
      sessionStorage.setItem("prism.lastFreshUrl", blobUrl);
      sessionStorage.setItem("prism.lastFreshName", file.name || "Document.pdf");
    };
    inp.click();
  }

  const sourceChips = useMemo(() => {
    return (sources || []).slice(0, 12).map((s, idx) => (
      <div
        key={`${s.docId}-${s.sectionId}-${idx}`}
        className={styles.card}
        title="Click to jump"
        onClick={() => {
          const p = Math.max(1, Number(s.page || 1));
          const y = typeof s.y === "number" ? s.y : 0;
          pdfRef.current?.goTo?.(p, y);
        }}
      >
        <div className={styles.mono} style={{ marginBottom: 6 }}>
          {s.docOrigName || s.docTitle || s.docId}
        </div>
        <div style={{ fontWeight: 700, marginBottom: 6 }}>{s.sectionTitle || s.sectionId}</div>
        <div style={{ fontSize: 13, opacity: 0.8, lineHeight: 1.4 }}>{s.snippet}</div>
        <div style={{ marginTop: 8, display: "flex", gap: 8, alignItems: "center" }}>
          <span className={styles.badge}>p.{s.page || 1}</span>
          {typeof s.score === "number" && <span className={styles.badge}>score {(s.score).toFixed(2)}</span>}
        </div>
      </div>
    ));
  }, [sources]);

  return (
    <div className={styles.wrap}>
      <div className={`${styles.panel} ${styles.left}`}>
        <div className={styles.headerRow}>
          <div>Workspace</div>
          <div className={styles.rowChips} style={{ gap: 10 }}>
            <button className={styles.chip} onClick={openLocalPdf}>Open PDF</button>
            {isOpening && <div className={styles.badge}>Opening…</div>}
          </div>
        </div>

        <PdfViewer
          ref={pdfRef}
          url={pdfUrl}
          fileName={pdfName}
          onReady={() => {}}
          onOpeningChange={(v) => setIsOpening(v)}
          onTextSelected={handleTextSelected}
        />
      </div>

      <div className={styles.right}>
        <div className={styles.panel}>
          <div className={styles.headerRow}>
            <div>Ask your document</div>
            <div className={styles.rowChips}>
              <Chip active={deep} onClick={() => setDeep((d) => !d)}>Deep</Chip>

              <Chip active={hlOn} onClick={toggleHighlights} title="Toggle related highlights">
                {relBusy ? "Finding…" : "Highlights"}
              </Chip>
              <Chip onClick={onInsights} title="Generate insights for the current context">Insights</Chip>
              <Chip active={narrate} onClick={() => setNarrate((n) => !n)}>Narrate</Chip>
              <VoiceSelect narrate={narrate} voice={voice} setVoice={setVoice} voices={voices} />
              <Chip active={!!onlyThisDoc} onClick={() => setOnlyThisDoc(v => !v)} title="Restrict to the current uploaded PDF">
                This PDF only
              </Chip>
              <Chip onClick={clearAll} title="Clear answer, sources, highlights">Clear</Chip>
            </div>
          </div>

          <div className={styles.askBox}>
            <textarea
              className={styles.askArea}
              placeholder="Ask something about your doc… (Tip: copy a small selection from the PDF to ground the answer)"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <button className={styles.btn} onClick={onAsk} disabled={busy}>
              {busy ? "Thinking…" : "Ask"}
            </button>
          </div>
        </div>

        <div className={`${styles.panel} ${styles.answer}`}>
          <div className={styles.headerRow} style={{ padding: 0, marginBottom: 8 }}>
            <div>Answer</div>
          </div>
          <div className={styles.defaultText} style={{ whiteSpace: "pre-wrap", lineHeight: 1.6 }}>
            {answer || <GlassLoading loaderCount={4}></GlassLoading>}
          </div>
        </div>

        <div className={`${styles.panel} ${styles.sources}`}>
          <div className={styles.headerRow} style={{ padding: 0, marginBottom: 8 }}>
            <div>Sources</div>
          </div>
          <div className={styles.cards}>
            {sourceChips.length ? sourceChips : <div className={styles.defaultText}><GlassLoading loaderCount={2}></GlassLoading></div>}
          </div>
        </div>

        <div className={`${styles.panel} ${styles.audio}`}>
          <div className={styles.headerRow} style={{ padding: 0, marginBottom: 8 }}>
            <div>Narration</div>
          </div>
          {audioUrl ? (
            <audio src={audioUrl} controls style={{ width: "100%" }} />
          ) : (
            <div className={styles.defaultText}><GlassLoading loaderCount={2}></GlassLoading></div>
          )}
        </div>
      </div>
    </div>
  );
}
