<script lang="ts">
  import { cn } from "$lib/utils";
  
  export let checked = false;
  export let onCheckedChange: ((checked: boolean) => void) | undefined = undefined;
  export let disabled = false;
  let className = "";
  export { className as class };
  
  function handleChange(e: Event) {
    const target = e.target as HTMLInputElement;
    checked = target.checked;
    onCheckedChange?.(checked);
  }
</script>

<input
  type="checkbox"
  {checked}
  {disabled}
  on:change={handleChange}
  class={cn(
    "h-4 w-4 rounded border-gray-300 text-primary focus:ring-2 focus:ring-primary/20",
    disabled && "cursor-not-allowed opacity-50",
    className
  )}
/>