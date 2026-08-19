// Double-read vision extraction workflow for historical poll releases.
//
// For each prepared document (rendered to page images by scripts/ingest_prep.py),
// two independent vision agents read the images and emit a structured extraction;
// a deterministic reconcile stage then (1) requires the two reads to agree on every
// detailed [All Respondents] value, (2) runs a per-reading sum gate, and (3) runs the
// trending cross-check: every scenario shown in the "N-Way Trial Heats Trending"
// summary must appear in the detailed extraction with matching values. Any failure
// flags the document for human review; clean documents carry a merged spec.
//
// Invoke via the Workflow tool with args = array of prep meta objects (each meta.json).
// No corpus mutation happens here — agents only produce reviewable specs.

export const meta = {
  name: 'double-read-poll-extraction',
  description: 'Two independent vision reads per document, reconciled with sum + trending cross-checks',
  phases: [{ title: 'extract', detail: 'two independent vision reads per document' }],
}

const READING_ITEM = {
  type: 'object',
  additionalProperties: false,
  properties: {
    scenario_label: { type: 'string' },
    question_text: { type: 'string' },
    denominator: { type: 'string' },
    base: { type: 'integer' },
    source_locator: { type: 'string' },
    responses: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        properties: {
          label: { type: 'string' },
          kind: { type: 'string' },
          value: { type: 'number' },
        },
        required: ['label', 'kind', 'value'],
      },
    },
  },
  required: ['scenario_label', 'question_text', 'denominator', 'base', 'source_locator', 'responses'],
}

const SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    pollster: { type: 'string' },
    fieldwork_start: { type: 'string' },
    fieldwork_end: { type: 'string' },
    publication_date: { type: 'string' },
    collection_mode: { type: 'string' },
    recruited_sample_size: { type: 'integer' },
    readings: { type: 'array', items: READING_ITEM },
    trending: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        properties: {
          scenario_label: { type: 'string' },
          responses: {
            type: 'array',
            items: {
              type: 'object',
              additionalProperties: false,
              properties: { label: { type: 'string' }, value: { type: 'number' } },
              required: ['label', 'value'],
            },
          },
        },
        required: ['scenario_label', 'responses'],
      },
    },
  },
  required: ['pollster', 'fieldwork_end', 'publication_date', 'collection_mode', 'recruited_sample_size', 'readings', 'trending'],
}

function extractPrompt(m) {
  return `You are extracting Toronto mayoral vote-intention data from a ${m.firm} poll release rendered to page images. Do NOT use any text-extraction tool; view each page with the Read tool and read the tables visually.

Document ${m.doc_id} (cycle ${m.cycle}). Page images (Read each):
${m.page_images.join('\n')}

1. DETAILED readings: find EVERY general vote-intention "trial heat / horserace" table shown for ALL RESPONDENTS / INCLUDING UNDECIDED (labels like "N-Way Mayoral Trial Heats" or "Mayoral Poll — Including Undecided Voters", above a question like "If a mayoral election were held today, who would you vote for ...?"). For each ballot scenario read ONLY the Total / [All Respondents] / Including-Undecided column: the percent for every named candidate AND the residual row ("Don't know" / "Undecided" / "Someone else"). IGNORE demographic breakdown columns (Age, Region, Income, Property, Children, Past Vote, etc.) and IGNORE approval and candidate-attribute tables. Record scenario_label (the field, e.g. "Ford / Tory / Stintz / Soknacki"), exact question_text, denominator "all_respondents", base (the Sample n), source_locator (e.g. "p.9 [All Respondents] Total column"), and responses (each candidate + residual, kind "candidate" / "dont_know" / "other", exact printed percent — KEEP any decimal, e.g. 45.5).

1b. DECIDED-VOTER readings: if the SAME race is ALSO reported among DECIDED VOTERS (a separate table/column excluding the undecided, e.g. "Mayoral Poll — Among Decided Voters" or a "[DECIDED/LEANING]" column), record it as a SEPARATE reading with denominator "decided_voters": same scenario_label, its own responses (candidates only, no undecided), base (the decided n if printed, else -1), and source_locator naming the decided table. Do not invent a decided reading if none is shown.

2. TRENDING cross-check: also read the "N-Way Mayoral Trial Heats Trending" SUMMARY tables if present. For each trended scenario record ONLY the CURRENT wave's row (the row dated this release) as {scenario_label, responses:[{label, value}]} in "trending". If there is no trending summary, return an empty trending array.

3. Sample-level metadata from the header/methodology: pollster, fieldwork_start and fieldwork_end (YYYY-MM-DD), publication_date (YYYY-MM-DD), collection_mode (e.g. "ivr"), recruited_sample_size.

Preserve exact published integers; do not compute, normalize, or infer. If a value is truly unreadable use -1. Return the structured object only.`
}

function candKey(responses) {
  return (responses || [])
    .filter((r) => (r.kind ? r.kind === 'candidate' : String(r.label).trim().toLowerCase() !== "don't know"))
    .map((r) => String(r.label).trim().toLowerCase())
    .sort()
    .join('|')
}

