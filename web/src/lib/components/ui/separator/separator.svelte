<script lang="ts">
  import { cn } from "$lib/utils";
  
  export let orientation: "horizontal" | "vertical" = "horizontal";
  export let decorative = true;
  
  let className: string = "";
  export { className as class };
</script>

<div
  data-orientation={orientation}
  role={decorative ? "none" : "separator"}
  aria-orientation={decorative ? undefined : orientation}
  class={cn(
    "shrink-0 bg-border",
    orientation === "horizontal" ? "h-[1px] w-full" : "h-full w-[1px]",
    className
  )}
  {...$$restProps}
></div>