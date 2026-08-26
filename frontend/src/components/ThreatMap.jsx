import { useEffect } from 'react'
import { CircleMarker, MapContainer, Polygon, Popup, TileLayer, Tooltip, Marker, useMap } from 'react-leaflet'
import { divIcon } from 'leaflet'

const risk = (score) => score >= .85 ? { name: 'critical', color: '#ff3b5c' } : score >= .65 ? { name: 'warning', color: '#ff9f1c' } : { name: 'watch', color: '#f5d547' }

const atmIcon = divIcon({ className: 'atm-marker', html: '<span>ATM</span>', iconSize: [34, 22], iconAnchor: [17, 11] })

function MapBoundsController({ hotspots, selected }) {
  const map = useMap()
  useEffect(() => {
    if (selected) {
      const target = hotspots.find((h) => h.h3_cell === selected)
      if (target && target.lat && target.lon) {
        map.flyTo([target.lat, target.lon], 13, { duration: 1.2 })
      }
    }
  }, [selected, hotspots, map])
  return null
}

export default function ThreatMap({ hotspots, transactions = [], selected, onSelect }) {
  // Extract high-risk individual transactions that have valid coordinates
  const flaggedTxs = transactions.filter(
    (tx) => (tx.is_high_risk || (tx.fraud_probability ?? 0) >= 0.65) && tx.lat && tx.lon
  )

  return (
    <MapContainer
      center={[22.5937, 78.9629]}
      zoom={5}
      minZoom={4}
      maxZoom={18}
      maxBounds={[[6.0, 68.0], [37.5, 97.5]]}
      zoomControl={true}
      className="threat-map"
    >
      <TileLayer
        attribution='&copy; OpenStreetMap &copy; CARTO'
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
      />
      <MapBoundsController hotspots={hotspots} selected={selected} />

      {/* 1. H3 Hexagonal Cluster Hotspot Zones */}
      {hotspots.map((hotspot) => {
        const level = risk(hotspot.risk_score)
        const points = hotspot.polygon_coordinates?.length
          ? hotspot.polygon_coordinates
          : [
              [hotspot.lat + 0.01, hotspot.lon],
              [hotspot.lat, hotspot.lon + 0.01],
              [hotspot.lat - 0.01, hotspot.lon],
              [hotspot.lat, hotspot.lon - 0.01],
            ]
        return (
          <Polygon
            key={hotspot.h3_cell}
            positions={points}
            pathOptions={{
              color: level.color,
              fillColor: level.color,
              fillOpacity: selected === hotspot.h3_cell ? 0.45 : 0.25,
              weight: selected === hotspot.h3_cell ? 3 : 2,
              className: level.name === 'critical' ? 'critical-zone' : '',
            }}
            eventHandlers={{ click: () => onSelect(hotspot.h3_cell) }}
          >
            <Tooltip direction="top">
              <b>{Math.round(hotspot.risk_score * 100)}% CLUSTER RISK</b>
              <br />
              ₹{Number(hotspot.total_amount).toLocaleString('en-IN')} exposed
              <br />
              {hotspot.unique_mule_accounts || 1} Mule Accounts
            </Tooltip>
          </Polygon>
        )
      })}

      {/* 2. Hotspot Centroid Circles */}
      {hotspots.map((hotspot) => (
        <CircleMarker
          key={`${hotspot.h3_cell}-core`}
          center={[hotspot.lat, hotspot.lon]}
          radius={6}
          pathOptions={{
            color: risk(hotspot.risk_score).color,
            fillColor: risk(hotspot.risk_score).color,
            fillOpacity: 1,
          }}
          eventHandlers={{ click: () => onSelect(hotspot.h3_cell) }}
        />
      ))}

      {/* 3. Individual High-Risk Transaction Alert Nodes */}
      {flaggedTxs.map((tx) => {
        const txScore = tx.fraud_probability ?? 0.8
        const level = risk(txScore)
        return (
          <CircleMarker
            key={`tx-${tx.tx_id}-${tx.timestamp}`}
            center={[tx.lat, tx.lon]}
            radius={3.5}
            pathOptions={{
              color: level.color,
              fillColor: level.color,
              fillOpacity: 0.85,
              weight: 1,
            }}
          >
            <Tooltip direction="top">
              <b>TX {tx.tx_id}</b> ({Math.round(txScore * 100)}% Risk)
              <br />
              ₹{Number(tx.amount || 0).toLocaleString('en-IN')} ({tx.channel || 'UPI'})
              <br />
              {tx.src_acc} → {tx.dest_acc}
            </Tooltip>
          </CircleMarker>
        )
      })}

      {/* 4. Target Physical ATMs for Selected or Active Hotspots */}
      {hotspots
        .filter((item) => !selected || item.h3_cell === selected)
        .flatMap((item) => item.nearby_atms || [])
        .map((atm) => (
          <Marker key={atm.id} position={[atm.lat, atm.lon]} icon={atmIcon}>
            <Popup>
              <b>{atm.bank}</b>
              <br />
              {atm.id}
              {atm.address && (
                <>
                  <br />
                  {atm.address}
                </>
              )}
            </Popup>
          </Marker>
        ))}
    </MapContainer>
  )
}
