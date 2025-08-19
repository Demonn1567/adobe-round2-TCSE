export default function SourcesToolbar({ onClear, onUnhighlight }) {
  return (
    <div style={{ display: "flex", gap: 8 }}>
      <button className="btnGhost" onClick={onUnhighlight} title="Clear in-PDF search highlights">
        Clear highlights
      </button>
      <button className="btnGhost" onClick={onClear} title="Remove current results">
        Clear sources
      </button>
    </div>
  );
}
