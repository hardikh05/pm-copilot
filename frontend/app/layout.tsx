import './globals.css';
import type { Metadata } from 'next';
import Nav from '@/components/nav';

export const metadata: Metadata = {
  title: 'PM Copilot',
  description: 'An AI copilot that turns raw user feedback into a prioritized roadmap.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-bg text-text font-sans antialiased">
        <Nav />
        <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
