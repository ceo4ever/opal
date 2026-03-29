#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

// === Data Loading ===

function loadJsonFile(filePath) {
  if (!fs.existsSync(filePath)) return null;
  const raw = fs.readFileSync(filePath, 'utf8');
  return JSON.parse(raw);
}

function flattenGroups(registry) {
  if (!registry || !registry.groups) return [];
  const skills = [];
  for (const [group, items] of Object.entries(registry.groups)) {
    if (Array.isArray(items)) {
      items.forEach(s => skills.push({ ...s, _group: group }));
    } else if (typeof items === 'object') {
      // nested groups (community)
      for (const [subgroup, subItems] of Object.entries(items)) {
        if (Array.isArray(subItems)) {
          subItems.forEach(s => skills.push({ ...s, _group: `${group}/${subgroup}` }));
        }
      }
    }
  }
  return skills;
}

function getReferencesDir() {
  // 배포 후: ~/.opal/references/
  const deployed = path.join(os.homedir(), '.opal', 'references');
  if (fs.existsSync(path.join(deployed, 'opal-skills-registry.json'))) return deployed;
  // 소스: opal/core/references/ (개발 시)
  const source = path.resolve(__dirname, '..', '..', 'core', 'references');
  if (fs.existsSync(path.join(source, 'opal-skills-registry.json'))) return source;
  return deployed; // fallback
}

function loadAllSkills() {
  const refDir = getReferencesDir();
  const main = loadJsonFile(path.join(refDir, 'opal-skills-registry.json'));
  const community = loadJsonFile(path.join(refDir, 'community-skills-registry.json'));

  const skills = [];
  if (main) skills.push(...flattenGroups(main));
  if (community) skills.push(...flattenGroups(community));
  return skills;
}

// === Match Command ===

function extractAlias(input) {
  const match = input.match(/\/\/(\S+)/);
  if (match) {
    const alias = match[1];
    const cleanInput = input.replace(/\/\/\S+/, '').trim();
    return { alias, cleanInput };
  }
  return { alias: null, cleanInput: input.trim() };
}

function matchByAlias(skills, alias) {
  const lower = alias.toLowerCase();
  return skills.find(s =>
    s.name.toLowerCase() === lower ||
    (s.alias && s.alias.toLowerCase() === lower)
  ) || null;
}

function matchByTriggers(skills, input) {
  for (const skill of skills) {
    if (!skill.triggers) continue;
    for (const pattern of skill.triggers) {
      try {
        let flags = '';
        let pat = pattern;
        if (pat.startsWith('(?i)')) {
          flags = 'i';
          pat = pat.slice(4);
        }
        const regex = new RegExp(pat, flags);
        if (regex.test(input)) {
          return skill;
        }
      } catch (e) {
        // invalid regex, skip
      }
    }
  }
  return null;
}

function resolveFirstPath(paths) {
  if (!paths) return null;
  for (const p of paths) {
    const resolved = p
      .replace(/^~/, os.homedir())
      .replace(/\{project\}/g, process.cwd());
    if (fs.existsSync(resolved)) {
      return resolved;
    }
  }
  return paths.length > 0 ? paths[paths.length - 1].replace(/^~/, os.homedir()) : null;
}

function matchCommand(input) {
  const skills = loadAllSkills();
  const { alias, cleanInput } = extractAlias(input);

  let skill = null;
  if (alias) {
    skill = matchByAlias(skills, alias);
  }
  if (!skill) {
    skill = matchByTriggers(skills, cleanInput || input);
  }

  if (skill) {
    return {
      found: true,
      name: skill.name,
      group: skill._group,
      alias: skill.alias,
      description: skill.description,
      path: resolveFirstPath(skill.paths),
      domain: skill.domain || null,
      cleanInput
    };
  }
  return { found: false, input };
}

// === Get Command ===

function getCommand(name) {
  const skills = loadAllSkills();
  const skill = skills.find(s => s.name === name);
  if (skill) {
    const { _group, ...rest } = skill;
    return { ...rest, group: _group };
  }
  return { error: `Skill not found: ${name}` };
}

// === List Command ===

