# Sri Lalitha Sahasranamavali — Phase 1

A static Telugu slideshow for parayanam with 1,000 names. Open index.html locally or use the GitHub Pages site.

The supplied master is preserved in data/original_names.txt. Name 922 receives a final danda in the player; the source text remains unchanged.

Pushes to main publish a static GitHub Pages build. The build adds content hashes to the stylesheet, font, and JavaScript URLs, including the names dataset. GitHub Pages controls caching of the HTML entry point. The updated asset URLs take effect once the browser receives the new HTML.

To build the Pages artifact locally, run `python scripts/build_pages.py _site` with a new or empty output directory. Local use of the repository's `index.html` and the PNG exporter does not require this build.
