# DV Public Outputs

A small public GitHub Pages site for Dr Dan van den Hoek's media, reports, university outputs, and public-facing research translation work.

## Files

- `index.html` renders the public card library.
- `outputs.json` stores the manually curated output list.
- `.github/workflows/validate-outputs.yml` checks that `outputs.json` remains valid.

## GitHub Pages

Enable Pages from the repository root:

`Settings → Pages → Deploy from a branch → main → / root`

The page should then be available at:

`https://dvandenhoek13.github.io/dv-public-outputs/`

## Updating outputs

Edit `outputs.json`. Each item should include:

- `title`
- `source`
- `year`
- `date`
- `category`
- `topic`
- `description`
- `url`
- `button_text`
