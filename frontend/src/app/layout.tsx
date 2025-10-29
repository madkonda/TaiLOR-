import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'TaiLOR • Video → Frames',
  description: 'Upload • Extract • Explore',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="header">
          <div className="brand">
            <div className="logo">TaiLOR</div>
            <div className="subtitle">Upload • Extract • Explore</div>
          </div>
          <nav className="tabs">
            <a href="/" className="tab">Upload</a>
            <a href="/gallery" className="tab">Gallery</a>
            <a href="/segment" className="tab">Segmentation</a>
          </nav>
        </header>
        <main className="container">{children}</main>
      </body>
    </html>
  );
}


