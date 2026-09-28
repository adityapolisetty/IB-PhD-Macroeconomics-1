import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import svelte from '@astrojs/svelte';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

// GitHub Actions supplies the actual Pages origin and repository subpath.
export default defineConfig({
  site: process.env.SITE_URL || 'https://adityapolisetty.github.io',
  base: process.env.BASE_PATH || '/',
  output: 'static',
  trailingSlash: 'always',
  integrations: [mdx(), svelte()],
  markdown: {
    remarkPlugins: [remarkMath],
    rehypePlugins: [[rehypeKatex, { strict: 'warn', throwOnError: true }]],
    shikiConfig: { theme: 'github-light' }
  },
  devToolbar: { enabled: false }
});
