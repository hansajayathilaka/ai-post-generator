# Astro Starter Kit: Minimal

```sh
npm create astro@latest -- --template minimal
```

> 🧑‍🚀 **Seasoned astronaut?** Delete this file. Have fun!

## 🚀 Project Structure

Inside of your Astro project, you'll see the following folders and files:

```text
/
├── public/
├── src/
│   └── pages/
│       └── index.astro
└── package.json
```

Astro looks for `.astro` or `.md` files in the `src/pages/` directory. Each page is exposed as a route based on its file name.

There's nothing special about `src/components/`, but that's where we like to put any Astro/React/Vue/Svelte/Preact components.

Any static assets, like images, can be placed in the `public/` directory.

## 🧞 Commands

All commands are run from the root of the project, from a terminal:

| Command                   | Action                                           |
| :------------------------ | :----------------------------------------------- |
| `npm install`             | Installs dependencies                            |
| `npm run dev`             | Starts local dev server at `localhost:4321`      |
| `npm run build`           | Build your production site to `./dist/`          |
| `npm run preview`         | Preview your build locally, before deploying     |
| `npm run astro ...`       | Run CLI commands like `astro add`, `astro check` |
| `npm run astro -- --help` | Get help using the Astro CLI                     |

## Optional Parallel topic research

The Python post generator can use [Parallel Search MCP](https://docs.parallel.ai/integrations/mcp/search-mcp)
to discover topics and gather citable web excerpts. Anonymous search uses Fast mode
and needs no Parallel account or API key. The existing `config.json` selects Gemini;
to opt in, change only `generation.research_provider` to `"parallel"`.

From the repository root, with Python 3.12:

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r scripts/requirements.txt
python scripts/generate_post.py
```

Set `ANTHROPIC_API_KEY` or `GEMINI_API_KEY` for writing the post. Parallel topic
discovery and research do not use `TAVILY_API_KEY` or a Parallel key. The nightly
workflow reads the same setting and installs the same requirements.

Search excerpts feed the writing prompt, and source URLs and titles are retained
in `sources.json` and the run log. Parallel errors, timeouts or research without excerpts
stop generation instead of silently switching providers. The anonymous endpoint
has rate limits and is intended for light use; see the linked service documentation
before relying on it for a production publishing schedule. This provider uses
search excerpts, without fetching full pages.

Run the provider checks with `python -m unittest discover -s tests -v`.

## 👀 Want to learn more?

Feel free to check [our documentation](https://docs.astro.build) or jump into our [Discord server](https://astro.build/chat).
