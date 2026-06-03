// @ts-check
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import { cpSync, existsSync, mkdirSync, readdirSync } from 'node:fs';
import { resolve } from 'node:path';

function syncPostAssets() {
  return {
    name: 'sync-post-assets',
    hooks: {
      'astro:config:setup': () => {
        const postsDir = resolve('posts');
        const publicPostsDir = resolve('public/posts');
        if (!existsSync(postsDir)) return;
        for (const postId of readdirSync(postsDir)) {
          if (postId === 'index.json') continue;
          const assetsDir = resolve(postsDir, postId, 'assets');
          if (existsSync(assetsDir)) {
            const destDir = resolve(publicPostsDir, postId, 'assets');
            mkdirSync(destDir, { recursive: true });
            cpSync(assetsDir, destDir, { recursive: true });
          }
        }
      },
    },
  };
}

export default defineConfig({
  integrations: [mdx(), syncPostAssets()],
});
