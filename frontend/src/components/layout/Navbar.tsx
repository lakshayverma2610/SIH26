"use client";

import Link from "next/link";
import { Menu, ShieldCheck, X } from "lucide-react";
import { useState } from "react";
import { motion, useMotionValueEvent, useScroll, useSpring, useTransform } from "motion/react";

const navigation = [
  ["Home", "#home"],
  ["How It Works", "#how-it-works"],
  ["Capabilities", "#capabilities"],
  ["Intelligence", "#intelligence"],
];

export default function Navbar() {
  const [raised, setRaised] = useState(false);
  const [open, setOpen] = useState(false);
  const { scrollY, scrollYProgress } = useScroll();
  const smoothProgress = useSpring(scrollYProgress, { stiffness: 110, damping: 28, mass: 0.3 });
  const width = useTransform(scrollY, [0, 180], ["94%", "90%"]);
  const y = useTransform(scrollY, [0, 180], [0, 12]);
  const scale = useTransform(scrollY, [0, 180], [1, 0.985]);
  useMotionValueEvent(scrollY, "change", (value) => setRaised(value > 24));

  return (
    <motion.header style={{ width, y, scale, x: "-50%" }} className={`fixed left-1/2 top-3 z-50 max-w-[1440px] overflow-hidden rounded-2xl border transition-[background-color,border-color,box-shadow] duration-500 ${raised ? "border-slate-200/90 bg-white/90 shadow-[0_16px_50px_rgba(15,23,42,.12)] backdrop-blur-xl" : "border-slate-200/70 bg-white/55 backdrop-blur-md"}`}>
      <nav className="flex h-16 items-center justify-between px-4 sm:px-6" aria-label="Main navigation">
        <Link href="#home" className="flex items-center gap-3">
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-[#0b1f3a] text-white"><ShieldCheck size={19} /></span>
          <span><b className="block text-[15px] tracking-tight text-navy">Geo-CashWatch</b><small className="block text-[8px] font-bold tracking-[.13em] text-slate-500">INTELLIGENCE SYSTEM</small></span>
        </Link>
        <div className="hidden items-center gap-8 md:flex">
          {navigation.map(([label, href]) => <Link key={href} href={href} className="text-[13px] font-semibold text-slate-600 transition hover:text-blue-700">{label}</Link>)}
        </div>
        <Link href="/login" className="button-primary hidden !min-h-10 md:inline-flex">Officer Login</Link>
        <button onClick={() => setOpen(!open)} className="grid h-10 w-10 place-items-center rounded-lg border border-slate-200 bg-white md:hidden" aria-label="Toggle navigation" aria-expanded={open}>{open ? <X size={19} /> : <Menu size={19} />}</button>
      </nav>
      {open && <div className="border-t border-slate-200 bg-white/95 p-5 backdrop-blur-xl md:hidden">{navigation.map(([label, href]) => <Link onClick={() => setOpen(false)} key={href} href={href} className="block border-b border-slate-100 py-3 text-sm font-semibold">{label}</Link>)}<Link href="/login" className="button-primary mt-4 flex">Officer Login</Link></div>}
      <motion.div aria-hidden="true" style={{ scaleX: smoothProgress, transformOrigin: "left" }} className="absolute inset-x-0 bottom-0 h-[2px] bg-gradient-to-r from-blue-700 via-cyan-600 to-teal-600" />
    </motion.header>
  );
}
