// Diagram B — Three user journeys through the system.

interface Step {
  x: number;
  label: string;
  sub?: string;
  route?: string;
  tone?: "default" | "accent" | "muted";
}

interface Lane {
  y: number;
  who: string;
  question: string;
  steps: Step[];
  endNote: string;
}

const lanes: Lane[] = [
  {
    y: 110,
    who: "Journalist",
    question: '"Does rent control reduce housing supply?"',
    steps: [
      { x: 260, label: "Google / referral", sub: "landing query" },
      { x: 420, label: "/h/<id>", sub: "hypothesis page", tone: "accent" },
      { x: 580, label: "Read verdict +", sub: "falsification rule" },
      { x: 740, label: "Cite permalink", sub: "with BibTeX" },
    ],
    endNote: "Needs: one page, plain-English verdict, citable URL",
  },
  {
    y: 270,
    who: "Researcher",
    question: '"Is this result actually replicable?"',
    steps: [
      { x: 260, label: "/h/<id>", sub: "hypothesis page", tone: "accent" },
      { x: 420, label: "git clone", sub: "repo" },
      { x: 580, label: "python replication.py", sub: "engine/runs/<id>/" },
      { x: 740, label: "Diff diagnostics", sub: "vs published" },
    ],
    endNote: "Needs: pinned vintage, deterministic seed, published artifacts",
  },
  {
    y: 430,
    who: "Policymaker",
    question: '"We\'re drafting reform X — what happened historically?"',
    steps: [
      { x: 260, label: "/q  (Phase 2)", sub: "describe axes moved", tone: "accent" },
      { x: 420, label: "Ranked analogues", sub: "similar historical policies" },
      { x: 580, label: "/p/<id>", sub: "per-match deep dive" },
      { x: 740, label: "/h/<id>", sub: "evidence + verdict" },
    ],
    endNote: "Needs: axis fingerprint match, outcome comparison across cases",
  },
];

function toneFill(tone: Step["tone"]): { fill: string; stroke: string; text: string } {
  if (tone === "accent") return { fill: "#e1ecf5", stroke: "#1f4e79", text: "#1f4e79" };
  if (tone === "muted") return { fill: "#fafaf8", stroke: "#d9d9d9", text: "#636363" };
  return { fill: "#ffffff", stroke: "#1f1f1f", text: "#1f1f1f" };
}

export function UserJourneys({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 900 580"
      className={`block h-auto w-full ${className}`}
      role="img"
      aria-labelledby="user-journeys-title"
    >
      <title id="user-journeys-title">Three user journeys through the system</title>
      <defs>
        <marker
          id="arrow-j"
          viewBox="0 0 10 10"
          refX="8"
          refY="5"
          markerWidth="8"
          markerHeight="8"
          orient="auto-start-reverse"
        >
          <path d="M0 0 L10 5 L0 10 Z" fill="#636363" />
        </marker>
      </defs>

      {lanes.map((lane, laneIdx) => (
        <g key={lane.who}>
          {/* lane background */}
          <rect
            x="0"
            y={lane.y - 50}
            width="900"
            height="160"
            fill={laneIdx % 2 === 0 ? "#ffffff" : "#fafaf8"}
          />
          <line
            x1="0"
            y1={lane.y - 50}
            x2="900"
            y2={lane.y - 50}
            stroke="#ececec"
            strokeWidth="1"
          />

          {/* lane header */}
          <text
            x="20"
            y={lane.y - 26}
            fontFamily="system-ui, sans-serif"
            fontSize="11"
            fontWeight="700"
            letterSpacing="0.1em"
            fill="#636363"
          >
            {lane.who.toUpperCase()}
          </text>
          <text
            x="20"
            y={lane.y - 8}
            fontFamily="Georgia, serif"
            fontSize="14"
            fontStyle="italic"
            fill="#1f1f1f"
          >
            {lane.question}
          </text>

          {/* step boxes + connectors */}
          {lane.steps.map((step, i) => {
            const t = toneFill(step.tone);
            const nextX = lane.steps[i + 1]?.x;
            return (
              <g key={i}>
                {nextX !== undefined && (
                  <line
                    x1={step.x + 60}
                    y1={lane.y + 20}
                    x2={nextX - 60}
                    y2={lane.y + 20}
                    stroke="#636363"
                    strokeWidth="1.3"
                    markerEnd="url(#arrow-j)"
                  />
                )}
                <rect
                  x={step.x - 60}
                  y={lane.y}
                  width="120"
                  height="52"
                  rx="6"
                  fill={t.fill}
                  stroke={t.stroke}
                  strokeWidth="1.4"
                />
                <text
                  x={step.x}
                  y={lane.y + 20}
                  textAnchor="middle"
                  fontFamily="system-ui, sans-serif"
                  fontSize="12.5"
                  fontWeight="600"
                  fill={t.text}
                >
                  {step.label}
                </text>
                {step.sub && (
                  <text
                    x={step.x}
                    y={lane.y + 38}
                    textAnchor="middle"
                    fontFamily="system-ui, sans-serif"
                    fontSize="10.5"
                    fill={step.tone === "accent" ? "#1f4e79" : "#636363"}
                  >
                    {step.sub}
                  </text>
                )}
              </g>
            );
          })}

          {/* end note */}
          <text
            x="20"
            y={lane.y + 90}
            fontFamily="system-ui, sans-serif"
            fontSize="11.5"
            fill="#636363"
          >
            <tspan fontWeight="600" fill="#1f1f1f">
              What they need:
            </tspan>{" "}
            {lane.endNote}
          </text>
        </g>
      ))}

      {/* bottom rule */}
      <line x1="0" y1="570" x2="900" y2="570" stroke="#ececec" strokeWidth="1" />
    </svg>
  );
}
