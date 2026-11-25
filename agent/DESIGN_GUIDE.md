# Bloomberg Minimal / Editorial Desk

A portable design and implementation guide for building interfaces that match the public UI of `personalweb`.

This guide is intentionally opinionated. It covers the design language, tokens, typography, layout, components, motion, media, accessibility, copy rules, and a porting checklist. Use it when another application needs to adopt the same visual system.

Reference implementation:

- `app/globals.css`
- `components/ui/button.tsx`
- `components/ui/badge.tsx`
- `components/ui/input.tsx`
- `components/ui/textarea.tsx`
- `components/ui/select.tsx`
- `components/page-shell.tsx`
- `components/sidebar.tsx`
- `components/mobile-sidebar.tsx`
- `components/themeSwitch.tsx`
- `components/shuffle-link.tsx`
- `components/shuffle-text.tsx`
- `components/rotating-hero-headline.tsx`
- `components/rotating-hero-text.tsx`
- `components/rotating-shuffle-text.tsx`
- `components/project-grid.tsx`
- `components/project-card.tsx`
- `components/project-media.tsx`
- `components/lazy-video.tsx`
- `components/article-row.tsx`
- `components/section-heading.tsx`
- `components/site-footer.tsx`
- `app/page.tsx`
- `app/pr/page.tsx`
- `app/blog/page.tsx`
- `app/blog/[slug]/page.tsx`
- `app/not-found.tsx`

Companion project-specific document: `design.md`.

---

## 1. Design DNA

### 1.1 What this system is

A dense, editorial, monochrome interface inspired by financial terminals and print desks.

The UI should feel:

- factual
- fast
- typographic
- restrained
- slightly technical
- durable rather than trendy

It is not:

- a SaaS dashboard with pastel cards
- a glassmorphism demo
- a neo-brutalist poster
- a landing page with a giant gradient hero
- a collection of floating rounded cards

### 1.2 Core principles

1. Information first.
2. Typography and spacing carry hierarchy before decoration.
3. Content cards stay flat. Only interactive controls get subtle depth.
4. Color is content, not chrome. Project media, social icons, and skill logos may be colorful; the surrounding UI stays monochrome.
5. Use one clear interaction behavior per control.
6. Motion explains state change. It must not decorate every section.
7. Respect `prefers-reduced-motion`.
8. Keep public pages fast and mostly static.
9. Prefer a hard edge for layout surfaces and a soft edge for controls.
10. Remove decorative punctuation and separator lines.
11. One ambient accent is allowed: the top-band pointer dot grid with its slow light bloom. It stays behind the hero and Stack, low-contrast, fades into the page background, and never becomes a full-page canvas.

### 1.3 The balance

The system deliberately mixes:

- sharp project cards
- rounded buttons and pills
- flat content surfaces
- subtly raised controls
- monochrome chrome
- full-color media

That contrast is the design. Do not round everything or flatten everything.

---

## 2. Foundations

### 2.1 Color system

The system is built on semantic CSS custom properties, mapped into Tailwind 4 with `@theme inline`.

Base tokens use OKLCH for neutral surfaces. Button depth tokens use `rgb()` because they are translucent highlights and shadows.

```css
@import "tailwindcss";

@custom-variant dark (&:is(.dark *));

@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-card: var(--card);
  --color-card-foreground: var(--card-foreground);
  --color-popover: var(--popover);
  --color-popover-foreground: var(--popover-foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  --color-secondary: var(--secondary);
  --color-secondary-foreground: var(--secondary-foreground);
  --color-muted: var(--muted);
  --color-muted-foreground: var(--muted-foreground);
  --color-accent: var(--accent);
  --color-accent-foreground: var(--accent-foreground);
  --color-destructive: var(--destructive);
  --color-border: var(--border);
  --color-input: var(--input);
  --color-ring: var(--ring);

  --font-sans: var(--font-geist-sans);
  --font-mono: var(--font-geist-mono);
  --font-heading: var(--font-geist-sans);

  --radius-sm: calc(var(--radius) * 0.6);
  --radius-md: calc(var(--radius) * 0.8);
  --radius-lg: var(--radius);
  --radius-xl: calc(var(--radius) * 1.4);
  --radius-2xl: calc(var(--radius) * 1.8);
  --radius-3xl: calc(var(--radius) * 2.2);
  --radius-4xl: calc(var(--radius) * 2.6);
}
```

#### Light tokens

```css
:root {
  --background: oklch(0.955 0 0);
  --foreground: oklch(0.145 0 0);
  --card: oklch(0.985 0 0);
  --card-foreground: oklch(0.145 0 0);
  --popover: oklch(0.985 0 0);
  --popover-foreground: oklch(0.145 0 0);
  --primary: oklch(0.145 0 0);
  --primary-foreground: oklch(0.955 0 0);
  --secondary: oklch(0.92 0 0);
  --secondary-foreground: oklch(0.145 0 0);
  --muted: oklch(0.92 0 0);
  --muted-foreground: oklch(0.45 0 0);
  --accent: oklch(0.92 0 0);
  --accent-foreground: oklch(0.145 0 0);
  --destructive: oklch(0.577 0.245 27.325);
  --border: oklch(0.86 0 0);
  --input: oklch(0.86 0 0);
  --ring: oklch(0.55 0 0);

  --button-sheen: rgb(255 255 255 / 0.12);
  --button-sheen-stop: 55%;
  --button-shadow:
    inset 0 1px 0 rgb(255 255 255 / 0.08),
    0 1px 1px rgb(0 0 0 / 0.06),
    0 4px 10px -8px rgb(0 0 0 / 0.28);
  --button-shadow-hover:
    inset 0 1px 0 rgb(255 255 255 / 0.10),
    0 1px 1px rgb(0 0 0 / 0.08),
    0 6px 14px -8px rgb(0 0 0 / 0.34);

  --radius: 0.25rem;
}
```

#### Dark tokens

