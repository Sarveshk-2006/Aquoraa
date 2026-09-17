import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Polygon, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix Leaflet's default icon path issue in Vite
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Defensive coordinate validator helper
const isValidCoord = (coord: any): coord is number => {
  return typeof coord === 'number' && !isNaN(coord) && isFinite(coord);
};

const sanitizeLatLng = (pos: any, fallback: [number, number] = [19.076, 72.8777]): [number, number] => {
  if (Array.isArray(pos) && pos.length >= 2 && isValidCoord(pos[0]) && isValidCoord(pos[1])) {
    return [pos[0], pos[1]];
  }
  return fallback;
};

// Helper component to update bounds or view position dynamically
const MapController: React.FC<{
  center?: [number, number];
  zoom?: number;
  bounds?: [number, number][];
}> = ({ center, zoom, bounds }) => {
  const map = useMap();

  useEffect(() => {
    const validCenter = sanitizeLatLng(center);
    const validBounds = (bounds || []).filter(
      (b) => Array.isArray(b) && b.length >= 2 && isValidCoord(b[0]) && isValidCoord(b[1])
    ) as [number, number][];

    if (validBounds.length > 1) {
      try {
        map.fitBounds(validBounds, { padding: [30, 30], maxZoom: 15 });
      } catch {
        map.setView(validCenter, zoom || 13);
      }
    } else {
      map.setView(validCenter, zoom || 13);
    }
  }, [map, center, zoom, bounds]);

  return null;
};

export interface MapMarkerItem {
  id: string;
  position: [number, number]; // [lat, lon]
  title?: string;
  subtitle?: string;
  badge?: string;
  color?: string; // hex or tailwind class
  iconSvg?: string;
  popupContent?: string;
  onClick?: () => void;
  details?: React.ReactNode;
}

export interface MapPolylineItem {
  id: string;
  positions: [number, number][]; // Array of [lat, lon]
  color?: string;
  weight?: number;
  dashArray?: string;
  opacity?: number;
  title?: string;
  onClick?: () => void;
}

export interface MapPolygonItem {
  id: string;
  positions: [number, number][]; // Array of [lat, lon]
  color?: string;
  fillColor?: string;
  fillOpacity?: number;
  strokeColor?: string;
  weight?: number;
  title?: string;
  popupContent?: string;
}

export interface FloodPoint {
  lat: number;
  lng: number;
  depth: number;
}

