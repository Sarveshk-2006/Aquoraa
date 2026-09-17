# Phase 7A — License & Attribution Manifest

## Overview

This document specifies the open-data licenses, usage terms, required citation statements, and copyright attributions for all third-party datasets specified for the **Aquora Urban Flood Intelligence & Response Platform**.

---

## Master Licensing Summary

| Data Category | Dataset Name | Provider / Source | License Type | Commercial Use Allowed | Required Attribution Statement |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Rainfall** | NASA GPM IMERG V07B | NASA GES DISC | Public Domain / NASA Open Data | Yes | *"NASA Goddard Earth Sciences Data and Information Services Center (GES DISC), GPM IMERG Final Precipitation L3 Half-Hourly V07B."* |
| **Terrain** | Copernicus DEM GLO-30 | ESA / Copernicus Programme | Open Access Copernicus License | Yes | *"© European Space Agency - ESA, Copernicus DEM GLO-30."* |
| **Land Cover** | ESA WorldCover 2021 | ESA / VITO Remote Sensing | CC BY 4.0 (Creative Commons) | Yes | *"Zanaga et al. (2022) ESA WorldCover 10m 2021 v200. European Space Agency."* |
| **Urban Layers**| OpenStreetMap (OSM) | OSM Contributors | Open Database License (ODbL) 1.0 | Yes (with ODbL compliance) | *"© OpenStreetMap contributors, licensed under the Open Database License (ODbL)."* |
| **Satellite SAR**| Sentinel-1 GRD IW | ESA / Copernicus Programme | Copernicus Open Access License | Yes | *"Contains modified Copernicus Sentinel data [2017–2021] processed by Aquora."* |
| **Tide Levels** | Mumbai Port Trust Tide Data | UHSLC / Survey of India | Academic / Research Open Data | Yes (Research) | *"University of Hawaii Sea Level Center (UHSLC) / Survey of India Tide Gauge Network."* |
| **Municipal Data**| BMC SWD & DMD Bulletins | BMC / Govt of Maharashtra | Public Disaster Records | Non-Commercial / Research | *"Brihanmumbai Municipal Corporation (BMC) Disaster Management Cell Archives."* |

---

## Detailed Attribution Protocols

### 1. OpenStreetMap (ODbL 1.0) Requirements
- **License**: [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1.0/)
- **Requirement**: Any derivative database or API endpoint distributing transformed OSM road/building layers MUST credit OSM contributors and provide access to the source OSM data upon request.
- **Aquora Compliance**: The frontend map footer and documentation include mandatory `© OpenStreetMap contributors` attribution.

### 2. Copernicus Sentinel Data Policy
- **License**: [Copernicus Sentinel Data Terms and Conditions](https://sentinels.copernicus.eu/documents/247904/695236/Sentinel_Data_Legal_Notice)
- **Requirement**: Free, full, and open access to Sentinel-1 SAR products for any user. Derivative flood classification maps must retain Copernicus credit.
- **Aquora Compliance**: All generated SAR change-detection rasters contain metadata referencing `Copernicus Sentinel-1 SAR` source scenes.

### 3. NASA Data & Information Policy
- **License**: Public Domain (US Government Work)
- **Requirement**: NASA data is free of copyright restriction. NASA requests standard academic citation of the product DOI (`10.5067/GPM/IMERG/3B-HH/07`).