```css
.dark {
  --background: oklch(0.145 0 0);
  --foreground: oklch(0.965 0 0);
  --card: oklch(0.19 0 0);
  --card-foreground: oklch(0.965 0 0);
  --popover: oklch(0.19 0 0);
  --popover-foreground: oklch(0.965 0 0);
  --primary: oklch(0.965 0 0);
  --primary-foreground: oklch(0.145 0 0);
  --secondary: oklch(0.22 0 0);
  --secondary-foreground: oklch(0.965 0 0);
  --muted: oklch(0.22 0 0);
  --muted-foreground: oklch(0.68 0 0);
  --accent: oklch(0.22 0 0);
  --accent-foreground: oklch(0.965 0 0);
  --destructive: oklch(0.704 0.191 22.216);
  --border: oklch(0.28 0 0);
  --input: oklch(0.28 0 0);
  --ring: oklch(0.55 0 0);

  --button-sheen: rgb(255 255 255 / 0.10);
  --button-sheen-stop: 58%;
  --button-shadow:
    inset 0 1px 0 rgb(255 255 255 / 0.10),
    0 0 12px -10px rgb(255 255 255 / 0.12),
    0 1px 2px rgb(0 0 0 / 0.55);
  --button-shadow-hover:
    inset 0 1px 0 rgb(255 255 255 / 0.12),
    0 0 16px -10px rgb(255 255 255 / 0.16),
    0 1px 2px rgb(0 0 0 / 0.55);
}
```

If you also use the full shadcn primitive set, copy the sidebar and chart token mappings from `app/globals.css`.

### 2.2 Color usage rules

- The UI chrome is monochrome.
- Body background is near-white in light mode and near-black in dark mode.
- Project images and videos keep their original color.
- Social icons and skill-scroll logos keep their brand colors.
- The personal portrait remains grayscale.
- Destructive red is functional and admin-only.
- Do not use colored gradients for buttons.
- Do not use colored glows.
- Do not use pure black `#000` or pure white `#fff` for large surfaces.

### 2.3 Radius system

`--radius` is `0.25rem`.

| Token | Formula | Approximate value | Use |
|---|---|---:|---|
| `rounded-sm` | `0.6 × radius` | `0.15rem` | tiny chips inside controls |
| `rounded-md` | `0.8 × radius` | `0.20rem` | legacy only |
| `rounded-lg` | `1 × radius` | `0.25rem` | code blocks, images |
| `rounded-xl` | `1.4 × radius` | `0.35rem` | textarea, menu items |
| `rounded-2xl` | `1.8 × radius` | `0.45rem` | popovers, dialogs |
| `rounded-3xl` | `2.2 × radius` | `0.55rem` | large panels |
| `rounded-4xl` | `2.6 × radius` | `0.65rem` | buttons, inputs, badges |

Rules:

- Buttons, inputs, selects, and badges use `rounded-4xl`.
- Skill pills use the badge radius, which visually becomes a pill at badge height.
- Textareas use `rounded-xl`.
- Dialogs and popovers use `rounded-2xl` or `rounded-4xl` depending on the primitive.
- Project cards remain square.
- Do not apply a global large radius to content cards.

### 2.4 Typography

Fonts:

- UI and body: Geist Sans.
- Metadata, dates, technical labels, public button labels: Geist Mono.

Load with `next/font/google`:

```tsx
const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
});
```

Scale:

| Role | Classes | Notes |
|---|---|---|
| Hero H1 | `text-4xl sm:text-5xl font-medium leading-[1.05] tracking-tight` | no giant `7rem` hero |
| Page H1 | `text-3xl sm:text-4xl font-medium tracking-tight` | Work, Notes, Article |
| Article H1 | `text-3xl sm:text-4xl font-medium leading-tight tracking-tight` | long titles wrap |
| Project title | `text-base font-medium leading-snug tracking-tight` | `h2` |
| Section heading | `text-sm font-medium tracking-tight` | no uppercase eyebrow |
| Body | `text-sm leading-relaxed` | UI body |
| Article body | `text-base leading-relaxed` via prose | comfortable line length |
| Metadata | `font-mono text-[10px]` or `text-[11px]` | dates, labels, footer |
| Public button | `font-mono text-sm font-medium` | ink buttons; 44px tall |
| Skill pill | `font-mono text-[10px]` | project cards |

Rules:

- Use `tracking-tight` sparingly.
- Avoid extreme negative letter spacing.
- Do not use all-caps mono eyebrows.
- Do not use numbered section labels.
- Do not use decorative separators in metadata.
- Use colons only in metadata titles where needed.
- Keep body line length around `max-w-2xl`.

### 2.5 Spacing and layout

Base spacing is 4px via Tailwind.

Page shell:

```tsx
<main
  id="content"
  className="mx-auto w-full max-w-5xl px-5 pb-16 pt-20 sm:px-8 lg:px-10 lg:pt-12"
>
  {children}
</main>
```

- Max width: `max-w-5xl`.
- Horizontal padding: `px-5` mobile, `sm:px-8`, `lg:px-10`.
- Mobile top padding: `pt-20` (5rem) to clear the 4rem fixed header with 1rem breathing room.
- Desktop top padding: `lg:pt-12` (3rem).
- Bottom padding: `pb-16` (4rem).
- Footer top margin: `mt-16` (4rem).

Desktop shell:

- Fixed sidebar at `left-6 top-6`.
- Sidebar width: `w-40` (10rem).
- Main content offset: `lg:pl-52` (13rem).
- Content starts at `lg:pt-12`.

Mobile shell:

- Fixed top bar: `h-16`.
- Page content begins at `pt-20`.
- Drawer padding: `pt-24 pb-6`.

Vertical rhythm:

| Area | Value |
|---|---|
| Hero paragraph to GPA stat | `mt-4` |
| GPA stat to CTA row | `mt-5` |
| CTA row to socials | `mt-7` |
| Hero to Stack | `mt-14` |
| Stack heading to marquee | `mt-3 py-3` |
| Stack to About | `mt-12` |
| About to contact | `mt-12` |
| Contact internal top padding | `pt-4` |
| Footer top | `mt-16` |
| Section heading bottom | `mb-4` |
| Work/Notes list start | `mt-8` |
| Article grid gap | `gap-8` |
| Article description | `mt-4` |
| Article body | `mt-7` |
| Article sidebar list | `mt-5` |
| Article sticky top | `lg:top-8` |
| Article row padding | `py-6` |
| Empty state padding | `py-8` |