/* ─── Hydrological Canvas Raster Water Overlay ───────────────── */
export const FloodWaterCanvasOverlay: React.FC<{
  points?: FloodPoint[];
  intensityMultiplier?: number;
}> = ({ points, intensityMultiplier = 1.0 }) => {
  const map = useMap();

  useEffect(() => {
    // Default data-driven points following Mithi River lowlands if none passed
    const defaultPoints: FloodPoint[] = [
      // River core (severe depth > 2.0m)
      { lat: 19.074, lng: 72.876, depth: 2.4 },
      { lat: 19.072, lng: 72.873, depth: 2.2 },
      { lat: 19.070, lng: 72.871, depth: 2.1 },
      { lat: 19.068, lng: 72.868, depth: 1.9 },
      // Kurla West & East lowlands (1.0 - 2.0m depth)
      { lat: 19.078, lng: 72.880, depth: 1.8 },
      { lat: 19.075, lng: 72.883, depth: 1.6 },
      { lat: 19.071, lng: 72.885, depth: 1.4 },
      { lat: 19.065, lng: 72.882, depth: 1.3 },
      { lat: 19.062, lng: 72.878, depth: 1.2 },
      // Kalina & BKC floodplain (0.5 - 1.0m depth)
      { lat: 19.082, lng: 72.865, depth: 0.9 },
      { lat: 19.080, lng: 72.870, depth: 0.85 },
      { lat: 19.077, lng: 72.862, depth: 0.8 },
      { lat: 19.069, lng: 72.861, depth: 0.75 },
      { lat: 19.064, lng: 72.864, depth: 0.7 },
      { lat: 19.058, lng: 72.860, depth: 0.65 },
      // Outer spread & shallow ponding (0.1 - 0.5m depth)
      { lat: 19.088, lng: 72.860, depth: 0.45 },
      { lat: 19.085, lng: 72.875, depth: 0.4 },
      { lat: 19.082, lng: 72.890, depth: 0.35 },
      { lat: 19.076, lng: 72.895, depth: 0.3 },
      { lat: 19.060, lng: 72.890, depth: 0.28 },
      { lat: 19.053, lng: 72.875, depth: 0.25 },
      { lat: 19.050, lng: 72.855, depth: 0.22 },
      { lat: 19.056, lng: 72.848, depth: 0.18 },
      { lat: 19.072, lng: 72.845, depth: 0.15 },
    ];

    const activePoints = (points && points.length > 0) ? points : defaultPoints;

    // Create container canvas
    const canvas = L.DomUtil.create('canvas', 'leaflet-flood-canvas-overlay');
    canvas.style.position = 'absolute';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.pointerEvents = 'none';
    canvas.style.zIndex = '200'; // Below markers (300+), above tile layer

    const overlayPane = map.getPanes().overlayPane;
    overlayPane.appendChild(canvas);

    const draw = () => {
      const size = map.getSize();
      const zoom = map.getZoom();

      canvas.width = size.x;
      canvas.height = size.y;

      const topLeft = map.containerPointToLayerPoint([0, 0]);
      L.DomUtil.setPosition(canvas, topLeft);

      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      ctx.clearRect(0, 0, size.x, size.y);

      // Base radius scales smoothly with map zoom level
      const baseRadius = Math.max(25, 42 * Math.pow(1.3, zoom - 13));

      // Draw soft radial water depth gradients that seamlessly merge
      activePoints.forEach((pt) => {
        const scaledDepth = pt.depth * intensityMultiplier;
        if (scaledDepth <= 0.02) return;

        const containerPt = map.latLngToContainerPoint([pt.lat, pt.lng]);
        const x = containerPt.x;
        const y = containerPt.y;

        // Skip off-screen points with padding
        if (x < -100 || x > size.x + 100 || y < -100 || y > size.y + 100) return;

        const radius = baseRadius * Math.min(1.6, Math.max(0.7, Math.sqrt(scaledDepth)));

        const grad = ctx.createRadialGradient(x, y, 0, x, y, radius);

        // Map depth to continuous water depth color & opacity gradient
        if (scaledDepth > 2.0) {
          grad.addColorStop(0.0, 'rgba(30, 64, 175, 0.75)'); // Deep Royal Blue
          grad.addColorStop(0.3, 'rgba(2, 132, 199, 0.60)');  // Strong Water Blue
          grad.addColorStop(0.6, 'rgba(56, 189, 248, 0.40)');  // Cyan
          grad.addColorStop(0.85, 'rgba(103, 232, 249, 0.20)'); // Light Cyan
          grad.addColorStop(1.0, 'rgba(103, 232, 249, 0)');    // Soft Feathered Edge
        } else if (scaledDepth > 1.0) {
          grad.addColorStop(0.0, 'rgba(2, 132, 199, 0.65)');  // Strong Water Blue
          grad.addColorStop(0.4, 'rgba(56, 189, 248, 0.45)');  // Cyan
          grad.addColorStop(0.8, 'rgba(103, 232, 249, 0.22)'); // Light Cyan
          grad.addColorStop(1.0, 'rgba(103, 232, 249, 0)');    // Soft Feathered Edge
        } else if (scaledDepth > 0.5) {
          grad.addColorStop(0.0, 'rgba(56, 189, 248, 0.50)');  // Cyan
          grad.addColorStop(0.5, 'rgba(103, 232, 249, 0.30)'); // Light Cyan
          grad.addColorStop(1.0, 'rgba(103, 232, 249, 0)');    // Soft Feathered Edge
        } else {
          grad.addColorStop(0.0, 'rgba(103, 232, 249, 0.35)'); // Light Cyan
          grad.addColorStop(0.6, 'rgba(165, 243, 252, 0.18)'); // Pale Cyan
          grad.addColorStop(1.0, 'rgba(165, 243, 252, 0)');    // Soft Feathered Edge
        }

        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fill();
      });
    };

    draw();

    map.on('move', draw);
    map.on('zoomend', draw);
    map.on('resize', draw);

    return () => {
      map.off('move', draw);
      map.off('zoomend', draw);
      map.off('resize', draw);
      if (overlayPane.contains(canvas)) {
        overlayPane.removeChild(canvas);
      }
    };
  }, [map, points, intensityMultiplier]);

  return null;
};

export interface LeafletMapProps {
  center?: [number, number]; // [lat, lon]
  zoom?: number;
  bounds?: [number, number][];
  autoFitBounds?: boolean;
  markers?: MapMarkerItem[];
  polylines?: MapPolylineItem[];
  polygons?: MapPolygonItem[];
  floodPoints?: FloodPoint[];
  floodIntensityMultiplier?: number;
  showFullscreenControl?: boolean;
  className?: string;
  style?: React.CSSProperties;
  height?: string;
  children?: React.ReactNode;
}

