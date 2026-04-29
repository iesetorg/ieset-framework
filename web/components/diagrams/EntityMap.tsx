// Diagram A — Entity map.
//
// Two panels, deliberately separate so each carries one message:
//
// PANEL 1 (top, dominant): "The five cards share one vocabulary — the axis."
//   Axis is a big, accent-coloured hub at the centre. The four other entity
//   types sit at the corners. The only arrows are the four spokes into the
//   hub, each labeled with the field that wires that entity to axes.
//
// PANEL 2 (bottom, secondary): "And they also chain directly."
//   A horizontal strip with the four entities laid out in narrative order:
//   Movement → Policy → Hypothesis ← Position. Three arrows, three labels.
//
// Splitting the two messages eliminates the crossing diagonals and triple
// arrow encodings of the old all-in-one diagram. If you need to show every
// edge in one frame for a print-only version, see the .drawio download.
const ACCENT = "#1f4e79";
const ACCENT_FILL = "#e1ecf5";
const INK = "#1f1f1f";
const MUTED = "#636363";
const RULE = "#dcdad4";

export function EntityMap({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 900 660"
      className={`block h-auto w-full ${className}`}
      role="img"
      aria-labelledby="entity-map-title"
    >
      <title id="entity-map-title">
        Entity map — Axis at the centre as the shared vocabulary, with each
        card type connected to it.
      </title>

      <defs>
        <marker
          id="em-arrow-accent"
          viewBox="0 0 10 10"
          refX="8"
          refY="5"
          markerWidth="8"
          markerHeight="8"
          orient="auto-start-reverse"
        >
          <path d="M0 0 L10 5 L0 10 Z" fill={ACCENT} />
        </marker>
        <marker
          id="em-arrow-muted"
          viewBox="0 0 10 10"
          refX="8"
          refY="5"
          markerWidth="8"
          markerHeight="8"
          orient="auto-start-reverse"
        >
          <path d="M0 0 L10 5 L0 10 Z" fill={MUTED} />
        </marker>
      </defs>

      {/* ============ PANEL 1 — Hub & spoke ============ */}

      {/* Panel caption */}
      <text
        x="450"
        y="28"
        textAnchor="middle"
        fontFamily="system-ui, sans-serif"
        fontSize="11"
        fontWeight="600"
        letterSpacing="0.08em"
        fill={MUTED}
      >
        FIVE CARD TYPES, ONE SHARED VOCABULARY
      </text>

      {/* Axis hub — centred, dominant */}
      <g>
        <rect
          x="335"
          y="200"
          width="230"
          height="120"
          rx="10"
          fill={ACCENT_FILL}
          stroke={ACCENT}
          strokeWidth="2.5"
        />
        <text
          x="450"
          y="240"
          textAnchor="middle"
          fontFamily="system-ui, sans-serif"
          fontSize="18"
          fontWeight="700"
          fill={ACCENT}
        >
          Axis /a
        </text>
        <text
          x="450"
          y="265"
          textAnchor="middle"
          fontFamily="system-ui, sans-serif"
          fontSize="11.5"
          fill={ACCENT}
        >
          the standard policy-lever
        </text>
        <text
          x="450"
          y="280"
          textAnchor="middle"
          fontFamily="system-ui, sans-serif"
          fontSize="11.5"
          fill={ACCENT}
        >
          taxonomy every other card
        </text>
        <text
          x="450"
          y="295"
          textAnchor="middle"
          fontFamily="system-ui, sans-serif"
          fontSize="11.5"
          fill={ACCENT}
        >
          is described in
        </text>
      </g>

      {/* Position — top-left */}
      <EntityCard
        x={70}
        y={70}
        title="Position /pos"
        sub1="school of thought"
        sub2="(Austrian, Keynesian…)"
      />

      {/* Hypothesis — top-right */}
      <EntityCard
        x={650}
        y={70}
        title="Hypothesis /h"
        sub1="pre-registered test"
        sub2="with falsification rule"
      />

      {/* Movement — bottom-left */}
      <EntityCard
        x={70}
        y={370}
        title="Movement /m"
        sub1="a government"
        sub2="(Bukele, Thatcher…)"
      />

      {/* Policy — bottom-right */}
      <EntityCard
        x={650}
        y={370}
        title="Policy /p"
        sub1="a specific reform"
        sub2="(Bitcoin Law 2021…)"
      />

      {/* Spokes — only axis links in panel 1 */}
      {/* Position → Axis (derived → dashed) */}
      <line
        x1="250"
        y1="150"
        x2="345"
        y2="210"
        stroke={ACCENT}
        strokeWidth="1.7"
        strokeDasharray="5 3"
        markerEnd="url(#em-arrow-accent)"
      />
      <SpokeLabel
        x={278}
        y={140}
        anchor="start"
        line1="fingerprint"
        line2="(derived)"
      />

      {/* Hypothesis → Axis */}
      <line
        x1="650"
        y1="150"
        x2="555"
        y2="210"
        stroke={ACCENT}
        strokeWidth="1.7"
        markerEnd="url(#em-arrow-accent)"
      />
      <SpokeLabel x={595} y={170} anchor="end" line1="tests outcomes on" />

      {/* Movement → Axis */}
      <line
        x1="250"
        y1="410"
        x2="345"
        y2="320"
        stroke={ACCENT}
        strokeWidth="1.7"
        markerEnd="url(#em-arrow-accent)"
      />
      <SpokeLabel x={278} y={373} anchor="start" line1="axes_summary" />

      {/* Policy → Axis */}
      <line
        x1="650"
        y1="410"
        x2="555"
        y2="320"
        stroke={ACCENT}
        strokeWidth="1.7"
        markerEnd="url(#em-arrow-accent)"
      />
      <SpokeLabel x={595} y={373} anchor="end" line1="axes_moved" />

      {/* Divider between panels */}
      <line
        x1="60"
        y1="490"
        x2="840"
        y2="490"
        stroke={RULE}
        strokeWidth="1"
      />

      {/* ============ PANEL 2 — Direct entity-to-entity links ============ */}

      <text
        x="450"
        y="515"
        textAnchor="middle"
        fontFamily="system-ui, sans-serif"
        fontSize="11"
        fontWeight="600"
        letterSpacing="0.08em"
        fill={MUTED}
      >
        AND THEY CHAIN DIRECTLY TO EACH OTHER
      </text>

      {/* Strip layout: 4 small boxes left → right */}
      {/* Movement */}
      <g>
        <rect
          x="55"
          y="555"
          width="160"
          height="50"
          rx="6"
          fill="#ffffff"
          stroke={INK}
          strokeWidth="1.3"
        />
        <text
          x="135"
          y="575"
          textAnchor="middle"
          fontFamily="system-ui, sans-serif"
          fontSize="13"
          fontWeight="700"
          fill={INK}
        >
          Movement
        </text>
        <text
          x="135"
          y="592"
          textAnchor="middle"
          fontFamily="system-ui, sans-serif"
          fontSize="10.5"
          fill={MUTED}
        >
          a government
        </text>
      </g>

      {/* Policy */}
      <g>
        <rect
          x="285"
          y="555"
          width="160"
          height="50"
          rx="6"
          fill="#ffffff"
          stroke={INK}
          strokeWidth="1.3"
        />
        <text
          x="365"
          y="575"
          textAnchor="middle"
          fontFamily="system-ui, sans-serif"
          fontSize="13"
          fontWeight="700"
          fill={INK}
        >
          Policy
        </text>
        <text
          x="365"
          y="592"
          textAnchor="middle"
          fontFamily="system-ui, sans-serif"
          fontSize="10.5"
          fill={MUTED}
        >
          a specific reform
        </text>
      </g>

      {/* Hypothesis */}
      <g>
        <rect
          x="515"
          y="555"
          width="160"
          height="50"
          rx="6"
          fill="#ffffff"
          stroke={INK}
          strokeWidth="1.3"
        />
        <text
          x="595"
          y="575"
          textAnchor="middle"
          fontFamily="system-ui, sans-serif"
          fontSize="13"
          fontWeight="700"
          fill={INK}
        >
          Hypothesis
        </text>
        <text
          x="595"
          y="592"
          textAnchor="middle"
          fontFamily="system-ui, sans-serif"
          fontSize="10.5"
          fill={MUTED}
        >
          a pre-registered test
        </text>
      </g>

      {/* Position */}
      <g>
        <rect
          x="745"
          y="555"
          width="135"
          height="50"
          rx="6"
          fill="#ffffff"
          stroke={INK}
          strokeWidth="1.3"
        />
        <text
          x="812"
          y="575"
          textAnchor="middle"
          fontFamily="system-ui, sans-serif"
          fontSize="13"
          fontWeight="700"
          fill={INK}
        >
          Position
        </text>
        <text
          x="812"
          y="592"
          textAnchor="middle"
          fontFamily="system-ui, sans-serif"
          fontSize="10.5"
          fill={MUTED}
        >
          a school
        </text>
      </g>

      {/* Movement → Policy */}
      <line
        x1="215"
        y1="580"
        x2="285"
        y2="580"
        stroke={MUTED}
        strokeWidth="1.4"
        markerEnd="url(#em-arrow-muted)"
      />
      <text
        x="250"
        y="572"
        textAnchor="middle"
        fontFamily="system-ui, sans-serif"
        fontSize="10.5"
        fill={MUTED}
      >
        enacts
      </text>

      {/* Policy → Hypothesis */}
      <line
        x1="445"
        y1="580"
        x2="515"
        y2="580"
        stroke={MUTED}
        strokeWidth="1.4"
        markerEnd="url(#em-arrow-muted)"
      />
      <text
        x="480"
        y="572"
        textAnchor="middle"
        fontFamily="system-ui, sans-serif"
        fontSize="10.5"
        fill={MUTED}
      >
        tested by
      </text>

      {/* Position → Hypothesis (right-to-left arrow) */}
      <line
        x1="745"
        y1="580"
        x2="675"
        y2="580"
        stroke={MUTED}
        strokeWidth="1.4"
        markerEnd="url(#em-arrow-muted)"
      />
      <text
        x="710"
        y="572"
        textAnchor="middle"
        fontFamily="system-ui, sans-serif"
        fontSize="10.5"
        fill={MUTED}
      >
        predicts on
      </text>

      {/* Tiny legend — simplified vs old version */}
      <g transform="translate(60, 630)">
        <line
          x1="0"
          y1="0"
          x2="28"
          y2="0"
          stroke={ACCENT}
          strokeWidth="1.7"
          markerEnd="url(#em-arrow-accent)"
        />
        <text
          x="35"
          y="4"
          fontFamily="system-ui, sans-serif"
          fontSize="10.5"
          fill={ACCENT}
        >
          axis-vocabulary edge
        </text>

        <line
          x1="225"
          y1="0"
          x2="253"
          y2="0"
          stroke={ACCENT}
          strokeWidth="1.7"
          strokeDasharray="5 3"
          markerEnd="url(#em-arrow-accent)"
        />
        <text
          x="260"
          y="4"
          fontFamily="system-ui, sans-serif"
          fontSize="10.5"
          fill={ACCENT}
        >
          derived (not authored)
        </text>

        <line
          x1="430"
          y1="0"
          x2="458"
          y2="0"
          stroke={MUTED}
          strokeWidth="1.4"
          markerEnd="url(#em-arrow-muted)"
        />
        <text
          x="465"
          y="4"
          fontFamily="system-ui, sans-serif"
          fontSize="10.5"
          fill={MUTED}
        >
          direct entity-to-entity link
        </text>
      </g>
    </svg>
  );
}