Rules:

- Remove excess, but do not compress into a dashboard.
- Reduce the largest gaps by one step before touching micro-spacing.
- Do not use horizontal separators to create rhythm.
- Do not use `mt-24` for public sections.
- Keep footer breathing room even after tightening.

### 2.6 Surfaces, borders, and depth

- Content cards: flat, border-only, no shadow, no blur, square corners.
- Interactive controls: rounded, subtle sheen/shadow, no glassmorphism.
- Borders: `border-border` for structure; `border-foreground/30` for card hover.
- No horizontal separator lines in public layout.
- No card shadows except the button skin.
- Media frames can be square and flat.
- Hover depth belongs to controls, not content.

Button depth utility:

```css
.button-skin {
  background-image: linear-gradient(
    180deg,
    var(--button-sheen),
    transparent var(--button-sheen-stop)
  );
  box-shadow: var(--button-shadow);
}

.button-skin:hover {
  box-shadow: var(--button-shadow-hover);
}

/* Inverted solid hover surface: dark/light fill with the same top sheen. */
.button-fill {
  background-color: var(--background);
  background-image: linear-gradient(
    180deg,
    var(--button-sheen),
    transparent var(--button-sheen-stop)
  );
  box-shadow: inset 0 1px 0 var(--button-fill-highlight);
}
```

Token:

```css
:root {
  --button-fill-highlight: transparent;
}

.dark {
  --button-fill-highlight: rgb(255 255 255 / 0.12);
}
```

Light mode intent:

- faint top sheen
- soft black shadow
- no glow

Dark mode intent:

- faint top sheen
- inner top highlight
- very soft white glow
- no colored glow

---

## 3. Button system

### 3.1 Variants

| Variant | Use | Depth |
|---|---|---|
| `default` | primary action, active nav | `button-skin` |
| `outline` | secondary action, Edit, Go Back | `button-skin` |
| `secondary` | muted action | `button-skin` |
| `destructive` | delete | `button-skin` |
| `ghost` | cancel, icon close | flat |
| `link` | inline text action | flat |

### 3.2 Sizes

| Size | Height | Use |
|---|---:|---|
| `xs` | `h-6` | tiny admin actions |
| `sm` | `h-8` | compact admin actions |
| `default` | `h-9` | standard |
| `lg` | `h-10` | prominent CTA |
| `icon` | `size-9` | icon-only |
| `icon-xs` | `size-6` | compact icon |
| `icon-sm` | `size-8` | dialog close |
| `icon-lg` | `size-10` | large icon |

Public ink buttons use `h-11` (44px) directly rather than the shared Button size.

### 3.3 Base classes

```tsx
const buttonVariants = cva(
  "group/button inline-flex shrink-0 items-center justify-center rounded-4xl border bg-clip-padding text-sm font-medium whitespace-nowrap transition-all outline-none select-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 active:not-aria-[haspopup]:translate-y-px disabled:pointer-events-none disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-[3px] aria-invalid:ring-destructive/20 dark:aria-invalid:border-destructive/50 dark:aria-invalid:ring-destructive/40 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  {
    variants: {
      variant: {
        default:
          "button-skin border-primary-foreground/15 bg-primary text-primary-foreground hover:border-primary-foreground/25 hover:bg-primary/90",
        outline:
          "button-skin border-foreground/15 bg-input/30 hover:border-foreground/25 hover:bg-input/50 hover:text-foreground aria-expanded:bg-muted aria-expanded:text-foreground",
        secondary:
          "button-skin border-foreground/15 bg-secondary text-secondary-foreground hover:border-foreground/25 hover:bg-secondary/90 aria-expanded:bg-secondary aria-expanded:text-secondary-foreground",
        ghost:
          "border-transparent hover:bg-muted hover:text-foreground aria-expanded:bg-muted aria-expanded:text-foreground dark:hover:bg-muted/50",
        destructive:
          "button-skin border-destructive/25 bg-destructive/10 text-destructive hover:border-destructive/35 hover:bg-destructive/20 focus-visible:border-destructive/40 focus-visible:ring-destructive/20 dark:bg-destructive/20 dark:hover:bg-destructive/30 dark:focus-visible:ring-destructive/40",
        link: "border-transparent text-primary underline-offset-4 hover:underline",
      },
    },
  },
);
```

#### Border treatment

Border is always `1px` and low-opacity. It should be visible on inspection, not from across the room.

| Control | Border | Hover |
|---|---|---|
| Solid/default | `border-primary-foreground/15` | `/25` |
| Outline | `border-foreground/15` | `/25` |
| Secondary | `border-foreground/15` | `/25` |
| Destructive | `border-destructive/25` | `/35` |
| Public ink solid | `border-background/20` | `/30` |
| Public ink outline | `border-foreground/20` | `/35` |
| Icon controls | `border-foreground/15` | `/30` |
| Ghost/link | `border-transparent` | none |

Why it works:

- `primary-foreground/15` contrasts with the solid fill in both themes.
- `background/20` gives the public solid button a defined rim.
- The light shadow includes `inset 0 1px 0 rgb(255 255 255 / 0.08)` so the top edge catches light without a halo.
- Hover increases opacity by about 10 points, never jumps to full opacity.

Do not:

- use `border-foreground/70`
- use full-opacity `border-foreground`
- use 2px borders
- add a second ring on top of the border

### 3.4 Public ink button recipe

File: `components/shuffle-link.tsx`

