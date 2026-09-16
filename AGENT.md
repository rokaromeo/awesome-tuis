# Project requirements

In this repository you find a readme. In the readme there are many links to projects that use the TUI user interface.

I want you to make a program to go through all of those project's readme files.

Get the images from the readme of every project. I want to see the images of the user interfaces of every project.

Make a new folder for every github project's data into this folder.

Make a copy of the project's readme in these folders with the images.

# Static gallery page

- Generate a single static `index.html` that shows every project that has at least one downloaded UI image.
- Each project is a card: a wide preview thumbnail (16:9), the project name, a one-sentence description (taken from the list README entry), and the image count.
- The preview thumbnail links to the project's GitHub page (new tab).
- Clicking the card body opens a lightbox to browse all of the project's images, with a "Open README" button that links to the copied local README.
- Include a search box that filters cards by project name.
- Regenerate with `python generate_gallery.py`. Do NOT resize image files — only the HTML/CSS controls layout.
- Mode switch (default = link): a "Mode: link / Mode: collect URLs" toggle in the header.
  - **link mode**: clicking a preview opens the project's GitHub page in a new tab (default).
  - **collect mode**: clicking a preview appends the project's GitHub URL to a fixed sidebar panel (~25% width) on the right side that stays in place while scrolling. The panel contains a textarea listing the collected URLs (one per line, no duplicates), a count, and Clear/Close buttons. The card grid shrinks to make room while the sidebar is open.

# Fetching pipeline

- `fetch_projects.py` parses the list README, creates `projects/<owner>_<repo>/`, downloads each project's README and all image files referenced in it into a local `images/` folder.
- The `projects/` folder is git-ignored (too large for GitHub). Users re-run the scripts to reproduce it.

# Image relevance filtering

The goal is to show UI screenshots. The first image in a project's folder is often decorative (icon/logo), while the interesting screenshots come later. Relevant images are filtered by rules below. Rules are being discovered iteratively from the user's examples — ask the user for examples when unsure, and add new rules to this section.

Rules so far:

1. Exclude images whose filename marks them as a logo or icon: filename matches `icon` (e.g. `icon.png`, `icon-*`), contains `logo` or `favicon`. Ignore case.
2. Anything else is still a candidate — more rules will be added as examples are reviewed.