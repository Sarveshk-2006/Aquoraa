import { create } from 'zustand';

interface AppState {
  activeTab: string;
  sidebarOpen: boolean; // Mobile menu state
  sidebarCollapsed: boolean; // Desktop rail collapse state
  setActiveTab: (tab: string) => void;
  toggleSidebar: () => void;
  toggleSidebarCollapse: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
}

const getInitialCollapsed = (): boolean => {
  if (typeof window === 'undefined') return false;
  try {
    return localStorage.getItem('aquora-sidebar-collapsed') === 'true';
  } catch {
    return false;
  }
};

export const useAppStore = create<AppState>((set) => ({
  activeTab: 'overview',
  sidebarOpen: true,
  sidebarCollapsed: getInitialCollapsed(),
  setActiveTab: (tab: string) => set({ activeTab: tab }),
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