function listCommand(options) {
  const skills = loadAllSkills();
  let filtered = skills;

  if (options.group) {
    filtered = filtered.filter(s => s._group === options.group || s._group.startsWith(options.group + '/'));
  }
  if (options.domain) {
    filtered = filtered.filter(s => s.domain === options.domain);
  }

  return filtered.map(s => ({
    name: s.name,
    group: s._group,
    alias: s.alias,
    description: s.description,
    domain: s.domain || null
  }));
}

// === Validate Command ===

function validate() {
  const errors = [];
  const warnings = [];

  const refDir = getReferencesDir();
  const mainPath = path.join(refDir, 'opal-skills-registry.json');
  const communityPath = path.join(refDir, 'community-skills-registry.json');

  let mainRegistry, communityRegistry;
  try {
    mainRegistry = loadJsonFile(mainPath);
    if (!mainRegistry) errors.push('opal-skills-registry.json not found');
  } catch (e) {
    errors.push(`opal-skills-registry.json parse error: ${e.message}`);
  }

  try {
    communityRegistry = loadJsonFile(communityPath);
    if (!communityRegistry) warnings.push('community-skills-registry.json not found (optional)');
  } catch (e) {
    errors.push(`community-skills-registry.json parse error: ${e.message}`);
  }

  const skills = loadAllSkills();
  const names = new Set();
  const aliases = new Set();

  for (const skill of skills) {
    if (!skill.name) errors.push('Skill missing "name" field');
    if (!skill.paths || !Array.isArray(skill.paths)) errors.push(`${skill.name}: missing "paths" array`);

    // name uniqueness
    if (names.has(skill.name)) errors.push(`Duplicate name: ${skill.name}`);
    names.add(skill.name);

    // alias uniqueness
    if (skill.alias) {
      if (aliases.has(skill.alias)) errors.push(`Duplicate alias: ${skill.alias}`);
      aliases.add(skill.alias);
    }

    // regex compilation test
    if (skill.triggers) {
      for (const pattern of skill.triggers) {
        try {
          let pat = pattern;
          let flags = '';
          if (pat.startsWith('(?i)')) { flags = 'i'; pat = pat.slice(4); }
          new RegExp(pat, flags);
        } catch (e) {
          errors.push(`${skill.name}: invalid regex "${pattern}": ${e.message}`);
        }
      }
    }

    // path existence check
    if (skill.paths) {
      let found = false;
      for (const p of skill.paths) {
        const resolved = p.replace(/^~/, os.homedir()).replace(/\{project\}/g, process.cwd());
        if (fs.existsSync(resolved)) { found = true; break; }
      }
      if (!found) warnings.push(`${skill.name}: no SKILL.md found at any path`);
    }
  }

  return {
    valid: errors.length === 0,
    total: skills.length,
    groups: mainRegistry ? Object.keys(mainRegistry.groups) : [],
    communityGroups: communityRegistry ? Object.keys(communityRegistry.groups) : [],
    errors,
    warnings
  };
}

// === CLI Router ===

function main() {
  const args = process.argv.slice(2);
  const command = args[0];

  if (!command) {
    console.error('Usage: skill-registry.js <match|get|list|validate> [args]');
    console.error('  match <input>          Match skill from user input');
    console.error('  get <name>             Get skill metadata');
    console.error('  list [--group=X] [--domain=X]  List skills');
    console.error('  validate               Validate registries');
    process.exit(1);
  }

  let result;

  switch (command) {
    case 'match':
      if (!args[1]) {
        console.error('Usage: skill-registry.js match <input>');
        process.exit(1);
      }
      result = matchCommand(args.slice(1).join(' '));
      break;

    case 'get':
      if (!args[1]) {
        console.error('Usage: skill-registry.js get <name>');
        process.exit(1);
      }
      result = getCommand(args[1]);
      break;

    case 'list': {
      const options = {};
      for (let i = 1; i < args.length; i++) {
        if (args[i].startsWith('--group=')) options.group = args[i].split('=')[1];
        if (args[i].startsWith('--domain=')) options.domain = args[i].split('=')[1];
      }
      result = listCommand(options);
      break;
    }

    case 'validate':
      result = validate();
      break;

    default:
      console.error(`Unknown command: ${command}`);
      process.exit(1);
  }

  console.log(JSON.stringify(result, null, 2));
  if (result.error || (result.valid === false)) {
    process.exit(1);
  }
}

main();
