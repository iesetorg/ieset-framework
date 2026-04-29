import type { Hypothesis } from "./types";

// Canonical permalink shape. In production this resolves against the domain; for
// local/preview it's a relative path.
export function hypothesisPermalink(h: Hypothesis): string {
  return `/h/${h.hypothesis_id}`;
}

export function hypothesisBibTex(h: Hypothesis): string {
  const key = h.hypothesis_id.replace(/_/g, "");
  const year = h._first_commit?.iso?.slice(0, 4) ?? new Date().getFullYear();
  const month = h._first_commit?.iso?.slice(5, 7) ?? "";
  const commit = h._first_commit?.hash ?? "unregistered";
  return [
    `@misc{ieset_${key},`,
    `  title        = {${h.claim.trim().split("\n").join(" ").slice(0, 180)}},`,
    `  author       = {IESET Framework},`,
    `  year         = {${year}},`,
    `  month        = {${month}},`,
    `  howpublished = {Pre-registered hypothesis, git commit ${commit}},`,
    `  url          = {https://ieset.dev/h/${h.hypothesis_id}},`,
    `  version      = {${h.version}}`,
    `}`,
  ].join("\n");
}

// Build query-string deep-linking for hero-chart state
export function heroChartQuery(params: { series?: string[]; scale?: "linear" | "log"; ref?: string }): string {
  const qs = new URLSearchParams();
  if (params.series && params.series.length) qs.set("series", params.series.join(","));
  if (params.scale) qs.set("scale", params.scale);
  if (params.ref) qs.set("ref", params.ref);
  return qs.toString();
}
