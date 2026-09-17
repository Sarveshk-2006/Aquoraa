# Phase 7A — Data Source Catalog

## Overview

This catalog defines the technical specification, provider details, acquisition protocol, spatial/temporal semantics, verification status, and scientific limitations for all nine data source categories required by the **Aquora Urban Flood Intelligence & Response Platform**.

---

## 1. Historical Precipitation & Rainfall

| Attribute | Specification |
| :--- | :--- |
| **Product Name** | NASA GPM IMERG Final Precipitation L3 Half-Hourly 0.1° x 0.1° V07B (`GPM_3IMERGHH_07`) |
| **Provider** | NASA Goddard Earth Sciences Data and Information Services Center (GES DISC) |
| **Official URL** | [GES DISC IMERG V07B Product Page](https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGHH_07/summary) |
| **Access Protocol** | HTTPS / Direct Earthdata User Token Authentication / OPeNDAP API |
| **Spatial Resolution** | ~0.1° x 0.1° (~10 km x 10 km) |
| **Temporal Resolution**| 30 minutes |
| **Native Format** | NetCDF4 / HDF5 |
| **Native Units** | mm/hr (`precipitationCal`) |
| **Coordinate System**| EPSG:4326 (WGS 84) |
| **Verification Status**| `DOCUMENTED_FROM_AUTHORITATIVE_SOURCE` |
| **Licensing** | Public Domain / NASA Open Data Policy |
| **Scientific Limitations** | Coarse spatial resolution (~10 km). IMERG provides basin-scale precipitation estimates, **NOT** street-level rainfall measurements. Downscaling onto the Phase 4 30m grid uses bilinear interpolation with explicit metadata tags. |

---

## 2. Digital Elevation Model (Terrain)

