"use client";

import dynamic from "next/dynamic";

export const InteractiveDriftChart = dynamic(
  () =>
    import("./InteractiveDriftChart").then((m) => m.InteractiveDriftChart),
  { ssr: false }
);
