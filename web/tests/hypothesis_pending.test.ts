import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import * as verdict from "../lib/verdict.ts";

const require = createRequire(import.meta.url);
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");
const ts = require("typescript");

// Render the shipped TSX with fixture data, without a Next build or content
// loader. This exercises the candidate and tested branches, including JSON-LD.
function loadTsx(path: string, mocks: Record<string, unknown>) {
  const source = readFileSync(new URL(path, import.meta.url), "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
  }).outputText;
  const module = { exports: {} as Record<string, any> };
  const localRequire = (id: string) => Object.hasOwn(mocks, id) ? mocks[id] : require(id);
  new Function("require", "module", "exports", compiled)(localRequire, module, module.exports);
  return module.exports;
}

const banner = loadTsx("../components/cards/ResultBanner.tsx", {
  "@/lib/verdict": verdict,
});
const brief = loadTsx("../components/cards/PolicyBriefCard.tsx", {
  "@/lib/verdict": verdict,
});
let fixture: { hypothesis: Record<string, any>; run: Record<string, any> };
const emptyComponent = () => null;
const page = loadTsx("../app/h/[id]/page.tsx", {
  "next/navigation": { notFound: () => { throw new Error("not found"); } },
  "next/link": { default: ({ children }: any) => React.createElement("a", null, children) },
  "@/lib/content": {
    loadAllHypotheses: async () => [fixture.hypothesis],
    loadHypothesis: async () => fixture.hypothesis,
    loadRunArtifacts: async () => fixture.run,
    parseSourceString: async () => [],
    schoolPredictionsForHypothesis: async () => [],
  },
  "@/lib/permalink": {
    hypothesisBibTex: () => "",
    hypothesisPermalink: () => "/h/pending_test/",
  },
  "@/lib/site": {
    absoluteUrl: (path: string) => `https://framework.ieset.org${path}`,
    githubCommitUrl: (sha: string) => `https://github.com/iesetorg/ieset-framework/commit/${sha}`,
  },
  "@/components/badges/Badge": {
    Badge: ({ children, variant }: any) => React.createElement("span", { "data-variant": variant }, children),
  },
  "@/components/cards/PreRegStrip": { PreRegStrip: emptyComponent },
  "@/components/cards/FalsificationCard": { FalsificationCard: emptyComponent },
  "@/components/cards/SteelmanBlock": { SteelmanBlock: emptyComponent },
  "@/components/cards/CiteBlock": { CiteBlock: emptyComponent },
  "@/components/cards/ResultBanner": banner,
  "@/components/cards/PolicyBriefCard": brief,
  "@/components/charts/HypothesisChart": {
    HypothesisChart: () => React.createElement("svg", { "data-result-chart": "true" }),
  },
});

function hypothesis(overrides: Record<string, unknown> = {}) {
  return {
    hypothesis_id: "pending_test", version: 1, status: "candidate", topic: "fiscal",
    claim: "A proposed policy hypothesis with no empirical finding.",
    evidence_type: "causal", variables: { outcome: [{ name: "proposed_outcome" }] },
    sample: { countries: ["AUS"], period: [2022, 2026] },
    _evidence_tier: "archive", _registration_status: "registered_no_run",
    _estimator_floor: "pass", ...overrides,
  };
}

async function renderFixture() {
  const params = Promise.resolve({ id: "pending_test" });
  const html = renderToStaticMarkup(await page.default({ params }));
  const json = html.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/);
  assert.ok(json, "rendered hypothesis has structured metadata");
  return { html, metadata: JSON.parse(json[1]), seo: await page.generateMetadata({ params }) };
}

describe("hypothesis evidence standing before a run", () => {
  it("does not present candidate plans as acquired data, a passed estimator or verified registration", async () => {
    fixture = { hypothesis: hypothesis(), run: { exists: false } };
    const { html, metadata, seo } = await renderFixture();
    assert.match(html, /No empirical run is available/);
    assert.match(html, /No coefficients or verdict have been/);
    assert.match(html, /Planned outcome variables/);
    assert.doesNotMatch(html, /data-result-chart|raw outcome-variable trajectories|pinned public-data vintages/);
    assert.doesNotMatch(metadata.abstract, /Pre-registered|strictly preceded/);
    assert.match(metadata.abstract, /Untested research specification/);
    assert.equal(metadata.additionalProperty.find((p: any) => p.name === "Estimator floor").value, "not assessed");
    assert.match(html, /data-variant="muted">not assessed/);
    assert.equal(seo.robots.index, false);
  });

  it("keeps the verdict, chart and verified history for tested records", async () => {
    fixture = {
      hypothesis: hypothesis({ status: "pre_registered", _evidence_tier: "featured", _registration_status: "verified" }),
      run: { exists: true, verdict: "SUPPORTED: the specified threshold passed.", run_dir_rel: "engine/runs/pending_test" },
    };
    const { html, metadata, seo } = await renderFixture();
    assert.match(html, /SUPPORTED/);
    assert.match(html, /data-result-chart="true"/);
    assert.match(html, /what was measured/);
    assert.match(html, /What we checked/);
    assert.match(metadata.abstract, /strictly preceded its first run in git/);
    assert.equal(metadata.additionalProperty.find((p: any) => p.name === "Estimator floor").value, "pass");
    assert.doesNotMatch(html, /No empirical run is available/);
    assert.equal(seo.robots.index, true);
  });

  it("renders the pending bracket-creep claim and planned inputs without an unrelated institutional summary", async () => {
    const candidate = require("js-yaml").load(readFileSync(new URL(
      "../../hypotheses/fiscal/aus_albanese_budget_repair_bracket_creep_2026_2037.yaml", import.meta.url
    ), "utf8"));
    fixture = { hypothesis: hypothesis(candidate), run: { exists: false } };
    const { html } = await renderFixture();
    const variables = Object.entries(candidate.variables).flatMap(([role, entries]) =>
      (entries as Record<string, unknown>[]).map((entry) => ({
        ...entry, role: role === "decomposition_channels" ? "channel" : role,
      }))
    );
    const briefHtml = renderToStaticMarkup(React.createElement(brief.PolicyBriefCard, {
      hypothesis: fixture.hypothesis, run: fixture.run, variables,
    }));
    const claimMarkup = renderToStaticMarkup(React.createElement("p", null,
      candidate.claim.replace(/\s+/g, " ").trim()
    )).slice(3, -4);

    assert.ok(briefHtml.includes(claimMarkup), "pending brief preserves the actual conditional projection claim");
    for (const output of [html, briefHtml]) {
      assert.match(output, /Proposed claim/);
      assert.match(output, /planned measurements/);
      assert.match(output, /Proposed exposure or scenario/);
      assert.match(output, /Planned outcomes/);
      assert.match(output, /Baseline primary UCB pct GDP/);
      assert.match(output, /No empirical run or verdict is available/);
      assert.match(output, /plan, not a completed analysis/);
      assert.doesNotMatch(output, /market-oriented institutions|what was measured|What we checked|What changed|question has been registered|It compares 1 country|primary ucb pct income|It narrows the claim/i);
    }
  });
});
