# Design System

Last updated: 2026-11-04
Direction: **Bloomberg Minimal / Editorial Desk**
Theme: monochrome chrome, with intentionally colored project media, social icons, and skill logos.
Portable implementation guide: `DESIGN_GUIDE.md`

## 1. Design principles

1. Information first.
2. Whitespace and typography first. Content cards stay flat; only interactive controls get subtle depth.
3. No horizontal separator lines in public layout.
4. No AI-slop punctuation: avoid decorative `/`, `|`, `•`, `·`, `—`, `–`, or unnecessary metadata commas.
5. One clear accent behavior per interaction.
6. Motion must explain state change or reward interaction, not decorate every section.
7. Respect `prefers-reduced-motion`.
8. Keep public pages fast and mostly static.
9. Project media stays in full color; the portrait remains grayscale.
10. Buttons and skill pills are rounded; project cards stay square.

Project cards on Work are an intentional exception to the no-card rule: they stay flat, border-only, sharp-cornered, and monochrome, with no card shadow, blur, or hover scale. Their media is full color and the media alone may scale slightly on hover.

The homepage top band has one intentional ambient exception: a pointer-reactive dot grid. It sits behind the hero and Stack content, uses very low-contrast monochrome dots, never intercepts pointer events, and is disabled for coarse pointers and reduced motion. It fades into the page background at every edge; it is not a full-page ASCII canvas.

## 2. Color tokens

Defined in `app/globals.css`.

### Light

- Background: `oklch(0.955 0 0)`
- Foreground: `oklch(0.145 0 0)`
- Card: `oklch(0.985 0 0)`
- Muted: `oklch(0.92 0 0)`
- Muted foreground: `oklch(0.45 0 0)`
- Border: `oklch(0.86 0 0)`
- Ring: `oklch(0.55 0 0)`
- Button sheen: `rgb(255 255 255 / 0.12)`
- Button fill highlight: `transparent`
- Button shadow: `inset 0 1px 0 rgb(255 255 255 / 0.08), 0 1px 1px rgb(0 0 0 / 0.06), 0 4px 10px -8px rgb(0 0 0 / 0.28)`
- Button shadow hover: `inset 0 1px 0 rgb(255 255 255 / 0.10), 0 1px 1px rgb(0 0 0 / 0.08), 0 6px 14px -8px rgb(0 0 0 / 0.34)`
- Radius: `0.25rem`
- Sidebar background: `oklch(0.94 0 0)`

### Dark

- Background: `oklch(0.145 0 0)`
- Foreground: `oklch(0.965 0 0)`
- Card: `oklch(0.19 0 0)`
- Muted: `oklch(0.22 0 0)`
- Muted foreground: `oklch(0.68 0 0)`
- Border: `oklch(0.28 0 0)`
- Ring: `oklch(0.55 0 0)`
- Button sheen: `rgb(255 255 255 / 0.10)`
- Button fill highlight: `rgb(255 255 255 / 0.12)`
- Button shadow: `inset 0 1px 0 rgb(255 255 255 / 0.10), 0 0 12px -10px rgb(255 255 255 / 0.12), 0 1px 2px rgb(0 0 0 / 0.55)`
- Button shadow hover: `inset 0 1px 0 rgb(255 255 255 / 0.12), 0 0 16px -10px rgb(255 255 255 / 0.16), 0 1px 2px rgb(0 0 0 / 0.55)`
- Sidebar background: `oklch(0.17 0 0)`

### Color rules

- UI chrome stays monochrome.
- Social icons use their original brand colors.
- Skill-scroll logos use original colors.
- Project images and videos stay in full color.
- The portrait/avatar remains grayscale.
- Next.js logo is inverted in dark mode so it stays visible.
- Destructive color remains functional red in admin components.
- Button depth is colorless: white sheen, black shadow, or white glow only.

## 3. Typography

