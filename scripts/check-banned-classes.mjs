#!/usr/bin/env node

import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const projectRoot = path.resolve(__dirname, '..')
const targetDir = path.resolve(projectRoot, 'frontend', 'components')

// Specific targets or default to all under frontend/components
const args = process.argv.slice(2)
const specificFiles = args.length > 0 ? args.map(f => path.resolve(process.cwd(), f)) : null

const BANNED_PATTERNS = [
  /\bbg-slate-\d+/,
  /\btext-slate-\d+/,
  /\bborder-slate-\d+/,
  /\bdark:bg-slate-\d+/,
  /\bdark:text-slate-\d+/,
  /\bdark:border-slate-\d+/,
  /\bbg-\[#[0-9a-fA-F]+\]/,
  /\btext-\[#[0-9a-fA-F]+\]/,
  /\bborder-\[#[0-9a-fA-F]+\]/,
  /\bdark:bg-\[#[0-9a-fA-F]+\]/,
  /\bdark:text-\[#[0-9a-fA-F]+\]/,
  /\bdark:border-\[#[0-9a-fA-F]+\]/,
]

function getFiles(dir) {
  let results = []
  const list = fs.readdirSync(dir)
  for (const file of list) {
    const fullPath = path.join(dir, file)
    const stat = fs.statSync(fullPath)
    if (stat && stat.isDirectory()) {
      results = results.concat(getFiles(fullPath))
    } else if (file.endsWith('.tsx') && file !== 'metaradar.tsx') {
      results.push(fullPath)
    }
  }
  return results
}

const filesToScan = specificFiles || getFiles(targetDir)
let totalViolations = 0
const violations = []

for (const filePath of filesToScan) {
  if (filePath.endsWith('metaradar.tsx')) continue
  if (!fs.existsSync(filePath)) continue

  const content = fs.readFileSync(filePath, 'utf-8')
  const lines = content.split('\n')

  lines.forEach((line, index) => {
    const trimmed = line.trim()
    // Skip comment lines
    if (trimmed.startsWith('//') || trimmed.startsWith('/*') || trimmed.startsWith('*')) {
      return
    }

    for (const pattern of BANNED_PATTERNS) {
      const match = line.match(pattern)
      if (match) {
        totalViolations++
        const relPath = path.relative(projectRoot, filePath).replace(/\\/g, '/')
        violations.push({
          file: relPath,
          line: index + 1,
          banned: match[0],
          snippet: trimmed,
        })
      }
    }
  })
}

if (totalViolations > 0) {
  console.error(`\x1b[31m[BANNED-CLASS-GATE] Found ${totalViolations} banned class violation(s):\x1b[0m`)
  for (const v of violations) {
    console.error(`  \x1b[33m${v.file}:${v.line}\x1b[0m - banned '\x1b[31m${v.banned}\x1b[0m' in: "${v.snippet.slice(0, 100)}"`)
  }
  process.exit(1)
} else {
  console.log(`\x1b[32m[BANNED-CLASS-GATE] Clean! Scanned ${filesToScan.length} file(s), 0 violations found.\x1b[0m`)
  process.exit(0)
}
