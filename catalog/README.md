# Sending the plugins to the IngeTrazo catalog

Every time you push to `main`, GitHub checks each plugin against the
[IngeTrazo extensions catalog](https://ingetrazo.com/extensiones). Any plugin
that is new, or has changed (its file, its picture, its name or summary), is
sent to the catalog as a pull request, one per plugin, with its picture.

- A **new version** of a plugin already in the catalog goes in **by itself**
  within a few minutes (the catalog trusts updates from the account in
  `author_url`). It shows as «Community» until a maintainer reads the new file.
- A **brand-new plugin** waits for a maintainer to approve it, once.

You don't have to change the version: when the file changes, the catalog's
version goes up one step (1.1 → 1.2). To jump to a version of your own (say
2.0), put `version = "2.0"` in its entry file.

## What's in this folder

| Path | What it is |
|---|---|
| `entries/<id>.toml` | The catalog entry for each plugin: name, summary and tags in English, Spanish and Portuguese, and `source`, the plugin file. `download`, `sha256` and `version` are filled in for you. |
| `send-to-ingetrazo-catalog.yml` | The GitHub workflow. It only works from `.github\workflows\` (see the setup below). |
| `tools/send_to_catalog.py` | What the workflow runs: works out what's new or changed and sends it. |
| `screenshots/<id>.webp` | The picture the catalog shows (png or jpg also work). About 1200 × 750, under 600 KB. Replace any of them with a real screenshot whenever you like: same name, push, done. |

**A new plugin:** copy one of the entry files, rename it to the plugin's id
(the file name without `ed3d_`), change `id`, `source`, `name`, `summary` and
`tags`, add a picture with the same name in `screenshots/`, and push.

## One-time setup

### 1. Put the workflow where GitHub looks for it

In File Explorer, in the `eddys-3d-plugins-ingetrazo` folder, make a folder
called `.github`, and inside it a folder called `workflows`. Move
`catalog\send-to-ingetrazo-catalog.yml` into `.github\workflows\`. Commit and
push as usual.

### 2. The token

GitHub needs permission to open pull requests on the catalog as you.

1. On github.com, signed in as **eddy-99**: your picture (top right) ▸
   **Settings** ▸ **Developer settings** ▸ **Personal access tokens** ▸
   **Tokens (classic)** ▸ **Generate new token (classic)**.
2. Note: `IngeTrazo catalog`. Expiration: whatever you like (a year, say).
   Tick **public_repo** and **workflow**. (**workflow** is needed because the
   catalog's own workflow files change from time to time, and GitHub won't let
   the token push them to your fork without it.) **Generate token**, and copy it.
3. Go to this repository on github.com ▸ **Settings** ▸ **Secrets and
   variables** ▸ **Actions** ▸ **New repository secret**. Name:
   `CATALOG_TOKEN`, Secret: paste the token. **Add secret**.

That's it. To try it without sending anything: **Actions** tab ▸ **Send to
IngeTrazo catalog** ▸ **Run workflow**, tick *Dry run*. The run's summary
lists what it would send, what's already up to date, and anything that
needs a look (a missing picture, say).

When the token expires, make a new one the same way and paste it over the old
secret.
