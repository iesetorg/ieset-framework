import Link from "next/link";

export const metadata = {
  title: "Integration Callback",
  description:
    "Reserved callback URL for IESET third-party app and OAuth configuration.",
  robots: { index: false, follow: false },
};

export default function AuthCallbackPage() {
  return (
    <main className="mx-auto max-w-[760px] px-8 py-16">
      <p className="sc mb-3">Reserved endpoint</p>
      <h1 className="mb-5 text-[34px] font-semibold leading-tight tracking-tight text-ink">
        IESET integration callback
      </h1>
      <div className="space-y-4 text-[16px] leading-7 text-muted">
        <p>
          This URL is reserved for third-party app verification and redirect
          configuration. If you reached it directly, there is nothing you need
          to do.
        </p>
        <p>
          A reachable callback page does not by itself complete OAuth sign-in or
          token exchange. Any live provider integration should document and
          implement the provider-specific callback flow before this route is
          used for production authentication.
        </p>
      </div>
      <div className="mt-8 flex flex-wrap gap-3 text-sm">
        <Link
          href="/"
          className="rounded border border-rule bg-panel px-4 py-2 font-medium text-ink hover:no-underline"
        >
          Return home
        </Link>
        <Link
          href="/privacy"
          className="rounded border border-rule px-4 py-2 font-medium text-muted hover:text-ink hover:no-underline"
        >
          Privacy Policy
        </Link>
        <Link
          href="/terms"
          className="rounded border border-rule px-4 py-2 font-medium text-muted hover:text-ink hover:no-underline"
        >
          Terms
        </Link>
      </div>
    </main>
  );
}
