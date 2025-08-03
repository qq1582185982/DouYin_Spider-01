import { writable } from 'svelte/store';

export const theme = writable<'light' | 'dark'>('light');

export function initTheme() {
  if (typeof window !== 'undefined') {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null;
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const initialTheme = savedTheme || (prefersDark ? 'dark' : 'light');
    
    theme.set(initialTheme);
    document.documentElement.classList.toggle('dark', initialTheme === 'dark');
    
    theme.subscribe(value => {
      localStorage.setItem('theme', value);
      document.documentElement.classList.toggle('dark', value === 'dark');
    });
  }
}