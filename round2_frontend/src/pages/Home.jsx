import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import MacTerminal from "../components/terminal/MacTerminal.jsx";
import styles from "./Home.module.css";

const script = [
  { cmd: "prism upload ./docs/*.pdf", out: ["Indexed 8 PDFs · 74 pages · ~1.2s"] },
  {
    cmd: 'prism ask "Summarize the Docker requirements"',
    out: ["• linux/amd64 base image", "• CPU: amd64 (x86_64)", "• No GPU deps · offline build"],
  },
  {
    cmd: "prism related --doc this.pdf",
    out: ["Found 5 passages ≥0.80 confidence", "Jump: p.4 · p.7 · p.10 · p.12 · p.13"],
  },
  { cmd: "prism podcast --voice en-US-JennyNeural", out: ["Generated 2m38s narrated overview"] },
];

export default function Home() {
  const [animateTerminal, setAnimateTerminal] = useState(false);
  const termRef = useRef(null);
  const hasPlayed = useRef(false);

  useEffect(() => {
    const el = termRef.current;
    if (!el) return;

    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasPlayed.current) {
          hasPlayed.current = true;
          setAnimateTerminal(true);
        }
      },
      { threshold: 0.3, rootMargin: "0px 0px -20% 0px" }
    );

    io.observe(el);
    return () => io.disconnect();
  }, []);

  return (
    <div className={styles.page}>
      <section className={styles.section} style={{ background: "none" }}>
        <div className={styles.container}>
          <h2 className={styles.mainHeading}>Why Prism</h2>
          <p className={styles.lead}>
            Minimal UI, maximum signal. Prism connects the dots across your PDFs, highlights what
            matters, and speaks the answer.
          </p>

          <div className={styles.grid}>
            <Card
              title="Context-aware highlights"
              body="Jump straight to the right passages with confidence scores."
            />
            <Card
              title="Grounded answers"
              body="Paste a small selection and get a precise, sourced answer."
            />
            <Card
              title="Narrated insights"
              body="Generate short audio overviews in your favorite neural voice."
            />
          </div>
        </div>
      </section>

      <section className={styles.section} style={{ background: "none" }}>
        <div className={styles.container}>
          <h2 className={styles.workTitle}>How it works</h2>
          <ol className={styles.steps} aria-label="How Prism works">
            <li style={{ background: "transparent", border: "1px solid rgba(255,255,255,.06)" }}>
              <span>1</span> Drop PDFs (or a .zip). Local-friendly indexing.
            </li>
            <li style={{ background: "transparent", border: "1px solid rgba(255,255,255,.06)" }}>
              <span>2</span> Select a snippet in the PDF to ground your question.
            </li>
            <li style={{ background: "transparent", border: "1px solid rgba(255,255,255,.06)" }}>
              <span>3</span> Get an answer with citations, highlights, and jump-links.
            </li>
            <li style={{ background: "transparent", border: "1px solid rgba(255,255,255,.06)" }}>
              <span>4</span> Tap Insights for crisp bullets or enable Narrate.
            </li>
          </ol>
        </div>
      </section>

      <section className={styles.section} ref={termRef} style={{ background: "none" }}>
        <div className={`${styles.container} ${styles.split}`}>
          <div className={styles.colText}>
            <h2 className={styles.cliHeading}>CLI that mirrors the app</h2>
            <p className={styles.cliLead}>
              Prefer keyboard? Use the same pipeline in a tiny CLI. Upload, ask, highlight, and
              generate narration — without leaving the terminal.
            </p>
            <div className={styles.row}>
              <Link to="/workspace" className={styles.ctaPrimary}>
                Open Workspace
              </Link>
              <a href="#demo" className={styles.ctaGhost}>
                Run the demo
              </a>
            </div>
          </div>

          <div className={styles.colTerm} aria-hidden="true">
            <MacTerminal script={script} typing={22} pause={420} loop={false} animate={animateTerminal} />
          </div>
        </div>
      </section>

      <section className={styles.section} style={{ background: "none" }}>
        <div className={`${styles.container} ${styles.center}`}>
          {/* <h2 className={styles.h2}>Beyond the page. Deeper insights.</h2> */}
          <p className={styles.startLead}>Start a focused session now.</p>
          <Link to="/workspace" className={styles.ctaPrimary}>
            Start a New Session
          </Link>
        </div>
      </section>
    </div>
  );
}

function Card({ title, body }) {
  return (
    <div className={styles.card}>
      <div className={styles.cardTitle}>{title}</div>
      <div className={styles.cardBody}>{body}</div>
    </div>
  );
}
