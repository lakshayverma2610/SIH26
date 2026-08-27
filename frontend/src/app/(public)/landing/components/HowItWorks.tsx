"use client";

import { useRef } from "react";
import { AlertTriangle, BellRing, Crosshair, Database, MapPinned, Radar, ScanLine, ShieldCheck } from "lucide-react";
import { motion, useScroll, useSpring, useTransform } from "motion/react";
import type { MotionValue } from "motion/react";

const steps=[
  {n:"01",name:"Collect",copy:"Complaint and transaction signals enter a shared intelligence field."},
  {n:"02",name:"Analyze",copy:"Related events connect. Patterns emerge from dispersed data."},
  {n:"03",name:"Predict",copy:"Probability paths converge on a likely future cash-out location."},
  {n:"04",name:"Visualize",copy:"Geographic context turns prediction into an operational picture."},
  {n:"05",name:"Act",copy:"A verified risk becomes an actionable alert for authorized personnel."},
];
const dots=[{x:90,y:96},{x:176,y:62},{x:250,y:122},{x:128,y:190},{x:280,y:212},{x:205,y:270},{x:96,y:304},{x:315,y:310}];

function StoryStep({step,index,progress}:{step:(typeof steps)[number];index:number;progress:MotionValue<number>}) {
  const center=index*.2+.08;
  const opacity=useTransform(progress,[center-.09,center-.025,center+.09,center+.16],[0,1,1,0]);
  const y=useTransform(progress,[center-.09,center-.025,center+.09,center+.16],[36,0,0,-30]);
  return <motion.div style={{opacity,y}} className="absolute inset-0 flex flex-col justify-center"><span className="text-xs font-extrabold tracking-[.2em] text-blue-300">{step.n} / 05</span><h2 className="mt-4 text-5xl font-semibold capitalize text-white md:text-7xl">{step.name}</h2><p className="mt-6 max-w-md text-base leading-7 text-slate-300">{step.copy}</p></motion.div>;
}

function StepProgress({index,progress}:{index:number;progress:MotionValue<number>}) {
  const width=useTransform(progress,[index*.2,index*.2+.18],[0,44]);
  return <span className="h-1 w-11 overflow-hidden rounded-full bg-white/15"><motion.i style={{width}} className="block h-full bg-blue-400"/></span>;
}

