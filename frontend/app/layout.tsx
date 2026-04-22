import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PortScanner — Network Port Scanner",
  description:
    "Web-based network port scanner for authorized network administration",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="text-(--fs-main)">{children}</body>
    </html>
  );
}
