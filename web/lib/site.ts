/** Canonical public origins and helpers for citation / SEO surfaces. */

export const PUBLIC_SITE_ORIGIN = "https://framework.ieset.org";
export const PUBLIC_GITHUB_REPO = "https://github.com/iesetorg/ieset-framework";
export const PUBLIC_GITHUB_TREE = `${PUBLIC_GITHUB_REPO}/tree/main`;
export const PUBLIC_X_PROFILE = "https://x.com/IESETorg";

export function absoluteUrl(path: string): string {
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${PUBLIC_SITE_ORIGIN}${p}`;
}

export function githubCommitUrl(fullOrShortHash: string): string {
  return `${PUBLIC_GITHUB_REPO}/commit/${fullOrShortHash}`;
}

export function shortCommit(hash: string | undefined | null): string {
  if (!hash) return "pending";
  return hash.length > 7 ? hash.slice(0, 7) : hash;
}