```tsx
<Comp
  className={cn(
    "button-skin group relative inline-flex h-11 items-center justify-center gap-2.5 overflow-hidden rounded-4xl border bg-clip-padding px-5 font-mono text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
    tone === "outline"
      ? "border-foreground/20 bg-background text-foreground hover:border-background/20"
      : "border-background/20 bg-foreground text-background hover:border-foreground/20",
    className,
  )}
>
  <span
    aria-hidden
    className={cn(
      "absolute inset-0 -translate-y-full transition-transform duration-300 ease-[cubic-bezier(.22,1,.36,1)] group-hover:translate-y-0 group-focus-visible:translate-y-0",
      tone === "outline" ? "bg-foreground" : "button-fill",
    )}
  />
  <span className="relative z-10 flex items-center gap-2.5 text-white mix-blend-difference">
    <ShuffleText text={label} trigger={trigger} />
    <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
  </span>
</Comp>
```

Behavior:

- Text scrambles on hover/focus.
- A solid panel fills from top over 300ms.
- Solid fill uses `.button-fill`, not flat `bg-background`. It has the same top sheen and inset highlight as the black button.
- Border flips with the fill:
  - solid: rest `border-background/20`, hover `border-foreground/20`
  - outline: rest `border-foreground/20`, hover `border-background/20`
- Label and icon use `text-white` plus `mix-blend-difference`.
- The blend inverts per pixel against the fill, so contrast stays correct while the fill is partially covering the button.
- Keep the label at mono `text-sm` medium. The old 11px tight-tracked label blurred on 1x displays.
- Keep the sheen and dark-mode glow reduced. Large white halos read as blur, not depth.
- Do not restore `group-hover:text-*` on the content span.
- Do not add `isolate` to the button; outline buttons need the page backdrop for the blend.
- Arrow moves diagonally.
- Focus ring is visible.
- External links use `ArrowUpRight` and open in a new tab.

### 3.5 Nav button recipe

- Use `buttonVariants`.
- Active: `default` variant, `rounded-4xl`, `button-skin`.
- Inactive: `ghost` variant, flat.
- Full width.
- Left aligned.
- No separate active border.
- No two-icon theme track.

### 3.6 Button do and do not

Do:

- use `rounded-4xl`
- keep sheen and shadow subtle
- keep monochrome depth
- keep visible focus rings
- use `/90` hover for solid/secondary
- use `text-white mix-blend-difference` for fill-sweep button content

Do not:

- use fully circular pills for text buttons
- use heavy drop shadows
- use colored gradients
- use glassmorphism
- apply depth to ghost/link buttons
- round project cards to match buttons
- animate label color with `group-hover:text-*` during a fill sweep

---

## 4. Forms, badges, and admin controls

### 4.1 Inputs

```tsx
<input
  className="h-9 w-full min-w-0 rounded-4xl border border-input bg-input/30 px-3 py-1 text-base transition-colors outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 md:text-sm"
/>
```

### 4.2 Textareas

- `rounded-xl`
- `bg-input/30`
- `border-input`
- `resize-none`
- `min-h-16`

### 4.3 Selects

- `rounded-4xl`
- `h-9`
- `bg-input/30`
- `border-input`
- focus ring

### 4.4 Dialogs

- `rounded-4xl`
- `bg-popover`
- `ring-1 ring-foreground/5`
- no heavy shadow
- overlay uses `bg-black/80` and optional light backdrop blur

### 4.5 Badges and skill pills

Badge base:

- `inline-flex`
- `h-5`
- `rounded-4xl`
- `border border-transparent`
- `px-2 py-0.5`
- `text-xs font-medium`

Skill pill recipe:

```tsx
<Badge
  variant="outline"
  className="font-mono text-[10px] font-normal text-muted-foreground"
>
  {skill}
</Badge>
```

Result:

- `border-border`
- `bg-input/30`
- rounded pill
- mono metadata type
- muted text
- no sharp square tags

Do not use solid accent-color skill pills on public pages.

---

## 5. Media

### 5.1 Project media

- Full color. No grayscale filter.
- `object-cover`.
- Aspect ratio: 16:9 on mobile, 2:1 from `sm`.
- Media may scale to `1.03` on card hover.
- The card itself does not scale.
- Blob and local images use `next/image`.
- External hosts fall back to `<img loading="lazy" decoding="async">`.
- Videos use `LazyVideo`.

Image recipe:

```tsx
<Image
  src={media.src}
  alt={media.alt || title}
  fill
  sizes="(min-width: 640px) 50vw, 100vw"
  quality={75}
  className="object-cover transition-transform duration-500 ease-out group-hover:scale-[1.03]"
/>
```

Video recipe:

```tsx
<LazyVideo
  src={media.src}
  autoPlay={media.autoPlay ?? false}
  loop={media.loop ?? false}
  muted={media.muted ?? true}
  controls={false}
  label={`${title} preview`}
  className="transition-transform duration-500 ease-out group-hover:scale-[1.03]"
/>
```

### 5.2 Portrait

- The personal portrait remains grayscale.
- Use `next/image` with `priority`, `sizes="192px"`, `quality={85}`.
- Square frame with a border.
- No rounded portrait.

### 5.3 Lazy video behavior

- IntersectionObserver with 200px root margin.
- Source attached only near viewport.
- `preload="none"` before load, `metadata` after.
- Autoplay only when in view.
- Pause offscreen.
- No autoplay under reduced motion.
- `playsInline`.
- Controls only when reduced motion is enabled.

---

## 6. Motion

### 6.1 Easing and duration

| Motion | Duration | Easing |
|---|---:|---|
| Button fill sweep | 300ms | `cubic-bezier(.22,1,.36,1)` |
| Button arrow | 300ms | default |
| Button depth hover | 150-260ms | ease |
| Theme wipe | 480ms | `cubic-bezier(.22,1,.36,1)` |
| Hero phrase hold | 4800ms | none |
| Hero word reveal | 560ms | `cubic-bezier(.22,1,.36,1)` |
| Hero word stagger | 55ms | none |
| Hero focus pull | 760ms | `easeOutCubic` |
| Button text scramble | 30ms per frame | stepped |
| Skill marquee | 34s loop | linear |
| Journey meta reveal | scroll `entry 0%` → `cover 28%` | linear |
| Journey title reveal | scroll `entry 0%` → `cover 38%` | linear |
| Journey body reveal | scroll `entry 8%` → `cover 50%` | linear |
| Pointer grid follow | continuous while moving | lerp 0.2 |
| Pointer grid wave | 28s alternate | ease-in-out |