- Body and UI: Geist Sans via `next/font/google`.
- Metadata and data: Geist Mono.
- Base body size: `text-sm` to `text-base`.
- Hero headline: `text-4xl` mobile, `text-5xl` desktop.
- Page title: `text-3xl` mobile, `text-4xl` desktop.
- Section title: `text-sm font-medium`.
- Public ink buttons: Geist Mono `text-sm` (14px) and `font-medium`.
- Admin buttons: Geist Sans `text-sm`.
- Skill pills: Geist Mono `text-[10px]` inside a Badge surface.
- Tracking: `tracking-tight` on headings; no extreme negative tracking.
- No uppercase mono eyebrows.
- No numbered section headings.
- No two-line giant name in the hero.
- Hero name is not repeated above the hero.
- Hero headline rotates fixed `I ...` / `for ...` pairs via `RotatingHeroHeadline`; the lead uses `RotatingHeroText` and the tail uses `RotatingShuffleText`.

## 4. Layout

### Root shell

- `app/layout.tsx`
- Skip link to `#content`.
- `ThemeProvider` from `@wrksz/themes`.
- Fixed desktop sidebar.
- Fixed mobile top bar.
- Main content wrapper: `relative z-10 lg:pl-52`.
- `Toaster`.
- No ASCII background.
- No market strip.
- The homepage hero may include the narrow, pointer-reactive dot grid; it stays behind content and never covers it.

### Sidebar

`components/sidebar.tsx`

- Fixed left 6, top 6.
- Width 40 (10rem).
- Hidden below `lg`.
- Theme switch at top.
- Three full-width nav buttons:
  - About
  - Work
  - Notes
- Active button uses inverted colors.
- Hover/focus triggers shuffle text.
- Footer links: email, github, copyright.
- No monogram.
- No location or clock.

### Mobile bar

`components/mobile-sidebar.tsx`

- Fixed top bar, height 16.
- Full name `Arco Zakwan Putra` on the left.
- Theme switch and menu button on the right.
- No bottom border.
- Full-screen overlay menu with large nav buttons.
- Drawer padding: `pt-24 pb-6`.
- Menu toggle uses `rounded-xl`.
- Theme switch uses `button-skin`.
- Body scroll locked while open.
- Menu closes on route change.

### Page shell

`components/page-shell.tsx`

```tsx
<main id="content" className="mx-auto w-full max-w-5xl px-5 pb-16 pt-20 sm:px-8 lg:px-10 lg:pt-12">
  {children}
</main>
```

- Mobile top padding is `5rem`, leaving `1rem` below the fixed `4rem` header.
- Desktop top padding is `3rem`, leaving `1.5rem` below the sidebar top edge.
- Bottom padding is `4rem`.
- Footer top margin is `4rem`.
- Section gaps use `mt-14`, `mt-12`, or `mt-8`; do not use `mt-24`.
- No market strip.
- No `showMarketStrip` prop.
- No top divider.

## 5. Components

### `Button`

File: `components/ui/button.tsx`

- Shared shadcn-style primitive used by the admin UI.
- Base radius: `rounded-4xl` (`0.65rem` at the current `--radius`).
- Sizes: `xs`, `sm`, `default`, `lg`, `icon`, `icon-xs`, `icon-sm`, `icon-lg`.
- Variants:
  - `default`: solid primary.
  - `outline`: bordered input surface.
  - `secondary`: muted surface.
  - `destructive`: functional red.
  - `ghost`: flat hover surface, no depth.
  - `link`: text link, no depth.
- `default`, `outline`, `secondary`, and `destructive` use the shared `button-skin` class.
- `ghost` and `link` stay flat.
- Default and secondary hover backgrounds use `/90`, not `/80`.
- Border is always `1px` and low-opacity:
  - default: `border-primary-foreground/15`, hover `/25`
  - outline: `border-foreground/15`, hover `/25`
  - secondary: `border-foreground/15`, hover `/25`
  - destructive: `border-destructive/25`, hover `/35`
  - ghost/link: `border-transparent`
- Public ink buttons:
  - solid: `border-background/20`, hover `/30`
  - outline: `border-foreground/20`, hover `/35`
- Do not use `border-foreground/70` or full-opacity borders.
- Button depth:
  - Light mode: faint white top sheen, inset top highlight, and soft black shadow.
  - Dark mode: faint white top sheen, inner top highlight, and a very soft white glow.
