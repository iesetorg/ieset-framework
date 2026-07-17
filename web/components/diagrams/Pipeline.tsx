// Diagram C — Pre-registration → run → verdict pipeline.
// Horizontal left-to-right with a loop back from open correction.

const stages: {
  x: number;
  label: string;
  sub: string;
  tone: "spec" | "data" | "run" | "review";
}[] = [
  { x: 90, label: "Spec commit", sub: "hypothesis.yaml", tone: "spec" },
  { x: 240, label: "Schema + preflight", sub: "CI validates", tone: "spec" },
  { x: 390, label: "Vintage pin", sub: "data/vintages/*", tone: "data" },
  { x: 540, label: "Run", sub: "replication.py", tone: "run" },
  { x: 690, label: "Artifacts", sub: "diagnostics + card", tone: "run" },
  { x: 840, label: "Publish", sub: "/h/<id>", tone: "run" },
];

const toneMap: Record<string, { fill: string; stroke: string; text: string; chip: string }> = {
  spec: { fill: "#ffffff", stroke: "#1f1f1f", text: "#1f1f1f", chip: "pre-registration" },
  data: { fill: "#fafaf8", stroke: "#8a8a8a", text: "#1f1f1f", chip: "data pin" },
  run: { fill: "#e1ecf5", stroke: "#1f4e79", text: "#1f4e79", chip: "execution" },
  review: { fill: "#fdf1da", stroke: "#b7791f", text: "#b7791f", chip: "adversarial" },
};

export function Pipeline({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 900 460"
      className={`block h-auto w-full ${className}`}
      role="img"
      aria-labelledby="pipeline-title"
    >
      <title id="pipeline-title">Pre-registration → run → verdict pipeline</title>

      <defs>
        <marker
          id="arrow-p"
          viewBox="0 0 10 10"
          refX="8"
          refY="5"
          markerWidth="8"
          markerHeight="8"
          orient="auto-start-reverse"
        >
          <path d="M0 0 L10 5 L0 10 Z" fill="#1f1f1f" />
        </marker>
        <marker
          id="arrow-loop"
          viewBox="0 0 10 10"
          refX="8"
          refY="5"
          markerWidth="8"
          markerHeight="8"
          orient="auto-start-reverse"
        >
          <path d="M0 0 L10 5 L0 10 Z" fill="#b7791f" />
        </marker>
      </defs>

      {/* Banner — the pre-registration invariant */}
      <rect
        x="40"
        y="30"
        width="820"
        height="40"
        rx="6"
        fill="#fafaf8"
        stroke="#ececec"
      />
      <text
        x="60"
        y="55"
        fontFamily="system-ui, sans-serif"
        fontSize="12"
        fontWeight="700"
        fill="#1f1f1f"
      >
        Invariant 1 — the spec commit timestamp must predate every run.
      </text>
      <text
        x="60"
        y="69"
        fontFamily="system-ui, sans-serif"
        fontSize="11.5"
        fill="#636363"
      >
        CI rejects any run where git log shows the spec was edited after data was examined.
      </text>

      {/* Stage boxes */}
      {stages.map((s, i) => {
        const t = toneMap[s.tone];
        return (
          <g key={i}>
            <rect
              x={s.x - 60}
              y="150"
              width="120"
              height="80"
              rx="8"
              fill={t.fill}
              stroke={t.stroke}
              strokeWidth="1.5"
            />
            <text
              x={s.x}
              y="135"
              textAnchor="middle"
              fontFamily="system-ui, sans-serif"
              fontSize="10"
              fontWeight="600"
              letterSpacing="0.08em"
              fill={t.stroke}
            >
              {`step ${i + 1}`}
            </text>
            <text
              x={s.x}
              y="185"
              textAnchor="middle"
              fontFamily="system-ui, sans-serif"
              fontSize="13"
              fontWeight="700"
              fill={t.text}
            >
              {s.label}
            </text>
            <text
              x={s.x}
              y="205"
              textAnchor="middle"
              fontFamily="ui-monospace, monospace"
              fontSize="10.5"
              fill={t.text}
            >
              {s.sub}
            </text>
            {/* connectors between stages */}
            {i < stages.length - 1 && (
              <line
                x1={s.x + 60}
                y1="190"
                x2={stages[i + 1].x - 60}
                y2="190"
                stroke="#1f1f1f"
                strokeWidth="1.3"
                markerEnd="url(#arrow-p)"
              />
            )}
          </g>
        );
      })}

      {/* Phase bands */}
      <g>
        <rect x="40" y="260" width="260" height="30" rx="4" fill="#ffffff" stroke="#1f1f1f" />
        <text
          x="170"
          y="280"
          textAnchor="middle"
          fontFamily="system-ui, sans-serif"
          fontSize="11.5"
          fontWeight="600"
          fill="#1f1f1f"
        >
          Pre-registration — no data yet
        </text>

        <rect x="315" y="260" width="140" height="30" rx="4" fill="#fafaf8" stroke="#8a8a8a" />
        <text
          x="385"
          y="280"
          textAnchor="middle"
          fontFamily="system-ui, sans-serif"
          fontSize="11.5"
          fontWeight="600"
          fill="#636363"
        >
          Data bound
        </text>

        <rect x="470" y="260" width="390" height="30" rx="4" fill="#e1ecf5" stroke="#1f4e79" />
        <text
          x="665"
          y="280"
          textAnchor="middle"
          fontFamily="system-ui, sans-serif"
          fontSize="11.5"
          fontWeight="600"
          fill="#1f4e79"
        >
          Execution — deterministic, replicable
        </text>
      </g>

      {/* Open correction loop */}
      <g>
        <rect
          x="330"
          y="340"
          width="240"
          height="64"
          rx="8"
          fill="#fdf1da"
          stroke="#b7791f"
          strokeWidth="1.5"
        />
        <text
          x="450"
          y="364"
          textAnchor="middle"
          fontFamily="system-ui, sans-serif"
          fontSize="13"
          fontWeight="700"
          fill="#b7791f"
        >
          Open correction pilot
        </text>
        <text
          x="450"
          y="382"
          textAnchor="middle"
          fontFamily="system-ui, sans-serif"
          fontSize="11"
          fill="#b7791f"
        >
          no active bounty programme;
        </text>
        <text
          x="450"
          y="396"
          textAnchor="middle"
          fontFamily="system-ui, sans-serif"
          fontSize="11"
          fill="#b7791f"
        >
          refutation reruns the spec
        </text>

        {/* Publish → review */}
        <path
          d="M 840 230 Q 840 300 570 370"
          fill="none"
          stroke="#b7791f"
          strokeWidth="1.5"
          markerEnd="url(#arrow-loop)"
        />
        {/* Review → spec (loop back) */}
        <path
          d="M 330 370 Q 90 300 90 230"
          fill="none"
          stroke="#b7791f"
          strokeWidth="1.5"
          strokeDasharray="4 3"
          markerEnd="url(#arrow-loop)"
        />
        <text
          x="190"
          y="315"
          fontFamily="system-ui, sans-serif"
          fontSize="11"
          fill="#b7791f"
        >
          falsification ⇒ new spec, new run
        </text>
      </g>

      {/* Bottom note */}
      <text
        x="40"
        y="440"
        fontFamily="system-ui, sans-serif"
        fontSize="11.5"
        fill="#636363"
      >
        <tspan fontWeight="600" fill="#1f1f1f">Every step is git-tracked.</tspan>{" "}
        Strict spec-before-run ancestry earns a verified badge; same-commit legacy records do not.
      </text>
    </svg>
  );
}
