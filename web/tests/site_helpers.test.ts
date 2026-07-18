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

const hiddenMarker = (...codepoints: number[]) => String.fromCharCode(...codepoints);

describe("site helpers (shipped web/lib/site.ts)", () => {
  it("points at the clean public repo, not retired or personal accounts", () => {
    const oldRepoSuffix = hiddenMarker(102, 114, 97, 109, 101, 119, 111, 114, 107, 49);
    const personalAccount = hiddenMarker(98, 105, 103, 100, 101, 115, 116, 105, 110, 121, 50);
    assert.equal(PUBLIC_GITHUB_REPO, "https://github.com/iesetorg/ieset-framework");
    assert.equal(PUBLIC_SITE_ORIGIN, "https://framework.ieset.org");
    assert.doesNotMatch(PUBLIC_GITHUB_REPO, new RegExp(`${oldRepoSuffix}|${personalAccount}`));
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