| Attribute | Specification |
| :--- | :--- |
| **Product Name** | Copernicus DEM GLO-30 (30-meter Global Digital Elevation Model) |
| **Provider** | European Space Agency (ESA) / Copernicus Programme |
| **Official Tile ID** | `Copernicus_DSM_COG_10_N19_00_E072_00` |
| **Official URL** | [Copernicus DEM AWS Open Data](https://registry.opendata.aws/copernicus-dem/) |
| **Access Protocol** | S3 Direct Download (`https://copernicus-dem-30m.s3.amazonaws.com/`) |
| **Spatial Resolution** | 1 arc-second (~30 meters at equator) |
| **Native Format** | Cloud-Optimized GeoTIFF (COG) |
| **Coordinate System**| EPSG:4326 (WGS 84) |
| **Verification Status**| `VERIFIED` |
| **Licensing** | WorldDEM License / Open Access Copernicus License |
| **Scientific Limitations** | GLO-30 is a Digital Surface Model (DSM), capturing canopy and building heights alongside ground elevation. |

---

## 3. Land Cover & Urban Density

| Attribute | Specification |
| :--- | :--- |
| **Product Name** | ESA WorldCover 2021 10m V200 |
| **Provider** | European Space Agency (ESA) / VITO Remote Sensing |
| **Official Tile ID** | `ESA_WorldCover_10m_2021_v200_N18E072` |
| **Official URL** | [ESA WorldCover S3 Open Data](https://esa-worldcover.s3.amazonaws.com/) |
| **Access Protocol** | HTTPS S3 Direct Download |
| **Spatial Resolution** | 10 meters |
| **Native Format** | Cloud-Optimized GeoTIFF (COG) |
| **Output Variables** | `landcover_class` (Categorical class ID), `built_up_fraction` (Derived urban density metric) |
| **Verification Status**| `VERIFIED` |
| **Licensing** | Creative Commons Attribution 4.0 International (CC BY 4.0) |

---

## 4. Urban Infrastructure & Network Assets

| Attribute | Specification |
| :--- | :--- |
| **Product Name** | OpenStreetMap (OSM) Bounding Box Extraction |
| **Provider** | OpenStreetMap Contributors / Overpass API |
| **Official URL** | [Overpass API Portal](https://overpass-api.de/api/interpreter) |
| **Access Protocol** | Overpass QL Bounding Box Query `[19.03, 72.82, 19.16, 72.93]` |
| **Native Format** | `GeoJSON` / `OSM_XML` |
| **Extracted Layers** | Roads (`highway=*`), Buildings (`building=*`), Waterways (`waterway=*`), Railway (`railway=*`), Emergency (`amenity=hospital|fire_station|police`) |
| **Verification Status**| `VERIFIED` |
| **Licensing** | Open Database License (ODbL) 1.0 |
| **Scientific Limitations** | OSM provides surface urban features and transport networks. OSM MUST **NOT** be treated as underground municipal storm drainage infrastructure. |

---

## 5. Municipal Stormwater Drainage Network

| Attribute | Specification |
| :--- | :--- |
| **Product Name** | BMC / BRIMSTOWAD Stormwater Drainage GIS |
| **Provider** | Brihanmumbai Municipal Corporation (BMC) Stormwater Drain Department |
| **Official URL** | Official BMC Open Data / Municipal Archives |
| **Access Protocol** | Manual GIS Ingestion / Digitized Vector Layers |
| **Primary Features** | Major Nallas (Mithi, Gazdarbandh, Cleaveland, Mogra), Outfalls, Pumping Stations |
| **Verification Status**| `AUTHORITATIVE_DRAINAGE_DATA = NEEDS_VERIFICATION` |
| **Data Quality Rules**| Pipe capacities or flow directions not explicitly recorded in official BMC GIS MUST remain marked as `UNKNOWN`. Inferred directions or dummy defaults are strictly prohibited. |

---

## 6. Satellite Flood Ground-Truth Labels (SAR)

| Attribute | Specification |
| :--- | :--- |
| **Product Name** | Sentinel-1 SAR Ground Range Detected (GRD) IW Dual VV+VH |
| **Provider** | European Space Agency (ESA) / Copernicus Programme / ASF DAAC |
| **Official URL** | [Alaska Satellite Facility DAAC Search](https://search.asf.alaska.edu/) |
| **Access Protocol** | ASF HP3 API / Sentinel Hub API |
| **Spatial Resolution** | 10m x 10m pixel spacing |
| **Native Format** | SAFE ZIP / GeoTIFF |
| **Verification Status**| `VERIFIED` (Scenes identified and verified for candidate events E02–E07) |
| **Licensing** | Copernicus Open Access License |

---

## 7. Coastal Tide & Sea-Level Dynamics

| Attribute | Specification |
| :--- | :--- |
| **Product Name** | Mumbai Port Trust (Apollo Bunder / Mahim Creek) Tide Data |
| **Provider** | University of Hawaii Sea Level Center (UHSLC) / Survey of India |
| **Official URL** | [UHSLC Hourly Tide Data (Station 846A)](https://uhslc.soest.hawaii.edu/data/csv/fast/hourly/h846a.csv) |
| **Access Protocol** | HTTPS Direct CSV Download |
| **Verification Status**| `DOCUMENTED_FROM_AUTHORITATIVE_SOURCE` |
| **Licensing** | Academic / Research Open Data |

---

## 8. River Water Level & Hydrometric Data

| Attribute | Specification |
| :--- | :--- |
| **Product Name** | Mithi River Water Level Monitoring Gauge Network (Kranti Nagar Gauge) |
| **Provider** | BMC Disaster Management Department (DMD) / Central Water Commission (CWC) |
| **Verification Status**| `NEEDS_VERIFICATION` (Machine-readable feed pending official release) |

---

## 9. Authoritative Flood Event Reports & Disaster Bulletins

| Attribute | Specification |
| :--- | :--- |
| **Product Name** | BMC Disaster Management Bulletins & Chitale Committee Inquiry Report (2006) |
| **Provider** | Brihanmumbai Municipal Corporation (BMC) / Government of Maharashtra |
| **Verification Status**| `DOCUMENTED_FROM_AUTHORITATIVE_SOURCE` |
