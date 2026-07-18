/**
 * Unit tests for shipped SEO/citation helpers (web/lib/site.ts).
 * Run: node --experimental-strip-types --test tests/site_helpers.test.ts
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  PUBLIC_GITHUB_REPO,
  PUBLIC_SITE_ORIGIN,
  absoluteUrl,
  githubCommitUrl,
  shortCommit,
} from "../lib/site.ts";

describe("site helpers (shipped web/lib/site.ts)", () => {
  it("points at the clean public repo, not framework1 or personal accounts", () => {
    assert.equal(PUBLIC_GITHUB_REPO, "https://github.com/iesetorg/ieset-framework");
    assert.equal(PUBLIC_SITE_ORIGIN, "https://framework.ieset.org");
    assert.doesNotMatch(PUBLIC_GITHUB_REPO, /framework1|bigdestiny2/);
  });

  it("builds absolute framework.ieset.org URLs", () => {
    assert.equal(absoluteUrl("/production/"), "https://framework.ieset.org/production/");
    assert.equal(absoluteUrl("h/foo/"), "https://framework.ieset.org/h/foo/");
    assert.equal(
      absoluteUrl("https://example.com/x"),
      "https://example.com/x"
    );
  });

  it("deep-links a full git SHA on the public GitHub repo", () => {
    const sha = "b63b576a7f221a39fbfa3717bbd2a9dd74d9aa90";
    assert.equal(
      githubCommitUrl(sha),
      `https://github.com/iesetorg/ieset-framework/commit/${sha}`
    );
  });

  it("shortens display hashes without losing the full URL target", () => {
    const sha = "b63b576a7f221a39fbfa3717bbd2a9dd74d9aa90";
    assert.equal(shortCommit(sha), "b63b576");
    assert.equal(shortCommit("abc"), "abc");
    assert.equal(shortCommit(null), "pending");
    // display short form is never what githubCommitUrl embeds alone
    assert.match(githubCommitUrl(sha), new RegExp(sha));
  });
});
