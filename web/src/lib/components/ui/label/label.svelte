<script lang="ts">
  import type { HTMLLabelAttributes } from "svelte/elements";
  import { cn } from "$lib/utils.js";

  type $$Props = HTMLLabelAttributes;

  let className: $$Props["class"] = undefined;
  export { className as class };
</script>

<label
  class={cn(
    "text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70",
    className
  )}
  {...$$restProps}
>
  <slot />
</label>