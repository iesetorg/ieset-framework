import Link from "next/link";

export function Footer() {
  return (
    <footer className="mt-20 border-t border-rule bg-panel px-8 py-8 text-xs text-muted">
      <div className="mx-auto flex max-w-content flex-wrap justify-between gap-4">
        <div className="max-w-xl">
          <span className="font-semibold text-ink">IESET</span> — an open
          empirical framework for contemporary economic policy questions.
          Results are not peer-reviewed by default; strict pre-registration
          status is shown per hypothesis.
        </div>
        <div className="space-x-4">
          <Link href="/methodology" className="text-muted hover:text-ink hover:no-underline">Methodology</Link>
          <Link href="/disclosure" className="text-muted hover:text-ink hover:no-underline">Transparency</Link>
          <Link href="/contribute" className="text-muted hover:text-ink hover:no-underline">Contribute</Link>
          <Link href="/terms" className="text-muted hover:text-ink hover:no-underline">Terms</Link>
          <Link href="/privacy" className="text-muted hover:text-ink hover:no-underline">Privacy</Link>
          <a
            href="https://twitter.com/IESETorg"
            target="_blank"
            rel="noopener noreferrer"
            className="text-muted hover:text-ink hover:no-underline"
          >
            @IESETorg
          </a>
        </div>
      </div>
    </footer>
  );
}
