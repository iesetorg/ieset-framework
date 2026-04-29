// Diagram D — Axis-fingerprint matching.
// Proposed policy → axis vector → matcher → ranked historical analogues.

const inputAxes = [
  { axis: "regulatory.financial_deregulation", dir: "+", mag: "strong" },
  { axis: "fiscal.tax_capital", dir: "-", mag: "moderate" },
  { axis: "institutional.property_rights", dir: "+", mag: "weak" },
];

const output = [
  {
    title: "UK Big Bang (1986)",
    score: 4.2,
    same: ["regulatory.financial_deregulation", "fiscal.tax_capital"],
    diff: [] as string[],
  },
  {
    title: "US Gramm-Leach-Bliley (1999)",
    score: 3.8,
    same: ["regulatory.financial_deregulation"],
    diff: ["institutional.property_rights"],
  },
  {
    title: "Iceland financial liberalisation (2001-2007)",
    score: 3.3,
    same: ["regulatory.financial_deregulation", "institutional.property_rights"],
    diff: [] as string[],
  },
];

function dirChip(dir: string) {
  if (dir === "+") return { bg: "#dff1e4", fg: "#2c7a4f", sym: "↑" };
  if (dir === "-") return { bg: "#f3d9d9", fg: "#9e2f2f", sym: "↓" };
  return { bg: "#f3f3f1", fg: "#636363", sym: "—" };
}