function valMap(responses) {
  const out = {}
  for (const r of responses || []) out[String(r.label).trim().toLowerCase()] = r.value
  return out
}

// a reading is identified by its candidate set AND its denominator, so the
// all-respondents and decided-voter tables of the same race stay distinct.
function readingKey(r) {
  return candKey(r.responses) + '|' + (r.denominator || 'all_respondents')
}

// Some Mainstreet reports (May/June 2023 onward) add a third horserace table,
// "(Decided and Undecided)", whose candidate set + all_respondents denominator
// collide with the standard "(All voters)" table in readingKey. We ingest only
// the "(All voters)" [all_respondents] and "(Decided voters)" [decided] tables to
// match the corpus, so drop the middle table before reconciling and merging.
function isMidTable(r) {
  const s = (String(r.question_text || '') + ' ' + String(r.scenario_label || '')).toLowerCase()
  return s.includes('decided and undecided')
}
function dropMidTables(x) {
  return x && x.readings ? { ...x, readings: x.readings.filter((r) => !isMidTable(r)) } : x
}

function reconcile(m, a, b) {
  if (!a || !b) return { doc_id: m.doc_id, clean: false, flags: ['an extraction returned null'], a, b }
  a = dropMidTables(a)
  b = dropMidTables(b)
  const flags = []
  for (const f of ['pollster', 'fieldwork_end', 'publication_date', 'recruited_sample_size']) {
    if (String(a[f]) !== String(b[f])) flags.push(`sample.${f}: A=${a[f]} B=${b[f]}`)
  }
  // (1)+(2) detailed reads must agree value-by-value; (2) sum gate
  const bByKey = {}
  for (const r of b.readings || []) bByKey[readingKey(r)] = r
  const matched = []
  const unmatchedA = []
  for (const ra of a.readings || []) {
    const key = readingKey(ra)
    const rb = bByKey[key]
    if (!rb) { unmatchedA.push(ra.scenario_label); continue }
    delete bByKey[key]
    const bResp = valMap(rb.responses)
    const disagreements = []
    let sum = 0
    for (const x of ra.responses) {
      sum += x.value
      const bv = bResp[String(x.label).trim().toLowerCase()]
      if (bv === undefined) disagreements.push(`${x.label}: A=${x.value} B=absent`)
      else if (bv !== x.value) disagreements.push(`${x.label}: A=${x.value} B=${bv}`)
    }
    const sumOk = sum >= 97 && sum <= 103
    matched.push({ scenario: ra.scenario_label, base: ra.base, sum, sumOk })
    if (!sumOk) flags.push(`${ra.scenario_label}: sum=${sum} outside [97,103]`)
    if (disagreements.length) flags.push(`${ra.scenario_label}: ${disagreements.join('; ')}`)
  }
  for (const label of unmatchedA) flags.push(`reading only in read A: ${label}`)
  for (const r of Object.values(bByKey)) flags.push(`reading only in read B: ${r.scenario_label}`)

  // (3) trending cross-check: every trended scenario must appear in detailed with matching values
  const detailByKey = {}
  for (const r of a.readings || []) {
    if ((r.denominator || 'all_respondents') === 'all_respondents') detailByKey[candKey(r.responses)] = r
  }
  for (const t of a.trending || []) {
    const key = candKey(t.responses)
    const detail = detailByKey[key]
    if (!detail) { flags.push(`trending scenario "${t.scenario_label}" missing from detailed extraction`); continue }
    const dv = valMap(detail.responses)
    for (const x of t.responses) {
      const d = dv[String(x.label).trim().toLowerCase()]
      if (d !== undefined && d !== x.value) {
        flags.push(`trending vs detailed mismatch (${t.scenario_label}) ${x.label}: trend=${x.value} detail=${d}`)
      }
    }
  }
  // the two reads must also agree on the trending set
  const aTrend = (a.trending || []).map((t) => candKey(t.responses)).sort().join(',')
  const bTrend = (b.trending || []).map((t) => candKey(t.responses)).sort().join(',')
  if (aTrend !== bTrend) flags.push('reads disagree on the trending scenario set')

  return {
    doc_id: m.doc_id,
    clean: flags.length === 0,
    n_readings_A: (a.readings || []).length,
    n_readings_B: (b.readings || []).length,
    n_trending: (a.trending || []).length,
    matched,
    flags,
    merged: flags.length === 0 ? a : null,
    a,
    b,
  }
}

phase('extract')
const results = await pipeline(
  args,
  (m) => parallel([
    () => agent(extractPrompt(m), { label: `readA:${m.doc_id}`, phase: 'extract', schema: SCHEMA, agentType: 'general-purpose' }),
    () => agent(extractPrompt(m), { label: `readB:${m.doc_id}`, phase: 'extract', schema: SCHEMA, agentType: 'general-purpose' }),
  ]),
  (reads, m) => reconcile(m, reads[0], reads[1]),
)
return results
