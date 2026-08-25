const toLeafletBoundary = (hotspot) => {
  if (hotspot.polygon_coordinates?.length) return hotspot.polygon_coordinates
  const ring = hotspot.h3_boundary?.coordinates?.[0]
    || hotspot.raw_geojson_feature?.geometry?.coordinates?.[0]
  return ring?.map(([lon, lat]) => [lat, lon]) || []
}

export function normalizeAtm(atm = {}) {
  return {
    ...atm,
    id: atm.atm_id || atm.terminal_id || atm.id || `${atm.lat}-${atm.lon}`,
    bank: atm.bank_name || atm.bank || 'Unknown operator',
    distanceMeters: atm.distance_meters ?? (atm.distance_km != null ? atm.distance_km * 1000 : null),
  }
}

export function normalizeHotspot(hotspot = {}) {
  const centerLat = hotspot.lat ?? hotspot.center_lat
  const centerLon = hotspot.lon ?? hotspot.center_lon
  return {
    ...hotspot,
    h3_cell: hotspot.h3_cell || hotspot.h3_res8 || hotspot.cluster_id,
    lat: centerLat,
    lon: centerLon,
    risk_score: hotspot.risk_score ?? hotspot.aggregate_risk_score ?? 0,
    total_amount: hotspot.total_amount ?? hotspot.total_funds_at_risk ?? 0,
    unique_mule_accounts: hotspot.unique_mule_accounts ?? hotspot.mule_count ?? 0,
    event_count: hotspot.event_count ?? hotspot.mule_count ?? 0,
    average_fraud_probability: hotspot.average_fraud_probability ?? hotspot.raw_geojson_feature?.properties?.risk_score ?? hotspot.aggregate_risk_score ?? hotspot.risk_score ?? 0,
    polygon_coordinates: toLeafletBoundary(hotspot),
    nearby_atms: (hotspot.nearby_atms || hotspot.nearest_atms || []).map(normalizeAtm),
  }
}

export function normalizeTransaction(transaction = {}) {
  return {
    ...transaction,
    fraud_probability: transaction.fraud_probability ?? transaction.fraud_score ?? 0,
    is_high_risk: transaction.is_high_risk ?? (transaction.fraud_probability ?? transaction.fraud_score ?? 0) >= .7,
    reasons: transaction.reasons || [],
  }
}

export function formatCashoutTime(value, fallback) {
  if (!value) return fallback
  const parsed = new Date(value)
  if (!Number.isNaN(parsed.getTime())) return parsed.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
  return String(value).replace(' UTC', '')
}