- Never use large drop shadows, colored glows, or glassmorphism.

### `ShuffleText`

File: `components/shuffle-text.tsx`

- Client component.
- Scrambles text on trigger.
- `totalFrames = letters.length * 4`
- Frame interval: 30 ms.
- Charset: lowercase alphanumerics from `lib/motion.ts`; no punctuation glyphs.
- Respects reduced motion.
- Used by `ShuffleLink` and admin login.
- The hero uses `RotatingShuffleText`, not this component.

### `ShuffleLink`

File: `components/shuffle-link.tsx`

- Client component.
- Props:
  - `href`
  - `label`
  - `appearance`: `ink` or `nav`
  - `tone`: `outline` or `solid`
  - `active`
  - `external`
- Ink appearance:
  - `rounded-4xl` button.
  - Height `h-11` (44px), padding `px-5`, icon `16px`.
  - Label uses Geist Mono `text-sm` (14px) with `font-medium` so it stays legible on 1x and low-resolution displays.
  - Shared `button-skin` depth with reduced sheen and glow.
  - A span fills from top on hover/focus over 300ms.
  - Solid fill uses `.button-fill`: `--background` plus the same top sheen and inset highlight as the black button. Do not use flat `bg-background`.
  - Label and icon use `text-white` plus `mix-blend-difference`.
  - The blend inverts per pixel against the moving fill, so contrast stays correct during the transition.
  - Outline tone uses `bg-background` as an opaque blend backdrop; do not make it transparent.
  - Border flips with the fill:
    - solid: `border-background/20`, hover `border-foreground/20`
    - outline: `border-foreground/20`, hover `border-background/20`
  - Do not restore `group-hover:text-*` classes on the content span.
  - Arrow shifts diagonally.
- Nav appearance:
  - Uses `buttonVariants`.
  - `rounded-4xl`, full width.
  - Active is default/inverted and receives the button skin.
  - Inactive is ghost and stays flat.
- Used on homepage CTAs, project `Open` buttons, and sidebar/mobile nav.

### `RotatingHeroHeadline`

File: `components/rotating-hero-headline.tsx`

- Client component.
- Owns the single 4800ms interval and the current pair index.
- Renders the lead with `RotatingHeroText` and the tail with `RotatingShuffleText`.
- Pairs, in order:
  1. `I build fast, useful software` / `for the web`
  2. `I make ideas feel native` / `for mobile`
  3. `I simplify messy workflows` / `for business`
  4. `I turn research into products` / `for AI`
  5. `I sweat the small details` / `for us`
  6. `I write code with care` / `for humans`
- Both lines always change together; do not restore independent timers.
- Height stability:
  - A CSS grid stacks an invisible sizer and the active pair in the same cell.
  - The sizer uses the tallest pair by character count.
  - The active pair is top-aligned in the cell; any spare height stays below the tail instead of opening a gap between the lines.
  - The paragraph below the H1 stays at the same `top` across all pairs.
  - Do not move the sizer back inside `RotatingHeroText`; that creates a blank line between the lead and tail when the active lead is shorter.
- Reduced motion: the interval never starts and the first pair stays static.
- The sizer is `aria-hidden`; the active lead is visible text; the tail uses its own `aria-label`.
- Used as the complete homepage H1 content.

### `RotatingShuffleText`

File: `components/rotating-shuffle-text.tsx`

- Client component.
- Tail renderer for the hero; driven by the pair index from `RotatingHeroHeadline`.
- Optional controlled `index` prop. When present, the internal interval is disabled.
- Uncontrolled use still works for standalone rotation.
- Phrases:
  1. `for the web`
  2. `for mobile`
  3. `for business`
  4. `for AI`
  5. `for us`
  6. `for humans`
- Interval: 4800 ms when uncontrolled.
- Decode: 760 ms with `requestAnimationFrame` and `easeOutCubic`.
- Reveal style: per-character focus pull from left to right.
- Each character animates:
  - opacity `0.12` → `1`
  - blur `1.2px` → `0`
  - translateY `0.08em` → `0`
