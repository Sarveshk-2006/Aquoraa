import React, { useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppShell } from '@/components/layout/AppShell';
import { LandingPage } from '@/features/landing';
import { useAppStore } from '@/store/useAppStore';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const MainContent: React.FC = () => {
  const { currentView, setCurrentView, setActiveTab } = useAppStore();

  useEffect(() => {
    const handlePopState = (e: PopStateEvent) => {
      const path = window.location.pathname;
      const hash = window.location.hash;
      if (path.startsWith('/app') || hash.startsWith('#app')) {
        setCurrentView('app');
        if (e.state?.tab) {
          setActiveTab(e.state.tab);
        }
      } else {
        setCurrentView('landing');
      }
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [setCurrentView, setActiveTab]);

  if (currentView === 'landing') {
    return <LandingPage />;
  }

  return <AppShell />;
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <MainContent />
    </QueryClientProvider>
  );
};

export default App;
