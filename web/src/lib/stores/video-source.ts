import { writable } from 'svelte/store';

export const videoSourceStore = writable(null);

export function setVideoSources(sources: any) {
  videoSourceStore.set(sources);
}