- The first phrase is stable on load; only later rotations decode.
- No random glyphs in the hero; `ShuffleText` keeps the random scramble for hover/focus.
- Static first phrase under reduced motion.
- `aria-live="off"` and `aria-label` set to the current phrase.
- Used as the second line of the homepage H1.

### `RotatingHeroText`

File: `components/rotating-hero-text.tsx`

- Presentational lead renderer; no timer and no height sizer.
- Props: `text`, `prefix`, `animate`, `className`.
- Prefix: static `I`.
- Word-by-word mask reveal when `animate` is true:
  - 560 ms with `cubic-bezier(0.22, 1, 0.36, 1)`.
  - 55 ms stagger per word.
  - Each word: opacity `0` → `1`, translateY `120%` → `0`, scale `0.97` → `1`, blur `4px` → `0`.
  - The `I` prefix is static and does not animate.
  - Each word is clipped by a `clip-path` mask; do not replace it with `overflow-hidden`, which changes the inline-block baseline.
- The parent remounts the component with `key={index}` so the CSS animation restarts on every pair change.
- No random glyphs in the hero.
- Height is owned by the grid sizer in `RotatingHeroHeadline`.

### `ThemeSwitch`

File: `components/themeSwitch.tsx`

- Client component.
- Single circular button.
- Uses the shared `button-skin` depth.
- Shows Sun in light mode.
- Shows Moon in dark mode.
- Only one icon in the DOM at a time.
- Uses `resolvedTheme`.
- Uses `flushSync` inside View Transition API callback.
- Sets `--theme-x` and `--theme-y` for circular wipe.
- `role="switch"`, `aria-checked`, accessible label and title.
- Called from desktop sidebar and mobile header.

### `SkillScroll`

File: `components/skill-scroll.tsx`

- Server component.
- Two marquee rows moving in opposite directions.
- Inline SVG logos.
- Original brand colors retained.
- No grayscale filter.
- Next.js logo gets `dark:invert`.
- 34-second CSS animation.
- Pauses on hover.
- Stops under reduced motion.
- Used in the Stack section of the homepage.

### `ProjectGrid`, `ProjectCard`, `ProjectMedia`

Files:
- `components/project-grid.tsx`
- `components/project-card.tsx`
- `components/project-media.tsx`

- ProjectGrid uses CSS columns: one column on mobile, two from `sm`.
- Cards use `break-inside-avoid`; no client-side masonry JS.
- Card is border-only, sharp-cornered, and flat. No card shadow, blur, or card hover scale.
- Card background is `bg-card/50`.
- Media uses 16:9 on mobile and 2:1 from `sm`; full color and `object-cover`.
- Blob and local images use `next/image`.
- External image hosts fall back to `<img loading="lazy" decoding="async">`.
- Video uses `LazyVideo` with no controls.
- Title is `h2`, `text-base font-medium`.
- Description is `text-sm text-muted-foreground`.
- Skills use `Badge variant="outline"`: rounded pill surface, `bg-input/30`, mono `text-[10px]`, muted text.
- Do not use sharp rectangular skill tags.
- `Open` is a full-width `ShuffleLink` when the project has an `href`, inheriting `rounded-4xl` and `button-skin`.
- External links open in a new tab with `rel="noopener noreferrer"`.
- Empty state is the mono line `No projects published yet.`
- No row separator lines.

### `ArticleRow`

File: `components/article-row.tsx`

- Server component.
- Grid columns:
  - date
  - title/description
  - arrow
- No top border.
- Hover background.
- Vertical padding: `py-6`.
- Date uses Geist Mono.
- Used on `/blog`.

### `SectionHeading`

File: `components/section-heading.tsx`

- No index number.
- No bottom border.
- Title `text-sm font-medium`.
- Optional action on the right.
- Margin bottom `mb-4`.

### `PointerGrid`

File: `components/pointer-grid.tsx`

