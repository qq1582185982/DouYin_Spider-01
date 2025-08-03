<script lang="ts">
  import { cn } from "$lib/utils.js";

  export let checked: boolean = false;
  export let disabled: boolean = false;
  export let id: string = "";
  
  let className: string = "";
  export { className as class };

  function toggle() {
    if (!disabled) {
      checked = !checked;
    }
  }
</script>

<button
  type="button"
  role="switch"
  aria-checked={checked}
  {id}
  {disabled}
  on:click={toggle}
  class={cn(
    "relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-50",
    checked ? "bg-primary" : "bg-input",
    className
  )}
  {...$$restProps}
>
  <span
    class={cn(
      "pointer-events-none inline-block h-5 w-5 transform rounded-full bg-background shadow-lg ring-0 transition-transform",
      checked ? "translate-x-5" : "translate-x-0"
    )}
  ></span>
</button>