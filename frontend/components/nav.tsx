import Link from 'next/link';
import { Sparkles } from 'lucide-react';

export default function Nav() {
  return (
    <header className="border-b border-border bg-panel/40 backdrop-blur sticky top-0 z-30">
      <div className="mx-auto max-w-7xl px-6 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight">
          <Sparkles className="w-4 h-4 text-accent" />
          <span>PM Copilot</span>
        </Link>
        <nav className="flex items-center gap-1 text-sm">
          <Link href="/samples" className="btn btn-ghost">Sample output</Link>
          <Link href="/projects" className="btn btn-ghost">Projects</Link>
          <a
            href="https://github.com/hardikh05/pm-copilot"
            target="_blank"
            rel="noreferrer"
            className="btn btn-ghost"
          >
            GitHub
          </a>
        </nav>
      </div>
    </header>
  );
}
