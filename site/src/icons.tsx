import type { ComponentChildren } from "preact";

/** One icon family: 16 px grid, 1.5 px round strokes. */
function Icon({ children }: { children: ComponentChildren }) {
  return (
    <svg
      class="icon"
      viewBox="0 0 16 16"
      width="16"
      height="16"
      fill="none"
      stroke="currentColor"
      stroke-width="1.5"
      stroke-linecap="round"
      stroke-linejoin="round"
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}

export const SearchIcon = () => (
  <Icon>
    <circle cx="7" cy="7" r="4.25" />
    <path d="m10.25 10.25 3.25 3.25" />
  </Icon>
);
export const BackIcon = () => (
  <Icon>
    <path d="M9.5 3.5 5 8l4.5 4.5" />
  </Icon>
);
export const DownloadIcon = () => (
  <Icon>
    <path d="M8 2.5v8M4.75 7.5 8 10.75l3.25-3.25M3 13.5h10" />
  </Icon>
);
export const TurnLeftIcon = () => (
  <Icon>
    <path d="M3 8a5 5 0 1 0 1.6-3.65" />
    <path d="M2.75 2.5v2.75H5.5" />
  </Icon>
);
export const TurnRightIcon = () => (
  <Icon>
    <path d="M13 8a5 5 0 1 1-1.6-3.65" />
    <path d="M13.25 2.5v2.75H10.5" />
  </Icon>
);
export const ResetIcon = () => (
  <Icon>
    <path d="M2.5 6.5 8 3.5l5.5 3L8 9.5z" />
    <path d="m2.5 9.5 5.5 3 5.5-3" />
  </Icon>
);
export const CopyIcon = () => (
  <Icon>
    <rect x="5.5" y="5.5" width="8" height="8" rx="1.5" />
    <path d="M10.5 3.5v-1h-8v8h1" />
  </Icon>
);
export const SunIcon = () => (
  <Icon>
    <circle cx="8" cy="8" r="2.75" />
    <path d="M8 1.75v1.5M8 12.75v1.5M1.75 8h1.5M12.75 8h1.5M3.6 3.6l1.05 1.05M11.35 11.35l1.05 1.05M3.6 12.4l1.05-1.05M11.35 4.65l1.05-1.05" />
  </Icon>
);
export const MoonIcon = () => (
  <Icon>
    <path d="M13.25 9.75A5.75 5.75 0 0 1 6.25 2.75a5.75 5.75 0 1 0 7 7z" />
  </Icon>
);
