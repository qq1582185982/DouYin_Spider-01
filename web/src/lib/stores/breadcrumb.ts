import { writable } from 'svelte/store';

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

export const breadcrumbStore = writable<BreadcrumbItem[]>([]);

export function setBreadcrumb(items: BreadcrumbItem[]) {
  breadcrumbStore.set(items);
}