#!/usr/bin/env node
/**
 * tools/fa/normalize-search.js — Persian normalization of the mdBook search index.
 *
 * Runs AFTER `mdbook build`:
 *   1. Rewrites the inverted-index tries (title/body/breadcrumbs) with
 *      src/js/lunr-fa.js applied to every token, so index-side and
 *      query-side normalization are byte-identical.
 *   2. Renames the pipeline to "stemmer-fa" (registered by lunr-fa.js).
 *   3. Writes searchindex.json (compact UTF-8, smaller than the \u-escaped
 *      original) and regenerates searchindex.js from it.
 *   4. Installs tools/fa/searcher-fa.js over book/html/searcher.js
 *      (lazy-loads the index instead of fetching 3MB on every page).
 *
 * Usage: node tools/fa/normalize-search.js [book/html]
 */
'use strict';
const fs = require('fs');
const path = require('path');

const OUT = process.argv[2] || path.join('book', 'html');
const lunrFa = require(path.join(__dirname, '..', '..', 'src', 'js', 'lunr-fa.js'));

const indexPath = path.join(OUT, 'searchindex.json');
const raw = fs.readFileSync(indexPath, 'utf8');
const data = JSON.parse(raw);
const index = data.index;

// ---- trie helpers -------------------------------------------------------
function emptyNode() { return { df: 0, docs: {} }; }

function extractTokens(trie) {
  const out = [];
  const root = trie.root;
  if (!root) return out;
  const stack = [[root, '']];
  while (stack.length) {
    const [node, prefix] = stack.pop();
    for (const key of Object.keys(node)) {
      if (key === 'df' || key === 'docs') continue;
      const child = node[key];
      const token = prefix + key;
      const refs = child.docs && Object.keys(child.docs);
      if (refs && refs.length) {
        out.push([token, child.docs]);
      }
      stack.push([child, token]);
    }
  }
  return out;
}

function insertToken(root, token, docs) {
  let node = root;
  for (const ch of token) {
    if (!node[ch]) node[ch] = emptyNode();
    node = node[ch];
  }
  node.df = Math.max(node.df, Object.keys(docs).length);
  for (const ref of Object.keys(docs)) {
    if (!node.docs[ref] || node.docs[ref].tf < docs[ref].tf) {
      node.docs[ref] = docs[ref];
    }
  }
}

// ---- rebuild each field's trie ------------------------------------------
let tokensIn = 0, tokensOut = 0, merged = 0;
for (const field of Object.keys(index.index)) {
  const tokens = extractTokens(index.index[field]);
  const newRoot = emptyNode();
  for (const [token, docs] of tokens) {
    tokensIn++;
    const norm = lunrFa.normalize(token);
    if (!norm) continue;
    const before = JSON.stringify(newRoot).length; // cheap collision signal
    insertToken(newRoot, norm, docs);
    tokensOut++;
  }
  index.index[field] = { root: newRoot };
  merged += tokensIn - tokensOut;
}

index.pipeline = ['stemmer-fa'];

const json = JSON.stringify(data);
fs.writeFileSync(indexPath, json, 'utf8');
fs.writeFileSync(path.join(OUT, 'searchindex.js'),
  'Object.assign(window.search, ' + json + ');', 'utf8');

// ---- install lazy-load searcher ------------------------------------------
const searcherSrc = path.join(__dirname, 'searcher-fa.js');
const searcherDst = path.join(OUT, 'searcher.js');
if (fs.existsSync(searcherSrc)) {
  fs.copyFileSync(searcherSrc, searcherDst);
} else {
  console.error('WARNING: tools/fa/searcher-fa.js not found; keeping stock searcher.js');
}

console.log('search index normalized: ' + tokensIn + ' tokens in, '
  + tokensOut + ' out (' + (tokensIn - tokensOut) + ' merged/dropped), '
  + 'size ' + Math.round(raw.length / 1024) + 'KB -> '
  + Math.round(json.length / 1024) + 'KB');
