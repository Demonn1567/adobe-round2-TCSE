const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8080/api";
const TIMEOUT_MS = 60000;


function abortableFetch(url, options = {}, timeout = TIMEOUT_MS) {
  const ctrl = new AbortController();
  const id = setTimeout(() => ctrl.abort(), timeout);
  return fetch(url, { ...options, signal: ctrl.signal }).finally(() =>
    clearTimeout(id)
  );
}

async function asJson(res) {
  const text = await res.text();
  try {
    return JSON.parse(text);
  } catch {
    throw new Error(text || `${res.status} ${res.statusText}`);
  }
}

async function get(path) {
  const res = await abortableFetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(await res.text());
  return asJson(res);
}

async function post(path, body) {
  const res = await abortableFetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body ?? {}),
  });
  if (!res.ok) throw new Error(await res.text());
  return asJson(res);
}

async function postMultipart(path, formData) {
  const res = await abortableFetch(`${BASE}${path}`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(await res.text());
  return asJson(res);
}


export async function uploadFresh(file) {
  if (!file) throw new Error("No file provided.");
  const fd = new FormData();
  fd.append("file", file);
  const data = await postMultipart("/upload/fresh", fd);

  let docIds = [];
  if (Array.isArray(data?.docIds) && data.docIds.length) {
    docIds = data.docIds.map(String);
  } else if (Array.isArray(data?.docs)) {
    docIds = data.docs.map((d) => d?.docId).filter(Boolean).map(String);
  } else if (data?.docId) {
    docIds = [String(data.docId)];
  }
  return { ...data, docIds };
}

export async function uploadMany(files) {
  const pdfs = Array.from(files).filter(
    (f) => f.type === "application/pdf" || /\.pdf$/i.test(f.name)
  );
  if (!pdfs.length) throw new Error("No PDF files provided.");

  try {
    const fd = new FormData();
    pdfs.forEach((f) => fd.append("files", f));
    const data = await postMultipart("/upload/batch", fd);
    const docIds = (Array.isArray(data?.docIds) ? data.docIds : [])
      .map(String)
      .filter(Boolean);
    return { ...data, docIds };
  } catch {
    const all = [];
    for (const f of pdfs) {
      const res = await uploadFresh(f);
      all.push(...(res.docIds || []));
    }
    return { ok: true, docIds: all };
  }
}

export async function uploadZip(zipFile) {
  if (!zipFile) throw new Error("No zip provided.");
  const fd = new FormData();
  fd.append("file", zipFile);
  const data = await postMultipart("/upload/zip", fd);
  const docIds = (Array.isArray(data?.docIds) ? data.docIds : [])
    .map(String)
    .filter(Boolean);
  return { ...data, docIds };
}


export async function answerSmart(payload) {
  if (!payload?.query || !payload.query.trim()) {
    throw new Error("Query is empty.");
  }
  return post("/answer/smart", payload);
}

export async function related(payload) {
  return post("/answer/related", payload);
}

export async function getInsights(payload) {
  return post("/answer/insights", payload);
}


/**. (NOTES FOR THE EVALUATORS BY TEAM TCSE)
 * Force OpenAI voices in the picker by default.
 * Falls back to a tiny built-in OpenAI set if backend returns 503,
 * so the UI never gets stuck on "Loading voices…".
 */
export async function listVoices(arg = { locale: "en", prefer: "openai" }) {
  let locale = "en";
  let prefer = "openai";
  if (typeof arg === "string") {
    locale = arg;
  } else if (arg && typeof arg === "object") {
    locale = arg.locale ?? "en";
    prefer = arg.prefer ?? "openai";
  }

  const qs = new URLSearchParams({ locale, prefer });
  try {
    const data = await get(`/tts/voices?${qs.toString()}`);
    const arr = Array.isArray(data) ? data : data?.voices ?? [];
    if (arr.length) return arr;
  } catch {
  }

  return [
    { shortName: "alloy", name: "alloy", locale: "en-US" },
    { shortName: "aria", name: "aria", locale: "en-US" },
    { shortName: "verse", name: "verse", locale: "en-US" },
    { shortName: "luna", name: "luna", locale: "en-US" },
    { shortName: "cove", name: "cove", locale: "en-US" },
    { shortName: "juniper", name: "juniper", locale: "en-US" },
  ];
}

export async function getTtsStatus() {
  try {
    return await get("/tts/status");
  } catch {
    return null;
  }
}


export function buildAudioUrl(relativeUrl) {
  if (!relativeUrl) return null;
  try {
    return new URL(relativeUrl).toString();
  } catch {
    const trimmed = relativeUrl.startsWith("/") ? relativeUrl : `/${relativeUrl}`;
    const apiBase = new URL(BASE);
    return `${apiBase.origin}${trimmed}`;
  }
}
