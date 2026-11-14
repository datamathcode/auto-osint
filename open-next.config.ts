// OpenNext Cloudflare adapter configuration.
// No incremental cache: every page here is either static or `no-store`, so R2/KV
// bindings would add setup without changing behaviour.
import { defineCloudflareConfig } from "@opennextjs/cloudflare/config";

export default defineCloudflareConfig({});
