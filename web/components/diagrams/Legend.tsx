// Diagram E — Legend / reading guide: verdict colors, badges, direction symbols, provenance dots.

export function Legend({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 900 520"
      className={`block h-auto w-full ${className}`}
      role="img"
      aria-labelledby="legend-title"
    >
      <title id="legend-title">Reading guide — colors, badges, and symbols across the site</title>

      {/* === Verdict tones === */}
      <text
        x="30"
        y="32"
        fontFamily="system-ui, sans-serif"
        fontSize="11"
        fontWeight="700"
        letterSpacing="0.1em"
        fill="#636363"
      >
        VERDICT TONES
      </text>
      <text
        x="30"
        y="51"
        fontFamily="system-ui, sans-serif"
        fontSize="12.5"
        fill="#636363"
      >
        A strip of colour at the top of every hypothesis / policy card.
      </text>

      {[
        { y: 72, color: "#2c7a4f", bg: "#dff1e4", label: "supported", note: "data ran as predicted, cleared threshold" },
        { y: 124, color: "#b7791f", bg: "#fdf1da", label: "partial / mixed", note: "some predictions held, others didn't" },
        { y: 176, color: "#9e2f2f", bg: "#f3d9d9", label: "refuted / weakened", note: "data ran opposite or failed threshold" },
        { y: 228, color: "#8a8a8a", bg: "#f3f3f1", label: "run pending", note: "registered, model not yet fired" },
      ].map((v, i) => (
        <g key={i}>
          <rect x="30" y={v.y} width="320" height="44" rx="4" fill="#ffffff" stroke="#d9d9d9" />
          <rect x="30" y={v.y} width="320" height="3" fill={v.color} />
          <rect x="40" y={v.y + 12} width="10" height="10" rx="2" fill={v.bg} stroke={v.color} />
          <text
            x="60"
            y={v.y + 21}
            fontFamily="system-ui, sans-serif"
            fontSize="13"
            fontWeight="700"
            fill={v.color}
          >
            {v.label}
          </text>
          <text
            x="60"
            y={v.y + 36}
            fontFamily="system-ui, sans-serif"
            fontSize="11"
            fill="#636363"
          >
            {v.note}
          </text>
        </g>
      ))}

      {/* === Axis direction symbols === */}
      <text
        x="380"
        y="32"
        fontFamily="system-ui, sans-serif"
        fontSize="11"
        fontWeight="700"
        letterSpacing="0.1em"
        fill="#636363"
      >
        AXIS DIRECTION
      </text>
      <text
        x="380"
        y="51"
        fontFamily="system-ui, sans-serif"
        fontSize="12.5"
        fill="#636363"
      >
        How a policy or movement moved an axis, not whether that is good or bad.
      </text>

      {[
        { y: 72, bg: "#dff1e4", fg: "#2c7a4f", sym: "↑", label: "+ increased", note: 'e.g. "more progressive taxation"' },
        { y: 124, bg: "#f3d9d9", fg: "#9e2f2f", sym: "↓", label: "− decreased", note: 'e.g. "less progressive taxation"' },
        { y: 176, bg: "#fdf1da", fg: "#b7791f", sym: "~", label: "mixed", note: "pushed in both directions" },
        { y: 228, bg: "#f3f3f1", fg: "#636363", sym: "—", label: "0 unchanged", note: "nominally on this axis, no actual movement" },
      ].map((d, i) => (
        <g key={i}>
          <rect x="380" y={d.y} width="320" height="44" rx="4" fill="#ffffff" stroke="#d9d9d9" />
          <rect x="394" y={d.y + 8} width="28" height="28" rx="4" fill={d.bg} />
          <text
            x="408"
            y={d.y + 28}
            textAnchor="middle"
            fontFamily="system-ui, sans-serif"
            fontSize="18"
            fontWeight="700"
            fill={d.fg}
          >
            {d.sym}
          </text>
          <text
            x="434"
            y={d.y + 21}
            fontFamily="system-ui, sans-serif"
            fontSize="13"
            fontWeight="700"
            fill="#1f1f1f"
          >
            {d.label}
          </text>
          <text
            x="434"
            y={d.y + 36}
            fontFamily="system-ui, sans-serif"
            fontSize="11"
            fill="#636363"
          >
            {d.note}
          </text>
        </g>
      ))}

      {/* === Data provenance dots === */}
      <text
        x="30"
        y="312"
        fontFamily="system-ui, sans-serif"
        fontSize="11"
        fontWeight="700"
        letterSpacing="0.1em"
        fill="#636363"
      >
        DATA PROVENANCE
      </text>
      <text
        x="30"
        y="331"
        fontFamily="system-ui, sans-serif"
        fontSize="12.5"
        fill="#636363"
      >
        Dot next to every data source shows whether the pipeline can fetch it today.
      </text>

      {[
        { y: 352, fg: "#2c7a4f", label: "ready", note: "publisher fetcher exists, vintage pinned, data on disk" },
        { y: 400, fg: "#b7791f", label: "pending", note: "publisher known, fetcher not yet wired" },
        { y: 448, fg: "#9e2f2f", label: "gap", note: "no known publisher; the variable must be reconstructed" },
      ].map((p, i) => (
        <g key={i}>
          <circle cx="44" cy={p.y + 10} r="5" fill={p.fg} />
          <text
            x="60"
            y={p.y + 14}
            fontFamily="system-ui, sans-serif"
            fontSize="13"
            fontWeight="700"
            fill={p.fg}
          >
            {p.label}
          </text>
          <text
            x="60"
            y={p.y + 30}
            fontFamily="system-ui, sans-serif"
            fontSize="11.5"
            fill="#636363"
          >
            {p.note}
          </text>
        </g>
      ))}

      {/* === Badges === */}
      <text
        x="380"
        y="312"
        fontFamily="system-ui, sans-serif"
        fontSize="11"
        fontWeight="700"
        letterSpacing="0.1em"
        fill="#636363"
      >
        BADGES YOU&apos;LL SEE
      </text>
      <text
        x="380"
        y="331"
        fontFamily="system-ui, sans-serif"
        fontSize="12.5"
        fill="#636363"
      >
        Short-form chips that carry information density without prose.
      </text>

      {[
        { y: 352, bg: "#dff1e4", fg: "#2c7a4f", label: "pre-reg" },
        { y: 352, bg: "#fdf1da", fg: "#b7791f", label: "candidate", x: 470 },
        { y: 352, bg: "#e1ecf5", fg: "#1f4e79", label: "inferred", x: 570 },
        { y: 400, bg: "#1f4e79", fg: "#ffffff", label: "treated", rect: true },
        { y: 400, bg: "#ffffff", fg: "#636363", label: "donor / comparison", x: 470, bordered: true },
        { y: 448, bg: "#fdf1da", fg: "#b7791f", label: "unintended", italic: true },
      ].map((b, i) => (
        <g key={i}>
          <rect
            x={b.x ?? 394}
            y={b.y + 2}
            width={Math.max(56, 16 + b.label.length * 7)}
            height="20"
            rx="3"
            fill={b.bg}
            stroke={b.bordered ? "#d9d9d9" : undefined}
          />
          <text
            x={(b.x ?? 394) + 8}
            y={b.y + 16}
            fontFamily="system-ui, sans-serif"
            fontSize="11"
            fontWeight="600"
            fontStyle={b.italic ? "italic" : "normal"}
            fill={b.fg}
          >
            {b.label}
          </text>
        </g>
      ))}

      <text
        x="394"
        y="470"
        fontFamily="system-ui, sans-serif"
        fontSize="11"
        fill="#636363"
      >
        Status badges: pre-reg = committed to git before data was examined. Candidate = still in draft.
      </text>
      <text
        x="394"
        y="485"
        fontFamily="system-ui, sans-serif"
        fontSize="11"
        fill="#636363"
      >
        Chart badges: treated = the policy subject. Donor = the comparison unit the estimator contrasts against.
      </text>
      <text
        x="394"
        y="500"
        fontFamily="system-ui, sans-serif"
        fontSize="11"
        fill="#636363"
      >
        Inferred = the link was derived by axis overlap, not hand-authored.
      </text>
    </svg>
  );
}
