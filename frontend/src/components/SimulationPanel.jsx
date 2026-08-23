import { Play, RotateCcw } from 'lucide-react'

const scenarios = [
  ['phishing', 'Phishing Burst'],
  ['arrest', 'Digital Arrest'],
  ['rat', 'APK / RAT Attack'],
]

export default function SimulationPanel({ onRun, onReset }) {
  return (
    <section>
      <div className="section-heading"><span>ATTACK SIMULATOR</span><small>DEMO CONTROL</small></div>
      <p className="section-copy">Inject a staged fraud pattern into the monitoring pipeline.</p>
      <div className="scenario-list">
        {scenarios.map(([key, label]) => <button key={key} onClick={() => onRun(key)}><Play size={13} fill="currentColor" />{label}</button>)}
      </div>
      <button className="reset-button" onClick={onReset}><RotateCcw size={13} /> Reset intelligence</button>
    </section>
  )
}