export default function HowItWorks(){
  const ref=useRef<HTMLElement>(null);
  const {scrollYProgress}=useScroll({target:ref,offset:["start start","end end"]});
  const progress=useSpring(scrollYProgress,{stiffness:85,damping:28,mass:.35});
  const pointsOpacity=useTransform(progress,[0,.05,.93,1],[.35,1,1,.35]);
  const linePath=useTransform(progress,[.08,.3],[0,1]);
  const mapOpacity=useTransform(progress,[.25,.42],[0,1]);
  const mapScale=useTransform(progress,[.25,.55],[.82,1]);
  const heatOpacity=useTransform(progress,[.43,.58],[0,.9]);
  const predictionX=useTransform(progress,[.52,.68],[90,0]);
  const predictionOpacity=useTransform(progress,[.5,.62,.78,.86],[0,1,1,.25]);
  const alertX=useTransform(progress,[.72,.84],[100,0]);
  const alertOpacity=useTransform(progress,[.7,.82],[0,1]);
  const frameScale=useTransform(progress,[.78,.94],[.94,1]);
  const chromeOpacity=useTransform(progress,[.82,.98],[0,1]);
  const signalPath=useTransform(progress,[.7,.84],[0,1]);
  return <section ref={ref} id="how-it-works" className="relative h-[560vh] bg-[#071a31] text-white">
    <div className="sticky top-0 h-screen overflow-hidden">
      <div className="section-shell grid h-full items-center gap-8 pt-16 lg:grid-cols-[.72fr_1.28fr]">
        <div className="relative z-20 h-[210px] lg:h-[430px]">
          <p className="eyebrow absolute -top-12 !text-blue-300">The intelligence journey</p>
          {steps.map((step,i)=><StoryStep key={step.n} step={step} index={i} progress={progress}/>)}
          <div className="absolute bottom-0 flex gap-1.5">{steps.map((_,i)=><StepProgress key={i} index={i} progress={progress}/>)}</div>
        </div>
        <motion.div style={{scale:frameScale}} className="relative h-[45vh] min-h-[290px] max-h-[650px] overflow-hidden rounded-[22px] border border-white/15 bg-[#0d2948] shadow-2xl shadow-black/30 lg:h-[68vh] lg:min-h-[390px]">
          <div className="absolute inset-0 grid-noise opacity-40"/><div className="absolute inset-0 bg-[radial-gradient(circle_at_58%_55%,rgba(29,78,216,.22),transparent_42%)]"/>
          <motion.div style={{opacity:chromeOpacity}} className="absolute inset-x-0 top-0 z-30 flex h-12 items-center justify-between border-b border-white/10 bg-[#071a31]/90 px-4"><div className="flex items-center gap-2 text-[9px] font-bold tracking-[.14em] text-slate-300"><Radar size={14} className="text-blue-300"/> COMMAND CENTER</div><span className="rounded-full bg-emerald-400/10 px-2 py-1 text-[8px] font-bold text-emerald-300">● LIVE</span></motion.div>
          <motion.svg style={{opacity:pointsOpacity}} viewBox="0 0 430 420" className="absolute inset-0 h-full w-full" aria-label="Cybercrime data transforming into geospatial intelligence">
            <defs><radialGradient id="storyHeat"><stop stopColor="#dc2626" stopOpacity=".5"/><stop offset=".45" stopColor="#d97706" stopOpacity=".2"/><stop offset="1" stopColor="#1d4ed8" stopOpacity="0"/></radialGradient></defs>
            <motion.path d="M123 40l57 3 27 21 39-8 23 21-19 29 18 34-20 28 5 39-24 26-10 47-31 42-21 48-18-53-29-39-7-49-27-29 15-33-13-42 23-33-10-38 29-24z" fill="#dce8ef" fillOpacity=".12" stroke="#9db6c9" strokeWidth="1.5" style={{opacity:mapOpacity,scale:mapScale,transformOrigin:"50% 50%"}}/>
            <motion.path d="M90 96L176 62L250 122L128 190L280 212L205 270L96 304L315 310M90 96L128 190L205 270M250 122L280 212L315 310" fill="none" stroke="#60a5fa" strokeWidth="1.2" strokeDasharray="5 6" style={{pathLength:linePath}}/>
            <motion.circle cx="245" cy="218" r="92" fill="url(#storyHeat)" style={{opacity:heatOpacity}}/>
            {dots.map((p,i)=><g key={i}><circle cx={p.x} cy={p.y} r="4" fill={i>5?"#f59e0b":"#60a5fa"}/><motion.circle cx={p.x} cy={p.y} r="9" fill="none" stroke="#60a5fa" animate={{r:[6,15],opacity:[.6,0]}} transition={{duration:2.2,delay:i*.13,repeat:Infinity}}/></g>)}
            <motion.circle cx="245" cy="218" r="8" fill="#dc2626" style={{opacity:heatOpacity}}/><motion.circle cx="245" cy="218" r="28" fill="none" stroke="#ef4444" style={{opacity:heatOpacity}}/>
            <motion.path d="M245 218 C300 205 330 176 362 155" fill="none" stroke="#ef4444" strokeWidth="2" strokeDasharray="4 5" style={{pathLength:signalPath}}/>
          </motion.svg>
          <motion.div style={{opacity:predictionOpacity,x:predictionX}} className="absolute bottom-5 right-5 z-20 w-56 rounded-xl border border-blue-200/30 bg-white p-4 text-slate-900 shadow-2xl"><div className="flex items-center gap-2 text-[9px] font-extrabold tracking-[.13em] text-blue-700"><Crosshair size={13}/> PREDICTED CASH-OUT</div><p className="mt-2 text-xs font-semibold">Priority zone · Sector 14</p><div className="mt-4 grid grid-cols-2 gap-3"><div><b className="text-2xl text-red-600">91%</b><small className="block text-[8px] font-bold text-slate-500">RISK SCORE</small></div><div><b className="text-2xl text-[#0b1f3a]">87%</b><small className="block text-[8px] font-bold text-slate-500">CONFIDENCE</small></div></div><p className="mt-3 border-t border-slate-100 pt-2 text-[9px] font-bold text-emerald-700">● MONITORING</p></motion.div>
          <motion.div style={{opacity:alertOpacity,x:alertX}} className="absolute right-5 top-16 z-30 w-60 rounded-xl border border-red-200 bg-white p-4 text-slate-900 shadow-2xl"><div className="flex items-center justify-between text-[9px] font-extrabold tracking-wider text-red-600"><span className="flex items-center gap-2"><AlertTriangle size={13}/> HIGH-RISK ACTIVITY</span><span className="h-2 w-2 rounded-full bg-red-500"/></div><p className="mt-3 text-xs font-bold text-[#0b1f3a]">Potential cash-out hotspot detected</p><div className="mt-3 flex items-center gap-2 text-[9px] font-bold text-amber-700"><BellRing size={12}/> OFFICER NOTIFIED</div></motion.div>
          <motion.div style={{opacity:chromeOpacity}} className="absolute bottom-0 left-0 top-12 z-20 hidden w-14 flex-col items-center gap-5 border-r border-white/10 bg-[#071a31]/90 py-5 text-slate-400 sm:flex"><Database size={15}/><ScanLine size={15}/><MapPinned size={15} className="text-blue-300"/><BellRing size={15}/><ShieldCheck size={15}/></motion.div>
          <motion.div style={{opacity:chromeOpacity}} className="absolute bottom-0 left-14 right-0 z-10 grid grid-cols-4 border-t border-white/10 bg-[#071a31]/90">{[["SIGNALS","8,247"],["PREDICTIONS","126"],["ALERTS","18"],["RISK ZONES","07"]].map(m=><div key={m[0]} className="p-3"><small className="text-[7px] text-slate-400">{m[0]}</small><b className="block text-sm">{m[1]}</b></div>)}</motion.div>
        </motion.div>
      </div>
      <div className="absolute bottom-0 left-0 right-0 h-px bg-white/10"><motion.div style={{scaleX:progress,transformOrigin:"left"}} className="h-full bg-blue-400"/></div>
    </div>
  </section>;
}
