// Vercel serverless function: GET /api/communities  (add ?view=flat for one record per spreadsheet row)
// Reads the generated JSON from a private GitHub repo so the token never reaches the browser.

const FILES = { grouped: "public/communities.json", flat: "public/communities-flat.json" };

module.exports = async (req, res) => {
  const { GITHUB_TOKEN, GITHUB_REPO, GITHUB_BRANCH = "main", COMMUNITIES_API_KEY, ALLOWED_ORIGIN } = process.env;

  if (ALLOWED_ORIGIN) {
    res.setHeader("Access-Control-Allow-Origin", ALLOWED_ORIGIN);
    res.setHeader("Access-Control-Allow-Headers", "x-api-key");
  }
  if (req.method === "OPTIONS") return res.status(204).end();
  if (req.method !== "GET") {
    res.setHeader("Allow", "GET, OPTIONS");
    return res.status(405).json({ error: "Method not allowed" });
  }
  if (!GITHUB_TOKEN || !GITHUB_REPO) return res.status(500).json({ error: "Server is not configured" });
  if (COMMUNITIES_API_KEY && req.headers["x-api-key"] !== COMMUNITIES_API_KEY) {
    return res.status(401).json({ error: "Unauthorized" });
  }

  const file = FILES[req.query && req.query.view === "flat" ? "flat" : "grouped"];
  const url = `https://api.github.com/repos/${GITHUB_REPO}/contents/${file}?ref=${encodeURIComponent(GITHUB_BRANCH)}`;

  try {
    const r = await fetch(url, {
      headers: {
        Authorization: `Bearer ${GITHUB_TOKEN}`,
        Accept: "application/vnd.github.raw+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "community-directory",
      },
    });
    if (!r.ok) {
      console.error("GitHub responded", r.status, await r.text());
      return res.status(502).json({ error: "Could not load community data" });
    }
    const body = await r.text();
    JSON.parse(body); // refuse to serve (and cache) anything that isn't valid JSON
    res.setHeader("Content-Type", "application/json; charset=utf-8");
    // Cached at Vercel's edge for 5 minutes, so a new upload shows up within about 5 minutes.
    res.setHeader("Cache-Control", "public, s-maxage=300, stale-while-revalidate=3600");
    return res.status(200).send(body);
  } catch (err) {
    console.error(err);
    return res.status(502).json({ error: "Could not load community data" });
  }
};