- Client component used only in the homepage hero.
- Three dot layers on a 36px grid:
  - base: static dots at 7% foreground.
  - wave: the same dots at 10%, masked by a large radial bloom that drifts over 28s; paused while the grid band is offscreen.
  - active: the same dots at 20%, masked by a 420px radial spotlight at the pointer.
- The wave bloom is soft and large; do not revert to a diagonal stripe.
- The spotlight follows the pointer with a short `requestAnimationFrame` lerp (0.2) and stops when idle.
- A background-colored gradient overlay (`.pointer-grid__fade`) fades the grid into the page at the left, right, top, and bottom edges.
- The layer is a full-bleed backdrop behind the hero and Stack on the homepage, not a boxed hero element. It starts after the sidebar on desktop.
- Layer height: `120vh` on mobile and `min(52rem, 88vh)` from `lg`.
- `absolute inset-x-0 top-0`, `pointer-events-none`, `aria-hidden`; page content sits at `relative z-10`.
- Pointer activation is checked against the grid layer bounds, so moving over the sidebar, journey, or About does nothing.
- Only runs for a fine pointer. Touch pointer events are ignored.
- `prefers-reduced-motion` hides the wave and active layers; the base grid stays static.
- Without JavaScript the base grid still renders; the wave stays paused.

### `JourneyTimeline`

File: `components/journey-timeline.tsx`

- Server component, no client JavaScript.
- Content comes from `lib/journey.ts`, a static typed module. The homepage stays static and does not query the database.
- Three chapters in order: Education, Experience, Achievements.
- Mobile: the label sits above the entries.
- Tablet: the label sits beside the entries but is not sticky, so it never collides with the fixed mobile header.
- Desktop from `lg`: the label sits in a `9rem` rail and sticks at `top-8` while the chapter's entries pass.
- Entry anatomy:
  - mono period label
  - `text-xl sm:text-2xl` title
  - organization and optional location
  - short detail paragraph
  - optional `Badge variant="outline"` topic pills
- Entries are flat editorial blocks: no cards, borders, shadows, or horizontal dividers.
- Chapter headings are `h2`; entry titles are `h3`.
- Scroll reveal lives in the `journey-*` classes in `app/globals.css`. See Motion.
- Content is fully visible when scroll-driven animations are unsupported or reduced motion is enabled.

### `SiteFooter`

File: `components/site-footer.tsx`

- No top border.
- Left: copyright.
- Right: email, work, notes, github.
- Mono small text.
- Margin top `mt-16`.

### `LazyVideo`

File: `components/lazy-video.tsx`

- Client component.
- IntersectionObserver with 200px root margin.
- Source attached only when near viewport.
- `preload="none"` until loaded, then `metadata`.
- Autoplay only when in view.
- Pauses offscreen.
- No autoplay under reduced motion.
- `controls` can be disabled for thumbnails.
- `playsInline`.

### `JsonLd`

File: `components/json-ld.tsx`

- Renders `application/ld+json`.
- Escapes `<` as `\u003c`.

## 6. Page specifications

### Homepage

File: `app/page.tsx`

- Static page.
- No database query.
- No market strip.
- Hero:
  - H1: `I build fast, useful software`
  - Rotating phrase on next line in muted text.
  - Pointer-reactive dot grid behind the hero and Stack content; a slow radial bloom drifts across the base grid and a 420px spotlight follows the pointer. The grid fades into the page background before About.
  - One short paragraph.
  - Academic stat line: `GPA` label plus `3.75 / 4.00`, `mt-4`, mono, no card or border.
  - CTAs: `Email me`, `Work`.
  - CTA row: `mt-5`.
  - Colored social icons.
  - Social row: `mt-7`.
- Hero aside:
  - Grayscale portrait.
  - No location, study, or status list.
  - The GPA stat belongs to the left column, not the portrait aside.
- Stack section:
  - `mt-14`.
  - `SectionHeading` title `Stack`.
  - Colorful `SkillScroll` with `mt-3 py-3`.
- About section:
  - `mt-12`.
  - Two paragraphs.
  - No "Fullstack" emphasis.
