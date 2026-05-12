import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "租屋聚合器",
  description: "雙通勤最佳化租屋搜尋",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-TW">
      <body>{children}</body>
    </html>
  );
}
