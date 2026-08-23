const now = () => Date.now() / 1000

export const mockTransactions = [
  { tx_id: 'TXN-98234710', src_acc: 'XXXX 4921', dest_acc: 'MULE 8834', amount: 49999, channel: 'UPI', fraud_probability: .94, is_high_risk: true, reasons: ['Rapid fan-out detected', 'Dormant beneficiary'], timestamp: now() },
  { tx_id: 'TXN-14409218', src_acc: 'XXXX 1047', dest_acc: 'MULE 1209', amount: 28500, channel: 'IMPS', fraud_probability: .78, is_high_risk: true, reasons: ['Shared device fingerprint'], timestamp: now() - 8 },
  { tx_id: 'TXN-77510336', src_acc: 'XXXX 7730', dest_acc: 'XXXX 3182', amount: 3200, channel: 'UPI', fraud_probability: .18, is_high_risk: false, reasons: [], timestamp: now() - 16 },
  { tx_id: 'TXN-30988142', src_acc: 'XXXX 0652', dest_acc: 'MULE 6011', amount: 82500, channel: 'NEFT', fraud_probability: .87, is_high_risk: true, reasons: ['Velocity threshold exceeded', 'IP multiplexing'], timestamp: now() - 24 },
]

export const mockHotspots = [
  {
    h3_cell: '8860145b59fffff', lat: 28.6304, lon: 77.2177, risk_score: .94,
    event_count: 14, total_amount: 485000, unique_mule_accounts: 9, resolution: 8,
    polygon_coordinates: [[28.646,77.208],[28.641,77.229],[28.626,77.237],[28.614,77.221],[28.619,77.200],[28.634,77.196]],
    predicted_cashout_window: { start_time: new Date(Date.now()+12*60000).toISOString(), end_time: new Date(Date.now()+42*60000).toISOString(), eta_minutes: 12 },
    nearby_atms: [{ terminal_id: 'ATM-HDFC-104', bank: 'HDFC Bank', lat: 28.6328, lon: 77.2167 }, { terminal_id: 'AEPS-DEL-044', bank: 'AePS Merchant', lat: 28.626, lon: 77.225 }],
  },
  {
    h3_cell: '8860145a21fffff', lat: 28.5692, lon: 77.2435, risk_score: .73,
    event_count: 7, total_amount: 176000, unique_mule_accounts: 5, resolution: 8,
    polygon_coordinates: [[28.582,77.233],[28.577,77.253],[28.562,77.259],[28.552,77.244],[28.558,77.226],[28.572,77.222]],
    predicted_cashout_window: { start_time: new Date(Date.now()+24*60000).toISOString(), end_time: new Date(Date.now()+54*60000).toISOString(), eta_minutes: 24 },
    nearby_atms: [{ terminal_id: 'ATM-SBI-218', bank: 'State Bank of India', lat: 28.568, lon: 77.241 }],
  },
  {
    h3_cell: '886014c969fffff', lat: 28.6728, lon: 77.1402, risk_score: .57,
    event_count: 4, total_amount: 82000, unique_mule_accounts: 3, resolution: 8,
    polygon_coordinates: [[28.686,77.131],[28.681,77.150],[28.667,77.157],[28.658,77.142],[28.663,77.124],[28.677,77.119]],
    predicted_cashout_window: { start_time: new Date(Date.now()+36*60000).toISOString(), end_time: new Date(Date.now()+66*60000).toISOString(), eta_minutes: 36 }, nearby_atms: [],
  },
]

export function createScenario(kind) {
  const labels = { phishing: 'PHISH', arrest: 'ARREST', rat: 'APK-RAT' }
  const factor = kind === 'arrest' ? 1.45 : kind === 'rat' ? 1.2 : 1
  const transaction = {
    tx_id: `${labels[kind]}-${Math.floor(Math.random()*90000+10000)}`, src_acc: 'VICTIM 1930', dest_acc: `MULE ${Math.floor(Math.random()*8999+1000)}`,
    amount: Math.round(76000 * factor), channel: kind === 'rat' ? 'IMPS' : 'UPI', fraud_probability: .97, is_high_risk: true,
    reasons: [kind === 'arrest' ? 'Digital arrest pattern' : kind === 'rat' ? 'Remote-access device anomaly' : 'Phishing beneficiary fan-out', 'NCRP risk correlation'], timestamp: now(),
  }
  return { transaction, hotspot: { ...mockHotspots[0], h3_cell: `8860145${Math.floor(Math.random()*899+100)}ffff`, total_amount: Math.round(485000*factor), event_count: 15, risk_score: .97 } }
}
