"use client";

import { useRef } from "react";
import Link from "next/link";
import { AlertTriangle, ArrowDown, ArrowRight, BellRing, Database, Fingerprint, MapPinned, Radar, ScanLine } from "lucide-react";
import { motion, useScroll, useSpring, useTransform } from "motion/react";
import type { MotionValue } from "motion/react";

type LayerConfig={id:string;index:string;title:string;color:string;explodeY:number;explodeX:number;z:number;tilt:number};
const layers:LayerConfig[]=[
  {id:"alert",index:"06",title:"Alert / Action",color:"#dc2626",explodeY:-250,explodeX:18,z:150,tilt:-1.5},
  {id:"risk",index:"05",title:"Risk Layer",color:"#d97706",explodeY:-150,explodeX:-38,z:95,tilt:2},
  {id:"prediction",index:"04",title:"Prediction Engine",color:"#1d4ed8",explodeY:-54,explodeX:42,z:50,tilt:-1},
  {id:"geo",index:"03",title:"Geospatial Analysis",color:"#0f766e",explodeY:48,explodeX:-30,z:10,tilt:1},
  {id:"pattern",index:"02",title:"Transaction Patterns",color:"#2563eb",explodeY:150,explodeX:34,z:-40,tilt:-1.5},
  {id:"raw",index:"01",title:"Raw Data",color:"#64748b",explodeY:250,explodeX:-16,z:-90,tilt:1},
];
const messages=[
  {at:0,title:"Predict. Locate. Act.",copy:"Transform cybercrime complaint and financial data into actionable intelligence — identifying likely cash-out locations before they become the next point of loss."},
  {at:.18,title:"Every signal tells a story.",copy:"The intelligence core opens to expose every operational layer."},
  {at:.37,title:"Separate signal from noise.",copy:"Six connected layers reveal how raw events become structured intelligence."},
  {at:.56,title:"See where the money moves next.",copy:"Geography, probability and risk converge on a predicted location."},
  {at:.73,title:"Turn prediction into action.",copy:"The alert layer activates while the evidence remains visibly connected."},
  {at:.91,title:"From data to intervention.",copy:"The transformed layers lock into one deployable command center."},
];

const dataDots=[{x:35,y:34},{x:88,y:52},{x:142,y:30},{x:196,y:57},{x:250,y:35},{x:305,y:56},{x:365,y:31},{x:430,y:52}];

function Narrative({message,index,progress}:{message:(typeof messages)[number];index:number;progress:MotionValue<number>}){
  const next=messages[index+1]?.at??1.08;
  const opacity=useTransform(progress,[Math.max(0,message.at-.035),message.at+.015,next-.075,next-.025],[0,1,1,0]);
  const y=useTransform(progress,[Math.max(0,message.at-.035),message.at+.015,next-.075,next-.025],[28,0,0,-24]);
  return <motion.div style={{opacity,y}} className="absolute inset-0 flex flex-col justify-center">
    <p className="eyebrow">{index===0?"Geospatial Cybercrime Intelligence":`Intelligence Core · Phase 0${index}`}</p>
    <h1 className="mt-6 max-w-3xl text-[clamp(3.2rem,7vw,7.4rem)] font-semibold leading-[.88] text-[#0b1f3a]">{message.title}</h1>
    <p className="mt-7 max-w-xl text-[15px] leading-7 text-slate-600 md:text-base">{message.copy}</p>
    {index===0&&<div className="mt-8 flex flex-col gap-3 sm:flex-row"><Link href="/login" className="button-primary inline-flex">Enter Command Center <ArrowRight size={16}/></Link><a href="#how-it-works" className="button-secondary inline-flex">Explore the intelligence <ArrowDown size={15}/></a></div>}
  </motion.div>;
}

