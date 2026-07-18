import type { MetadataRoute } from "next";

import { PUBLIC_SITE_ORIGIN } from "@/lib/site";

/**
 * Explicit crawler policy for an open-science evidence site.
 * Retrieval and answer-engine bots are welcome; training is allowed on
 * CC-BY content (see LICENSE-DATA). Cloudflare "Block AI Bots" should be
 * aligned with this file in the dashboard.
 */
export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
      },
      // Answer-engine / retrieval bots
      { userAgent: "OAI-SearchBot", allow: "/" },
      { userAgent: "ChatGPT-User", allow: "/" },
      { userAgent: "PerplexityBot", allow: "/" },
      { userAgent: "Perplexity-User", allow: "/" },
      { userAgent: "Claude-User", allow: "/" },
      { userAgent: "Claude-SearchBot", allow: "/" },
      { userAgent: "Amazonbot", allow: "/" },
      // Training / grounding crawlers (open-science default: allow)
      { userAgent: "GPTBot", allow: "/" },
      { userAgent: "ClaudeBot", allow: "/" },
      { userAgent: "CCBot", allow: "/" },
      { userAgent: "Google-Extended", allow: "/" },
      { userAgent: "Applebot-Extended", allow: "/" },
    ],
    sitemap: `${PUBLIC_SITE_ORIGIN}/sitemap.xml`,
    host: PUBLIC_SITE_ORIGIN,
  };
}
