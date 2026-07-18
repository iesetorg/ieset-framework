#!/usr/bin/env node

const HOST = "framework.ieset.org";
const ORIGIN = `https://${HOST}`;
const KEY =
  "21afc21907fd637f17e951f3191e83afe90ed4f0b7fceb65a358e33ea19219a4";
const KEY_LOCATION = `${ORIGIN}/${KEY}.txt`;
const ENDPOINT = "https://api.indexnow.org/indexnow";

const sitemapResponse = await fetch(`${ORIGIN}/sitemap.xml`, {
  headers: { "User-Agent": "IESET-IndexNow/1.0" },
});
if (!sitemapResponse.ok) {
  throw new Error(
    `Could not fetch live sitemap: ${sitemapResponse.status} ${sitemapResponse.statusText}`
  );
}

const sitemap = await sitemapResponse.text();
const urls = [...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)]
  .map((match) => match[1].replaceAll("&amp;", "&"))
  .filter((url) => url.startsWith(`${ORIGIN}/`));

if (urls.length === 0) {
  throw new Error("Live sitemap contained no canonical IESET URLs");
}
if (urls.length > 10_000) {
  throw new Error(
    `IndexNow accepts at most 10,000 URLs per request; found ${urls.length}`
  );
}

const response = await fetch(ENDPOINT, {
  method: "POST",
  headers: {
    "Content-Type": "application/json; charset=utf-8",
    "User-Agent": "IESET-IndexNow/1.0",
  },
  body: JSON.stringify({
    host: HOST,
    key: KEY,
    keyLocation: KEY_LOCATION,
    urlList: urls,
  }),
});

if (![200, 202].includes(response.status)) {
  const body = await response.text();
  throw new Error(
    `IndexNow rejected the sitemap: ${response.status} ${body.slice(0, 500)}`
  );
}

console.log(`IndexNow accepted ${urls.length} canonical URLs (${response.status})`);
