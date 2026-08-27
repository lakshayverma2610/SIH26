"use client";

import { motion, useReducedMotion } from "motion/react";
import type { ReactNode } from "react";

export function Reveal({ children, className = "", delay = 0 }: { children: ReactNode; className?: string; delay?: number }) {
  const reduce = useReducedMotion();
  return <motion.div className={className} initial={reduce ? false : { opacity:0, y:26, filter:"blur(8px)" }} whileInView={{ opacity:1, y:0, filter:"blur(0px)" }} viewport={{ once:true, margin:"-80px" }} transition={{ duration:.7, delay, ease:[.22,1,.36,1] }}>{children}</motion.div>;
}

export function Stagger({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <motion.div className={className} initial="hidden" whileInView="show" viewport={{ once:true, margin:"-60px" }} variants={{ hidden:{}, show:{ transition:{ staggerChildren:.1 } } }}>{children}</motion.div>;
}

export const itemVariants = { hidden:{ opacity:0, y:20 }, show:{ opacity:1, y:0, transition:{ duration:.55 } } };
export { motion };
