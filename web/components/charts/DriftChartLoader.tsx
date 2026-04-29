"use client";

import dynamic from "next/dynamic";

// Server-side rendering Observable Plot fails because of micromark's CommonJS
// dependency tree. Wrap in next/dynamic with ssr:false.
export const DriftChart = dynamic(
  () => import("./DriftChart").then((m) => m.DriftChart),
  { ssr: false }
);
