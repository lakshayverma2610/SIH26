import { CircleMarker, MapContainer, Polygon, Popup, TileLayer, Tooltip } from 'react-leaflet'
import { divIcon } from 'leaflet'
import { Marker } from 'react-leaflet'

const risk = (score) => score >= .85 ? { name: 'critical', color: '#ff3b5c' } : score >= .65 ? { name: 'warning', color: '#ff9f1c' } : { name: 'watch', color: '#f5d547' }
const atmIcon = divIcon({ className: 'atm-marker', html: '<span>ATM</span>', iconSize: [34, 22], iconAnchor: [17, 11] })

export default function ThreatMap({ hotspots, selected, onSelect }) {
  return (
    <MapContainer center={[28.6139, 77.209]} zoom={11} zoomControl={false} className="threat-map">
      <TileLayer attribution='&copy; OpenStreetMap &copy; CARTO' url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" />
      {hotspots.map((hotspot) => {
        const level = risk(hotspot.risk_score)
        const points = hotspot.polygon_coordinates?.length ? hotspot.polygon_coordinates : [[hotspot.lat+.01,hotspot.lon],[hotspot.lat,hotspot.lon+.01],[hotspot.lat-.01,hotspot.lon],[hotspot.lat,hotspot.lon-.01]]
        return (
          <Polygon key={hotspot.h3_cell} positions={points} pathOptions={{ color: level.color, fillColor: level.color, fillOpacity: selected === hotspot.h3_cell ? .42 : .22, weight: selected === hotspot.h3_cell ? 3 : 2, className: level.name === 'critical' ? 'critical-zone' : '' }} eventHandlers={{ click: () => onSelect(hotspot.h3_cell) }}>
            <Tooltip direction="top"><b>{Math.round(hotspot.risk_score*100)}% RISK</b><br />₹{Number(hotspot.total_amount).toLocaleString('en-IN')} exposed</Tooltip>
          </Polygon>
        )
      })}
      {hotspots.map((hotspot) => <CircleMarker key={`${hotspot.h3_cell}-core`} center={[hotspot.lat, hotspot.lon]} radius={4} pathOptions={{ color: risk(hotspot.risk_score).color, fillOpacity: 1 }} />)}
      {hotspots.filter((item) => item.h3_cell === selected).flatMap((item) => item.nearby_atms || []).map((atm) => (
        <Marker key={atm.id} position={[atm.lat, atm.lon]} icon={atmIcon}><Popup><b>{atm.bank}</b><br />{atm.id}{atm.address && <><br />{atm.address}</>}</Popup></Marker>
      ))}
    </MapContainer>
  )
}
