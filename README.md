# HealCUT

HealCUT is a browser-based live clipping prototype for YouTube streams. It embeds a YouTube player, lets the operator choose an IN/OUT range, and records the selected playback as an MP4 when supported by the browser.

## Deploy with GitHub Pages

1. Push this repository to GitHub.
2. In the repository settings, open **Pages**.
3. Choose **Deploy from a branch**, select `main` and `/ (root)`, and save.
4. Open the HTTPS Pages URL. Browser tab capture requires a secure context and permission to share the HealCUT tab with audio.

## Notes

- The current link-based workflow captures the shared browser tab and crops the player area. It does not access YouTube's underlying video feed.
- The page is static and has no server-side storage. Clips remain in browser memory until downloaded; refreshes clear them.
- MP4 recording depends on browser support and can be resource-intensive for long 1080p clips.
- Use only streams you have permission to record and clip.

