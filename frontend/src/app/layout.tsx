import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Geo-CashWatch | Predictive Geospatial Intelligence",
  description: "Predictive geospatial intelligence for cybercrime intervention.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="scroll-smooth">
      <body>{children}</body>
    </html>
  );
}
