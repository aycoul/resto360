import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RESTO360 POS",
  description: "Restaurant POS System",
  manifest: "/manifest.json",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
