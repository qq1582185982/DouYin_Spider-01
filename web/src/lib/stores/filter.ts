import { writable } from 'svelte/store';

export const filterStore = writable({
  search: '',
  type: 'all',
  status: 'all'
});

export function clearAll() {
  filterStore.set({
    search: '',
    type: 'all',
    status: 'all'
  });
}