### 6.2 Hero rotating text

Components:

- `components/rotating-hero-headline.tsx` coordinates the pair and the height sizer.
- `components/rotating-hero-text.tsx` renders the lead.
- `components/rotating-shuffle-text.tsx` renders the tail.

Paired copy:

1. `I build fast, useful software` / `for the web`
2. `I make ideas feel native` / `for mobile`
3. `I simplify messy workflows` / `for business`
4. `I turn research into products` / `for AI`
5. `I sweat the small details` / `for us`
6. `I write code with care` / `for humans`

Behavior:

- One timer and one index; both lines always change together.
- Static `I` prefix on the lead.
- Hold each pair for 4800ms.
- Lead: 560ms word-mask reveal with a 55ms stagger.
- Tail: 760ms per-character focus pull.
- First pair is stable in initial HTML.
- No random glyphs in the hero.
- Use `aria-live="off"` on the tail and `aria-label` with the current tail phrase.
- Respect reduced motion; show the first pair statically.
- Height:
  - A CSS grid stacks an invisible sizer and the active pair in the same cell.
  - The sizer uses the tallest pair by character count.
  - The active pair is top-aligned; spare height stays below the tail, not between the lines.
  - The paragraph below the H1 keeps the same `top` across all pairs.

Lead reveal:

- Per-word mask reveal:
  - opacity `0` → `1`
  - translateY `120%` → `0`
  - scale `0.97` → `1`
  - blur `4px` → `0`
  - 55ms stagger.
- Use a `clip-path` mask, not `overflow-hidden`, to preserve the inline-block baseline.

Tail reveal:

- Per-character focus pull from left to right.
- Character state:
  - opacity `0.12` → `1`
  - blur `1.2px` → `0`
  - translateY `0.08em` → `0`
- Use `requestAnimationFrame`.
- Use `easeOutCubic`.

Character style:

```tsx
<span
  className="inline-block whitespace-pre"
  style={{
    opacity: 0.12 + glyph.progress * 0.88,
    filter: `blur(${(1 - glyph.progress) * 1.2}px)`,
    transform: `translateY(${(1 - glyph.progress) * 0.08}em)`,
  }}
>
  {glyph.char === " " ? "\u00A0" : glyph.char}
</span>
```

### 6.3 Button text shuffle

Component: `components/shuffle-text.tsx`

- Triggered by hover or focus.
- Scrambles only while trigger is active.
- Charset is lowercase alphanumerics from `lib/motion.ts`.
- Frame interval: 30ms.
- `totalFrames = letters.length * 4`.
- Reduced motion shows the final text immediately.
- Do not use punctuation glyphs.

### 6.4 Button fill sweep

- A span is absolutely positioned over the button.
- Starts at `-translate-y-full`.
- Moves to `translate-y-0` on hover/focus.
- 300ms.
- Solid fill uses `.button-fill`: `--background` plus the same top sheen and inset highlight as the black button.
- Outline fill uses `bg-foreground`.
- Border flips with the fill so the rim always contrasts with the fill.
- The label and icon sit above it with `z-10`.
- Label and icon use `text-white` plus `mix-blend-difference`.
- The blend inverts per pixel against the moving fill, so contrast stays correct while the fill is partially covering the button.
- Outline tone uses `bg-background` to provide an opaque blend backdrop. Do not make outline buttons transparent.
- Do not restore `group-hover:text-*` on the content span.
- Do not add `isolate` to the button; outline buttons need the page/background backdrop for the blend.

### 6.5 Theme wipe

- Uses the View Transition API.
- Theme switch measures its own center.
- Sets `--theme-x` and `--theme-y`.
- Circular clip-path wipe from the button.
- 480ms.
- Falls back to instant theme change when reduced motion is on or View Transitions are unavailable.
- Only one icon exists in the DOM at a time: sun in light, moon in dark.

### 6.6 Skill marquee

- Two rows.
- Opposite directions.
- 34 second linear loop.
- Pause on hover.
- Masked edges.
- Stops under reduced motion.

### 6.7 Journey timeline

Files: `lib/journey.ts`, `components/journey-timeline.tsx`, `app/globals.css`

- Server-rendered content; no client JavaScript and no motion library.
- Each entry declares a named view timeline:

```css
.journey-entry {
  view-timeline-name: --journey-entry;
  view-timeline-axis: block;
}
```

- Descendants animate against that timeline:
  - meta: `entry 0%` to `cover 28%`, fade and 12px rise
  - title: `entry 0%` to `cover 38%`, masked rise from `translateY(108%)`
  - body: `entry 8%` to `cover 50%`, fade and 20px rise
- The masked title wrapper uses `overflow: hidden` with `0.12em` vertical padding and a matching negative margin so descenders stay visible.
- Only transform and opacity animate. Do not add scroll-linked blur to the list.
- The chapter label is `sticky top-8` from `lg`.
- All animation rules live inside `@supports (animation-timeline: view())`. Browsers without support see the static, fully visible content.
- Under reduced motion, set `animation: none` and restore `opacity: 1; transform: none`.

### 6.8 Pointer grid

Files: `components/pointer-grid.tsx`, `app/globals.css`

