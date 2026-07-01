import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { spawnSync } from 'child_process';
import os from 'os';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');

const packageJsonPath = path.join(rootDir, 'package.json');
const tauriConfPath = path.join(rootDir, 'src-tauri', 'tauri.conf.json');
const cargoTomlPath = path.join(rootDir, 'src-tauri', 'Cargo.toml');

// Determine bump type
const bumpType = process.argv[2] || 'patch';
if (!['major', 'minor', 'patch'].includes(bumpType)) {
  console.error('Invalid bump type. Use "major", "minor", or "patch".');
  process.exit(1);
}

// 1. Read current version from package.json
const pkg = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
let [major, minor, patch] = pkg.version.split('.').map(Number);

if (bumpType === 'major') {
  major++;
  minor = 0;
  patch = 0;
} else if (bumpType === 'minor') {
  minor++;
  patch = 0;
} else if (bumpType === 'patch') {
  patch++;
}

const newVersion = `${major}.${minor}.${patch}`;
console.log(`Bumping version to ${newVersion}...`);

// 2. Update package.json
pkg.version = newVersion;
fs.writeFileSync(packageJsonPath, JSON.stringify(pkg, null, 2) + '\n');
console.log('✅ Updated package.json');

// 3. Update tauri.conf.json
const tauriConf = JSON.parse(fs.readFileSync(tauriConfPath, 'utf8'));
tauriConf.version = newVersion;
fs.writeFileSync(tauriConfPath, JSON.stringify(tauriConf, null, 2) + '\n');
console.log('✅ Updated tauri.conf.json');

// 4. Update Cargo.toml
let cargoToml = fs.readFileSync(cargoTomlPath, 'utf8');
cargoToml = cargoToml.replace(/^version = ".*"/m, `version = "${newVersion}"`);
fs.writeFileSync(cargoTomlPath, cargoToml);
console.log('✅ Updated Cargo.toml');

// 5. Build Tauri App
console.log('\n🚀 Building Tauri App... (This may take a minute)');
const buildResult = spawnSync('npm', ['run', 'tauri', 'build'], {
  stdio: 'inherit',
  cwd: rootDir
});

if (buildResult.status !== 0) {
  console.error('❌ Build failed!');
  process.exit(1);
}

// 6. Deploy to ~/Applications
const appName = 'ACIS Chat.app';
const sourceAppPath = path.join(rootDir, 'src-tauri', 'target', 'release', 'bundle', 'macos', appName);
const destAppPath = path.join(os.homedir(), 'Applications', appName);

// Ensure ~/Applications exists
const appsDir = path.join(os.homedir(), 'Applications');
if (!fs.existsSync(appsDir)) {
  fs.mkdirSync(appsDir, { recursive: true });
}

console.log(`\n📦 Copying to ${destAppPath}...`);
const rsyncResult = spawnSync('rsync', ['-av', '--delete', `${sourceAppPath}/`, destAppPath], {
  stdio: 'inherit',
});

if (rsyncResult.status !== 0) {
  console.error('❌ Failed to copy application.');
  process.exit(1);
}

console.log(`\n🎉 Successfully released and installed ${appName} v${newVersion}!`);