- Journey section:
  - Wrapper `mt-14`.
  - `JourneyTimeline` rendered from the static `lib/journey.ts` content.
  - Chapters: Education, Experience, Achievements.
  - No database query; the homepage stays static.
  - Desktop uses a sticky chapter rail; entries reveal with the scroll-scrubbed mask and fade.
  - No cards or horizontal dividers.
- Contact section:
  - `mt-12`, `pt-4`.
  - Text: `Have a project or a role in mind?`
  - Button: `Start a conversation`.
- Footer.
- JSON-LD Person and WebSite.

### Work page

File: `app/pr/page.tsx`

- URL remains `/pr`.
- H1: `Work`.
- Metadata title: `Work`.
- No Selected work wording.
- Masonry project cards via `ProjectGrid`.
- List starts with `mt-8`.
- Five original projects seeded for local QA.
- Footer.

### Notes page

File: `app/blog/page.tsx`

- URL remains `/blog`.
- H1: `Notes`.
- Metadata title: `Notes`.
- Article rows.
- List starts with `mt-8`.
- Empty state: `No notes published yet. Stay tuned.`
- Empty state padding: `py-8`.
- Footer.

### Article page

File: `app/blog/[slug]/page.tsx`

- Left metadata rail:
  - back to Notes
  - published date
  - reading time
  - author
- Grid gap: `gap-8`.
- Sticky rail: `lg:top-8`.
- Metadata list: `mt-5`.
- Article H1: `text-3xl sm:text-4xl`.
- Header has no bottom border.
- Description: `mt-4`.
- Body uses `prose-blog` with `mt-7`.
- JSON-LD BlogPosting and BreadcrumbList.
- Footer.

### 404

File: `app/not-found.tsx`

- Page shell.
- `Page not found` label.
- Large 404.
- Back home button with shuffle.
- No divider line.

### Admin shell

Files:
- `app/admin/layout.tsx`
- `app/admin/_components/admin-shell.tsx`
- `components/site-chrome.tsx`

- `/admin` uses its own rail instead of the public sidebar.
- Desktop rail mirrors the public shell: theme switch, `Admin` label, nav, and mono footer links.
- Nav: Overview, Work, Notes, CV.
- Active nav uses the inverted `button-skin` treatment.
- Mobile uses a fixed top bar and full-screen drawer with body scroll lock.
- `Admin` label is plain text, not a monogram.
- Admin footer links: `view site`, `sign out`.
- Public `SidebarMini` and `SidebarMobile` are hidden on admin routes by `SiteChrome`.
- Admin content uses `max-w-6xl`, `pt-20`, and `lg:pt-12`, matching the public page shell.
- Admin pages do not nest their own `<main>`; `AdminShell` owns `main#content`.

### Admin pages

Files:
- `app/admin/page.tsx`
- `app/admin/blogs/blogsClient.tsx`
- `app/admin/works/worksClient.tsx`
- `app/admin/login/page.tsx`

- Dashboard uses square, border-only tiles with mono counts.
- Notes and Work use flat editorial rows with hover backgrounds, not cards with shadows.
- Work dialog is a two-column form plus live `ProjectCard` preview.
- `Node.tsx` was removed; the preview uses the real public project card.
- Admin status colors are functional only: green for published, red for destructive.
- Login is a centered, minimal two-step form with rounded inputs and the theme switch.
- No uppercase micro-labels, decorative punctuation, or glassmorphism.

### Note editor

Files:
- `app/admin/blogs/editor/editorClient.tsx`
- `components/tiptap-editor.tsx`
- `components/editor/slash-command.tsx`
- `app/admin/blogs/tiptap.css`

- Notion-style paper layout, `max-w-3xl`.
- Title, description, and slug live inline above the content.
- Sticky action bar: back, status, publish switch, preview, save, word count.
- Slash menu `/`: Text, Heading 1–3, bulleted list, numbered list, to-do list, quote, code block, divider, table, image.
- Bubble menu: bold, italic, strike, inline code, highlight, link.
- Link and image dialogs replace browser prompts.
- Plain-text Markdown paste is converted with `markdown-it`:
  - headings, emphasis, links, images
  - bulleted, numbered, and task lists
  - blockquotes, fenced code blocks, dividers
  - GFM tables