- Homepage top-band ambient accent behind the hero and Stack.
- Base layer: a 36px radial dot grid at `color-mix(in oklab, var(--foreground) 7%, transparent)` with 1.25px dots.
- Wave layer: the same grid at 10%, clipped by a large radial bloom. The mask moves over 28s with `ease-in-out` and `alternate`; `data-inview` pauses it offscreen, and `data-active` raises its opacity to 1.
- Active layer: the same grid at 20%, clipped by `radial-gradient(circle 420px at var(--grid-x) var(--grid-y), black 0%, black 30%, transparent 75%)`.
- A background-colored gradient overlay (`.pointer-grid__fade`) fades the grid into the page at the left, right, top, and bottom edges. There is no hard box.
- The layer is full-bleed behind the hero and Stack; on desktop it starts after the sidebar. Height is `120vh` on mobile and `min(52rem, 88vh)` from `lg`.
- `pointer-events-none`, `aria-hidden`, behind the page content.
- The pointer listener sits on the homepage wrapper, but activation is checked against the grid layer bounds.
- Coordinates are relative to the grid layer. A rAF lerp of 0.2 follows the pointer and stops once the delta is under 0.4px. Pointer leave, pointer cancel, and window blur reset the active state.
- Fine pointer only. Touch pointer events are ignored.
- `prefers-reduced-motion` hides the wave and active layers; the base grid stays.
- Without JavaScript, only the static base grid renders; the wave stays paused.
- Do not make it full-page, place it above content, or turn it into a cursor follower outside the grid band.

### 6.9 Reduced motion

Global rule:

```css
@media (prefers-reduced-motion: reduce) {
  html {
    scroll-behavior: auto;
  }

  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }

  .marquee-left,
  .marquee-right {
    animation: none;
  }
}
```

Additional behavior:

- Hero shows the final phrase instantly.
- Button text does not scramble.
- Journey entries are fully visible with no reveal.
- The pointer grid wave and spotlight are hidden; the base grid stays static.
- Video autoplay is disabled.
- Theme wipe is skipped.
- Smooth scroll is disabled.

---

## 7. Components

### 7.1 PageShell

- Semantic `<main id="content">`.
- Max width `5xl`.
- Responsive horizontal padding.
- Tighter top/bottom spacing.
- Skip link target.
- No separator lines.

### 7.2 Sidebar

- Fixed desktop rail.
- `left-6 top-6`.
- `w-40`.
- Hidden below `lg`.
- Theme switch at top.
- Three nav buttons: About, Work, Notes.
- Active nav uses default button variant.
- Inactive nav uses ghost.
- Hover/focus triggers text shuffle.
- Footer links: email, github, copyright.
- No monogram.
- No location, clock, or status block.

### 7.3 MobileSidebar

- Fixed top bar, `h-16`.
- Full name on the left.
- Theme switch and menu toggle on the right.
- Menu toggle is a bordered square with `rounded-xl`.
- Full-screen overlay menu.
- Drawer `pt-24 pb-6`.
- Body scroll lock.
- Menu closes on route change.
- `aria-expanded` and `aria-controls`.

### 7.4 ThemeSwitch

- Circular button, `h-9 w-9`.
- `rounded-full`.
- `button-skin`.
- One icon only.
- Uses `resolvedTheme`.
- Uses `flushSync` inside the View Transition callback.
- Sets `--theme-x` and `--theme-y`.
- `role="switch"`, `aria-checked`, label, title.

### 7.5 ShuffleLink

- Client component.
- Props: `href`, `label`, `appearance`, `tone`, `active`, `external`.
- Ink appearance: 44px rounded public CTA with fill sweep and button skin.
- Label is mono `text-sm` medium; the arrow is 16px.
- Nav appearance: full-width nav button using `buttonVariants`.
- External links open in a new tab with `rel="noopener noreferrer"`.
- `aria-current="page"` when active.

### 7.5b JourneyTimeline

- Server component.
- Renders Education, Experience, and Achievements from `lib/journey.ts`.
- Static content; no database query.
- Mobile: label above the entries.
- Tablet: label beside the entries, not sticky, so it stays clear of the fixed header.
- Desktop: `9rem` label rail with a sticky chapter heading.
- Flat entries with mono period, `text-xl sm:text-2xl` title, organization, detail, and optional outline badges.
- Scroll-driven masked title and delayed body; see 6.7.

### 7.5c PointerGrid

- Client component, homepage top band only.
- Renders a static base dot grid, a slow radial bloom, and a pointer-reactive active layer.
- The wave uses a 28s alternate mask and pauses when the grid band is offscreen.
- The active layer is a radial mask that follows the pointer with a short lerp.
- A background-colored gradient overlay fades the grid into the page at every edge.
- `aria-hidden` and `pointer-events-none`; page content sits above it.
- Runs only for a fine pointer; touch is ignored.
- Reduced motion hides the wave and active layers.
- No dependency, no canvas, no layout impact.

### 7.6 RotatingShuffleText

- Client component.
- Six phrases, 4800ms hold, 760ms focus pull.
- Stable first phrase on load.
- No random glyphs in the hero.
- Uses `useSyncExternalStore` for reduced-motion changes.
- Keeps per-character layout width stable.

### 7.7 ProjectGrid

- CSS columns, not JS masonry.
- One column on mobile.
- Two columns from `sm`.
- `gap-4`.
- Cards use `break-inside-avoid`.

### 7.8 ProjectCard

- `<article>` with `group`.
- Flat, square, border-only.
- `bg-card/50`.
- Hover strengthens border to `foreground/30`.
- No card shadow, blur, or scale.
- Title `h2`.
- Description `text-sm text-muted-foreground`.
- Skills as Badge outline pills.
- Full-width `Open` ShuffleLink when `href` exists.
- No separator lines.

### 7.9 ProjectMedia

- Colored media.
- 16:9 mobile, 2:1 desktop.
- `next/image` or lazy video.
- External image fallback.
- Media scales on card hover.

### 7.10 LazyVideo

- IntersectionObserver.
- Loads near viewport.
- Autoplay only in view.
- Pauses offscreen.
- Respects reduced motion.
- `playsInline`.

### 7.11 ArticleRow

- Grid: date, title/description, arrow.
- No top border.
- Hover background.
- `py-6`.
- Mono date.
- Arrow moves diagonally on hover.

### 7.12 SectionHeading

- `mb-4`.
- No index number.
- No bottom border.
- `text-sm font-medium`.
- Optional action on the right in mono.

### 7.13 SiteFooter

- `mt-16`.
- No top border.
- Left: copyright.
- Right: email, work, notes, github.
- Mono small text.

