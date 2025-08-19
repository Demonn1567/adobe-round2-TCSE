import { useEffect, useMemo, useRef, useState } from "react";
import styles from "./MacTerminal.module.css";

export default function MacTerminal({
  script = [],
  typing = 22,
  pause = 420,
  loop = false,              
  title = "bash — 80x24",
  animate = false,            
}) {
  const [lines, setLines] = useState([]);
  const [cursorOn, setCursorOn] = useState(true);

  const timersRef = useRef(new Set());
  const runningRef = useRef(false);

  const schedule = (fn, ms) => {
    const id = window.setTimeout(fn, ms);
    timersRef.current.add(id);
    return id;
  };
  const clearTimers = () => {
    timersRef.current.forEach((id) => window.clearTimeout(id));
    timersRef.current.clear();
  };

  const steps = useMemo(() => {
    const out = [];
    for (const s of script) {
      out.push({ kind: "cmd", text: s.cmd });
      for (const o of s.out || []) out.push({ kind: "out", text: o });
    }
    return out;
  }, [script]);

  useEffect(() => {
    const id = window.setInterval(() => setCursorOn((c) => !c), 530);
    return () => window.clearInterval(id);
  }, []);

  useEffect(() => {
    if (!animate || runningRef.current) return;

    runningRef.current = true;
    clearTimers();
    setLines([]);

    const prefersReduced =
      typeof window !== "undefined" &&
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    (async () => {
      do {
        for (let i = 0; i < steps.length; i++) {
          const s = steps[i];
          const text = (s.kind === "cmd" ? "$ " : "") + s.text;

          if (prefersReduced) {
            setLines((prev) => [...prev, text]);
          } else {
            await typeLine(text, setLines, typing, schedule);
            await sleep(pause, schedule);
          }
        }

        if (loop && !prefersReduced) {
          await sleep(800, schedule);
          setLines([]);
        }
      } while (loop && !prefersReduced);

      runningRef.current = false;
    })();

    return () => {
      clearTimers();
    };
  }, [animate, steps, typing, pause, loop]);

  return (
    <div className={styles.shell} aria-label="Terminal window">
      <div className={styles.titlebar}>
        <span className={`${styles.dot} ${styles.red}`} />
        <span className={`${styles.dot} ${styles.yellow}`} />
        <span className={`${styles.dot} ${styles.green}`} />
        <div className={styles.winTitle}>{title}</div>
      </div>
      <div className={styles.body}>
        {lines.map((l, i) => (
          <div key={i} className={styles.line}>{l}</div>
        ))}
        <div className={styles.line}>
          <span className={styles.cursor} style={{ opacity: cursorOn ? 1 : 0 }}>▮</span>
        </div>
      </div>
    </div>
  );
}


function sleep(ms, schedule) {
  return new Promise((resolve) => schedule(resolve, ms));
}

function typeLine(text, setLines, speed, schedule) {
  return new Promise((resolve) => {
    let i = 0;

    const tick = () => {
      setLines((prev) => {
        const next = [...prev];
        if (i === 0) next.push(text[0] || "");
        else next[next.length - 1] = text.slice(0, i + 1);
        return next;
      });

      if (i < text.length - 1) {
        i += 1;
        const jitter = Math.max(10, speed + Math.round(Math.random() * 28 - 14));
        schedule(tick, jitter);
      } else {
        resolve();
      }
    };

    tick();
  });
}
