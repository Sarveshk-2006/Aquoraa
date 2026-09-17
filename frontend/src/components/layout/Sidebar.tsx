import React from 'react';
import {
  LayoutDashboard,
  CloudRain,
  Navigation,
  ShieldAlert,
  Building2,
  Camera,
  Sliders,
  ChevronLeft,
  ChevronRight,
  X,
} from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';

interface NavItem {
  id: string;
  label: string;
  description: string;
  icon: React.ElementType;
}

export const NAV_ITEMS: NavItem[] = [
  { id: 'overview',        label: 'Overview',          description: 'Current situation at a glance',      icon: LayoutDashboard },
  { id: 'flood-map',       label: 'Flood Outlook',      description: 'See where water may develop',        icon: CloudRain },
  { id: 'travel-window',   label: 'Travel Window',      description: 'Check route safety & timing',        icon: Navigation },
  { id: 'critical-access', label: 'Critical Access',    description: 'Essential facilities & access',      icon: ShieldAlert },
  { id: 'protect-city',    label: 'Protect the City',   description: 'Where intervention may help most',   icon: Building2 },
  { id: 'ground-truth',    label: 'Ground Truth',       description: 'Report what you\'re seeing',         icon: Camera },
  { id: 'simulator',       label: 'Simulator',          description: 'Explore what-if scenarios',          icon: Sliders },
];

interface SidebarProps {
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ mobileOpen = false, onCloseMobile }) => {
  const { activeTab, setActiveTab, sidebarCollapsed, toggleSidebarCollapse } = useAppStore();

  const handleSelect = (id: string) => {
    setActiveTab(id);
    if (onCloseMobile) onCloseMobile();
  };

  const sidebarWidthClass = sidebarCollapsed ? 'w-[68px]' : 'w-[220px]';

  const content = (
    <div className={`relative h-full ${sidebarWidthClass} shrink-0 transition-all duration-300 ease-in-out select-none overflow-visible`}>

      {/* ── Desktop Collapse Toggle Button (Unclipped boundary button) ── */}
      <button
        id="sidebar-collapse-toggle"
        onClick={toggleSidebarCollapse}
        className="hidden md:flex absolute top-4 -right-3 z-50 w-6 h-6 rounded-full bg-white text-slate-700 hover:text-[#008080] hover:bg-slate-50 border border-slate-300/90 items-center justify-center shadow-md transition-all cursor-pointer focus:outline-none focus:ring-2 focus:ring-[#008080]"
        aria-label={sidebarCollapsed ? 'Expand navigation' : 'Collapse navigation'}
        title={sidebarCollapsed ? 'Expand navigation' : 'Collapse navigation'}
      >
        {sidebarCollapsed ? (
          <ChevronRight className="w-3.5 h-3.5 stroke-[2.5]" />
        ) : (
          <ChevronLeft className="w-3.5 h-3.5 stroke-[2.5]" />
        )}
      </button>

      {/* ── Inner Sidebar Content Container ───────────────── */}
      <div
        className="aq-sidebar flex flex-col h-full w-full overflow-y-auto overflow-x-hidden border-r"
        style={{ background: 'var(--aq-navy)', borderColor: 'rgba(255,255,255,0.06)' }}
      >
        {/* Main Nav items */}
        <nav className="flex-1 py-4 px-2.5 space-y-1" aria-label="Main navigation">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;

            return (
              <button
                key={item.id}
                id={`nav-${item.id}`}
                onClick={() => handleSelect(item.id)}
                aria-current={isActive ? 'page' : undefined}
                title={sidebarCollapsed ? item.label : undefined}
                className={`w-full flex items-center ${
                  sidebarCollapsed ? 'justify-center px-0 py-3' : 'gap-3 px-3 py-2.5'
                } rounded-xl text-left transition-all duration-200 group relative cursor-pointer`}
                style={{
                  background: isActive ? '#008080' : 'transparent',
                  borderLeft: isActive ? '3px solid #F5F5DC' : '3px solid transparent',
                  boxShadow: isActive ? '0 2px 8px rgba(0,128,128,0.30)' : 'none',
                }}
                onMouseEnter={(e) => {
                  if (!isActive) (e.currentTarget as HTMLElement).style.background = 'rgba(0,128,128,0.20)';
                }}
                onMouseLeave={(e) => {
                  if (!isActive) (e.currentTarget as HTMLElement).style.background = 'transparent';
                }}
              >
                {/* Icon */}
                <span className="shrink-0 flex items-center justify-center">
                  <Icon
                    className="w-4.5 h-4.5 w-[18px] h-[18px] transition-colors"
                    style={{ color: isActive ? '#ffffff' : 'rgba(255,255,255,0.65)' }}
                  />
                </span>

                {/* Text labels (Visible only when expanded) */}
                {!sidebarCollapsed && (
                  <span className="flex flex-col min-w-0 flex-1 overflow-hidden transition-opacity duration-200">
                    <span
                      className="text-[13px] font-semibold leading-tight truncate"
                      style={{ color: isActive ? '#ffffff' : 'rgba(255,255,255,0.85)' }}
                    >
                      {item.label}
                    </span>
                    <span
                      className="text-[11px] leading-snug mt-0.5 truncate"
                      style={{ color: isActive ? 'rgba(245,245,220,0.85)' : 'rgba(255,255,255,0.40)' }}
                    >
                      {item.description}
                    </span>
                  </span>
                )}

                {/* Collapsed mode hover tooltip indicator */}
                {sidebarCollapsed && (
                  <span className="absolute left-full ml-3 px-2.5 py-1.5 rounded-lg bg-slate-900 text-white text-[11px] font-bold whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-xl border border-slate-700">
                    {item.label}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Bottom Tagline (Visible only when expanded) */}
        {!sidebarCollapsed && (
          <>
            <div className="mx-4 h-px" style={{ background: 'var(--aq-sidebar-border)' }} />
            <div className="px-5 py-4 transition-opacity duration-200">
              <p className="text-[12.5px] font-semibold leading-snug" style={{ color: '#F5F5DC' }}>
                A more resilient<br />Mumbai, together.
              </p>
              <p className="text-[10.5px] mt-1" style={{ color: 'rgba(255,255,255,0.40)' }}>
                Data · People · Action
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop persistent sidebar */}
      <aside className="hidden md:block h-full shrink-0 z-30 relative overflow-visible" aria-label="Sidebar">
        {content}
      </aside>

      {/* Mobile overlay drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex" role="dialog" aria-modal="true" aria-label="Navigation menu">
          <div
            className="fixed inset-0 transition-opacity"
            style={{ background: 'rgba(15,35,64,0.50)' }}
            onClick={onCloseMobile}
          />
          <div className="relative z-10 h-full flex flex-col">
            {content}
            <button
              onClick={onCloseMobile}
              className="absolute top-3 right-3 p-1.5 rounded-lg text-white/60 hover:text-white hover:bg-white/10 transition-colors"
              aria-label="Close navigation menu"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default Sidebar;