---

## 8. Page templates

### 8.1 Home

- Static page, no database query.
- Hero rotates fixed `I ...` / `for ...` pairs; the lead is foreground, the tail is muted.
- Full-bleed pointer dot grid behind the hero and Stack; the page content stays above it and the grid fades into the background before About.
- One short paragraph.
- Academic stat line: `GPA` label plus `3.75 / 4.00`, mono, no card or border.
- CTA row: `Email me`, `Work`.
- Colored social icons.
- Grayscale portrait.
- Stack section with colored marquee.
- About section with two paragraphs.
- Journey section with Education, Experience, and Achievements from static content.
- Contact line and `Start a conversation`.
- Footer.
- JSON-LD Person and WebSite.

Spacing:

- Hero paragraph to GPA stat `mt-4`.
- GPA stat to CTA `mt-5`.
- Socials `mt-7`.
- Stack `mt-14`.
- Marquee `mt-3 py-3`.
- About `mt-12`.
- Journey wrapper `mt-14`.
- Contact `mt-12 pt-4`.

### 8.2 Work

- URL can be anything; in this project it is `/pr`.
- H1: `Work`.
- Short descriptive paragraph.
- Masonry project cards.
- List starts at `mt-8`.
- Footer.

### 8.3 Notes

- H1: `Notes`.
- Short descriptive paragraph.
- Article rows.
- List starts at `mt-8`.
- Empty state `py-8`.
- Footer.

### 8.4 Article

- Desktop left metadata rail.
- Mobile compact metadata row.
- Grid gap `gap-8`.
- Sticky rail `lg:top-8`.
- Description `mt-4`.
- Prose `mt-7`.
- Max prose width `max-w-2xl`.
- JSON-LD BlogPosting and BreadcrumbList.
- Footer.

### 8.5 404

- Page shell.
- Small `Page not found` label.
- Large 404.
- Short explanation.
- Back home button with shuffle.
- No divider line.

### 8.6 Admin

Admin is an extension of the same design language, not a separate dashboard theme.

Shell:

- Dedicated admin rail on desktop, mirroring the public shell.
- Theme switch at the top, `Admin` label, then Overview, Work, Notes, CV.
- Mono footer links for `view site` and `sign out`.
- Mobile top bar plus full-screen drawer with body scroll lock.
- Hide the public rail on admin routes.
- Admin content uses the same width and top padding as the public page shell.

Pages:

- Dashboard uses square, border-only tiles with mono counts.
- Lists use flat editorial rows and hover backgrounds, not shadowed cards.
- Work uses a two-column dialog: form on the left, live public `ProjectCard` preview on the right.
- CV is a visual consistency pass. Keep the document preview layout intact.
- Login is a centered two-step form with rounded inputs, a theme switch, and no glassmorphism.

Note editor:

- Paper layout with inline title, description, and slug.
- Slash menu for block insertion.
- Bubble menu for inline formatting.
- Link and image dialogs instead of browser prompts.
- Word count, reading time, publish switch, `Cmd/Ctrl + S`.
- Plain-text Markdown paste converts to formatted blocks with `markdown-it`.
- Markdown support includes headings, lists, task lists, quotes, code fences, links, images, dividers, and GFM tables.
- Rich clipboard HTML is left to ProseMirror.
- Tables use Tiptap table extensions and an overflow wrapper.
- Editor typography mirrors the public article prose.
- Keep the editor extension list aligned with the HTML renderer.
- Keep one `prosemirror-model` version; duplicate copies break typing.
- Keep the build-time dedupe check in `scripts/check-editor-deps.ts`.

Do not:

- copy the old black admin tiles with hover scale
- use uppercase micro-labels
- use `rounded-none` inputs
- turn admin into a rounded SaaS dashboard
- use glassmorphism or heavy shadows

---

## 9. Accessibility

- Every page has one H1.
- Project cards use H2.
- Skip link points to `#content`.
- Icon-only links have `aria-label`.
- Theme switch has `role="switch"`, `aria-checked`, label, title.
- Mobile menu toggle has `aria-expanded` and `aria-controls`.
- Active nav uses `aria-current="page"`.
- Focus rings are visible and offset.
- Rounded buttons do not clip focus rings.
- Project skill lists use a `ul` with an accessible label.
- Hero rotating text uses `aria-live="off"` and an `aria-label`.
- Reduced motion is respected.
- Video controls appear under reduced motion.
- Color is not the only state indicator.
- Text contrast is checked in light and dark.

---

## 10. Copy rules

Use:

- `Work`
- `Notes`
- `Computer Science student`
- `Software development`
- Short declarative sentences
- Plain spacing for metadata

Avoid:

- `AZP`
- `Selected work`
- `Writing` as a public heading
- `Fullstack developer`
- Decorative `/`, `|`, `•`, `·`, `—`, `–`
- Metadata commas used as separators
- All-caps mono eyebrows
- Numbered section labels
- Giant full-screen name blocks

---

## 11. Porting checklist

Use this order when applying the system to another app.

1. Install Geist Sans and Geist Mono with `next/font/google`.
2. Copy the semantic color tokens into `globals.css`.
3. Copy the `@theme inline` mapping.
4. Copy the radius scale.
5. Add `.button-skin` and the button depth tokens.
6. Build or update the shared `Button` primitive.
7. Build or update `Badge`, `Input`, `Textarea`, and `Select`.
8. Build `PageShell`, `Sidebar`, `MobileSidebar`, and `ThemeSwitch`.
9. Build `ShuffleLink`, `ShuffleText`, `RotatingHeroHeadline`, `RotatingHeroText`, and `RotatingShuffleText`.
10. Build `ProjectGrid`, `ProjectCard`, `ProjectMedia`, and `LazyVideo`.
11. Build `JourneyTimeline` and add the scroll-driven `journey-*` motion.
12. Build `PointerGrid` as a full-bleed top-band backdrop and keep it pointer-events-none.
13. Apply the homepage, Work, Notes, and Article templates.
14. Apply the copy rules and remove decorative separators.
15. Run the visual QA matrix.
16. Verify reduced motion, the static scroll-timeline fallback, touch behavior, and keyboard focus.
17. Verify light and dark contrast.

