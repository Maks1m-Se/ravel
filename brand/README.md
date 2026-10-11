# Ravel logo

Adopted 11 October 2026. Five horizontal threads carry a 3 × 5 cell pattern; the
middle row is Fichte green. The master drawing and the pixel-fitted 32, 24 and
16 px drawings form one set. [ravel-brand-overview.png](ravel-brand-overview.png)
shows every asset on one page.

## Files

| Folder | Contents |
|--------|----------|
| `svg/` | Transparent marks: `ravel-mark-{light,dark,mono-black,mono-white}.svg` (master) and `ravel-mark-{32,24,16}-…svg` (pixel drawings) |
| `png/mark/` | Transparent marks, light and dark, at 16, 24, 32, 64, 128, 256 and 512 px |
| `png/app-icon/` | App tiles, light and dark, at 64, 128, 256 and 512 px |
| `favicon/` | `favicon.svg` (16 px drawing, follows `prefers-color-scheme`) and `favicon.ico` (16, 24, 32, 48 px) |
| `lockup/` | Mark plus wordmark, light and dark, as SVG (text outlined) and PNG (128 px high) |
| `source/` | `ravel-logo-source.svg`: editable layers with one `rect` per thread and cell, lockups with live text |

`light` files are for light backgrounds and `dark` files for dark backgrounds.
Monochrome files fill every element with one colour.

## Which drawing at which size

| Rendered size | Drawing |
|---------------|---------|
| 16 px | `…-16-…` (favicon, tabs) |
| 24 px | `…-24-…` (toolbars) |
| 32 px | `…-32-…` |
| 48 px and larger | master |

Pixel drawings are only exact at their own size. Do not scale them.

## Colours

| Role | Light background | Dark background |
|------|------------------|-----------------|
| Threads and cells | Graphite `#1E2329` | Light ink `#E8EBEE` |
| Middle row | Fichte `#3A6B57` | Fichte light `#8DBAA2` |
| App tile | `#F3F4F6` | `#1C1F23` |

Monochrome: `#000000` or `#FFFFFF`.

## Geometry

Master on a 64 × 64 unit grid:

- Threads: five, 2 units high, x 1–63, centred on each cell row.
- Cells: 8 × 8 units with 3-unit gaps; columns at x 17, 28, 39; rows at y 6, 17, 28, 39, 50.
- Pattern by row, left to right: `111`, `101`, `111`, `110`, `101`. Row 3 is Fichte.
- Bounding box x 1–63, y 6–58, centred.

Pixel drawings (all values in pixels):

| Size | Cell | Gap | Thread | Thread position | Thread span | Centre offset |
|------|------|-----|--------|-----------------|-------------|---------------|
| 32 | 4 | 2 | 1 | 3rd pixel of the cell | x 1–31 | 0 |
| 24 | 3 | 1 | 1 | middle pixel | x 2–23 | +0.5, +0.5 |
| 16 | 2 | 1 | 1 | lower pixel | x 1–15 | 0 |

The 24 px block is 11 × 19 px, so it cannot sit exactly in the centre; it is set
half a pixel right and down. A 40 px drawing (cell 5, gap 2, thread 1) is used
only inside the 64 and 128 px app tiles.

## Wordmark

- Typeface: Instrument Sans SemiBold (600), SIL Open Font License 1.1. The font
  is not bundled; lockup SVGs contain outlines, the source file uses live text.
- Tracking −1 %. Size 56 units next to the 64-unit mark box, 24 units gap,
  baseline at y 52 so the cap height is centred on the mark.

## App tiles

The 64-unit mark box fills 62.5 % of the tile. Corner radius is 7/32 of the tile
size.

## Checks

Rendered at actual size before export:

- 16, 24, 32 and 40 px and the master at 64 px: every pixel fully on or off,
  identical to the drawing, no thread end touching an edge, all rows and cells
  separated.
- `favicon.ico` frames at 16, 24 and 32 px are identical to the PNG marks; the
  48 px frame is the 24 px drawing doubled.
