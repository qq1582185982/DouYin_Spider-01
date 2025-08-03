<script lang="ts">
  import { cn } from '$lib/utils';
  
  export let type: string = 'text';
  export let value: string | number = '';
  export let placeholder: string = '';
  export let disabled: boolean = false;
  
  let className: string | undefined = undefined;
  export { className as class };
</script>

<input
  {type}
  bind:value
  {placeholder}
  {disabled}
  class={cn(
    'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
    className
  )}
  on:input
  on:change
  on:focus
  on:blur
  on:keydown
  on:keypress
  on:keyup
  {...$$restProps}
/>