import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "堂單 — 一條連結收學費",
  description: "家長打開一條連結，見到今個月堂數、未付金額同轉數快。一年 HK$480。",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-Hant">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,560;9..144,660&family=Noto+Sans+TC:wght@400;500;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <div className="wrap">
          <header className="top">
            <a className="brand" href="/">堂單</a>
            <nav className="nav">
              <a href="/p/miss-chan">示範</a>
              <a href="/studio">老師後台</a>
            </nav>
          </header>
          {children}
          <footer className="site-footer">家長直接轉數快俾老師。堂單收唔到學費。</footer>
        </div>
      </body>
    </html>
  );
}
