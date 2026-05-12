# teremo4ek.github.io

Personal site and blog of Yury Bely. Built with Hugo and Tailwind CSS.

## Tech Stack

- [Hugo](https://gohugo.io/) — static site generator
- [Tailwind CSS](https://tailwindcss.com/) — utility-first CSS
- Hugo Modules — plugins by [gethugothemes](https://gethugothemes.com/hugo-modules)

## Commands

```bash
npm install          # install dependencies
npm run dev          # start dev server
npm run build        # production build → public/
npm run preview      # preview production build locally
npm run update-modules  # update Hugo modules
```

## Project Structure

```
content/english/   — site content (pages, blog, about)
config/_default/   — Hugo config (params, menus, languages)
data/              — theme colors, fonts, social links
assets/scss/       — custom styles
themes/hugoplate/  — theme (do not edit directly)
static/            — static files
public/            — build output
```
