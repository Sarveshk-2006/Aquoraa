import React, { useState, useEffect, useRef } from 'react';
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
  Layers,
  Cpu,
  Users,
  Activity,
  Menu,
  X,
  Play,
  MapPin,
  TrendingUp,
  HeartPulse
} from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import mumbaiHeroImg from '@/assets/aquora-mumbai-hero.webp';

/* ─── Scroll Reveal Wrapper Component ────────────────────────── */
interface RevealProps {
  children: React.ReactNode;
  className?: string;
  delayMs?: number;
}

const Reveal: React.FC<RevealProps> = ({ children, className = '', delayMs = 0 }) => {
  const [isVisible, setIsVisible] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.unobserve(entry.target);
        }
      },
      { threshold: 0.15, rootMargin: '0px 0px -50px 0px' }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      style={{ transitionDelay: `${delayMs}ms` }}
      className={`transition-all duration-700 ease-out ${
        isVisible ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-8 scale-[0.98]'
      } ${className}`}
    >
      {children}
    </div>
  );
};

/* ─── Floating Header Navbar ─────────────────────────────────── */
const LandingNavbar: React.FC = () => {
  const { navigateToApp } = useAppStore();
  const [scrolled, setScrolled] = useState<boolean>(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (id: string) => {
    setMobileMenuOpen(false);
    const elem = document.getElementById(id);
    if (elem) {
      const yOffset = -90; // Offset for fixed navbar
      const y = elem.getBoundingClientRect().top + window.pageYOffset + yOffset;
      window.scrollTo({ top: y, behavior: 'smooth' });
    }
  };

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        scrolled
          ? 'bg-[#04191C]/95 backdrop-blur-xl border-b border-teal-500/20 py-3 shadow-2xl shadow-black/40'
          : 'bg-gradient-to-b from-[#04191C]/90 via-[#04191C]/40 to-transparent py-4'
      }`}
    >
      <div className="max-w-[1360px] mx-auto px-5 md:px-8 flex items-center justify-between">
        {/* Left: Brand Logo & Tagline */}
        <div
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          className="flex items-center gap-3 cursor-pointer group"
        >
          <div className="w-9 h-9 rounded-xl bg-[#008080] flex items-center justify-center shadow-md group-hover:bg-[#009696] group-hover:scale-105 transition-all duration-300">
            <Waves className="w-5 h-5 text-white" />
          </div>
          <div className="flex flex-col">
            <span className="text-base font-black text-white tracking-wider leading-none">
              AQUORA
            </span>
            <span className="text-[11px] text-teal-200/80 font-medium tracking-tight mt-0.5 hidden sm:inline-block">
              See the flood before it reaches the road.
            </span>
          </div>
        </div>

        {/* Center: Desktop Navigation Links */}
        <nav className="hidden lg:flex items-center gap-8 text-[13.5px] font-medium text-slate-200">
          <button
            onClick={() => scrollToSection('about')}
            className="hover:text-teal-300 transition-colors cursor-pointer py-1 relative group"
          >
            About
            <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-teal-400 group-hover:w-full transition-all duration-300" />
          </button>
          <button
            onClick={() => scrollToSection('how-it-works')}
            className="hover:text-teal-300 transition-colors cursor-pointer py-1 relative group"
          >
            How it works
            <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-teal-400 group-hover:w-full transition-all duration-300" />
          </button>
          <button
            onClick={() => scrollToSection('platform')}
            className="hover:text-teal-300 transition-colors cursor-pointer py-1 relative group"
          >
            Platform
            <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-teal-400 group-hover:w-full transition-all duration-300" />
          </button>
          <button
            onClick={() => scrollToSection('science')}
            className="hover:text-teal-300 transition-colors cursor-pointer py-1 relative group"
          >
            Science & Data
            <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-teal-400 group-hover:w-full transition-all duration-300" />
          </button>
          <button
            onClick={() => scrollToSection('impact')}
            className="hover:text-teal-300 transition-colors cursor-pointer py-1 relative group"
          >
            Impact
            <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-teal-400 group-hover:w-full transition-all duration-300" />
          </button>
        </nav>

        {/* Right: Live Badge & Enter AQUORA CTA */}
        <div className="hidden sm:flex items-center gap-4">
          <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-teal-950/80 border border-teal-500/30 text-[11px] font-medium text-teal-300 shadow-sm backdrop-blur-md">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Live Environment</span>
            <span className="text-slate-400">• Mumbai · Mithi Catchment</span>
          </div>

          <button
            onClick={() => navigateToApp('overview')}
            className="inline-flex items-center gap-2 px-4.5 py-2.5 rounded-xl bg-[#008080] hover:bg-[#009696] text-white text-[13px] font-bold transition-all duration-300 shadow-lg shadow-teal-950/80 hover:shadow-teal-600/40 hover:-translate-y-0.5 cursor-pointer active:translate-y-0"
          >
            <span>Enter AQUORA</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* Mobile Toggle */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="lg:hidden p-2 rounded-lg bg-teal-950/80 text-slate-200 hover:text-white border border-teal-800/40"
        >
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Mobile Menu Overlay */}
      {mobileMenuOpen && (
        <div className="lg:hidden bg-[#04191C]/98 backdrop-blur-2xl border-b border-teal-900/50 px-6 py-5 space-y-3 text-slate-200 animate-in fade-in slide-in-from-top-2">
          <div className="flex items-center gap-2 text-[11px] font-medium text-teal-300 pb-2 border-b border-teal-900/40">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Live Environment · Mumbai Mithi Catchment</span>
          </div>
          <button
            onClick={() => scrollToSection('about')}
            className="block w-full text-left py-2 text-sm font-medium hover:text-teal-300"
          >
            About
          </button>
          <button
            onClick={() => scrollToSection('how-it-works')}
            className="block w-full text-left py-2 text-sm font-medium hover:text-teal-300"
          >
            How it works
          </button>
          <button
            onClick={() => scrollToSection('platform')}
            className="block w-full text-left py-2 text-sm font-medium hover:text-teal-300"
          >
            Platform
          </button>
          <button
            onClick={() => scrollToSection('science')}
            className="block w-full text-left py-2 text-sm font-medium hover:text-teal-300"
          >
            Science & Data
          </button>
          <button
            onClick={() => scrollToSection('impact')}
            className="block w-full text-left py-2 text-sm font-medium hover:text-teal-300"
          >
            Impact
          </button>
          <div className="pt-2">
            <button
              onClick={() => {
                setMobileMenuOpen(false);
                navigateToApp('overview');
              }}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-[#008080] text-white font-bold text-sm shadow-md"
            >
              <span>Enter AQUORA</span>
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
      const yOffset = -90;
      const y = elem.getBoundingClientRect().top + window.pageYOffset + yOffset;
      window.scrollTo({ top: y, behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen bg-[#04191C] text-slate-100 font-sans selection:bg-[#008080] selection:text-white">
      {/* ── Floating Header Navbar ───────────────────────────── */}
      <LandingNavbar />

      {/* ── 1. CINEMATIC HERO SECTION (100vh) ───────────────── */}
      <section className="relative min-h-screen flex items-center justify-center pt-28 pb-20 overflow-hidden">
        {/* Background Image with slow cinematic ambient zoom */}
        <div className="absolute inset-0 z-0 overflow-hidden">
          <img
            src={mumbaiHeroImg}
            alt="Panoramic Mumbai skyline and Bandra-Worli Sea Link during sunset"
            className="w-full h-full object-cover object-center transition-transform duration-[30000ms] ease-out scale-100 hover:scale-105"
          />
          {/* Deep dark gradient overlay for crystal clear typography readability */}
          <div className="absolute inset-0 bg-gradient-to-r from-[#04191C] via-[#04191C]/85 via-55% to-transparent opacity-95 sm:opacity-90" />
          <div className="absolute inset-0 bg-gradient-to-t from-[#04191C] via-transparent to-[#04191C]/60" />
        </div>

        <div className="relative z-10 max-w-[1360px] mx-auto px-5 md:px-8 w-full grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Left Hero Column */}
          <div className="lg:col-span-7 space-y-6 pt-4 sm:pt-0">
            {/* Hero Eyebrow */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-teal-500/15 border border-teal-500/30 text-teal-300 text-[11px] font-bold tracking-[0.2em] uppercase shadow-sm">
              <span>MUMBAI. PEOPLE. A SAFER TOMORROW.</span>
            </div>

            {/* Main Headline */}
            <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-[4rem] font-black text-white tracking-tight leading-[1.08]">
              See the flood <br />
              before it reaches <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#00e5d4] via-teal-300 to-emerald-400">
                the road.
              </span>
            </h1>

            {/* Supporting Copy */}
            <p className="text-base sm:text-lg text-slate-200 font-medium leading-relaxed max-w-[580px]">
              Real-time flood intelligence, route safety, and critical facility access — powered by live data and scientific modelling.
            </p>

            {/* Hero CTA Buttons */}
            <div className="pt-2 flex flex-wrap items-center gap-4">
              <button
                onClick={() => navigateToApp('overview')}
                className="inline-flex items-center gap-3 px-7.5 py-4 rounded-xl bg-[#008080] hover:bg-[#009696] text-white text-base font-bold tracking-wide transition-all duration-300 shadow-xl shadow-teal-950 hover:shadow-teal-600/40 hover:-translate-y-0.5 cursor-pointer active:translate-y-0"
              >
                <span>Enter AQUORA</span>
                <ChevronRight className="w-5 h-5" />
              </button>

              <button
                onClick={() => scrollToId('how-it-works')}
                className="inline-flex items-center gap-2.5 px-6 py-4 rounded-xl bg-slate-900/70 hover:bg-slate-800/90 text-slate-100 border border-slate-700/60 text-sm font-semibold transition-all duration-300 backdrop-blur-md cursor-pointer hover:border-teal-500/40"
              >
                <div className="w-6 h-6 rounded-full bg-teal-500/20 flex items-center justify-center">
                  <Play className="w-3 h-3 text-teal-300 fill-teal-300 ml-0.5" />
                </div>
                <span>Watch our story</span>
              </button>
            </div>

            {/* Bottom Hero Tagline */}
            <div className="pt-6 border-t border-teal-900/50 flex items-center gap-3 text-xs font-semibold text-slate-400 tracking-wider uppercase">
              <span>Data</span>
              <span className="text-teal-500">•</span>
              <span>People</span>
              <span className="text-teal-500">•</span>
              <span>Action</span>
            </div>
          </div>

          {/* Right Hero Column — Live Intelligence Card & Callout */}
          <div className="lg:col-span-5 hidden lg:flex flex-col gap-6">
            {/* Live Flood Intelligence Overlay Card */}
            <div className="p-6 rounded-2xl bg-[#04191C]/85 backdrop-blur-xl border border-teal-500/30 shadow-2xl space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CloudRain className="w-4 h-4 text-teal-300" />
                  <span className="text-xs font-extrabold text-teal-200 uppercase tracking-wider">
                    LIVE FLOOD INTELLIGENCE
                  </span>
                </div>
                <span className="text-[10px] font-medium text-slate-300 px-2 py-0.5 rounded bg-teal-500/20 border border-teal-500/30">
                  Real-time data & modelling
                </span>
              </div>

              <div className="space-y-2.5 pt-1">
                <div className="flex items-center gap-2 text-xs text-slate-200">
                  <MapPin className="w-3.5 h-3.5 text-teal-400 shrink-0" />
                  <span className="font-bold text-white">Mumbai · Mithi Catchment</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-200">
                  <TrendingUp className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span>Forecast horizon: <strong className="text-emerald-300 font-extrabold">0 – 180 min</strong></span>
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-300 pt-1 border-t border-teal-900/40">
                  <Activity className="w-3.5 h-3.5 text-teal-300 shrink-0" />
                  <span className="text-[11px] font-medium text-slate-300">
                    Weather · Terrain · Runoff · Access
                  </span>
                </div>
              </div>
            </div>

            {/* Stylized Handwritten/Serif Script Accent */}
            <div className="p-5 rounded-2xl bg-gradient-to-r from-teal-950/60 to-[#04191C]/90 border border-teal-800/40 backdrop-blur-md text-right">
              <p className="text-xl sm:text-2xl font-serif italic text-teal-200/90 leading-snug">
                "A more resilient Mumbai is possible."
              </p>
            </div>
          </div>
        </div>

        {/* Scroll Indicator */}
        <button
          onClick={() => scrollToId('about')}
          className="absolute bottom-6 right-8 hidden md:flex items-center gap-2 text-xs font-bold text-slate-300 hover:text-teal-300 transition-colors cursor-pointer group"
        >
          <ArrowDown className="w-4 h-4 text-teal-400 group-hover:translate-y-1 transition-transform" />
          <span>Scroll to explore</span>
        </button>
      </section>

      {/* ── 2. THE CHALLENGE (Light Warm Background) ─────────── */}
      <section id="about" className="py-24 bg-[#F5F5F0] text-slate-900 scroll-mt-24 relative">
        <div className="max-w-[1360px] mx-auto px-5 md:px-8">
          <Reveal>
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
              {/* Left Content */}
              <div className="lg:col-span-6 space-y-6">
                <span className="text-xs font-extrabold tracking-[0.2em] text-[#008080] uppercase">
                  THE CHALLENGE
                </span>
                <h2 className="text-3xl sm:text-4xl md:text-5xl font-black text-slate-900 tracking-tight leading-tight">
                  Mumbai doesn't stop <br />
                  <span className="text-[#008080]">when the rain starts.</span>
                </h2>
                <p className="text-slate-700 text-base sm:text-lg leading-relaxed font-normal">
                  Intense rainfall, high tides, and a complex urban landscape can quickly turn roads impassable, disrupt essential services, and impact millions of lives. AQUORA helps the city anticipate change, make better decisions, and stay one step ahead.
                </p>

                {/* 3 Challenge Indicators */}
                <div className="pt-4 grid grid-cols-3 gap-4 border-t border-slate-300">
                  <div className="space-y-1">
                    <div className="text-2xl sm:text-3xl font-black text-[#008080]">12M+</div>
                    <div className="text-[11px] font-medium text-slate-600 leading-snug">
                      People live in flood-prone areas
                    </div>
                  </div>
                  <div className="space-y-1">
                    <div className="text-2xl sm:text-3xl font-black text-emerald-700">Higher</div>
                    <div className="text-[11px] font-medium text-slate-600 leading-snug">
                      Exposure to extreme rainfall events
                    </div>
                  </div>
                  <div className="space-y-1">
                    <div className="text-2xl sm:text-3xl font-black text-slate-900">Complex</div>
                    <div className="text-[11px] font-medium text-slate-600 leading-snug">
                      Urban drainage and terrain
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Visual Box (Mumbai Rain Scene Card with Stylized Overlay) */}
              <div className="lg:col-span-6 relative">
                <div className="relative rounded-3xl overflow-hidden shadow-2xl border border-slate-300/80 bg-slate-900 group">
                  <div className="aspect-[4/3] relative overflow-hidden bg-gradient-to-br from-slate-800 to-slate-900">
                    <img
                      src={mumbaiHeroImg}
                      alt="Mumbai street infrastructure during heavy rain"
                      className="w-full h-full object-cover filter brightness-[0.7] contrast-[1.1] transition-transform duration-700 group-hover:scale-105"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-[#04191C]/90 via-[#04191C]/30 to-transparent" />
                  </div>

                  {/* Overlaid Quote Card */}
                  <div className="absolute bottom-6 right-6 left-6 p-6 rounded-2xl bg-[#04191C]/90 backdrop-blur-md border border-teal-500/30 text-white shadow-xl">
                    <p className="text-lg sm:text-xl font-serif italic text-teal-200">
                      "A city that keeps moving deserves to be better prepared."
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ── 3. HOW AQUORA WORKS (Dark Teal) ──────────────────── */}
      <section id="how-it-works" className="py-24 bg-[#04191C] border-t border-teal-900/40 scroll-mt-24 relative">
        <div className="max-w-[1360px] mx-auto px-5 md:px-8">
          <Reveal>
            <div className="max-w-2xl mb-16 space-y-3">
              <span className="text-xs font-extrabold tracking-[0.2em] text-teal-400 uppercase">
                HOW AQUORA WORKS
              </span>
              <h2 className="text-3xl sm:text-4xl md:text-5xl font-black text-white tracking-tight leading-tight">
                From data to decisions, <br />
                <span className="text-teal-300">for a safer Mumbai.</span>
              </h2>
            </div>
          </Reveal>

          {/* 4 Horizontal Process Steps */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 relative">
            <Reveal delayMs={100}>
              <div className="p-7 rounded-2xl bg-[#062327] border border-teal-900/50 hover:border-teal-500/50 transition-all duration-300 space-y-4 shadow-xl group hover:-translate-y-1">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-xl bg-teal-500/15 border border-teal-500/30 flex items-center justify-center text-teal-300">
                    <CloudRain className="w-5 h-5" />
                  </div>
                  <span className="text-2xl font-black text-teal-500/30 group-hover:text-teal-400/50 transition-colors">
                    01
                  </span>
                </div>
                <h3 className="text-base font-bold text-white tracking-wide uppercase">
                  LIVE DATA
                </h3>
                <p className="text-xs text-slate-300 leading-relaxed font-medium">
                  Forecasts, rain, tides and real-time inputs
                </p>
              </div>
            </Reveal>

            <Reveal delayMs={200}>
              <div className="p-7 rounded-2xl bg-[#062327] border border-teal-900/50 hover:border-teal-500/50 transition-all duration-300 space-y-4 shadow-xl group hover:-translate-y-1">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-xl bg-teal-500/15 border border-teal-500/30 flex items-center justify-center text-teal-300">
                    <Layers className="w-5 h-5" />
                  </div>
                  <span className="text-2xl font-black text-teal-500/30 group-hover:text-teal-400/50 transition-colors">
                    02
                  </span>
                </div>
                <h3 className="text-base font-bold text-white tracking-wide uppercase">
                  UNDERSTAND RISK
                </h3>
                <p className="text-xs text-slate-300 leading-relaxed font-medium">
                  Model flood behaviour across the city
                </p>
              </div>
            </Reveal>

            <Reveal delayMs={300}>
              <div className="p-7 rounded-2xl bg-[#062327] border border-teal-900/50 hover:border-teal-500/50 transition-all duration-300 space-y-4 shadow-xl group hover:-translate-y-1">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-xl bg-teal-500/15 border border-teal-500/30 flex items-center justify-center text-teal-300">
                    <Navigation className="w-5 h-5" />
                  </div>
                  <span className="text-2xl font-black text-teal-500/30 group-hover:text-teal-400/50 transition-colors">
                    03
                  </span>
                </div>
                <h3 className="text-base font-bold text-white tracking-wide uppercase">
                  FIND SAFER OPTIONS
                </h3>
                <p className="text-xs text-slate-300 leading-relaxed font-medium">
                  Analyse routes and critical access
                </p>
              </div>
            </Reveal>

            <Reveal delayMs={400}>
              <div className="p-7 rounded-2xl bg-[#062327] border border-teal-900/50 hover:border-teal-500/50 transition-all duration-300 space-y-4 shadow-xl group hover:-translate-y-1">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-xl bg-teal-500/15 border border-teal-500/30 flex items-center justify-center text-teal-300">
                    <ShieldAlert className="w-5 h-5" />
                  </div>
                  <span className="text-2xl font-black text-teal-500/30 group-hover:text-teal-400/50 transition-colors">
                    04
                  </span>
                </div>
                <h3 className="text-base font-bold text-white tracking-wide uppercase">
                  ACT EARLIER
                </h3>
                <p className="text-xs text-slate-300 leading-relaxed font-medium">
                  Support response and intervention
                </p>
              </div>
            </Reveal>
          </div>
        </div>
      </section>

      {/* ── 4. THE PLATFORM (Light Background) ───────────────── */}
      <section id="platform" className="py-24 bg-[#F8FAFC] text-slate-900 scroll-mt-24 relative">
        <div className="max-w-[1360px] mx-auto px-5 md:px-8">
          <Reveal>
            <div className="flex flex-col md:flex-row md:items-end justify-between mb-16 gap-6">
              <div className="max-w-2xl space-y-3">
                <span className="text-xs font-extrabold tracking-[0.2em] text-[#008080] uppercase">
                  THE PLATFORM
                </span>
                <h2 className="text-3xl sm:text-4xl md:text-5xl font-black text-slate-900 tracking-tight leading-tight">
                  Integrated tools for <br />
                  <span className="text-[#008080]">a more resilient city.</span>
                </h2>
                <p className="text-slate-600 text-base font-normal">
                  Explore real-time insights, plan with confidence, and support safer, more connected communities.
                </p>
              </div>

              <button
                onClick={() => navigateToApp('overview')}
                className="inline-flex items-center gap-2 text-sm font-bold text-[#008080] hover:text-[#006666] transition-colors cursor-pointer group shrink-0"
              >
                <span>Explore the platform</span>
                <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>
            </div>
          </Reveal>

          {/* 7 Feature Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {/* Card 1 */}
            <Reveal delayMs={100}>
              <div
                onClick={() => navigateToApp('flood-map')}
                className="p-6 rounded-2xl bg-white border border-slate-200 hover:border-teal-500/60 shadow-md hover:shadow-xl transition-all duration-300 cursor-pointer group space-y-3 hover:-translate-y-1"
              >
                <div className="w-10 h-10 rounded-xl bg-teal-50 border border-teal-100 flex items-center justify-center text-[#008080] group-hover:bg-[#008080] group-hover:text-white transition-colors">
                  <CloudRain className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-slate-900 group-hover:text-[#008080] transition-colors">
                  Flood Outlook
                </h3>
                <p className="text-xs text-slate-600 leading-relaxed font-normal">
                  See where water may develop over the next 3 hours.
                </p>
              </div>
            </Reveal>

            {/* Card 2 */}
            <Reveal delayMs={150}>
              <div
                onClick={() => navigateToApp('travel-window')}
                className="p-6 rounded-2xl bg-white border border-slate-200 hover:border-emerald-500/60 shadow-md hover:shadow-xl transition-all duration-300 cursor-pointer group space-y-3 hover:-translate-y-1"
              >
                <div className="w-10 h-10 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-700 group-hover:bg-emerald-700 group-hover:text-white transition-colors">
                  <Navigation className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-slate-900 group-hover:text-emerald-700 transition-colors">
                  Travel Window
                </h3>
                <p className="text-xs text-slate-600 leading-relaxed font-normal">
                  Check route safety and timing.
                </p>
              </div>
            </Reveal>

            {/* Card 3 */}
            <Reveal delayMs={200}>
              <div
                onClick={() => navigateToApp('critical-access')}
                className="p-6 rounded-2xl bg-white border border-slate-200 hover:border-red-500/60 shadow-md hover:shadow-xl transition-all duration-300 cursor-pointer group space-y-3 hover:-translate-y-1"
              >
                <div className="w-10 h-10 rounded-xl bg-red-50 border border-red-100 flex items-center justify-center text-red-600 group-hover:bg-red-600 group-hover:text-white transition-colors">
                  <ShieldAlert className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-slate-900 group-hover:text-red-600 transition-colors">
                  Critical Access
                </h3>
                <p className="text-xs text-slate-600 leading-relaxed font-normal">
                  See how essential facilities may be affected.
                </p>
              </div>
            </Reveal>

            {/* Card 4 */}
            <Reveal delayMs={250}>
              <div
                onClick={() => navigateToApp('protect-city')}
                className="p-6 rounded-2xl bg-white border border-slate-200 hover:border-teal-500/60 shadow-md hover:shadow-xl transition-all duration-300 cursor-pointer group space-y-3 hover:-translate-y-1"
              >
                <div className="w-10 h-10 rounded-xl bg-teal-50 border border-teal-100 flex items-center justify-center text-[#008080] group-hover:bg-[#008080] group-hover:text-white transition-colors">
                  <Building2 className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-slate-900 group-hover:text-[#008080] transition-colors">
                  Protect the City
                </h3>
                <p className="text-xs text-slate-600 leading-relaxed font-normal">
                  Explore where intervention may help.
                </p>
              </div>
            </Reveal>

            {/* Card 5 */}
            <Reveal delayMs={300}>
              <div
                onClick={() => navigateToApp('ground-truth')}
                className="p-6 rounded-2xl bg-white border border-slate-200 hover:border-purple-500/60 shadow-md hover:shadow-xl transition-all duration-300 cursor-pointer group space-y-3 hover:-translate-y-1"
              >
                <div className="w-10 h-10 rounded-xl bg-purple-50 border border-purple-100 flex items-center justify-center text-purple-700 group-hover:bg-purple-700 group-hover:text-white transition-colors">
                  <Camera className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-slate-900 group-hover:text-purple-700 transition-colors">
                  Ground Truth
                </h3>
                <p className="text-xs text-slate-600 leading-relaxed font-normal">
                  Connect modelled conditions with observations.
                </p>
              </div>
            </Reveal>

            {/* Card 6 */}
            <Reveal delayMs={350}>
              <div
                onClick={() => navigateToApp('simulator')}
                className="p-6 rounded-2xl bg-white border border-slate-200 hover:border-orange-500/60 shadow-md hover:shadow-xl transition-all duration-300 cursor-pointer group space-y-3 hover:-translate-y-1"
              >
                <div className="w-10 h-10 rounded-xl bg-orange-50 border border-orange-100 flex items-center justify-center text-orange-600 group-hover:bg-orange-600 group-hover:text-white transition-colors">
                  <Sliders className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-slate-900 group-hover:text-orange-600 transition-colors">
                  Simulator
                </h3>
                <p className="text-xs text-slate-600 leading-relaxed font-normal">
                  Explore what-if scenarios.
                </p>
              </div>
            </Reveal>

            {/* Card 7 */}
            <Reveal delayMs={400} className="sm:col-span-2 xl:col-span-2">
              <div
                onClick={() => navigateToApp('alerts')}
                className="w-full h-full p-6 rounded-2xl bg-white border border-slate-200 hover:border-teal-500/60 shadow-md hover:shadow-xl transition-all duration-300 cursor-pointer group flex flex-col justify-between space-y-3 hover:-translate-y-1"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-teal-50 border border-teal-100 flex items-center justify-center text-[#008080] group-hover:bg-[#008080] group-hover:text-white transition-colors shrink-0">
                    <AlertCircle className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-slate-900 group-hover:text-[#008080] transition-colors">
                      Alert Center
                    </h3>
                    <p className="text-xs text-slate-600 leading-relaxed font-normal">
                      Stay aware of important changes across Mumbai.
                    </p>
                  </div>
                </div>
                <div className="text-xs font-bold text-[#008080] group-hover:translate-x-1 transition-transform">
                  Launch Alert Center →
                </div>
              </div>
            </Reveal>
          </div>
        </div>
      </section>

      {/* ── 5. SCIENCE & TRUST (Dark Teal) ────────────────────── */}
      <section id="science" className="py-24 bg-[#04191C] border-t border-teal-900/40 scroll-mt-24 relative">
        <div className="max-w-[1360px] mx-auto px-5 md:px-8">
          <Reveal>
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
              {/* Left Content */}
              <div className="lg:col-span-6 space-y-6">
                <span className="text-xs font-extrabold tracking-[0.2em] text-teal-400 uppercase">
                  BUILT ON SCIENCE
                </span>
                <h2 className="text-3xl sm:text-4xl md:text-5xl font-black text-white tracking-tight leading-tight">
                  Trusted data. <br />
                  <span className="text-teal-300">Real-world impact.</span>
                </h2>
                <p className="text-slate-300 text-base leading-relaxed font-medium">
                  AQUORA combines live data with physics-based modelling and real-world observations to provide a clearer, earlier view of flood risk.
                </p>

                {/* Data Layer Diagram List */}
                <div className="space-y-3 pt-2">
                  <div className="p-3.5 rounded-xl bg-[#062327] border border-teal-900/50 flex items-center justify-between text-xs text-slate-200">
                    <span className="font-bold text-white">Live weather forecasts</span>
                    <span className="text-slate-400 font-mono text-[11px]">(e.g. Open-Meteo)</span>
                  </div>
                  <div className="p-3.5 rounded-xl bg-[#062327] border border-teal-900/50 flex items-center justify-between text-xs text-slate-200">
                    <span className="font-bold text-white">Terrain & land cover</span>
                    <span className="text-slate-400 font-mono text-[11px]">(e.g. NASA, Open data)</span>
                  </div>
                  <div className="p-3.5 rounded-xl bg-[#008080]/30 border border-teal-500/40 flex items-center justify-between text-xs text-white">
                    <span className="font-bold text-teal-200">Physics-based flood modelling</span>
                    <span className="text-teal-300 font-mono text-[11px]">(Digital Twin)</span>
                  </div>
                  <div className="p-3.5 rounded-xl bg-[#062327] border border-teal-900/50 flex items-center justify-between text-xs text-slate-200">
                    <span className="font-bold text-white">Route & access analysis</span>
                    <span className="text-slate-400 font-mono text-[11px]">(e.g. OSRM)</span>
                  </div>
                  <div className="p-3.5 rounded-xl bg-[#062327] border border-teal-900/50 flex items-center justify-between text-xs text-slate-200">
                    <span className="font-bold text-white">Ground truth & observations</span>
                    <span className="text-slate-400 font-mono text-[11px]">(Citizen reports)</span>
                  </div>
                  <div className="p-3.5 rounded-xl bg-[#062327] border border-teal-900/50 flex items-center justify-between text-xs text-slate-200">
                    <span className="font-bold text-white">AI/ML (Advisory)</span>
                    <span className="text-slate-400 font-mono text-[11px]">Prototype models to enhance insights</span>
                  </div>
                </div>

                <div className="pt-2">
                  <button
                    onClick={() => navigateToApp('overview')}
                    className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[#008080] hover:bg-[#009696] text-white font-bold text-sm transition-all duration-300 shadow-md hover:-translate-y-0.5 cursor-pointer"
                  >
                    <span>Learn more about our approach</span>
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Right Card */}
              <div className="lg:col-span-6 p-8 sm:p-10 rounded-3xl bg-gradient-to-br from-[#062327] to-[#04191C] border border-teal-700/40 shadow-2xl space-y-6">
                <div className="w-12 h-12 rounded-2xl bg-teal-500/15 border border-teal-500/30 flex items-center justify-center text-teal-300">
                  <Cpu className="w-6 h-6" />
                </div>
                <h3 className="text-2xl sm:text-3xl font-black text-white leading-tight">
                  Science for a <br />
                  <span className="text-teal-300">safer tomorrow.</span>
                </h3>
                <p className="text-slate-300 text-sm sm:text-base leading-relaxed font-medium">
                  We combine open data, proven modelling approaches and real-world evidence to support smarter, faster, and more inclusive decisions.
                </p>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ── 6. PEOPLE & HUMAN IMPACT (Light Background) ───────── */}
      <section id="impact" className="py-24 bg-[#F8FAFC] text-slate-900 scroll-mt-24 relative">
        <div className="max-w-[1360px] mx-auto px-5 md:px-8">
          <Reveal>
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
              {/* Left Visual Card */}
              <div className="lg:col-span-5 relative">
                <div className="rounded-3xl overflow-hidden shadow-2xl border border-slate-300 bg-slate-900 relative group">
                  <img
                    src={mumbaiHeroImg}
                    alt="People navigating Mumbai streets during monsoon"
                    className="w-full h-full object-cover filter brightness-[0.75] contrast-[1.1] transition-transform duration-700 group-hover:scale-105"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-transparent to-transparent" />
                  <div className="absolute bottom-6 left-6 right-6 p-5 rounded-2xl bg-white/95 backdrop-blur-md shadow-lg border border-slate-200">
                    <div className="text-lg font-serif italic text-slate-900">
                      People. Places. Possibilities.
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Content */}
              <div className="lg:col-span-7 space-y-6">
                <span className="text-xs font-extrabold tracking-[0.2em] text-[#008080] uppercase">
                  FOR PEOPLE. FOR COMMUNITIES.
                </span>
                <h2 className="text-3xl sm:text-4xl md:text-5xl font-black text-slate-900 tracking-tight leading-tight">
                  Because flood intelligence <br />
                  <span className="text-[#008080]">is ultimately about people.</span>
                </h2>
                <p className="text-slate-600 text-base leading-relaxed font-normal">
                  Safer commutes. Accessible hospitals. Stronger communities. A more resilient Mumbai.
                </p>

                {/* 4 Impact Pillars */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                  <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm space-y-1 hover:border-teal-500/40 transition-colors">
                    <div className="flex items-center gap-2 text-sm font-bold text-slate-900">
                      <Navigation className="w-4 h-4 text-[#008080]" />
                      <span>Commuters</span>
                    </div>
                    <p className="text-xs text-slate-600">Safer journeys</p>
                  </div>

                  <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm space-y-1 hover:border-red-500/40 transition-colors">
                    <div className="flex items-center gap-2 text-sm font-bold text-slate-900">
                      <HeartPulse className="w-4 h-4 text-red-600" />
                      <span>Emergency services</span>
                    </div>
                    <p className="text-xs text-slate-600">Uninterrupted access</p>
                  </div>

                  <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm space-y-1 hover:border-emerald-500/40 transition-colors">
                    <div className="flex items-center gap-2 text-sm font-bold text-slate-900">
                      <Building2 className="w-4 h-4 text-emerald-700" />
                      <span>Municipal teams</span>
                    </div>
                    <p className="text-xs text-slate-600">Better planning</p>
                  </div>

                  <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm space-y-1 hover:border-purple-500/40 transition-colors">
                    <div className="flex items-center gap-2 text-sm font-bold text-slate-900">
                      <Users className="w-4 h-4 text-purple-700" />
                      <span>Communities</span>
                    </div>
                    <p className="text-xs text-slate-600">Greater resilience</p>
                  </div>
                </div>

                {/* Quote Banner */}
                <div className="p-5 rounded-2xl bg-teal-50 border border-teal-100 text-slate-800 font-serif italic text-base leading-snug">
                  "A smarter, safer Mumbai is not just possible — it's within our reach."
                </div>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ── 7. THE NEXT STEP / FINAL CTA (Dark Teal) ─────────── */}
      <section className="py-24 bg-[#04191C] border-t border-teal-900/40 relative overflow-hidden">
        <div className="max-w-[1360px] mx-auto px-5 md:px-8 relative z-10">
          <Reveal>
            <div className="p-10 md:p-16 rounded-3xl bg-gradient-to-r from-[#062327] via-[#04191C] to-[#003B3B]/50 border border-teal-700/40 shadow-2xl flex flex-col lg:flex-row items-start lg:items-center justify-between gap-8">
              <div className="space-y-4 max-w-2xl">
                <span className="text-xs font-extrabold tracking-[0.2em] text-teal-400 uppercase">
                  THE NEXT STEP
                </span>
                <h2 className="text-3xl sm:text-4xl md:text-5xl font-black text-white tracking-tight leading-tight">
                  A safer, more resilient Mumbai starts with seeing what's ahead.
                </h2>
                <p className="text-slate-300 text-base font-medium">
                  Explore AQUORA's live flood intelligence platform.
                </p>
              </div>

              <div className="space-y-3 shrink-0">
                <button
                  onClick={() => navigateToApp('overview')}
                  className="inline-flex items-center gap-3 px-8 py-4 rounded-xl bg-[#008080] hover:bg-[#009696] text-white text-base font-bold transition-all duration-300 shadow-xl shadow-teal-950 hover:-translate-y-0.5 cursor-pointer active:translate-y-0"
                >
                  <span>Enter AQUORA</span>
                  <ChevronRight className="w-5 h-5" />
                </button>
                <div className="text-right text-sm font-serif italic text-teal-200/80">
                  Same city. A safer tomorrow.
                </div>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ── 8. FOOTER ─────────────────────────────────────────── */}
      <footer className="bg-[#031113] border-t border-teal-950 py-16 text-slate-400 text-xs">
        <div className="max-w-[1360px] mx-auto px-5 md:px-8 grid grid-cols-1 md:grid-cols-12 gap-12">
          {/* Col 1: Brand Info */}
          <div className="md:col-span-5 space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-[#008080] flex items-center justify-center">
                <Waves className="w-4 h-4 text-white" />
              </div>
              <span className="text-lg font-black text-white tracking-wider">AQUORA</span>
            </div>
            <p className="text-slate-400 max-w-sm leading-relaxed font-medium">
              See the flood before it reaches the road.
            </p>
            <div className="pt-2 text-[11px] font-semibold text-teal-400 space-y-1">
              <div>Mumbai · Mithi Catchment</div>
              <div className="text-slate-400">Data · People · Action</div>
            </div>
          </div>

          {/* Col 2: Navigation Links */}
          <div className="md:col-span-4 space-y-3">
            <div className="text-xs font-bold text-white uppercase tracking-wider mb-2">
              Platform Modules
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

          {/* Col 3: Legal & Metadata */}
          <div className="md:col-span-3 space-y-3">
            <div className="text-xs font-bold text-white uppercase tracking-wider mb-2">
              AQUORA System
            </div>
            <div className="space-y-1.5 font-medium text-slate-400">
              <div>Urban Flood Intelligence</div>
              <div>Mithi River Reach (17.8 km)</div>
              <div>0-180 Minute Lead Horizon</div>
            </div>
          </div>
        </div>

        <div className="max-w-[1360px] mx-auto px-5 md:px-8 pt-12 mt-12 border-t border-teal-950/80 flex flex-col sm:flex-row justify-between items-center gap-4 text-slate-500">
          <div>© 2026 AQUORA. Building a more resilient Mumbai.</div>
          <div className="flex items-center gap-6 text-[11px] font-medium text-slate-400">
            <span>Privacy</span>
            <span>Terms</span>
            <span>Contact</span>
            <button onClick={() => navigateToApp('overview')} className="hover:text-teal-300 font-bold text-teal-400">
              Enter AQUORA →
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
