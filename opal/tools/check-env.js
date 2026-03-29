#!/usr/bin/env node
'use strict';

const MIN_VERSION = 18;

function checkEnv() {
  const version = process.version;
  const major = parseInt(version.replace('v', '').split('.')[0], 10);

  if (major >= MIN_VERSION) {
    return { node: true, version, minimum: `v${MIN_VERSION}` };
  }
  return { node: false, version, minimum: `v${MIN_VERSION}`, error: `Node.js v${MIN_VERSION}+ required, got ${version}` };
}

const result = checkEnv();
console.log(JSON.stringify(result, null, 2));
process.exit(result.node ? 0 : 1);
