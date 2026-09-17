import { create } from 'zustand';

export type ViewMode = 'landing' | 'app';

interface AppState {
  currentView: ViewMode;
  activeTab: string;
  sidebarOpen: boolean; // Mobile menu state
  sidebarCollapsed: boolean; // Desktop rail collapse state
  setCurrentView: (view: ViewMode) => void;
  setActiveTab: (tab: string) => void;
  navigateToApp: (tab?: string) => void;
  navigateToLanding: () => void;
  toggleSidebar: () => void;
  toggleSidebarCollapse: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
}

const getInitialView = (): ViewMode => {
  if (typeof window === 'undefined') return 'landing';
  const path = window.location.pathname;
  const hash = window.location.hash;
  if (path.startsWith('/app') || hash.startsWith('#app')) {
    return 'app';
  }
  return 'landing';
};

const getInitialCollapsed = (): boolean => {
  if (typeof window === 'undefined') return false;
  try {
    return localStorage.getItem('aquora-sidebar-collapsed') === 'true';
  } catch {
    return false;
  }
};

export const useAppStore = create<AppState>((set) => ({
  currentView: getInitialView(),
  activeTab: 'overview',
  sidebarOpen: true,
  sidebarCollapsed: getInitialCollapsed(),
  setCurrentView: (view: ViewMode) => set({ currentView: view }),
  setActiveTab: (tab: string) => set({ activeTab: tab }),
  navigateToApp: (tab?: string) => {
    if (typeof window !== 'undefined' && window.history.pushState) {
      window.history.pushState({ view: 'app', tab: tab || 'overview' }, '', '/app');
    }
    set({
      currentView: 'app',
      activeTab: tab || 'overview',
    });
  },
  navigateToLanding: () => {
    if (typeof window !== 'undefined' && window.history.pushState) {
      window.history.pushState({ view: 'landing' }, '', '/');
    }
    set({ currentView: 'landing' });
  },
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  toggleSidebarCollapse: () => set((state) => {
    const next = !state.sidebarCollapsed;
    try {
      localStorage.setItem('aquora-sidebar-collapsed', String(next));
    } catch {
      // ignore
    }
    return { sidebarCollapsed: next };
  }),
  setSidebarCollapsed: (collapsed: boolean) => {
    try {
      localStorage.setItem('aquora-sidebar-collapsed', String(collapsed));
    } catch {
      // ignore
    }
    set({ sidebarCollapsed: collapsed });
  },
}));