function LayerContent({id,reveal}:{id:string;reveal:MotionValue<number>}){
  if(id==="raw") return <motion.svg style={{opacity:reveal}} viewBox="0 0 470 78" className="absolute inset-0 h-full w-full">{dataDots.map((d,i)=><g key={i}><circle cx={d.x} cy={d.y} r="3.5" fill="#64748b"/><circle cx={d.x} cy={d.y} r="9" fill="none" stroke="#94a3b8" strokeOpacity=".45"/></g>)}</motion.svg>;
  if(id==="pattern") return <motion.svg style={{opacity:reveal}} viewBox="0 0 470 78" className="absolute inset-0 h-full w-full"><path d="M35 34L88 52L142 30L196 57L250 35L305 56L365 31L430 52M88 52L196 57L305 56M142 30L250 35L365 31" fill="none" stroke="#2563eb" strokeWidth="1.2" strokeDasharray="4 4"/>{dataDots.map((d,i)=><circle key={i} cx={d.x} cy={d.y} r="3" fill="#2563eb"/>)}</motion.svg>;
  if(id==="geo") return <motion.svg style={{opacity:reveal}} viewBox="0 0 470 78" className="absolute inset-0 h-full w-full"><path d="M205 8l32 2 15 12 23-5 13 12-11 16 10 19-11 10h-77l8-18-7-23 13-18z" fill="#d7e8e5" stroke="#0f766e" strokeWidth="1"/><path d="M201 38c31 8 53-2 82 7M228 11c-2 20 3 40-5 60" fill="none" stroke="#0f766e" strokeOpacity=".45" strokeDasharray="2 3"/><circle cx="255" cy="44" r="4" fill="#0f766e"/></motion.svg>;
  if(id==="prediction") return <motion.svg style={{opacity:reveal}} viewBox="0 0 470 78" className="absolute inset-0 h-full w-full"><path d="M75 58Q165 8 255 42T405 20" fill="none" stroke="#1d4ed8" strokeWidth="2" strokeDasharray="5 5"/><circle cx="255" cy="42" r="6" fill="#1d4ed8"/><circle cx="405" cy="20" r="9" fill="none" stroke="#1d4ed8"/><text x="328" y="58" fill="#1d4ed8" fontSize="8" fontWeight="700">PREDICTION PATH · 87%</text></motion.svg>;
  if(id==="risk") return <motion.div style={{opacity:reveal}} className="absolute inset-0 flex items-center justify-center"><span className="absolute h-16 w-40 rounded-[50%] bg-amber-500/10"/><span className="absolute h-10 w-24 rounded-[50%] border border-amber-500/50"/><b className="relative text-xs text-amber-700">RISK ZONE · 91%</b></motion.div>;
  return <motion.div style={{opacity:reveal}} className="absolute inset-0 flex items-center justify-center gap-3"><span className="relative h-2.5 w-2.5 rounded-full bg-red-600"><i className="dot-pulse absolute inset-0 rounded-full bg-red-500"/></span><b className="text-xs text-red-700">HIGH-RISK ACTIVITY · OFFICER NOTIFIED</b><BellRing size={14} className="text-red-600"/></motion.div>;
}

function CoreLayer({layer,progress}:{layer:LayerConfig;progress:MotionValue<number>}){
  const assembledY=(Number(layer.index)-3.5)*7;
  const y=useTransform(progress,[0,.1,.4,.62,.79,.9,1],[assembledY,assembledY,layer.explodeY,layer.explodeY*.92,layer.explodeY*.45,assembledY,assembledY]);
  const x=useTransform(progress,[0,.1,.4,.62,.79,.9,1],[0,0,layer.explodeX,layer.explodeX*1.15,layer.explodeX*.35,0,0]);
  const z=useTransform(progress,[0,.1,.4,.62,.79,.9,1],[Number(layer.index)*5,Number(layer.index)*5,layer.z,layer.z*1.18,layer.z*.35,Number(layer.index)*5,0]);
  const rotateX=useTransform(progress,[0,.15,.4,.7,.9],[64,64,54,46,0]);
  const rotateZ=useTransform(progress,[0,.4,.72,.9],[0,layer.tilt,-layer.tilt*.5,0]);
  const scale=useTransform(progress,[0,.4,.68,.9],[1,1.02,1.06,1]);
  const content=useTransform(progress,[.23,.45,.78,.9],[.08,1,1,.4]);
  const labelOpacity=useTransform(progress,[.1,.28,.78,.9],[0,1,1,0]);
  return <div style={{translate:"-50% -50%"}} className="absolute left-1/2 top-1/2 h-[82px] w-[min(76vw,540px)]"><motion.div style={{x,y,z,rotateX,rotateZ,scale,transformStyle:"preserve-3d"}} className="absolute inset-0 will-change-transform">
    <div className="absolute inset-0 overflow-hidden rounded-2xl border border-slate-300/90 bg-white/86 shadow-[0_20px_45px_rgba(15,31,58,.13)] backdrop-blur-md">
      <div className="absolute inset-x-0 top-0 h-[3px]" style={{backgroundColor:layer.color}}/>
      <div className="absolute inset-0 grid-noise opacity-30"/><LayerContent id={layer.id} reveal={content}/>
    </div>
    <motion.div style={{opacity:labelOpacity}} className="absolute -left-28 top-1/2 hidden -translate-y-1/2 text-right lg:block"><b className="block text-[9px] tracking-[.16em]" style={{color:layer.color}}>{layer.index}</b><span className="whitespace-nowrap text-[10px] font-bold uppercase tracking-[.1em] text-slate-600">{layer.title}</span></motion.div>
    <motion.span style={{opacity:labelOpacity,backgroundColor:layer.color}} className="absolute -right-3 top-1/2 h-1.5 w-1.5 -translate-y-1/2 rounded-full" animate={{scale:[1,1.5,1]}} transition={{duration:2.4,repeat:Infinity}} />
  </motion.div></div>;
}