Common mistakes:

- rounding project cards
- adding shadows to content cards
- making button shadows too heavy
- shrinking public ink labels to 11px or tight tracking
- restoring the old 20px/28px dark-mode button glow
- using colored gradients on buttons
- making project media grayscale
- using sharp rectangular skill tags
- using a fast random scramble in the hero
- removing the grid sizer from `RotatingHeroHeadline`
- using a giant `7rem` hero
- adding horizontal separator lines
- using two theme icons at once
- adding decorative punctuation
- turning the pointer grid into a full-page overlay
- leaving a hard-edged rectangular grid box
- letting the pointer grid cover or intercept content
- adding a global cursor follower
- blocking CSS or JS in robots.txt
- turning the design into a generic SaaS dashboard

---

## 12. Visual QA matrix

Test at:

- 390px
- 768px
- 1024px
- 1440px

Test in:

- light mode
- dark mode

Check:

- no horizontal overflow
- no clipped focus rings
- button radius matches admin `+ Add work`
- button sheen is subtle
- light button shadow is soft
- dark button glow is subtle
- ghost buttons stay flat
- nav active state is clear
- nav inactive state is readable
- hero phrase holds for 4.8s
- hero lines always rotate as fixed pairs
- hero lead uses the word-mask reveal
- hero tail focus pull is smooth
- hero has no layout jump
- pointer grid base dots stay faint and do not reduce text contrast
- pointer grid wave blooms softly and pauses when the band is offscreen
- pointer grid fades into the page background at every edge, with no hard box
- pointer grid extends through the Stack and disappears before About
- pointer grid wave and spotlight stop on touch devices and reduced motion
- pointer spotlight follows smoothly and fades on pointer leave
- pointer grid is absent outside the hero
- pointer grid does not intercept clicks or focus
- pointer grid stops on touch devices and reduced motion
- reduced motion shows a static phrase
- journey entries reveal as they enter and reverse smoothly on scroll up
- journey chapter labels stick on desktop and do not collide with the mobile header
- journey stays fully visible without scroll-timeline support
- journey titles keep descenders inside the mask
- public ink labels stay legible at 1x
- project media is full color
- project card is flat and square
- skill pills are rounded
- project Open button is rounded and has depth
- article rows have `py-6`
- footer uses `mt-16`
- page shell uses `pt-20` mobile and `lg:pt-12`
- theme switch has one icon
- theme wipe works
- mobile drawer opens and closes
- body scroll locks while drawer is open
- no separator lines
- no decorative punctuation
- one H1 per page

Acceptance criteria:

- The page reads as editorial, not dashboard-like.
- The eye lands on content before controls.
- Controls feel tactile but not glossy.
- Media is the only large colorful surface besides logos.
- Whitespace is tight but not cramped.
- The design still works with JavaScript disabled for static content.

---

## 13. Reference file map

| Concern | File |
|---|---|
| Tokens, base CSS, button skin | `app/globals.css` |
| Root metadata, fonts, theme provider | `app/layout.tsx` |
| Page shell spacing | `components/page-shell.tsx` |
| Desktop nav | `components/sidebar.tsx` |
| Mobile nav | `components/mobile-sidebar.tsx` |
| Theme switch | `components/themeSwitch.tsx` |
| Shared buttons | `components/ui/button.tsx` |
| Badges and skill pills | `components/ui/badge.tsx` |
| Public CTA | `components/shuffle-link.tsx` |
| Button text scramble | `components/shuffle-text.tsx` |
| Hero pair coordinator | `components/rotating-hero-headline.tsx` |
| Hero lead reveal | `components/rotating-hero-text.tsx` |
| Hero tail focus pull | `components/rotating-shuffle-text.tsx` |
| Journey content | `lib/journey.ts` |
| Journey timeline | `components/journey-timeline.tsx` |
| Top-band pointer grid | `components/pointer-grid.tsx` |
| Motion constants | `lib/motion.ts` |
| Work grid | `components/project-grid.tsx` |
| Work card | `components/project-card.tsx` |
| Work media | `components/project-media.tsx` |
| Lazy video | `components/lazy-video.tsx` |
| Notes list row | `components/article-row.tsx` |
| Section heading | `components/section-heading.tsx` |
| Footer | `components/site-footer.tsx` |
| Homepage | `app/page.tsx` |
| Work page | `app/pr/page.tsx` |
| Notes page | `app/blog/page.tsx` |
| Article page | `app/blog/[slug]/page.tsx` |
| 404 | `app/not-found.tsx` |
| Admin shell | `app/admin/_components/admin-shell.tsx` |
| Admin page header | `app/admin/_components/admin-page-header.tsx` |
| Admin dashboard | `app/admin/page.tsx` |
| Admin notes list | `app/admin/blogs/blogsClient.tsx` |
| Admin work list and dialog | `app/admin/works/worksClient.tsx` |
| Admin login | `app/admin/login/page.tsx` |
| Note editor page | `app/admin/blogs/editor/editorClient.tsx` |
| Note editor surface | `components/tiptap-editor.tsx` |
| Slash menu | `components/editor/slash-command.tsx` |
| Editor error boundary | `components/editor/editor-error-boundary.tsx` |
| Markdown paste | `lib/markdown-paste.ts` |
| Plain Tiptap JSON | `lib/tiptap-json.ts` |
| Editor styles | `app/admin/blogs/tiptap.css` |
| Editor build guard | `scripts/check-editor-deps.ts` |
| Blog HTML renderer | `components/tiptap-renderer.tsx` |
| Project-specific decisions | `design.md` |

---

## 14. Final rule

When in doubt, choose the quieter option:

- one less shadow
- one less gradient
- one less color
- one less separator
- one less animation
- one more step of typographic hierarchy
- one more step of breathing room only where it helps reading

The interface should feel like a well-edited desk, not a decorated dashboard.
