const fs = require('fs');
const path = require('path');
const { htmlToEditable, rebuildSectionInner, normalizeForCompare, headingAndLinkFor, updateHeading, updateWrapLink, insertNewSectionBlock } = require('/tmp/rt-test/shipped.js');

const SECTION_RE = /<!--\s*CMS:section\s+id=([^\s]+)\s*-->([\s\S]*?)<!--\s*\/CMS:section\s*-->/g;

const sites = ['maed', 'onsset', 'osemosys', 'clews', 'ffrm', 'nismod', 'onstove', 'pathcalc', 'fintrack', 'finplan', 'minfin', 'hub'];
const files = ['index.html', 'about.markdown', 'application.markdown', 'dataset.markdown', 'get_involved.markdown', 'learning_capacity.markdown'];

const NEW_LINK = 'https://example.org/edited-link';

// The title and link boxes a manager sees for every section of a page.
const boxesOf = (content) => {
  const boxes = [];
  content.replace(SECTION_RE, (full, id, inner, offset) => {
    boxes.push(Object.assign({ id }, headingAndLinkFor(content, offset)));
    return full;
  });
  return boxes;
};

let totalSections = 0;
let noopFailures = [];
let editFailures = [];
let linkFailures = [];

for (const site of sites) {
  for (const file of files) {
    const p = path.join('/tmp/emt-' + site, file);
    if (!fs.existsSync(p)) continue;
    const original = fs.readFileSync(p, 'utf8');

    // Case 1: manager opens the issue and saves without changing anything.
    const untouched = original.replace(SECTION_RE, (full, id, inner) => {
      totalSections++;
      const editable = htmlToEditable(inner);
      if (normalizeForCompare(inner, false) === normalizeForCompare(editable, true)) return full;
      return `<!-- CMS:section id=${id} -->${rebuildSectionInner(inner, editable)}<!-- /CMS:section -->`;
    });
    if (untouched !== original) {
      noopFailures.push(`${site}/${file}`);
    }

    // Case 2: manager appends one word to every section. Text must survive.
    let missing = 0;
    original.replace(SECTION_RE, (full, id, inner) => {
      const editable = htmlToEditable(inner);
      if (!editable.trim()) return full;
      const edited = editable + ' SENTINELWORD';
      const rebuilt = rebuildSectionInner(inner, edited);
      if (!rebuilt.includes('SENTINELWORD')) missing++;
      // The rest of the text must still be there.
      const before = normalizeForCompare(editable, true);
      const after = normalizeForCompare(rebuilt, false).replace(/ ?SENTINELWORD/, '');
      if (before !== after) missing++;
      return full;
    });
    if (missing) editFailures.push(`${site}/${file} (${missing})`);

    // Case 3: manager saves the prefilled title and link boxes untouched. The
    // markup around the section, including neighbouring buttons, must not move.
    const boxes = boxesOf(original);
    let linked = original;
    for (const box of boxes) {
      if (box.heading) linked = updateHeading(linked, box.id, box.heading, box.link);
      if (box.link) linked = updateWrapLink(linked, box.id, box.link);
    }
    if (linked !== original) linkFailures.push(`${site}/${file}`);

    // Case 4: a real title or link edit must reach its own section's boxes and
    // leave every other section's boxes alone.
    for (const box of boxes) {
      // Sections under the same heading share these boxes, so they move together.
      const shared = new Set(boxes.filter((b) => b.headingAt === box.headingAt).map((b) => b.id));
      const key = (b) => (b ? `${b.id}|${b.heading}|${b.link}` : '(missing)');
      const was = boxes.filter((b) => !shared.has(b.id));
      const strayEdit = (content) => {
        const now = boxesOf(content).filter((b) => !shared.has(b.id));
        for (let i = 0; i < Math.max(was.length, now.length); i++) {
          if (key(was[i]) !== key(now[i])) return `${key(was[i])} became ${key(now[i])}`;
        }
        return '';
      };
      if (box.heading) {
        const out = updateHeading(original, box.id, `${box.heading} EDITED`, box.link);
        const now = boxesOf(out).find((b) => b.id === box.id);
        if (!now || now.heading !== `${box.heading} EDITED`) {
          editFailures.push(`${site}/${file}: title edit lost (${box.id})`);
        }
        const stray = strayEdit(out);
        if (stray) editFailures.push(`${site}/${file}: title edit of ${box.id} changed ${stray}`);
      }
      if (box.link) {
        let out = updateHeading(original, box.id, box.heading, NEW_LINK);
        out = updateWrapLink(out, box.id, NEW_LINK);
        const now = boxesOf(out).find((b) => b.id === box.id);
        if (!now || now.link !== NEW_LINK) {
          editFailures.push(`${site}/${file}: link edit lost (${box.id})`);
        }
        const stray = strayEdit(out);
        if (stray) editFailures.push(`${site}/${file}: link edit of ${box.id} changed ${stray}`);
      }
    }
  }
}

console.log('sections round-tripped:', totalSections);
console.log('');
console.log('no-op edit rewrote the file:', noopFailures.length ? noopFailures.join(', ') : 'none  ✅');
console.log('edit lost or mangled text:  ', editFailures.length ? editFailures.join(', ') : 'none  ✅');
console.log('no-op title/link moved a link:', linkFailures.length ? linkFailures.join(', ') : 'none  ✅');

const NEW = '<h2 id="inserted-test">NEW SECTION</h2>\n<div class="col-md-12 animate-out mb-2">x</div>';
const insertFailures = [];
for (const site of ['onsset', 'maed', 'osemosys', 'onstove', 'clews']) {
  const p = path.join('/tmp/emt-' + site, 'about.markdown');
  if (!fs.existsSync(p)) continue;
  const original = fs.readFileSync(p, 'utf8');
  const out = insertNewSectionBlock(original, NEW);
  const newAt = out.indexOf('id="inserted-test"');
  const lastOld = original.lastIndexOf('<!-- /CMS:section -->');
  const iconAt = out.indexOf('<!-- Icon Links');
  if (newAt < 0) {
    insertFailures.push(`${site}: new section missing`);
    continue;
  }
  if (newAt < lastOld) insertFailures.push(`${site}: inserted before last existing section`);
  if (iconAt >= 0 && newAt > iconAt) insertFailures.push(`${site}: inserted at or after Icon Links`);
  const between = out.slice(newAt, iconAt >= 0 ? iconAt : out.length);
  const leftoverCloses = (between.match(/<\/div>/g) || []).length;
  // The new block itself contains one </div>; at least one more should remain
  // before Icon Links (the inner content column).
  if (iconAt >= 0 && leftoverCloses < 2) {
    insertFailures.push(`${site}: new section is outside the inner content column (${leftoverCloses} closing divs before Icon Links)`);
  }
}
console.log('new section stays in column: ', insertFailures.length ? insertFailures.join(', ') : 'none  ✅');
process.exit(noopFailures.length || editFailures.length || linkFailures.length || insertFailures.length ? 1 : 0);
