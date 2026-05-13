import { useContext } from 'react';
import { BackendSettingsContext } from '../context/BackendSettingsContext';

export function useBackendSettings() {
  const context = useContext(BackendSettingsContext);
  if (context === undefined) {
    throw new Error('useBackendSettings must be used within a BackendSettingsProvider');
  }
  return context;
}