// Helper: a top-row entity card (Position / Hypothesis / Movement / Policy)
function EntityCard({
  x,
  y,
  title,
  sub1,
  sub2,
}: {
  x: number;
  y: number;
  title: string;
  sub1: string;
  sub2?: string;
}) {
  return (
    <g>
      <rect
        x={x}
        y={y}
        width="180"
        height="80"
        rx="8"
        fill="#ffffff"
        stroke={INK}
        strokeWidth="1.5"
      />
      <text
        x={x + 90}
        y={y + 30}
        textAnchor="middle"
        fontFamily="system-ui, sans-serif"
        fontSize="15"
        fontWeight="700"
        fill={INK}
      >
        {title}
      </text>
      <text
        x={x + 90}
        y={y + 50}
        textAnchor="middle"
        fontFamily="system-ui, sans-serif"
        fontSize="11.5"
        fill={MUTED}
      >
        {sub1}
      </text>
      {sub2 && (
        <text
          x={x + 90}
          y={y + 65}
          textAnchor="middle"
          fontFamily="system-ui, sans-serif"
          fontSize="11.5"
          fill={MUTED}
        >
          {sub2}
        </text>
      )}
    </g>
  );
}

// Helper: a 1- or 2-line label hugging a spoke
function SpokeLabel({
  x,
  y,
  anchor,
  line1,
  line2,
}: {
  x: number;
  y: number;
  anchor: "start" | "middle" | "end";
  line1: string;
  line2?: string;
}) {
  return (
    <g>
      <text
        x={x}
        y={y}
        textAnchor={anchor}
        fontFamily="system-ui, sans-serif"
        fontSize="11.5"
        fontWeight="500"
        fill={ACCENT}
      >
        {line1}
      </text>
      {line2 && (
        <text
          x={x}
          y={y + 14}
          textAnchor={anchor}
          fontFamily="system-ui, sans-serif"
          fontSize="11.5"
          fill={ACCENT}
        >
          {line2}
        </text>
      )}
    </g>
  );
}
