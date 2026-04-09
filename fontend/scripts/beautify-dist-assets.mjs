import { readdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { transform } from 'esbuild';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');
const assetsDir = path.join(rootDir, 'dist', 'assets');

const targetMatchers = [
  { ext: '.js', loader: 'js' },
  { ext: '.css', loader: 'css' },
];

async function findTargetFiles(dirPath, ext) {
  const entries = await readdir(dirPath, { withFileTypes: true });
  const nestedResults = await Promise.all(
    entries.map(async (entry) => {
      const entryPath = path.join(dirPath, entry.name);
      if (entry.isDirectory()) {
        return findTargetFiles(entryPath, ext);
      }

      if (entry.isFile() && entry.name.endsWith(ext)) {
        return [entryPath];
      }

      return [];
    }),
  );

  return nestedResults.flat().sort();
}

async function beautifyFile(filePath, loader) {
  const source = await readFile(filePath, 'utf8');
  const result = await transform(source, {
    loader,
    minify: false,
    legalComments: 'inline',
  });

  await writeFile(filePath, result.code, 'utf8');
  console.log(`Beautified ${path.relative(rootDir, filePath)}`);
}

async function main() {
  for (const target of targetMatchers) {
    const filePaths = await findTargetFiles(assetsDir, target.ext);

    if (filePaths.length === 0) {
      throw new Error(`Could not find any *${target.ext} files in ${assetsDir}`);
    }

    for (const filePath of filePaths) {
      await beautifyFile(filePath, target.loader);
    }
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
});
