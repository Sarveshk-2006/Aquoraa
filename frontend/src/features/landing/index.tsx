import React, { useState, useEffect } from 'react';
import {
  Waves,
  ChevronRight,
  CloudRain,
  Navigation,
  ShieldAlert,
  Building2,
  Camera,
  Sliders,
  AlertCircle,
  ArrowDown,
  Cpu,
  Compass,
  Activity,
  Menu,
  X,
  Globe
} from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import mumbaiHeroImg from '@/assets/aquora-mumbai-hero.webp';

/* ─── Floating Header Navbar ─────────────────────────────────── */
const LandingNavbar: React.FC = () => {
  const { navigateToApp } = useAppStore();
  const [scrolled, setScrolled] = useState<boolean>(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 40);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (id: string) => {
    setMobileMenuOpen(false);
    const elem = document.getElementById(id);
    if (elem) {
      elem.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? 'bg-[#06191C]/90 backdrop-blur-md border-b border-teal-900/40 py-3 shadow-xl'
          : 'bg-gradient-to-b from-[#06191C]/80 via-[#06191C]/40 to-transparent py-5'
      }`}
    >
      <div className="max-w-[1340px] mx-auto px-5 md:px-8 flex items-center justify-between">
        {/* Brand Logo */}
        <div
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          className="flex items-center gap-2.5 cursor-pointer group"
        >
          <div className="w-9 h-9 rounded-xl bg-[#008080] flex items-center justify-center shadow-md group-hover:bg-[#009696] transition-colors">
            <Waves className="w-5 h-5 text-white" />
          </div>
          <div className="flex flex-col">
            <span className="text-base font-extrabold text-white tracking-wider flex items-center gap-1.5 leading-none">
              AQUORA
              <span className="text-[9.5px] font-bold px-1.5 py-0.5 rounded bg-teal-500/20 text-teal-300 border border-teal-500/30 uppercase tracking-widest hidden sm:inline-block">
                LIVE
              </span>
            </span>
            <span className="text-[10px] text-teal-200/70 font-medium tracking-wide leading-tight mt-0.5">
              Urban Flood Intelligence
            </span>
          </div>
        </div>

        {/* Desktop Navigation Links */}
        <nav className="hidden md:flex items-center gap-8 text-[13px] font-medium text-slate-300">
          <button
            onClick={() => scrollToSection('problem')}
            className="hover:text-white transition-colors cursor-pointer"
          >
            The Challenge
          </button>
          <button
            onClick={() => scrollToSection('how-it-works')}
            className="hover:text-white transition-colors cursor-pointer"
          >
            How it Works
          </button>
          <button
            onClick={() => scrollToSection('capabilities')}
            className="hover:text-white transition-colors cursor-pointer"
          >
            Capabilities
          </button>
          <button
            onClick={() => scrollToSection('science')}
            className="hover:text-white transition-colors cursor-pointer"
          >
            Science & Data
          </button>
        </nav>

        {/* Right Action & Live Badge */}
        <div className="hidden sm:flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-teal-950/60 border border-teal-500/30 text-[11px] font-medium text-teal-300">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Mithi Catchment · Active</span>
          </div>

          <button
            onClick={() => navigateToApp('overview')}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#008080] hover:bg-[#009696] text-white text-[13px] font-bold transition-all duration-200 shadow-md hover:shadow-teal-900/50 hover:-translate-y-0.5 cursor-pointer active:translate-y-0"
          >
            <span>Enter AQUORA</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* Mobile Hamburger Toggle */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden p-2 rounded-lg bg-teal-950/60 text-slate-300 hover:text-white border border-teal-800/40"
        >
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Mobile Menu Overlay */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-[#06191C] border-b border-teal-900/40 px-6 py-5 space-y-4 text-slate-200 animate-in fade-in slide-in-from-top-2">
          <div className="flex items-center justify-between pb-3 border-b border-teal-900/40">
            <div className="flex items-center gap-2 text-[11px] font-medium text-teal-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>Live Environment Connected</span>
            </div>
          </div>
          <button
            onClick={() => scrollToSection('problem')}
            className="block w-full text-left py-2 text-sm font-medium hover:text-teal-300"
          >
            The Challenge
          </button>
          <button
            onClick={() => scrollToSection('how-it-works')}
            className="block w-full text-left py-2 text-sm font-medium hover:text-teal-300"
          >
            How it Works
          </button>
          <button
            onClick={() => scrollToSection('capabilities')}
            className="block w-full text-left py-2 text-sm font-medium hover:text-teal-300"
          >
            Capabilities
          </button>
          <button
            onClick={() => scrollToSection('science')}
            className="block w-full text-left py-2 text-sm font-medium hover:text-teal-300"
          >
            Science & Data
          </button>
          <div className="pt-2">
            <button
              onClick={() => {
                setMobileMenuOpen(false);
                navigateToApp('overview');
              }}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-[#008080] text-white font-bold text-sm"
            >
              <span>Enter AQUORA Platform</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </header>
  );
};

/* ─── Main Landing Page Component ────────────────────────────── */
export const LandingPage: React.FC = () => {
  const { navigateToApp } = useAppStore();

  const scrollToId = (id: string) => {
    const elem = document.getElementById(id);
    if (elem) {
      elem.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen bg-[#06191C] text-slate-100 font-sans selection:bg-[#008080] selection:text-white">
      {/* ── Floating Header ───────────────────────────────────── */}
      <LandingNavbar />

      {/* ── 1. CINEMATIC HERO SECTION ───────────────────────── */}
      <section className="relative min-h-screen flex items-center justify-center pt-24 pb-16 overflow-hidden">
        {/* Background Image with subtle zoom micro-animation */}
        <div className="absolute inset-0 z-0 overflow-hidden">
          <img
            src={mumbaiHeroImg}
            alt="Panoramic Mumbai skyline and Bandra-Worli Sea Link during sunset"
            className="w-full h-full object-cover object-center transition-transform duration-[20000ms] ease-out scale-100 hover:scale-105"
          />
          {/* Dark Teal Controlled Gradients for WCAG Readability */}
          <div className="absolute inset-0 bg-gradient-to-r from-[#06191C] via-[#06191C]/85 via-50% to-transparent opacity-95 sm:opacity-90" />
          <div className="absolute inset-0 bg-gradient-to-t from-[#06191C] via-[#06191C]/30 to-[#06191C]/40" />
        </div>

        {/* Hero Content Grid */}
        <div className="relative z-10 max-w-[1340px] mx-auto px-5 md:px-8 w-full grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Left Column — Text & Action */}
          <div className="lg:col-span-7 space-y-6 pt-6 sm:pt-0">
            {/* Eyebrow */}
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/30 text-teal-300 text-[11px] font-bold tracking-[0.25em] uppercase">
              <Waves className="w-3.5 h-3.5" />
              <span>A Q U O R A</span>
            </div>

            {/* Primary Headline */}
            <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-[3.8rem] font-extrabold text-white tracking-tight leading-[1.06]">
              See the flood <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#00e5d4] via-teal-300 to-emerald-400">
                before it reaches the road.
              </span>
            </h1>

            {/* Subtext */}
            <p className="text-base sm:text-lg text-slate-200 font-medium leading-relaxed max-w-[580px]">
              Real-time flood intelligence for a more resilient Mumbai. Anticipate changing monsoon conditions, understand flood risk, find safer routes, and protect critical access — all from one live platform.
            </p>

            {/* Action Buttons */}
            <div className="pt-3 flex flex-wrap items-center gap-4">
              <button
                onClick={() => navigateToApp('overview')}
                className="inline-flex items-center gap-3 px-7 py-3.5 rounded-xl bg-[#008080] hover:bg-[#009696] text-white text-base font-bold tracking-wide transition-all duration-200 shadow-xl shadow-teal-950/80 hover:shadow-teal-800/40 hover:-translate-y-0.5 cursor-pointer active:translate-y-0"
              >
                <span>Enter AQUORA</span>
                <ChevronRight className="w-5 h-5" />
              </button>

              <button
                onClick={() => scrollToId('how-it-works')}
                className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl bg-slate-900/60 hover:bg-slate-800/80 text-slate-200 hover:text-white border border-slate-700/60 text-sm font-semibold transition-all duration-200 backdrop-blur-md cursor-pointer"
              >
                <span>Explore How It Works</span>
                <ArrowDown className="w-4 h-4 text-teal-400" />
              </button>
            </div>

            {/* Quick Metrics Strip */}
            <div className="pt-6 grid grid-cols-3 gap-4 border-t border-teal-900/50 max-w-[540px]">
              <div>
                <div className="text-xl sm:text-2xl font-black text-white">0–180m</div>
                <div className="text-[11px] font-medium text-slate-400">Forecast Horizon</div>
              </div>
              <div>
                <div className="text-xl sm:text-2xl font-black text-emerald-400">366</div>
                <div className="text-[11px] font-medium text-slate-400">Critical Facilities</div>
              </div>
              <div>
                <div className="text-xl sm:text-2xl font-black text-teal-300">2D Depth</div>
                <div className="text-[11px] font-medium text-slate-400">Physics Solver</div>
              </div>
            </div>
          </div>

          {/* Right Column — Intelligence System Glass Overlays */}
          <div className="lg:col-span-5 hidden lg:flex flex-col gap-4">
            {/* Overlay Card 1: Operational Status */}
            <div className="p-5 rounded-2xl bg-[#06191C]/80 backdrop-blur-xl border border-teal-500/25 shadow-2xl space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-xs font-bold text-teal-200 uppercase tracking-wider">
                    LIVE FLOOD INTELLIGENCE
                  </span>
                </div>
                <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-teal-500/20 text-teal-300 border border-teal-500/30">
                  IMD / ECMWF SYNTHESIS
                </span>
              </div>
              <div className="space-y-1.5 pt-1">
                <div className="flex justify-between text-xs text-slate-300">
                  <span className="font-medium">Primary Focus Zone:</span>
                  <span className="font-bold text-white">Mithi Catchment · Mumbai</span>
                </div>
                <div className="flex justify-between text-xs text-slate-300">
                  <span className="font-medium">Active Model Horizon:</span>
                  <span className="font-bold text-teal-300">0 — 180 Minutes</span>
                </div>
                <div className="flex justify-between text-xs text-slate-300">
                  <span className="font-medium">Core Solver Status:</span>
                  <span className="font-bold text-emerald-400">Operational · 2D Shallow Water</span>
                </div>
              </div>
            </div>

            {/* Overlay Card 2: Feature Quick Jump */}
            <div className="p-5 rounded-2xl bg-[#06191C]/70 backdrop-blur-xl border border-slate-700/50 shadow-2xl space-y-3">
              <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                EXPLORE PLATFORM MODULES
              </div>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => navigateToApp('flood-map')}
                  className="p-2.5 rounded-xl bg-slate-900/80 hover:bg-teal-950/60 border border-slate-800 hover:border-teal-700/50 text-left transition-all group cursor-pointer"
                >
                  <div className="flex items-center gap-2">
                    <CloudRain className="w-3.5 h-3.5 text-teal-400" />
                    <span className="text-xs font-bold text-white group-hover:text-teal-300">Flood Outlook</span>
                  </div>
                </button>
                <button
                  onClick={() => navigateToApp('travel-window')}
                  className="p-2.5 rounded-xl bg-slate-900/80 hover:bg-teal-950/60 border border-slate-800 hover:border-teal-700/50 text-left transition-all group cursor-pointer"
                >
                  <div className="flex items-center gap-2">
                    <Navigation className="w-3.5 h-3.5 text-emerald-400" />
                    <span className="text-xs font-bold text-white group-hover:text-emerald-300">Travel Window</span>
                  </div>
                </button>
                <button
                  onClick={() => navigateToApp('critical-access')}
                  className="p-2.5 rounded-xl bg-slate-900/80 hover:bg-teal-950/60 border border-slate-800 hover:border-teal-700/50 text-left transition-all group cursor-pointer"
                >
                  <div className="flex items-center gap-2">
                    <ShieldAlert className="w-3.5 h-3.5 text-red-400" />
                    <span className="text-xs font-bold text-white group-hover:text-red-300">Critical Access</span>
                  </div>
                </button>
                <button
                  onClick={() => navigateToApp('protect-city')}
                  className="p-2.5 rounded-xl bg-slate-900/80 hover:bg-teal-950/60 border border-slate-800 hover:border-teal-700/50 text-left transition-all group cursor-pointer"
                >
                  <div className="flex items-center gap-2">
                    <Building2 className="w-3.5 h-3.5 text-teal-300" />
                    <span className="text-xs font-bold text-white group-hover:text-teal-200">Protect City</span>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── 2. THE CHALLENGE & PURPOSE ───────────────────────── */}
      <section id="problem" className="py-24 bg-[#041215] border-t border-teal-900/30 relative">
        <div className="max-w-[1340px] mx-auto px-5 md:px-8">
          <div className="max-w-3xl mb-16">
            <span className="text-xs font-bold tracking-[0.2em] text-teal-400 uppercase">
              THE URBAN CHALLENGE
            </span>
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white tracking-tight mt-3 leading-tight">
              When water moves fast, <br />
              <span className="text-teal-300">decisions need to move faster.</span>
            </h2>
            <p className="mt-4 text-slate-300 text-base sm:text-lg leading-relaxed font-medium">
              Mumbai's high-density topography and intense monsoon rainfall create rapid surface water accumulation. Traditional static alerts are insufficient for dynamic route safety and essential facility access.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
            {/* 4 Problem Pillar Cards */}
            <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-6 rounded-2xl bg-[#06191C] border border-teal-900/40 hover:border-teal-700/50 transition-all space-y-3">
                <div className="w-10 h-10 rounded-xl bg-teal-500/10 border border-teal-500/20 flex items-center justify-center">
                  <CloudRain className="w-5 h-5 text-teal-300" />
                </div>
                <h3 className="text-base font-bold text-white">Monsoon Accumulation</h3>
                <p className="text-xs text-slate-400 leading-relaxed font-medium">
                  High-intensity rainfall events overwhelm natural drainage in low-lying Mithi catchment corridors within minutes.
                </p>
              </div>

              <div className="p-6 rounded-2xl bg-[#06191C] border border-teal-900/40 hover:border-teal-700/50 transition-all space-y-3">
                <div className="w-10 h-10 rounded-xl bg-teal-500/10 border border-teal-500/20 flex items-center justify-center">
                  <Activity className="w-5 h-5 text-teal-300" />
                </div>
                <h3 className="text-base font-bold text-white">Tidal Lockout Effect</h3>
                <p className="text-xs text-slate-400 leading-relaxed font-medium">
                  High Arabian Sea tides block river discharge, creating compounding backwater flooding near Kurla and BKC.
                </p>
              </div>

              <div className="p-6 rounded-2xl bg-[#06191C] border border-teal-900/40 hover:border-teal-700/50 transition-all space-y-3">
                <div className="w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center">
                  <ShieldAlert className="w-5 h-5 text-red-400" />
                </div>
                <h3 className="text-base font-bold text-white">Hospital Route Disruption</h3>
                <p className="text-xs text-slate-400 leading-relaxed font-medium">
                  Key arterial routes to hospitals like Sion Hospital become impassable without predictive routing advice.
                </p>
              </div>

              <div className="p-6 rounded-2xl bg-[#06191C] border border-teal-900/40 hover:border-teal-700/50 transition-all space-y-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                  <Compass className="w-5 h-5 text-emerald-400" />
                </div>
                <h3 className="text-base font-bold text-white">Emergency Coordination</h3>
                <p className="text-xs text-slate-400 leading-relaxed font-medium">
                  Civic response teams require actionable 0-180 minute lead times to deploy mobile pumps and clear critical routes.
                </p>
              </div>
            </div>

            {/* Right Side — Catchment Feature Highlight Visual */}
            <div className="lg:col-span-5 p-7 rounded-2xl bg-gradient-to-br from-[#06191C] to-[#041215] border border-teal-700/30 flex flex-col justify-between shadow-2xl relative overflow-hidden">
              <div className="space-y-4 relative z-10">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/10 text-teal-300 text-xs font-bold uppercase tracking-wider">
                  MITHI CATCHMENT TARGET ZONE
                </div>
                <h3 className="text-2xl font-extrabold text-white leading-snug">
                  Precision spatial intelligence for Mumbai's central corridor.
                </h3>
                <p className="text-xs text-slate-300 leading-relaxed font-medium">
                  AQUORA models 2D surface water dynamics across Copernicus DSM elevation grids, continuously synthesizing rainfall forecasts to predict inundation depths before roads become flooded.
                </p>
              </div>

              <div className="pt-6 border-t border-teal-900/60 space-y-2 relative z-10">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400 font-medium">Corridor Length:</span>
                  <span className="font-bold text-white">17.8 km River Reach</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400 font-medium">Elevation Coverage:</span>
                  <span className="font-bold text-teal-300">0m — 35m DEM Grid</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400 font-medium">Critical Nodes Monitored:</span>
                  <span className="font-bold text-emerald-400">366 OSM Facilities</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── 3. HOW AQUORA WORKS — 3-STEP PROCESS ─────────────── */}
      <section id="how-it-works" className="py-24 bg-[#06191C] relative border-t border-teal-900/30">
        <div className="max-w-[1340px] mx-auto px-5 md:px-8">
          <div className="text-center max-w-2xl mx-auto mb-20">
            <span className="text-xs font-bold tracking-[0.2em] text-teal-400 uppercase">
              WORKFLOW & ARCHITECTURE
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight mt-3">
              How AQUORA Operates
            </h2>
            <p className="mt-3 text-slate-300 text-base font-medium">
              From raw satellite precipitation forecasts to real-time route safety in 3 steps.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
            {/* Step 1 */}
            <div className="p-8 rounded-2xl bg-[#041215] border border-teal-900/40 relative group hover:border-teal-600/50 transition-all shadow-xl">
              <div className="text-5xl font-black text-teal-500/20 group-hover:text-teal-400/30 transition-colors mb-4">
                01
              </div>
              <h3 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
                <span>SEE</span>
                <span className="text-xs font-medium px-2 py-0.5 rounded bg-teal-500/10 text-teal-300">0-180 Min</span>
              </h3>
              <p className="text-sm font-bold text-teal-300 mb-3">
                Understand where flood risk may develop.
              </p>
              <p className="text-xs text-slate-400 leading-relaxed font-medium">
                Continuously ingests IMD and ECMWF weather forecast streams, projecting 2D surface water depth across Mumbai's catchment topography.
              </p>
            </div>

            {/* Step 2 */}
            <div className="p-8 rounded-2xl bg-[#041215] border border-teal-900/40 relative group hover:border-teal-600/50 transition-all shadow-xl">
              <div className="text-5xl font-black text-emerald-500/20 group-hover:text-emerald-400/30 transition-colors mb-4">
                02
              </div>
              <h3 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
                <span>DECIDE</span>
                <span className="text-xs font-medium px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300">Routing</span>
              </h3>
              <p className="text-sm font-bold text-emerald-300 mb-3">
                Evaluate routes, access, and critical locations.
              </p>
              <p className="text-xs text-slate-400 leading-relaxed font-medium">
                Analyses travel windows using dynamic OSRM routing, checking essential hospital access and identifying safe alternative corridors.
              </p>
            </div>

            {/* Step 3 */}
            <div className="p-8 rounded-2xl bg-[#041215] border border-teal-900/40 relative group hover:border-teal-600/50 transition-all shadow-xl">
              <div className="text-5xl font-black text-cyan-500/20 group-hover:text-cyan-400/30 transition-colors mb-4">
                03
              </div>
              <h3 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
                <span>ACT</span>
                <span className="text-xs font-medium px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300">Response</span>
              </h3>
              <p className="text-sm font-bold text-cyan-300 mb-3">
                Respond earlier and protect communities.
              </p>
              <p className="text-xs text-slate-400 leading-relaxed font-medium">
                Generates targeted intervention advice for mobile pumps, alerts emergency responders, and integrates ground-truth field reports.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── 4. PLATFORM CAPABILITIES — 7 CARDS ───────────────── */}
      <section id="capabilities" className="py-24 bg-[#041215] border-t border-teal-900/30">
        <div className="max-w-[1340px] mx-auto px-5 md:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="text-xs font-bold tracking-[0.2em] text-teal-400 uppercase">
              PLATFORM MODULES
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight mt-3">
              One platform. A clearer view of what's ahead.
            </h2>
            <p className="mt-3 text-slate-300 text-base font-medium">
              Explore the 7 core modules powering Mumbai's live urban flood intelligence.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Card 1: Flood Outlook */}
            <div
              onClick={() => navigateToApp('flood-map')}
              className="p-6 rounded-2xl bg-[#06191C] border border-teal-900/40 hover:border-teal-500/60 transition-all group cursor-pointer shadow-lg hover:-translate-y-1"
            >
              <div className="w-10 h-10 rounded-xl bg-teal-500/10 border border-teal-500/20 flex items-center justify-center mb-4 group-hover:bg-[#008080] transition-colors">
                <CloudRain className="w-5 h-5 text-teal-300 group-hover:text-white" />
              </div>
              <h3 className="text-lg font-bold text-white group-hover:text-teal-300 transition-colors flex items-center justify-between">
                <span>Flood Outlook</span>
                <ChevronRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity text-teal-400" />
              </h3>
              <p className="text-xs text-slate-300 mt-2 font-medium">
                See where water may develop over the next 3 hours with interactive 2D flood depth maps.
              </p>
            </div>

            {/* Card 2: Travel Window */}
            <div
              onClick={() => navigateToApp('travel-window')}
              className="p-6 rounded-2xl bg-[#06191C] border border-teal-900/40 hover:border-emerald-500/60 transition-all group cursor-pointer shadow-lg hover:-translate-y-1"
            >
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-4 group-hover:bg-[#059669] transition-colors">
                <Navigation className="w-5 h-5 text-emerald-300 group-hover:text-white" />
              </div>
              <h3 className="text-lg font-bold text-white group-hover:text-emerald-300 transition-colors flex items-center justify-between">
                <span>Travel Window</span>
                <ChevronRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity text-emerald-400" />
              </h3>
              <p className="text-xs text-slate-300 mt-2 font-medium">
                Understand route safety, travel times, and safe departure timing across transit corridors.
              </p>
            </div>

            {/* Card 3: Critical Access */}
            <div
              onClick={() => navigateToApp('critical-access')}
              className="p-6 rounded-2xl bg-[#06191C] border border-teal-900/40 hover:border-red-500/60 transition-all group cursor-pointer shadow-lg hover:-translate-y-1"
            >
              <div className="w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mb-4 group-hover:bg-red-600 transition-colors">
                <ShieldAlert className="w-5 h-5 text-red-400 group-hover:text-white" />
              </div>
              <h3 className="text-lg font-bold text-white group-hover:text-red-300 transition-colors flex items-center justify-between">
                <span>Critical Access</span>
                <ChevronRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity text-red-400" />
              </h3>
              <p className="text-xs text-slate-300 mt-2 font-medium">
                See how essential facilities like Sion Hospital remain accessible from responder units.
              </p>
            </div>

            {/* Card 4: Protect the City */}
            <div
              onClick={() => navigateToApp('protect-city')}
              className="p-6 rounded-2xl bg-[#06191C] border border-teal-900/40 hover:border-teal-500/60 transition-all group cursor-pointer shadow-lg hover:-translate-y-1"
            >
              <div className="w-10 h-10 rounded-xl bg-teal-500/10 border border-teal-500/20 flex items-center justify-center mb-4 group-hover:bg-teal-700 transition-colors">
                <Building2 className="w-5 h-5 text-teal-300 group-hover:text-white" />
              </div>
              <h3 className="text-lg font-bold text-white group-hover:text-teal-300 transition-colors flex items-center justify-between">
                <span>Protect the City</span>
                <ChevronRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity text-teal-400" />
              </h3>
              <p className="text-xs text-slate-300 mt-2 font-medium">
                Explore where targeted mobile pumps and temporary barrier interventions help reduce risk.
              </p>
            </div>

            {/* Card 5: Ground Truth */}
            <div
              onClick={() => navigateToApp('ground-truth')}
              className="p-6 rounded-2xl bg-[#06191C] border border-teal-900/40 hover:border-purple-500/60 transition-all group cursor-pointer shadow-lg hover:-translate-y-1"
            >
              <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center mb-4 group-hover:bg-purple-600 transition-colors">
                <Camera className="w-5 h-5 text-purple-300 group-hover:text-white" />
              </div>
              <h3 className="text-lg font-bold text-white group-hover:text-purple-300 transition-colors flex items-center justify-between">
                <span>Ground Truth</span>
                <ChevronRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity text-purple-400" />
              </h3>
              <p className="text-xs text-slate-300 mt-2 font-medium">
                Connect physical field observations and citizen evidence with scientific model runs.
              </p>
            </div>

            {/* Card 6: Simulator */}
            <div
              onClick={() => navigateToApp('simulator')}
              className="p-6 rounded-2xl bg-[#06191C] border border-teal-900/40 hover:border-orange-500/60 transition-all group cursor-pointer shadow-lg hover:-translate-y-1"
            >
              <div className="w-10 h-10 rounded-xl bg-orange-500/10 border border-orange-500/20 flex items-center justify-center mb-4 group-hover:bg-orange-600 transition-colors">
                <Sliders className="w-5 h-5 text-orange-300 group-hover:text-white" />
              </div>
              <h3 className="text-lg font-bold text-white group-hover:text-orange-300 transition-colors flex items-center justify-between">
                <span>Simulator</span>
                <ChevronRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity text-orange-400" />
              </h3>
              <p className="text-xs text-slate-300 mt-2 font-medium">
                Test custom what-if rainfall scenarios and model peak runoff under extreme weather.
              </p>
            </div>

            {/* Card 7: Alert Center (Full Width on 3-col Grid) */}
            <div
              onClick={() => navigateToApp('alerts')}
              className="sm:col-span-2 lg:col-span-3 p-6 rounded-2xl bg-gradient-to-r from-[#06191C] to-[#041215] border border-teal-900/50 hover:border-teal-500/60 transition-all group cursor-pointer shadow-lg flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-teal-500/10 border border-teal-500/20 flex items-center justify-center shrink-0 group-hover:bg-[#008080] transition-colors">
                  <AlertCircle className="w-6 h-6 text-teal-300 group-hover:text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white group-hover:text-teal-300 transition-colors">
                    Alert Center Operations
                  </h3>
                  <p className="text-xs text-slate-300 mt-0.5 font-medium">
                    Stay aware of important catchment-wide risk escalations and real-time civic notifications.
                  </p>
                </div>
              </div>
              <button className="px-4 py-2 rounded-xl bg-teal-500/20 text-teal-300 font-bold text-xs group-hover:bg-[#008080] group-hover:text-white transition-all shrink-0">
                Launch Alert Center →
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ── 5. SCIENCE & DATA TRUST ───────────────────────────── */}
      <section id="science" className="py-24 bg-[#06191C] border-t border-teal-900/30">
        <div className="max-w-[1340px] mx-auto px-5 md:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="text-xs font-bold tracking-[0.2em] text-teal-400 uppercase">
              INTELLIGENCE STACK
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight mt-3">
              Built on data. Grounded in science.
            </h2>
            <p className="mt-3 text-slate-300 text-base font-medium">
              A transparent, multi-layered computing pipeline for urban flood risk prediction.
            </p>
          </div>

          <div className="space-y-4 max-w-4xl mx-auto">
            {/* Pipeline Stage 1 */}
            <div className="p-5 rounded-2xl bg-[#041215] border border-teal-900/40 flex items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="w-8 h-8 rounded-lg bg-teal-500/10 text-teal-300 font-mono font-bold text-xs flex items-center justify-center">
                  01
                </div>
                <div>
                  <h4 className="text-sm font-bold text-white">Live Forecasts & Radar Data</h4>
                  <p className="text-xs text-slate-400 font-medium">IMD precipitation feeds & ECMWF GFS/HRES forecast synthesis (0-180 min lead time).</p>
                </div>
              </div>
              <span className="text-[10px] font-mono px-2.5 py-1 rounded bg-teal-950 text-teal-300 border border-teal-800 hidden sm:inline-block">
                INPUT STREAM
              </span>
            </div>

            {/* Pipeline Stage 2 */}
            <div className="p-5 rounded-2xl bg-[#041215] border border-teal-900/40 flex items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="w-8 h-8 rounded-lg bg-teal-500/10 text-teal-300 font-mono font-bold text-xs flex items-center justify-center">
                  02
                </div>
                <div>
                  <h4 className="text-sm font-bold text-white">Terrain & Elevation Modeling</h4>
                  <p className="text-xs text-slate-400 font-medium">Copernicus 30m Digital Surface Model (DSM) & Sentinel-1 SAR flood extent mapping.</p>
                </div>
              </div>
              <span className="text-[10px] font-mono px-2.5 py-1 rounded bg-teal-950 text-teal-300 border border-teal-800 hidden sm:inline-block">
                GEOSPATIAL GRID
              </span>
            </div>

            {/* Pipeline Stage 3 */}
            <div className="p-5 rounded-2xl bg-[#041215] border border-teal-700/50 flex items-center justify-between gap-4 shadow-lg">
              <div className="flex items-center gap-4">
                <div className="w-8 h-8 rounded-lg bg-[#008080] text-white font-mono font-bold text-xs flex items-center justify-center">
                  03
                </div>
                <div>
                  <h4 className="text-sm font-bold text-white flex items-center gap-2">
                    <span>Physics-Based 2D Hydraulic Solver</span>
                    <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 uppercase">
                      AUTHORITATIVE
                    </span>
                  </h4>
                  <p className="text-xs text-slate-300 font-medium">Shallow water equations solving surface water flow and inundation depth across Mithi River catchment.</p>
                </div>
              </div>
              <span className="text-[10px] font-mono px-2.5 py-1 rounded bg-[#008080]/30 text-teal-200 border border-teal-500/40 hidden sm:inline-block">
                CORE SOLVER
              </span>
            </div>

            {/* Pipeline Stage 4 */}
            <div className="p-5 rounded-2xl bg-[#041215] border border-teal-900/40 flex items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="w-8 h-8 rounded-lg bg-teal-500/10 text-teal-300 font-mono font-bold text-xs flex items-center justify-center">
                  04
                </div>
                <div>
                  <h4 className="text-sm font-bold text-white">Route Safety & Access Graph</h4>
                  <p className="text-xs text-slate-400 font-medium">OSRM dynamic matrix graph calculating travel windows to 366 critical MCGM healthcare facilities.</p>
                </div>
              </div>
              <span className="text-[10px] font-mono px-2.5 py-1 rounded bg-teal-950 text-teal-300 border border-teal-800 hidden sm:inline-block">
                GRAPH MATRIX
              </span>
            </div>
          </div>

          {/* Advisory ML Note */}
          <div className="mt-8 max-w-4xl mx-auto p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-start gap-3">
            <Cpu className="w-5 h-5 text-teal-400 shrink-0 mt-0.5" />
            <p className="text-xs text-slate-400 leading-relaxed font-medium">
              <span className="font-bold text-slate-200">Note on Machine Learning:</span> AQUORA incorporates an XGBoost prototype model as an advisory acceleration layer. The Phase 6 2D physical hydraulic solver remains authoritative for all civic safety decisions.
            </p>
          </div>
        </div>
      </section>

      {/* ── 6. MUMBAI MISSION & CIVIC IMPACT ──────────────────── */}
      <section className="py-24 bg-[#041215] border-t border-teal-900/30 relative overflow-hidden">
        <div className="max-w-[1340px] mx-auto px-5 md:px-8 relative z-10">
          <div className="p-10 md:p-16 rounded-3xl bg-gradient-to-r from-[#06191C] via-[#041215] to-[#003B3B]/40 border border-teal-700/40 shadow-2xl space-y-6">
            <span className="text-xs font-bold tracking-[0.2em] text-teal-400 uppercase">
              OUR CIVIC MISSION
            </span>
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white tracking-tight max-w-3xl leading-tight">
              A safer, more resilient Mumbai starts with seeing what's ahead.
            </h2>
            <p className="text-base sm:text-lg text-slate-300 font-medium max-w-2xl leading-relaxed">
              Empowering citizens, urban planners, and emergency responders with clear, actionable flood intelligence today for a safer tomorrow.
            </p>

            <div className="pt-4">
              <button
                onClick={() => navigateToApp('overview')}
                className="inline-flex items-center gap-3 px-8 py-4 rounded-xl bg-[#008080] hover:bg-[#009696] text-white text-base font-bold transition-all duration-200 shadow-xl shadow-teal-950 hover:-translate-y-0.5 cursor-pointer"
              >
                <span>Open AQUORA Live Platform</span>
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ── 7. FOOTER ─────────────────────────────────────────── */}
      <footer className="bg-[#030e10] border-t border-teal-950 py-16 text-slate-400 text-xs">
        <div className="max-w-[1340px] mx-auto px-5 md:px-8 grid grid-cols-1 md:grid-cols-12 gap-12">
          {/* Col 1: Brand Info */}
          <div className="md:col-span-5 space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-[#008080] flex items-center justify-center">
                <Waves className="w-4 h-4 text-white" />
              </div>
              <span className="text-lg font-black text-white tracking-wider">AQUORA</span>
            </div>
            <p className="text-slate-400 max-w-sm leading-relaxed font-medium">
              Urban flood intelligence & response platform built for Mumbai. See the flood before it reaches the road.
            </p>
            <div className="pt-2 text-[11px] font-semibold text-teal-400 flex items-center gap-2">
              <Globe className="w-3.5 h-3.5" />
              <span>Mumbai · Mithi River Catchment (Lat: 19.0600, Lon: 72.8650)</span>
            </div>
          </div>

          {/* Col 2: Platform Links */}
          <div className="md:col-span-4 space-y-3">
            <div className="text-xs font-bold text-white uppercase tracking-wider mb-2">
              Platform Features
            </div>
            <div className="grid grid-cols-2 gap-2 font-medium">
              <button onClick={() => navigateToApp('overview')} className="text-left hover:text-teal-300">Overview</button>
              <button onClick={() => navigateToApp('flood-map')} className="text-left hover:text-teal-300">Flood Outlook</button>
              <button onClick={() => navigateToApp('travel-window')} className="text-left hover:text-teal-300">Travel Window</button>
              <button onClick={() => navigateToApp('critical-access')} className="text-left hover:text-teal-300">Critical Access</button>
              <button onClick={() => navigateToApp('protect-city')} className="text-left hover:text-teal-300">Protect the City</button>
              <button onClick={() => navigateToApp('ground-truth')} className="text-left hover:text-teal-300">Ground Truth</button>
              <button onClick={() => navigateToApp('simulator')} className="text-left hover:text-teal-300">Simulator</button>
              <button onClick={() => navigateToApp('alerts')} className="text-left hover:text-teal-300">Alert Center</button>
            </div>
          </div>

          {/* Col 3: Principles & Metadata */}
          <div className="md:col-span-3 space-y-3">
            <div className="text-xs font-bold text-white uppercase tracking-wider mb-2">
              Core Principles
            </div>
            <div className="space-y-1.5 font-medium text-slate-400">
              <div>Data · People · Action</div>
              <div>0-180 Minute Lead Time</div>
              <div>Strict Phase Boundaries</div>
              <div>Strict Type Safety</div>
            </div>
          </div>
        </div>

        <div className="max-w-[1340px] mx-auto px-5 md:px-8 pt-12 mt-12 border-t border-teal-950/80 flex flex-col sm:flex-row justify-between items-center gap-4 text-slate-500">
          <div>© 2026 AQUORA. Built for people, cities and a safer tomorrow.</div>
          <div className="flex items-center gap-4">
            <button onClick={() => navigateToApp('overview')} className="hover:text-teal-300 font-bold text-teal-400">
              Enter Live Platform →
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
