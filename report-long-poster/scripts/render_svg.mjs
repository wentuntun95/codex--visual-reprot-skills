import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const sharp = require('sharp');

function usage() {
  console.error('Usage: node render_svg.mjs <input.svg> <output.png> [scale=2]');
  process.exit(2);
}

const [, , inputArg, outputArg, scaleArg = '2'] = process.argv;
if (!inputArg || !outputArg) usage();

const scale = Number(scaleArg);
if (!Number.isFinite(scale) || scale <= 0 || scale > 6) {
  throw new Error('scale must be a number greater than 0 and no more than 6');
}

const input = path.resolve(inputArg);
const output = path.resolve(outputArg);
await fs.access(input);
await fs.mkdir(path.dirname(output), { recursive: true });

const metadata = await sharp(input).metadata();
if (!metadata.width || !metadata.height) throw new Error('Cannot read SVG dimensions');

await sharp(input, { density: 96 * scale })
  .resize(Math.round(metadata.width * scale), Math.round(metadata.height * scale))
  .png({ compressionLevel: 9, adaptiveFiltering: true })
  .toFile(output);

const result = await sharp(output).metadata();
console.log(JSON.stringify({ input, output, width: result.width, height: result.height, scale }));