export default function CinematicJourney(){
  const ref=useRef<HTMLElement>(null);
  const {scrollYProgress}=useScroll({target:ref,offset:["start start","end end"]});
  const p=useSpring(scrollYProgress,{stiffness:82,damping:27,mass:.38});
  const objectX=useTransform(p,[0,.12,.24,.82,.94],[220,90,135,100,0]);
  const objectScale=useTransform(p,[0,.12,.4,.72,.92,1],[.88,1,1.02,.96,.84,1]);
  const rotateY=useTransform(p,[0,.25,.5,.75,1],[0,15,35,20,0]);
  const rotateX=useTransform(p,[0,.4,.7,1],[0,-2,3,0]);
  const coreLift=useTransform(p,[0,.4,.8,1],[20,0,-10,0]);
  const connectors=useTransform(p,[.17,.38,.78,.88],[0,1,1,0]);
  const shellOpacity=useTransform(p,[.84,.96],[0,1]);
  const shellScale=useTransform(p,[.84,1],[.8,1]);
  const narrativeOpacity=useTransform(p,[0,.82,.92],[1,1,0]);
  const background=useTransform(p,[0,.45,.82,1],["#f8fafc","#f3f7fb","#eef4f8","#e8eff6"]);
  return <motion.section ref={ref} id="home" style={{backgroundColor:background}} className="relative h-[1000vh]">
    <span id="how-it-works" className="absolute top-[110vh]"/><span id="intelligence" className="absolute top-[620vh]"/>
    <div className="sticky top-0 h-screen overflow-hidden">
      <div className="absolute inset-0 grid-noise opacity-40"/><div className="absolute left-[7%] top-0 h-full w-px bg-gradient-to-b from-transparent via-blue-200 to-transparent"/>
      <motion.div style={{opacity:narrativeOpacity}} className="section-shell absolute inset-x-0 top-0 z-30 grid h-screen lg:grid-cols-[.84fr_1.16fr]"><div className="relative h-[56vh] self-center">{messages.map((message,i)=><Narrative key={message.title} message={message} index={i} progress={p}/>)}</div></motion.div>

      <div className="absolute inset-0 [perspective:1600px]">
        <motion.div style={{x:objectX,y:coreLift,scale:objectScale,rotateY,rotateX,transformStyle:"preserve-3d"}} className="absolute inset-0 will-change-transform">
          <motion.div style={{opacity:connectors,scaleY:connectors}} className="absolute left-1/2 top-1/2 z-0 h-[520px] w-px -translate-x-1/2 -translate-y-1/2 origin-center bg-gradient-to-b from-red-300 via-blue-300 to-slate-300"/>
          {layers.map(layer=><CoreLayer key={layer.id} layer={layer} progress={p}/>)}
        </motion.div>
      </div>

      <motion.div style={{opacity:shellOpacity,scale:shellScale,x:"-50%"}} className="absolute bottom-[8%] left-1/2 z-20 h-[72vh] w-[88vw] max-w-[1280px] overflow-hidden rounded-2xl border border-slate-300 bg-white/82 shadow-[0_45px_120px_rgba(15,31,58,.18)] backdrop-blur-xl">
        <header className="flex h-12 items-center justify-between border-b border-slate-200 px-4"><span className="flex items-center gap-2 text-[9px] font-extrabold tracking-[.15em] text-[#0b1f3a]"><Radar size={14} className="text-blue-700"/> GEO-CASHWATCH COMMAND CENTER</span><span className="rounded-full bg-emerald-50 px-2 py-1 text-[8px] font-bold text-emerald-700">● OPERATIONAL</span></header>
        <aside className="absolute bottom-0 left-0 top-12 flex w-14 flex-col items-center gap-6 border-r border-slate-200 py-6 text-slate-400"><Database size={15}/><ScanLine size={15}/><MapPinned size={15} className="text-blue-700"/><BellRing size={15}/><Fingerprint size={15}/></aside>
        <div className="absolute bottom-14 left-14 right-[270px] top-12 grid-noise"><div className="absolute inset-0 bg-[radial-gradient(circle_at_58%_50%,rgba(29,78,216,.12),transparent_38%)]"/></div>
        <aside className="absolute bottom-14 right-0 top-12 w-[270px] border-l border-slate-200 bg-white/85 p-4"><p className="text-[9px] font-extrabold tracking-[.12em] text-red-600">ACTIVE INTELLIGENCE</p><div className="mt-4 rounded-xl border border-red-100 p-4"><AlertTriangle size={14} className="text-red-600"/><b className="mt-3 block text-xs text-[#0b1f3a]">Cash-out hotspot detected</b><p className="mt-2 text-[10px] text-slate-500">Risk 91% · Confidence 87%</p></div></aside>
        <div className="absolute bottom-0 left-14 right-0 grid h-14 grid-cols-4 border-t border-slate-200 bg-white">{[["SIGNALS","8,247"],["PREDICTIONS","126"],["PRIORITY ALERTS","18"],["RISK ZONES","07"]].map(m=><div key={m[0]} className="border-r border-slate-100 px-4 py-2 last:border-0"><small className="text-[7px] font-bold text-slate-400">{m[0]}</small><b className="block text-sm text-[#0b1f3a]">{m[1]}</b></div>)}</div>
      </motion.div>

      <div className="absolute bottom-4 left-1/2 z-40 -translate-x-1/2"><p className="text-[8px] font-bold uppercase tracking-[.18em] text-slate-400">Scroll controls the intelligence core</p><div className="mx-auto mt-2 h-8 w-px bg-slate-200"><motion.div style={{scaleY:p,transformOrigin:"top"}} className="h-full bg-blue-700"/></div></div>
    </div>
  </motion.section>;
}
