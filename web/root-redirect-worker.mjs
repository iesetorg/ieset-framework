const CANONICAL_HOST = "framework.ieset.org";

export default {
  async fetch(request) {
    const target = new URL(request.url);
    target.protocol = "https:";
    target.hostname = CANONICAL_HOST;
    target.port = "";

    return new Response(null, {
      status: 308,
      headers: {
        Location: target.toString(),
        "Cache-Control": "public, max-age=3600",
      },
    });
  },
};
