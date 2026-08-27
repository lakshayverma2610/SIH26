import Link from "next/link";

export default function NotFound() {
  return <main className="grid min-h-screen place-items-center bg-slate-50 p-6"><div className="text-center"><p className="eyebrow">404 · Route not found</p><h1 className="mt-4 text-4xl font-semibold text-navy">This intelligence route is unavailable.</h1><Link className="button-primary mt-8 inline-flex" href="/">Return home</Link></div></main>;
}
