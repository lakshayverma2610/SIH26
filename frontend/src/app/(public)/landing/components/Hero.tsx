"use client";

import Link from "next/link";
import { ArrowDown, ArrowRight, LockKeyhole } from "lucide-react";
import { useRef } from "react";
import { motion, useScroll, useSpring, useTransform } from "motion/react";
import GeoVisual from "./GeoVisual";

export default function Hero(){
  const ref=useRef<HTMLElement>(null);
  const {scrollYProgress}=useScroll({target:ref,offset:["start start","end end"]});
  const progress=useSpring(scrollYProgress,{stiffness:90,damping:30});
  const textY=useTransform(progress,[0,.75],[0,-120]);
  const textOpacity=useTransform(progress,[.38,.82],[1,.12]);
  const visualScale=useTransform(progress,[0,.85],[.88,1.12]);
  const visualX=useTransform(progress,[0,.82],[35,-20]);
  const visualOpacity=useTransform(progress,[0,.18,.9],[.38,1,1]);
  const visualClip=useTransform(progress,[0,.65],["inset(12% 14% 12% 14% round 24px)","inset(0% 0% 0% 0% round 18px)"]);
  return <section ref={ref} id="home" className="relative h-[185vh] bg-[radial-gradient(circle_at_75%_20%,#ddecf6_0,transparent_32%),linear-gradient(180deg,#fff_0%,#f7f9fc_100%)]">
    <div className="sticky top-0 h-screen overflow-hidden pt-24"><div className="absolute left-0 top-0 h-full w-px bg-gradient-to-b from-transparent via-blue-200 to-transparent md:left-[8%]"/><div className="section-shell grid h-full items-center gap-12 lg:grid-cols-[.9fr_1.1fr]">
      <motion.div style={{y:textY,opacity:textOpacity}} initial={{opacity:0}} animate={{opacity:1}} transition={{duration:.8}} className="relative z-10"><div className="eyebrow">Geospatial Cybercrime Intelligence</div><h1 className="mt-7 text-[clamp(3.5rem,7vw,6.8rem)] font-semibold leading-[.88] text-navy">Predict.<br/><span className="text-blue-700">Locate.</span> Act.</h1><p className="mt-8 max-w-xl text-[17px] leading-8 text-slate-600">Transform cybercrime complaint and financial data into actionable intelligence — identifying likely cash-out locations before they become the next point of loss.</p><div className="mt-9 flex flex-col gap-3 sm:flex-row"><Link href="/login" className="button-primary inline-flex">Enter Command Center <ArrowRight size={16}/></Link><Link href="#problem" className="button-secondary inline-flex">Explore how it works <ArrowDown size={15}/></Link></div><p className="mt-6 flex items-center gap-2 text-xs font-medium text-slate-500"><LockKeyhole size={13}/> Restricted to authorized law-enforcement personnel</p></motion.div>
      <motion.div style={{scale:visualScale,x:visualX,opacity:visualOpacity,clipPath:visualClip}} className="relative hidden will-change-transform lg:block"><div className="absolute -inset-10 rounded-full bg-blue-300/15 blur-3xl"/><GeoVisual/><div className="absolute -left-5 bottom-12 hidden rounded-lg border border-slate-200 bg-white p-3 shadow-xl xl:block"><p className="text-[9px] font-bold tracking-wider text-slate-500">SIGNALS ANALYZED</p><p className="mt-1 text-lg font-bold text-navy">24 / 7</p></div></motion.div>
    </div><motion.div style={{scaleX:progress,transformOrigin:"left"}} className="absolute bottom-0 left-0 h-0.5 w-full bg-blue-600"/></div>
  </section>;
}
