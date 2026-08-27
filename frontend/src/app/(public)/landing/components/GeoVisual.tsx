"use client";

import { motion } from "motion/react";

const points = [{x:142,y:104,r:6},{x:202,y:157,r:8},{x:155,y:224,r:5},{x:231,y:268,r:7},{x:118,y:298,r:5}];

export default function GeoVisual({ compact=false }: { compact?:boolean }) {
  return <div className={`relative overflow-hidden ${compact?"h-full min-h-72":"aspect-[5/4]"} rounded-2xl border border-slate-200 bg-[#eef4f8] grid-noise`}>
    <div className="absolute left-5 top-5 z-10 flex items-center gap-2 rounded-full border border-slate-200 bg-white/90 px-3 py-2 text-[10px] font-bold tracking-[.14em] text-slate-600"><span className="h-2 w-2 rounded-full bg-emerald-600"/> LIVE GEOSPATIAL SIGNAL</div>
    <svg viewBox="0 0 360 410" className="absolute inset-0 h-full w-full" role="img" aria-label="Abstract India map with predicted risk locations">
      <defs><linearGradient id="land" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#d7e4ed"/><stop offset="1" stopColor="#edf3f7"/></linearGradient><filter id="glow"><feGaussianBlur stdDeviation="7"/></filter></defs>
      <path d="M126 40l48 2 24 18 35-7 18 18-16 24 15 30-17 23 4 35-21 22-8 41-27 38-18 48-18 39-13-46-26-35-6-42-23-25 13-28-11-37 20-28-8-34 25-20z" fill="url(#land)" stroke="#9fb5c8" strokeWidth="1.5"/>
      <path d="M93 122c47 28 95 12 145 33M105 206c42-18 78 8 124 13M129 65c12 84 7 179 23 263M192 64c-11 88 12 155-28 235" fill="none" stroke="#b8c8d6" strokeDasharray="3 5"/>
      <motion.path d="M142 104 Q174 120 202 157 T231 268" fill="none" stroke="#1d4ed8" strokeWidth="1.7" strokeDasharray="5 6" initial={{pathLength:0,opacity:0}} animate={{pathLength:1,opacity:.8}} transition={{duration:2.2,repeat:Infinity,repeatDelay:1}}/>
      {points.map((p,i)=><g key={i}><circle cx={p.x} cy={p.y} r={p.r*3} fill={i===1?"#dc2626":"#1d4ed8"} opacity=".12" filter="url(#glow)"/><motion.circle cx={p.x} cy={p.y} r={p.r+5} fill="none" stroke={i===1?"#dc2626":"#1d4ed8"} strokeWidth="1" animate={{r:[p.r,p.r+12],opacity:[.7,0]}} transition={{duration:2,delay:i*.3,repeat:Infinity}}/><circle cx={p.x} cy={p.y} r={p.r/2} fill={i===1?"#dc2626":"#1d4ed8"}/></g>)}
    </svg>
    <motion.div initial={{opacity:0,x:20}} animate={{opacity:1,x:0}} transition={{delay:.8,duration:.6}} className="absolute bottom-5 right-5 w-48 rounded-xl border border-slate-200 bg-white/95 p-4 shadow-xl backdrop-blur">
      <div className="flex justify-between text-[9px] font-extrabold tracking-[.12em] text-red-600"><span>HIGH-RISK ACTIVITY</span><span className="h-2 w-2 rounded-full bg-red-500"/></div><p className="mt-2 text-xs font-semibold text-slate-700">Predicted cash-out zone</p><div className="mt-3 grid grid-cols-2 gap-3"><div><b className="text-xl text-navy">91%</b><span className="block text-[9px] uppercase text-slate-500">Risk score</span></div><div><b className="text-xl text-navy">87%</b><span className="block text-[9px] uppercase text-slate-500">Confidence</span></div></div><div className="mt-3 border-t border-slate-100 pt-2 text-[10px] font-bold text-emerald-700">● MONITORING</div>
    </motion.div>
  </div>;
}