- Rich HTML clipboard content is left to ProseMirror.
- Tables use Tiptap table extensions and a horizontal overflow wrapper.
- Public table styles live in `app/globals.css`.
- `Cmd/Ctrl + S` saves.
- Unsaved changes are tracked; leaving triggers a confirm and `beforeunload`.
- Word count and reading time use mono metadata.
- Editor JSON stays compatible with the public renderer.
- Tiptap extension list must match `components/tiptap-renderer.tsx`.
- Highlight is monochrome in both editor and public output.
- `scripts/check-editor-deps.ts` fails the build if `prosemirror-model` duplicates.

## 7. Motion

- Hero: 4.8s hold. The lead and tail always change together as a fixed pair; the lead uses a 560ms word-by-word mask reveal with a 55ms stagger, and the tail uses the 760ms per-character focus pull.
- Journey: scroll-driven `view()` timeline. The entry meta fades up over `entry 0%` to `cover 28%`, the title uses a masked rise over `entry 0%` to `cover 38%`, and the body follows over `entry 8%` to `cover 50%`. The effect is continuous and reversible, uses only transform and opacity, and never adds blur. The chapter label is sticky on desktop.
- Pointer grid: the active dot layer follows the pointer with a 0.2 lerp. The rAF loop stops when the pointer is idle; the layer fades out on pointer leave. A slow radial bloom drifts across the hero and Stack band, pauses when offscreen, and brightens when the pointer is active. Coarse pointers and reduced motion never start the wave or the follow.
- Buttons: shuffle label + 300ms fill sweep + arrow movement + subtle `button-skin` shadow transition.
- Theme: 480ms circular wipe.
- Skill scroll: continuous marquee, pause on hover.
- Project cards: border strengthens, color media scales slightly, and the Open arrow moves. The card itself does not scale.
- Article rows: subtle hover background and arrow movement.
- Focus states: visible ring.
- Reduced motion:
  - No shuffle.
  - No hero word reveal or focus pull.
  - No journey reveal; every entry is fully visible.
  - No pointer-grid wave or spotlight; the base grid is static.
  - No marquee.
  - No smooth scroll.
  - No theme transition.
  - Video autoplay disabled.
  - Button depth transitions become effectively instant through the global reduced-motion rule.

## 8. Copy rules

Avoid:

- `AZP`
- `Selected work`
- `Writing` as a public heading
- `Fullstack developer`
- Decorative `/`, `|`, `•`, `·`, `—`, `–`
- Metadata commas used as separators
- All-caps mono eyebrows
- Numbered section labels

Use:

- `Work`
- `Notes`
- `Computer Science student`
- `Software development`
- Short declarative sentences
- Colons only in metadata titles
- Plain spacing or layout for metadata

## 9. Media and Blob

- Blob host: `9a9a9kybzrewury8.public.blob.vercel-storage.com`
- `next.config.ts`:
  - remote pattern host with `pathname: "/**"`
  - AVIF/WebP
  - `minimumCacheTTL: 2678400`
  - `maximumRedirects: 0`
  - `deviceSizes: [640, 768, 960, 1280, 1600]`
  - `imageSizes: [64, 96, 128, 256, 384]`
  - `qualities: [75, 85]`
- Blog images use `/_next/image` with 640/960/1280 widths.
- Project media uses `next/image` for Blob and local URLs; external hosts fall back to plain images.
- Project media stays in full color and uses 16:9 on mobile and 2:1 from `sm`.
- Project media scales to `1.03` on card hover; the card itself stays flat and square.
- The portrait/avatar remains grayscale.
- Project videos use `LazyVideo`; autoplay only in view and never under reduced motion.
- Unknown hosts fall back to plain images.
- Vercel Blob serves `cache-control: public, max-age=2592000`.

## 10. SEO