// Custom DivIcon generator to render floating pill markers matching reference image
export const createCustomPin = (colorHex: string = '#0284c7', label?: string, title?: string, badgeText?: string) => {
  if (title) {
    // Rich floating pill marker (e.g. "Kurla Junction | High risk")
    const isRed = colorHex === '#dc2626' || colorHex === '#b91c1c' || badgeText?.toLowerCase().includes('risk');
    const badgeColor = isRed ? '#dc2626' : colorHex;

    return L.divIcon({
      className: 'custom-leaflet-pill-marker',
      html: `
        <div style="
          display: inline-flex;
          align-items: center;
          gap: 6px;
          background: #ffffff;
          padding: 3px 8px 3px 4px;
          border-radius: 9999px;
          border: 1px solid rgba(15,35,64,0.15);
          box-shadow: 0 4px 12px rgba(15,35,64,0.15);
          font-family: ui-sans-serif, system-ui, sans-serif;
          white-space: nowrap;
          transform: translate(-50%, -50%);
        ">
          <div style="
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: ${badgeColor};
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 11px;
            shrink: 0;
          ">
            ${badgeText || (isRed ? '!' : '+')}
          </div>
          <div style="display: flex; flex-direction: column; leading: 1;">
            <span style="font-size: 11px; font-weight: 700; color: #0f2340;">${title}</span>
            ${label ? `<span style="font-size: 9px; font-weight: 600; color: ${badgeColor}; flex: 1;">${label}</span>` : ''}
          </div>
        </div>
      `,
      iconSize: [140, 30],
      iconAnchor: [70, 15],
      popupAnchor: [0, -15],
    });
  }

  // Standard circular pin fallback
  return L.divIcon({
    className: 'custom-leaflet-marker',
    html: `
      <div style="
        background-color: ${colorHex};
        width: 24px;
        height: 24px;
        border-radius: 50%;
        border: 2px solid #ffffff;
        box-shadow: 0 4px 8px rgba(15, 35, 64, 0.2);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #ffffff;
        font-weight: bold;
        font-size: 11px;
        font-family: ui-sans-serif, system-ui, sans-serif;
      ">
        ${badgeText || label || '•'}
      </div>
    `,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -12],
  });
};

/* ─── Custom Floating Aquora Zoom Control ─────────────────────── */
const AquoraZoomControl: React.FC = () => {
  const map = useMap();
  return (
    <div
      className="absolute top-4 left-4 z-[1000] flex flex-col bg-white/95 backdrop-blur-md rounded-xl border overflow-hidden"
      style={{
        borderColor: 'rgba(15,35,64,0.12)',
        boxShadow: '0 4px 14px rgba(15,35,64,0.12)',
      }}
    >
      <button
        onClick={() => map.zoomIn()}
        className="w-8 h-8 flex items-center justify-center text-[#0f2340] hover:bg-slate-100 font-bold text-base transition-colors border-b"
        style={{ borderColor: 'rgba(15,35,64,0.08)' }}
        title="Zoom in"
        aria-label="Zoom in"
      >
        +
      </button>
      <button
        onClick={() => map.zoomOut()}
        className="w-8 h-8 flex items-center justify-center text-[#0f2340] hover:bg-slate-100 font-bold text-base transition-colors"
        title="Zoom out"
        aria-label="Zoom out"
      >
        −
      </button>
    </div>
  );
};

/* ─── Custom Floating Aquora Fullscreen Control ───────────────── */
const AquoraFullscreenControl: React.FC<{ containerRef: React.RefObject<HTMLDivElement | null> }> = ({ containerRef }) => {
  const [isFullscreen, setIsFullscreen] = React.useState(false);

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().catch(() => {});
      setIsFullscreen(true);
    } else {
      document.exitFullscreen().catch(() => {});
      setIsFullscreen(false);
    }
  };

  React.useEffect(() => {
    const handleFSChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFSChange);
    return () => document.removeEventListener('fullscreenchange', handleFSChange);
  }, []);

  return (
    <button
      onClick={toggleFullscreen}
      className="absolute bottom-4 right-4 z-[1000] bg-white/95 backdrop-blur-md px-3 py-1.5 rounded-xl text-[11px] font-semibold text-[#0f2340] hover:bg-white flex items-center gap-1.5 border shadow-sm transition-all hover:shadow-md cursor-pointer"
      style={{
        borderColor: 'rgba(15,35,64,0.12)',
        boxShadow: '0 4px 14px rgba(15,35,64,0.12)',
      }}
      title="Toggle fullscreen"
    >
      <svg className="w-3.5 h-3.5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        {isFullscreen ? (
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 9L4 4m0 0l4 0m-4 0l0 4m11 -4l4 4m-4 -4l4 0m0 0l0 4m-4 11l4 -4m-4 4l4 0m0 0l0 -4m-11 4l-4 -4m4 4l-4 0m0 0l0 -4" />
        ) : (
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 3h6v6M9 21H3v-6M21 9V3m0 0l-7 7M3 15v6m0 0l7-7" />
        )}
      </svg>
      <span>{isFullscreen ? 'Exit full screen' : 'View full screen'}</span>
    </button>
  );
};

