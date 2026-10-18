import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const outputDirectory = path.join(root, 'docs');
const output = path.join(outputDirectory, 'SCRIPT-FUENTE.md');
const sourceFiles = [
  'package.json',
  'angular.json',
  'src/app/scheduler.ts',
  'src/app/app.ts',
  'src/app/app.html',
  'src/app/app.css',
  'src/styles.css',
  'src/app/scheduler.spec.ts',
  'src/app/app.spec.ts',
];

const languageFor = (file) => ({
  '.ts': 'ts',
  '.css': 'css',
  '.html': 'html',
  '.json': 'json',
  '.js': 'js',
}[path.extname(file)] ?? 'text');

const sections = await Promise.all(sourceFiles.map(async (file) => {
  const source = await readFile(path.join(root, file), 'utf8');
  return `## ${file}\n\n\`\`\`${languageFor(file)}\n${source}\n\`\`\``;
}));

await mkdir(outputDirectory, { recursive: true });
await writeFile(output, `# Script del código fuente\n\nDocumento generado con \`npm run export:source\`. Contiene los archivos principales del proyecto Angular, su motor de simulación y sus pruebas.\n\n${sections.join('\n\n')}\n`, 'utf8');
console.log(`Documento generado: ${path.relative(root, output)}`);
