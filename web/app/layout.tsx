import type { Metadata } from "next";
import "./globals.css";
import { Topbar } from "@/components/layout/Topbar";
import { Footer } from "@/components/layout/Footer";

export const metadata: Metadata = {
  title: {
    default: "IESET — empirically-grounded economic policy framework",
    template: "%s · IESET",
  },
  description:
    "An adversarially-reviewed framework for contemporary economic policy questions. Every hypothesis pre-registered in git before the data is examined.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Topbar />
        {children}
        <Footer />
      </body>
    </html>
  );
}
