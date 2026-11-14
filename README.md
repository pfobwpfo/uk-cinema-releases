# UK Cinema Releases

A lightweight, text-only GitHub Pages site listing UK theatrical releases for the current week.

## Publishing

1. In the repository, open **Settings → Pages**.
2. Under **Build and deployment**, choose **Deploy from a branch**.
3. Select branch **main** and folder **/(root)**, then Save.
4. The site will appear at https://pfobwpfo.github.io/uk-cinema-releases/.

## Weekly updates

GitHub Actions runs every Thursday at 18:00 UTC and can also be run manually from **Actions → Update UK cinema releases → Run workflow**. It reads the Film Distributors' Association print release schedule and updates `data/current.json`. Previous weeks are saved under `data/archive/`.

## Editorial information

The FDA schedule is the source for release dates. Certificate and running time are included only when verified. Add verified details and concise review summaries to `data/editorial.json`, keyed by the exact FDA title. Review summaries should synthesise more than one reputable UK critic and link directly to the original reviews. The updater deliberately does not invent certificates, runtimes or critic opinions when that editorial information is not supplied.

The current seed list is an initial snapshot; run the workflow once after enabling Pages to refresh it from the FDA.