export const LeafletMap: React.FC<LeafletMapProps> = ({
  center = [19.076, 72.8777], // Default Mithi Catchment Mumbai Lat/Lon
  zoom = 13,
  bounds,
  markers = [],
  polylines = [],
  polygons = [],
  floodPoints,
  floodIntensityMultiplier = 1.0,
  showFullscreenControl = true,
  className = 'h-full w-full rounded-2xl overflow-hidden shadow-2xs border border-slate-200/90',
  style,
  children,
}) => {
  const safeCenter = sanitizeLatLng(center);
  const containerRef = React.useRef<HTMLDivElement>(null);

  // Sanitize markers defensively
  const safeMarkers = markers.filter(
    (mk) => mk && Array.isArray(mk.position) && isValidCoord(mk.position[0]) && isValidCoord(mk.position[1])
  );

  // Sanitize polylines defensively
  const safePolylines = polylines
    .map((pl) => ({
      ...pl,
      positions: (pl.positions || []).filter(
        (p) => Array.isArray(p) && p.length >= 2 && isValidCoord(p[0]) && isValidCoord(p[1])
      ),
    }))
    .filter((pl) => pl.positions.length >= 2);

  // Sanitize polygons defensively
  const safePolygons = polygons
    .map((pg) => ({
      ...pg,
      positions: (pg.positions || []).filter(
        (p) => Array.isArray(p) && p.length >= 2 && isValidCoord(p[0]) && isValidCoord(p[1])
      ),
    }))
    .filter((pg) => pg.positions.length >= 3);

  return (
    <div ref={containerRef} className={`relative ${className}`} style={style}>
      <MapContainer
        center={safeCenter}
        zoom={zoom}
        zoomControl={false}
        scrollWheelZoom={true}
        className="w-full h-full min-h-[350px] z-0 font-sans"
      >
        <AquoraZoomControl />
        {showFullscreenControl && <AquoraFullscreenControl containerRef={containerRef} />}

        {/* High-quality clean OpenStreetMap basemap with contrast tuning for crisp flood overlay visibility */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          maxZoom={19}
        />

        <MapController center={safeCenter} zoom={zoom} bounds={bounds} />

        {/* Hydrological Continuous Water Depth Canvas Overlay */}
        <FloodWaterCanvasOverlay points={floodPoints} intensityMultiplier={floodIntensityMultiplier} />

        {/* Polygons */}
        {safePolygons.map((pg) => (
          <Polygon
            key={pg.id}
            positions={pg.positions}
            pathOptions={{
              color: pg.strokeColor || 'transparent',
              fillColor: pg.fillColor || pg.color || '#38bdf8',
              fillOpacity: pg.fillOpacity ?? 0.45,
              weight: pg.weight ?? 0,
            }}
          >
            {(pg.popupContent || pg.title) && (
              <Popup>
                {pg.popupContent ? (
                  <div className="p-1 text-xs font-sans leading-relaxed" dangerouslySetInnerHTML={{ __html: pg.popupContent }} />
                ) : (
                  <span className="text-xs font-semibold">{pg.title}</span>
                )}
              </Popup>
            )}
          </Polygon>
        ))}

        {/* Polylines */}
        {safePolylines.map((pl) => (
          <Polyline
            key={pl.id}
            positions={pl.positions}
            pathOptions={{
              color: pl.color || '#0284c7',
              weight: pl.weight || 4,
              dashArray: pl.dashArray,
              opacity: pl.opacity || 0.85,
            }}
            eventHandlers={{
              click: () => pl.onClick && pl.onClick(),
            }}
          >
            {pl.title && <Popup><span className="text-xs font-semibold">{pl.title}</span></Popup>}
          </Polyline>
        ))}

        {/* Custom floating label markers */}
        {safeMarkers.map((mk) => (
          <Marker
            key={mk.id}
            position={mk.position}
            icon={createCustomPin(mk.color || '#0284c7', mk.subtitle, mk.title, mk.badge)}
            eventHandlers={{
              click: () => mk.onClick && mk.onClick(),
            }}
          >
            <Popup>
              {mk.popupContent ? (
                <div className="p-1 text-xs font-sans leading-relaxed text-slate-800" dangerouslySetInnerHTML={{ __html: mk.popupContent }} />
              ) : (
                <div className="p-1 space-y-1 font-sans">
                  {mk.title && <h4 className="font-bold text-xs text-slate-900">{mk.title}</h4>}
                  {mk.subtitle && <p className="text-[11px] text-slate-600 leading-tight">{mk.subtitle}</p>}
                  {mk.details}
                </div>
              )}
            </Popup>
          </Marker>
        ))}

        {children}
      </MapContainer>
    </div>
  );
};

export default LeafletMap;
