import { copyFile, mkdir, access } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const root = fileURLToPath(new URL('../', import.meta.url));
const target = path.join(root, 'public', 'notebooks');
await mkdir(target, { recursive: true });
for (const number of [1, 2, 3, 6, 7, 9, 10]) {
  const name = `Tutorial_${number}.ipynb`;
  const source = path.resolve(root, '..', 'Tutorials', name);
  let exists = true;
  try { await access(source); }
  catch (error) { if (error.code !== 'ENOENT') throw error; exists = false; }
  if (exists) await copyFile(source, path.join(target, name));
  else await access(path.join(target, name));
}
