import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BIZ360",
  description: "Universal Business Operating System",
  manifest: "/manifest.json",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
