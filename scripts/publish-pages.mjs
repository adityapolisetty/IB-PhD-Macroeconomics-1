import { existsSync, mkdirSync, readdirSync, rmSync, cpSync, writeFileSync } from 'node:fs';
import { resolve, join, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const root = fileURLToPath(new URL('../', import.meta.url));
const publishDir = resolve(root, '.pages-publish');
const repo = 'https://github.com/adityapolisetty/IB-PhD-Macroeconomics-1.git';
const cache = join(root, '.cache');
const env = {
  ...process.env,
  ASTRO_TELEMETRY_DISABLED: '1',
  SITE_URL: process.env.SITE_URL || 'https://adityapolisetty.github.io',
  BASE_PATH: process.env.BASE_PATH || '/IB-PhD-Macroeconomics-1',
  XDG_CACHE_HOME: cache,
  XDG_CONFIG_HOME: join(cache, 'config'),
  COREPACK_HOME: join(cache, 'corepack'),
  PNPM_HOME: join(cache, 'pnpm-home'),
  npm_config_cache: join(cache, 'npm'),
  TEMP: join(cache, 'tmp'), TMP: join(cache, 'tmp'), TMPDIR: join(cache, 'tmp')
};
mkdirSync(env.TEMP, { recursive: true });

function git(args, cwd = root, allowed = [0]) {
  const result = spawnSync('git', [
    '-c', `safe.directory=${cwd.replaceAll('\\', '/')}`,
    '-c', `core.excludesFile=${join(root, '.gitignore')}`,
    ...args
  ], { cwd, env, encoding: 'utf8' });
  if (!allowed.includes(result.status)) {
    throw new Error(result.error?.message || result.stderr || result.stdout || 'Git failed');
  }
  if (result.stderr) process.stderr.write(result.stderr);
  return result;
}

if (!process.argv.includes('--skip-build')) {
  const build = spawnSync('pnpm --config.stateDir=.cache/pnpm-state build', {
    cwd: root, env, shell: true, stdio: 'inherit'
  });
  if (build.status !== 0) process.exit(build.status || 1);
}
if (!existsSync(join(root, 'dist', 'index.html'))) throw new Error('Build the site before publishing.');
if (!publishDir.startsWith(resolve(root) + sep)) throw new Error('Invalid publishing directory.');

const author = git(['log', '-1', '--format=%an']).stdout.trim();
const email = git(['log', '-1', '--format=%ae']).stdout.trim();
const remoteExists = git(['ls-remote', '--heads', repo, 'refs/heads/gh-pages']).stdout.trim() !== '';
if (!existsSync(join(publishDir, '.git'))) {
  if (remoteExists) {
    git(['clone', '--single-branch', '--branch', 'gh-pages', repo, publishDir]);
  } else {
    mkdirSync(publishDir, { recursive: true });
    git(['init', '-b', 'gh-pages'], publishDir);
    git(['remote', 'add', 'origin', repo], publishDir);
  }
} else if (remoteExists) {
  git(['fetch', 'origin', 'gh-pages'], publishDir);
  git(['merge', '--ff-only', 'origin/gh-pages'], publishDir);
}

// Only generated files in the verified publishing folder are replaced.
for (const name of readdirSync(publishDir)) {
  if (name === '.git') continue;
  const target = resolve(publishDir, name);
  if (!target.startsWith(publishDir + sep)) throw new Error('Invalid generated file path.');
  rmSync(target, { recursive: true, force: true });
}
cpSync(join(root, 'dist'), publishDir, { recursive: true });
writeFileSync(join(publishDir, '.nojekyll'), '');
git(['add', '--all'], publishDir);
if (git(['diff', '--cached', '--quiet'], publishDir, [0, 1]).status === 1) {
  git(['-c', `user.name=${author}`, '-c', `user.email=${email}`, 'commit', '-m', 'Publish the Macro course site'], publishDir);
}
git(['push', '-u', 'origin', 'gh-pages'], publishDir);
console.log('Published files to gh-pages. GitHub Pages will serve the updated course site.');
