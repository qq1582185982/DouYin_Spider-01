import Badge from './badge.svelte';

export type BadgeProps = {
  variant?: 'default' | 'secondary' | 'destructive' | 'outline';
  class?: string;
};

export { Badge };