- Root metadata in `app/layout.tsx`.
- `metadataBase` uses `NEXT_PUBLIC_SITE_URL` or `https://arcozp.online`.
- `NEXT_PUBLIC_SITE_URL` must be a bare origin; production requires HTTPS.
- Title template: `%s: Arco Zakwan Putra`.
- Canonical per page.
- OG and Twitter images.
- `app/sitemap.ts`:
  - content-backed `lastModified`
  - post OG image entries
  - static fallback if the database is unavailable
- `app/robots.ts`:
  - production allows public pages and blocks `/admin` and `/api`
  - preview deployments serve `Disallow: /`
- `app/rss.xml/route.ts`.
- JSON-LD.
- Static/ISR public pages.
- Admin and API are noindex/no-store via headers.
- Preview deployments also receive `X-Robots-Tag: noindex, nofollow` and page metadata noindex.

## 11. Accessibility

- Skip link.
- `aria-label` on icon-only links and theme switch.
- `aria-current` on active nav.
- Focus-visible rings.
- Reduced-motion support.
- Mobile menu `aria-expanded` and `aria-controls`.
- Semantic headings: one H1 per page; project cards use H2.
- Project skill lists use a `ul` with an accessible label.
- Project skill pills remain readable at `text-[10px]` with `text-muted-foreground`.
- Rounded buttons keep a visible focus ring with offset.
- Hero rotating text uses `aria-live="off"` and an `aria-label` with the current phrase.
- Article metadata is a compact mono row on mobile and a labelled rail on desktop.
- Article body headings are lower than H1 after the sanitizer transform.
- Journey chapters are `section` elements labelled by an `h2`; entries are an ordered list with `h3` titles.
- Journey content is readable without animation; reduced motion removes the reveal entirely.
- The homepage pointer grid is decorative: `aria-hidden`, `pointer-events-none`, excluded from the tab order, and disabled as a motion source for coarse pointers and reduced motion. The wave and spotlight are both removed under reduced motion.

## 12. Known visual debt

- Skill-scroll SVG bundle is large.
- Dark logo contrast was checked: Next.js, Express, and Prisma are inverted; C++ and Docker rely on bright shapes.
- Admin uses the same shell language as the public site. The CV editor is a visual consistency pass, not a full information-architecture rewrite.
- The note editor uses Tiptap v2 because v3 is a breaking migration. `@tiptap/core` still has a moderate advisory; do not upgrade blindly.
- The note editor does not include block drag handles or image uploads yet. Images are inserted by URL.
- Local project and blog data are demo seed content; production still needs real content.
- Slot Machine GitHub and ToDox demo links are currently dead.
- Mobile fixed header still shows the full name; the removed market strip is not present.
- Project cards remain intentionally sharp and flat. Do not round the card or add a card shadow.
- Project media is intentionally full color. Do not reintroduce a grayscale filter.
- The hero uses a word-mask reveal on the lead and a slow focus-pull on the tail, rotating fixed pairs. Do not restore independent timers or revert either line to a fast random scramble.
- Keep the grid sizer in `RotatingHeroHeadline`; moving it into `RotatingHeroText` opens a blank line between the lead and tail on shorter pairs.
- `ArticleRow` and `SectionHeading` use the tighter spacing scale.
- Journey scroll motion relies on CSS scroll-driven animations. Chrome 115+ and Safari 26+ animate; browsers without support show the static content because the animation rules live inside `@supports (animation-timeline: view())`. Do not move the initial hidden state outside that guard.
- The journey chapter label is sticky only from `lg`; enabling it at `sm` collides with the fixed mobile header.
- Journey dates and chapter details are static demo copy; replace the marked assumptions in `lib/journey.ts` with real dates and roles.
- The homepage pointer grid is the only ambient background accent. Keep it as a top-band backdrop behind the hero and Stack; do not turn it into a full-page canvas or a cursor follower over the journey and About.
- The pointer grid depends on CSS masks and `color-mix`; the fallback is the static base dot grid. The wave pauses offscreen through `data-inview`; keep the observer.
- The grid boundary is a background-colored gradient overlay (`.pointer-grid__fade`), not a hard box. Do not remove it.
- The pointer is checked against the grid layer bounds; do not switch back to the hero wrapper or the whole-page host rect.