export function AxisMatching({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 900 620"
      className={`block h-auto w-full ${className}`}
      role="img"
      aria-labelledby="axis-matching-title"
    >
      <title id="axis-matching-title">
        Axis-fingerprint matching — how a proposed policy finds historical analogues
      </title>

      <defs>
        <marker
          id="arrow-m"
          viewBox="0 0 10 10"
          refX="8"
          refY="5"
          markerWidth="8"
          markerHeight="8"
          orient="auto-start-reverse"
        >
          <path d="M0 0 L10 5 L0 10 Z" fill="#1f4e79" />
        </marker>
      </defs>

      {/* === INPUT — proposed policy fingerprint === */}
      <g>
        <text
          x="30"
          y="30"
          fontFamily="system-ui, sans-serif"
          fontSize="11"
          fontWeight="700"
          letterSpacing="0.1em"
          fill="#636363"
        >
          STEP 1 — INPUT
        </text>
        <text
          x="30"
          y="52"
          fontFamily="system-ui, sans-serif"
          fontSize="14"
          fontWeight="700"
          fill="#1f1f1f"
        >
          Proposed policy: a UK financial-sector liberalisation package
        </text>
        <text
          x="30"
          y="71"
          fontFamily="system-ui, sans-serif"
          fontSize="12"
          fill="#636363"
        >
          Expressed as an axis fingerprint — direction + magnitude per channel-separated axis.
        </text>

        {/* fingerprint rows */}
        {inputAxes.map((a, i) => {
          const y = 100 + i * 42;
          const chip = dirChip(a.dir);
          return (
            <g key={i}>
              <rect
                x="30"
                y={y}
                width="360"
                height="32"
                rx="4"
                fill="#ffffff"
                stroke="#d9d9d9"
              />
              <rect
                x="38"
                y={y + 6}
                width="20"
                height="20"
                rx="3"
                fill={chip.bg}
                stroke={chip.fg}
              />
              <text
                x="48"
                y={y + 21}
                textAnchor="middle"
                fontFamily="system-ui, sans-serif"
                fontSize="14"
                fontWeight="700"
                fill={chip.fg}
              >
                {chip.sym}
              </text>
              <text
                x="70"
                y={y + 21}
                fontFamily="ui-monospace, monospace"
                fontSize="12"
                fill="#1f1f1f"
              >
                {a.axis}
              </text>
              <text
                x="330"
                y={y + 21}
                fontFamily="system-ui, sans-serif"
                fontSize="11"
                fill="#636363"
              >
                {a.mag}
              </text>
            </g>
          );
        })}
      </g>

      {/* === ARROW + MATCHER === */}
      <g>
        <line
          x1="400"
          y1="142"
          x2="485"
          y2="142"
          stroke="#1f4e79"
          strokeWidth="1.7"
          markerEnd="url(#arrow-m)"
        />

        <rect
          x="495"
          y="100"
          width="280"
          height="140"
          rx="10"
          fill="#e1ecf5"
          stroke="#1f4e79"
          strokeWidth="2"
        />
        <text
          x="635"
          y="125"
          textAnchor="middle"
          fontFamily="system-ui, sans-serif"
          fontSize="12"
          fontWeight="700"
          letterSpacing="0.08em"
          fill="#1f4e79"
        >
          STEP 2 — MATCHER
        </text>
        <text
          x="635"
          y="150"
          textAnchor="middle"
          fontFamily="system-ui, sans-serif"
          fontSize="14"
          fontWeight="700"
          fill="#1f4e79"
        >
          score = Σ (same_dir ? 1 : 0.5)
        </text>
        <text
          x="635"
          y="170"
          textAnchor="middle"
          fontFamily="system-ui, sans-serif"
          fontSize="13"
          fill="#1f4e79"
        >
          × magnitude_weight
        </text>
        <text
          x="635"
          y="198"
          textAnchor="middle"
          fontFamily="system-ui, sans-serif"
          fontSize="11"
          fill="#1f4e79"
        >
          over every shared axis
        </text>
        <text
          x="635"
          y="215"
          textAnchor="middle"
          fontFamily="system-ui, sans-serif"
          fontSize="11"
          fill="#1f4e79"
        >
          with every policy in the corpus
        </text>
      </g>

      {/* corpus cloud */}
      <g opacity="0.9">
        <text
          x="800"
          y="80"
          textAnchor="middle"
          fontFamily="system-ui, sans-serif"
          fontSize="11"
          fontWeight="600"
          letterSpacing="0.08em"
          fill="#636363"
        >
          1,130 POLICIES
        </text>
        {[
          { x: 780, y: 100, w: 55 },
          { x: 848, y: 105, w: 48 },
          { x: 785, y: 130, w: 62 },
          { x: 850, y: 138, w: 50 },
          { x: 792, y: 163, w: 55 },
          { x: 848, y: 168, w: 46 },
          { x: 782, y: 195, w: 52 },
          { x: 847, y: 198, w: 45 },
          { x: 787, y: 224, w: 58 },
        ].map((r, i) => (
          <rect
            key={i}
            x={r.x}
            y={r.y}
            width={r.w}
            height="12"
            rx="2"
            fill="#fafaf8"
            stroke="#ececec"
          />
        ))}
        {/* arrow from cloud to matcher */}
        <line
          x1="780"
          y1="170"
          x2="775"
          y2="170"
          stroke="#1f4e79"
          strokeWidth="1.3"
        />
      </g>

      {/* === OUTPUT === */}
      <g>
        <text
          x="30"
          y="310"
          fontFamily="system-ui, sans-serif"
          fontSize="11"
          fontWeight="700"
          letterSpacing="0.1em"
          fill="#636363"
        >
          STEP 3 — OUTPUT
        </text>
        <text
          x="30"
          y="332"
          fontFamily="system-ui, sans-serif"
          fontSize="14"
          fontWeight="700"
          fill="#1f1f1f"
        >
          Ranked historical analogues
        </text>
        <text
          x="30"
          y="351"
          fontFamily="system-ui, sans-serif"
          fontSize="12"
          fill="#636363"
        >
          Each match carries its shared axes; same-direction axes are the strongest signal.
        </text>

        {/* arrow from matcher down */}
        <line
          x1="635"
          y1="240"
          x2="635"
          y2="310"
          stroke="#1f4e79"
          strokeWidth="1.7"
          markerEnd="url(#arrow-m)"
        />

        {output.map((o, i) => {
          const y = 380 + i * 70;
          return (
            <g key={i}>
              <rect
                x="30"
                y={y}
                width="840"
                height="56"
                rx="6"
                fill="#ffffff"
                stroke="#d9d9d9"
              />
              {/* rank */}
              <text
                x="60"
                y={y + 33}
                textAnchor="middle"
                fontFamily="system-ui, sans-serif"
                fontSize="16"
                fontWeight="700"
                fill="#1f1f1f"
              >
                {i + 1}
              </text>
              {/* title */}
              <text
                x="90"
                y={y + 26}
                fontFamily="system-ui, sans-serif"
                fontSize="13"
                fontWeight="600"
                fill="#1f1f1f"
              >
                {o.title}
              </text>
              {/* score */}
              <text
                x="840"
                y={y + 26}
                textAnchor="end"
                fontFamily="system-ui, sans-serif"
                fontSize="12"
                fill="#636363"
              >
                match
              </text>
              <text
                x="840"
                y={y + 43}
                textAnchor="end"
                fontFamily="system-ui, sans-serif"
                fontSize="14"
                fontWeight="700"
                fill="#1f1f1f"
              >
                {o.score.toFixed(1)}
              </text>
              {/* shared axes */}
              {o.same.map((ax, j) => (
                <g key={`s${j}`}>
                  <rect
                    x={90 + j * 240}
                    y={y + 35}
                    width={Math.min(220, 8 + ax.length * 6.1)}
                    height="14"
                    rx="2"
                    fill="#e1ecf5"
                  />
                  <text
                    x={94 + j * 240}
                    y={y + 46}
                    fontFamily="ui-monospace, monospace"
                    fontSize="10.5"
                    fontWeight="700"
                    fill="#1f4e79"
                  >
                    {ax}
                  </text>
                </g>
              ))}
              {o.diff.map((ax, j) => (
                <g key={`d${j}`}>
                  <rect
                    x={90 + (o.same.length + j) * 240}
                    y={y + 35}
                    width={Math.min(220, 8 + ax.length * 6.1)}
                    height="14"
                    rx="2"
                    fill="#f3f3f1"
                  />
                  <text
                    x={94 + (o.same.length + j) * 240}
                    y={y + 46}
                    fontFamily="ui-monospace, monospace"
                    fontSize="10.5"
                    fill="#636363"
                  >
                    {ax}
                  </text>
                </g>
              ))}
            </g>
          );
        })}
      </g>

      {/* footer legend */}
      <g>
        <rect x="30" y="580" width="14" height="12" rx="2" fill="#e1ecf5" />
        <text
          x="50"
          y="590"
          fontFamily="system-ui, sans-serif"
          fontSize="11"
          fill="#636363"
        >
          same-direction axis (strong)
        </text>
        <rect x="230" y="580" width="14" height="12" rx="2" fill="#f3f3f1" />
        <text
          x="250"
          y="590"
          fontFamily="system-ui, sans-serif"
          fontSize="11"
          fill="#636363"
        >
          opposite-direction axis (weak, still relevant)
        </text>
      </g>
    </svg>
  );
}
