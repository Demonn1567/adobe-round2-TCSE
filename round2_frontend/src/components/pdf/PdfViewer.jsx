import { useEffect, useRef, forwardRef, useImperativeHandle } from "react";
import "./pdf.css";
import GlassPdf from "../glassPdf/glassPdf";
const PdfViewer = forwardRef(function PdfViewer(
  { url, fileName = "Document.pdf", onReady, onTextSelected, onOpeningChange },
  ref
) {
  const divId = useRef(`adobe-view-${Math.random().toString(36).slice(2)}`);
  const adobeViewRef = useRef(null);
  const viewerRef = useRef(null);
  const overlayRef = useRef(null); 

  useImperativeHandle(ref, () => ({
    async goTo(page = 1, yRatio = 0) {
      if (!viewerRef.current) return;
      try {
        const apis = await viewerRef.current.getAPIs();
        await apis.gotoLocation({ pageNumber: page, yOffset: yRatio });
      } catch (e) {
        console.warn("gotoLocation failed:", e);
      }
    },
    async highlightHits(bands = []) {
      ensureOverlay();
      renderBands(bands);
    },
    async clearHighlights() {
      if (overlayRef.current) overlayRef.current.innerHTML = "";
    },
  }));

  function ensureOverlay() {
    if (!overlayRef.current) {
      const host = document.getElementById(divId.current);
      const ov = document.createElement("div");
      ov.className = "pdf-overlay";
      host?.appendChild(ov);
      overlayRef.current = ov;
    }
  }
  function renderBands(bands) {
    if (!overlayRef.current) return;
    overlayRef.current.innerHTML = "";
    bands.forEach((b, i) => {
      const el = document.createElement("div");
      el.className = "pdf-highlight-band";
      el.style.top = `${Math.max(0, Math.min(100, (b?.y ?? 0) * 100))}%`;
      el.style.background = b?.color || "rgba(255,215,0,.45)"; 
      el.title = `p.${b?.page || "?"}`;
      overlayRef.current.appendChild(el);
    });
  }

  useEffect(() => {
    let cancelled = false;

    async function ensureSdk() {
      if (window.AdobeDC?.View) return;
      await new Promise((resolve, reject) => {
        const scriptId = "adobe-dc-view";
        if (document.getElementById(scriptId)) {
          const check = setInterval(() => {
            if (window.AdobeDC?.View) {
              clearInterval(check);
              resolve();
            }
          }, 50);
          setTimeout(() => {
            clearInterval(check);
            window.AdobeDC?.View ? resolve() : reject(new Error("AdobeDC View failed to load"));
          }, 5000);
          return;
        }
        const s = document.createElement("script");
        s.id = scriptId;
        s.src = "https://documentcloud.adobe.com/view-sdk/main.js";
        s.onload = () => resolve();
        s.onerror = () => reject(new Error("Failed to load Adobe View SDK"));
        document.head.appendChild(s);
      });
    }

    async function openPdf() {
      if (!url) return;
      onOpeningChange?.(true);
      await ensureSdk();
      if (cancelled) return;

      const clientId = import.meta.env.VITE_ADOBE_EMBED_API_KEY || window.__ADOBE_EMBED_API_KEY;
      if (!clientId) {
        console.error("Missing VITE_ADOBE_EMBED_API_KEY");
      }

      const view = new window.AdobeDC.View({
        clientId,
        divId: divId.current,
      });
      adobeViewRef.current = view;

      const previewPromise = view.previewFile(
        {
          content: { location: { url } },
          metaData: { fileName },
        },
        {
          embedMode: "SIZED_CONTAINER",
          showDownloadPDF: false,
          showPrintPDF: false,
          showLeftHandPanel: false,
          dockPageControls: false,
          enableAnnotationAPIs: false,
          showZoomControl: true,
          defaultViewMode: "FIT_PAGE",
          backgroundColor: "#101426",
        }
      );

      previewPromise.then(async (viewer) => {
        if (cancelled) return;
        viewerRef.current = viewer;

        try { await viewer.getAPIs(); } catch {}
        onOpeningChange?.(false);
        onReady?.();

        try {
          view.registerCallback(
            window.AdobeDC.View.Enum.CallbackType.EVENT_LISTENER,
            async (event) => {
              if (event?.type === window.AdobeDC.View.Enum.Events.TEXT_SELECTED) {
                let text = "";
                try {
                  const apis = await viewer.getAPIs();
                  const result = await apis.getSelectedContent();
                  text = typeof result === "string"
                    ? result
                    : (result?.data || result?.selectedText || "");
                } catch (e) {
                  text = event?.data?.selectedText || "";
                }
                if (text && text.trim()) onTextSelected?.(text.trim());
              }
            },
            { enablePDFAnalytics: false }
          );
        } catch (err) {
          console.warn("Event register failed:", err);
        }
      });

      previewPromise.catch((e) => {
        console.error("previewFile error:", e);
        onOpeningChange?.(false);
      });
    }

    openPdf();
    return () => { cancelled = true; };
  }, [url, fileName]);

  return <div id={divId.current} className="pdf-host" ><GlassPdf/></div>;
});

export default PdfViewer;
