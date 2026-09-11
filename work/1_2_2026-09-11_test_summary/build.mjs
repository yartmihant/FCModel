import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { Workbook } from '@oai/artifact-tool';

const root = '/home/antonov/Base/Libs/FCModel';
const output = path.join(root, 'work/1_2_2026-09-11_test_summary.csv');
const support = path.dirname(new URL(import.meta.url).pathname);
const rtPath = 'work/1_2_2026-09-11_json_cleanup/roundtrip_results.json';
const fiPath = 'work/1_2_2026-09-11_fidesys_roundtrip/results.json';
const read = async p => JSON.parse(await fs.readFile(path.join(root, p), 'utf8'));
const rt = await read(rtPath);
const rtMap = new Map(rt.files.map(r => [r.file, r]));
assert.equal(rtMap.size, rt.files.length);
const fiReport = await read(fiPath);
const fiMap = new Map();
for (const record of fiReport.files) {
  const combine = key => [...new Set([...record.import_stage[key], ...record.export_stage[key]])];
  fiMap.set(record.file, {
    ...record, report: fiPath, runFinished: fiReport.finished_utc,
    completion: record.import_stage.completion,
    errors: combine('errors'), primary_errors: combine('primary_errors'),
    warnings: combine('warnings').filter(w => w.trim().replace(/\.+$/, '') !== 'The distance between nodesets is not accurate'),
  });
}
assert.equal(fiMap.size, fiReport.selected_files);
const corpus = path.join(root, 'data/fc_core_tests');
async function listFC(directory, prefix = '') {
  const files = [];
  for (const e of await fs.readdir(directory, { withFileTypes: true })) {
    const name = prefix + e.name;
    if (e.isDirectory()) files.push(...await listFC(path.join(directory, e.name), name + '/'));
    else if (e.isFile() && e.name.toLowerCase().endsWith('.fc')) files.push(name);
  }
  return files;
}
const names = (await listFC(corpus)).sort();
assert.equal(names.length, 1130);
assert.deepEqual(names, [...rtMap.keys()].sort());
const rtLabels = { equal: 'Пройден', different: 'Расхождения JSON', error: 'Ошибка загрузки модели' };
const headers = [
  'Файл', 'Roundtrip_статус', 'Fidesys_статус', 'Сопоставление',
  'Roundtrip_этап_ошибки', 'Roundtrip_тип_исключения', 'Roundtrip_сообщение_ошибки',
  'Roundtrip_место_ошибки', 'Roundtrip_число_расхождений', 'Roundtrip_виды_расхождений',
  'Roundtrip_пути_JSON', 'Roundtrip_подробности_JSON',
  'Fidesys_ошибок_по_API', 'Fidesys_уникальных_сообщений_ошибок', 'Fidesys_ошибки',
  'Fidesys_первичные_ошибки', 'Fidesys_уникальных_предупреждений', 'Fidesys_предупреждения',
  'Fidesys_импорт_завершён', 'Fidesys_загружено_узлов', 'Fidesys_загружено_элементов',
  'Fidesys_пояснение', 'Fidesys_повторный_запуск', 'Fidesys_длительность_сек',
  'Fidesys_код_launcher', 'SHA256', 'Путь_исходного_файла', 'Roundtrip_реестр',
  'Roundtrip_конец_прогона_UTC', 'Fidesys_реестр', 'Fidesys_конец_прогона_UTC',
  'Fidesys_полный_лог', 'Fidesys_лог_повторного_запуска',
];
const kinds = { added: 'Добавлено поле', removed: 'Удалено поле', value_changed: 'Изменено значение',
  type_changed: 'Изменён тип', length_changed: 'Изменена длина массива' };
const rows = [];
const meshComparisons = new Map();
const meshComparisonCounts = {};
const rtCounts = {}, fiCounts = {}, cross = {};
for (const name of names) {
  const r = rtMap.get(name), f = fiMap.get(name);
  assert.ok(f, name);
  const sourceBytes = await fs.readFile(path.join(corpus, name));
  const mesh = JSON.parse(sourceBytes.toString('utf8')).mesh;
  const digest = crypto.createHash('sha256').update(sourceBytes).digest('hex');
  assert.equal(digest, r.sha256, 'Stale roundtrip: ' + name);
  assert.equal(digest, f.sha256, 'Stale Fidesys: ' + name);
  assert.equal(r.source_unchanged, true);
  assert.equal(f.source_unchanged, true);
  const done = f.completion !== null;
  const mismatches = [], unavailable = [];
  for (const [key, counter, label] of [['nodes_count', 'nodes', 'узлы'], ['elems_count', 'elements', 'элементы']]) {
    const expected = mesh?.[key], loaded = f.completion?.[counter];
    if (!Number.isSafeInteger(expected) || expected < 0 || !Number.isSafeInteger(loaded) || loaded < 0) {
      unavailable.push(label);
    } else if (expected !== loaded) {
      mismatches.push(`${label}: JSON=${expected}, Fidesys=${loaded}`);
    }
  }
  const meshComparison = mismatches.length
    ? 'Да; ' + mismatches.join('; ') + (unavailable.length ? '; нет данных: ' + unavailable.join(', ') : '')
    : unavailable.length ? 'Неизвестно; нет данных: ' + unavailable.join(', ') : 'Нет';
  meshComparisons.set(name, meshComparison);
  const meshCategory = mismatches.length ? 'different' : unavailable.length ? 'unknown' : 'equal';
  meshComparisonCounts[meshCategory] = (meshComparisonCounts[meshCategory] ?? 0) + 1;
  const good = f.alive;
  assert.equal(good, f.status === 'roundtrip_passed');
  if (good) assert.ok(done && f.completion.errors === 0 && f.export_completion?.errors === 0 && f.errors.length === 0 && f.output_valid);
  const fiLabels = {
    roundtrip_passed: f.warnings.length ? 'Roundtrip пройден, есть предупреждения' : 'Roundtrip пройден',
    import_error: 'Ошибка импорта', export_error: 'Ошибка экспорта',
    import_incomplete: 'Импорт не подтверждён', export_incomplete: 'Экспорт не подтверждён',
    invalid_output: 'Некорректный FC после экспорта', timeout: 'Таймаут', abnormal_exit: 'Аварийное завершение',
  };
  assert.ok(fiLabels[f.status], f.status);
  const fiLabel = fiLabels[f.status];
  const compare = r.status === 'equal' ? (good ? 'Оба теста пройдены' : 'Только fc-model roundtrip пройден')
    : good ? 'Только Fidesys roundtrip пройден' : 'Оба теста с проблемами';
  const ds = r.differences ?? [];
  const log = path.join(path.dirname(f.report), f.log);
  await fs.access(path.join(root, log));
  if (f.output_exists) {
    const bytes = await fs.readFile(path.join(root, path.dirname(fiPath), f.output));
    assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'), f.output_sha256, 'Stale export: ' + name);
  }
  rows.push([
    name, rtLabels[r.status], fiLabel, compare,
    r.stage ?? '', r.error_type ?? '', r.error ?? '', r.location ?? '',
    r.status === 'error' ? null : ds.length,
    [...new Set(ds.map(d => kinds[d.kind] ?? d.kind))].sort().join(' | '),
    [...new Set(ds.map(d => d.path))].join(' | '), ds.length ? JSON.stringify(ds) : '',
    f.export_completion?.errors ?? null, f.errors.length, f.errors.join(' | '),
    f.primary_errors.join(' | '), f.warnings.length, f.warnings.join(' | '), done ? 'Да' : 'Нет',
    done ? f.completion.nodes : null, done ? f.completion.elements : null,
    good ? 'Импорт и экспорт завершены без ошибок; FC прочитан. Живая модель для калибровки; равенство JSON проверено отдельно.'
      : fiLabel + (f.output_error ? '; ' + f.output_error : '; частичный экспорт не подтверждает жизнеспособность модели.'),
    '', f.duration_seconds, f.returncode,
    digest, 'data/fc_core_tests/' + name, rtPath, rt.finished_utc, f.report, f.runFinished, log, '',
  ]);
  rtCounts[r.status] = (rtCounts[r.status] ?? 0) + 1;
  fiCounts[f.status] = (fiCounts[f.status] ?? 0) + 1;
  const key = r.status + ' / ' + f.status;
  cross[key] = (cross[key] ?? 0) + 1;
}
assert.deepEqual(rtCounts, { equal: 453, error: 66, different: 611 });
assert.deepEqual(fiCounts, fiReport.counts);
assert.equal(names.length, fiMap.size);

// Extend the same table with the independent specification audit, if present.
const specPath = 'work/1_2_2026-09-11_spec_audit/results.json';
let specReport = null;
try { await fs.access(path.join(root, specPath)); specReport = await read(specPath); }
catch (error) { if (error.code !== 'ENOENT') throw error; }
if (specReport) {
  const specMap = new Map(specReport.files.map(record => [record.file, record]));
  assert.equal(specMap.size, 1130);
  const hashFile = async p => crypto.createHash('sha256').update(await fs.readFile(path.join(root, p))).digest('hex');
  assert.equal(await hashFile(specReport.spec), specReport.spec_sha256, 'Stale specification');
  for (const [file, digest] of Object.entries(specReport.checker_sha256)) {
    assert.equal(await hashFile(path.join(path.dirname(specPath), file)), digest, 'Stale checker: ' + file);
  }
  const reviews = new Map();
  for (const domain of ['mesh', 'materials', 'conditions']) {
    const source = `work/1_2_2026-09-11_spec_audit/review_${domain}.json`;
    for (const review of await read(source)) {
      const file = review.file.replace(/^data\/fc_core_tests\//, '');
      reviews.set(file, `${source}; поля: ${review.reviewed_paths.join(', ')}`);
    }
  }
  headers.push(
    'Спецификация_статус', 'Спецификация_нарушений', 'Спецификация_legacy',
    'Спецификация_неясностей', 'Спецификация_ошибок_проверки',
    'Спецификация_нарушения', 'Спецификация_legacy_описание', 'Спецификация_неясности',
    'Спецификация_коды_правил', 'Спецификация_пути_JSON', 'Спецификация_подробности_JSON',
    'Спецификация_охват', 'Спецификация_документ', 'Спецификация_SHA256',
    'Спецификация_реестр', 'Спецификация_конец_прогона_UTC', 'Спецификация_Luna_перепроверка',
  );
  for (const row of rows) {
    const record = specMap.get(row[0]);
    assert.equal(record.sha256, row[25]);
    assert.deepEqual(record.completed_domains, ['document', 'mesh', 'materials', 'conditions']);
    assert.equal(record.counts.check_error, 0);
    const details = record.findings;
    const description = severity => details.filter(f => f.severity === severity)
      .map(f => `${f.rule} ${f.path}: ${f.message} Найдено: ${JSON.stringify(f.actual)}; ожидается: ${JSON.stringify(f.expected)} (${f.spec})`).join(' | ');
    row.push(
      record.status, record.counts.violation, record.counts.legacy, record.counts.ambiguity, record.counts.check_error,
      description('violation'), description('legacy'), description('ambiguity'),
      [...new Set(details.map(f => f.rule))].sort().join(' | '),
      [...new Set(details.map(f => f.path))].sort().join(' | '), JSON.stringify(details),
      'Завершены 4 области: header/settings, mesh/CS/sets/blocks, materials/property_tables, conditions/constraints/receivers. Неясности и непроверяемая семантика указаны отдельно; методика: work/1_2_2026-09-11_spec_audit/README.md',
      specReport.spec, specReport.spec_sha256, specPath, specReport.finished_utc,
      reviews.get(record.file) ?? 'Выполнены общие правила, подготовленные Luna и проверенные основным агентом',
    );
  }
}

const cycleHeaders = [
  'Fidesys_живая_модель', 'Fidesys_экспорт_завершён', 'Fidesys_выход_FC_валиден',
  'Fidesys_ошибки_импорта', 'Fidesys_ошибки_экспорта', 'Fidesys_ошибка_чтения_экспорта',
  'Fidesys_экспорт_узлов', 'Fidesys_экспорт_элементов',
  'Fidesys_JSON_статус', 'Fidesys_JSON_число_расхождений', 'Fidesys_JSON_виды_расхождений',
  'Fidesys_JSON_пути', 'Fidesys_JSON_подробности',
];
headers.push(...cycleHeaders);
const jsonLabels = { equal: 'Совпадает', different: 'Различается', invalid_output: 'Некорректный выходной FC', not_available: 'Нет экспорта' };
for (const row of rows) {
  const f = fiMap.get(row[0]), ds = f.differences;
  row.push(
    f.alive ? 'Да' : 'Не подтверждено', f.export_completion ? 'Да' : 'Нет', f.output_valid ? 'Да' : 'Нет',
    f.import_stage.errors.join(' | '), f.export_stage.errors.join(' | '), f.output_error,
    f.output_mesh?.nodes_count ?? null, f.output_mesh?.elems_count ?? null,
    jsonLabels[f.json_status], f.output_valid ? ds.length : null,
    [...new Set(ds.map(d => kinds[d.kind] ?? d.kind))].sort().join(' | '),
    [...new Set(ds.map(d => d.path))].join(' | '), ds.length ? JSON.stringify(ds) : '',
  );
}

// Publish only analytical columns. Provenance stays in the source registries.
const removed = new Set([
  'Roundtrip_место_ошибки', 'Fidesys_длительность_сек', 'Fidesys_код_launcher',
  'SHA256', 'Путь_исходного_файла', 'Roundtrip_реестр', 'Roundtrip_конец_прогона_UTC',
  'Fidesys_реестр', 'Fidesys_конец_прогона_UTC', 'Fidesys_полный_лог', 'Fidesys_лог_повторного_запуска',
  'Спецификация_охват', 'Спецификация_документ', 'Спецификация_SHA256',
  'Спецификация_реестр', 'Спецификация_конец_прогона_UTC', 'Спецификация_Luna_перепроверка',
]);
for (let i = 0; i < headers.length; i++) {
  if (new Set(rows.map(row => row[i])).size === 1) removed.add(headers[i]);
}
const publishedIndexes = headers.map((h, i) => removed.has(h) || cycleHeaders.includes(h) ? -1 : i).filter(i => i >= 0);
const cycleIndexes = cycleHeaders.filter(h => !removed.has(h)).map(h => headers.indexOf(h));
const cyclePosition = publishedIndexes.indexOf(headers.indexOf('Fidesys_статус')) + 1;
publishedIndexes.splice(cyclePosition, 0, ...cycleIndexes);
const publishedHeaders = publishedIndexes.map(i => headers[i]);
const comparisonIndex = publishedHeaders.indexOf('Fidesys_загружено_элементов') + 1;
assert.ok(comparisonIndex > 0);
publishedHeaders.splice(comparisonIndex, 0, 'Fidesys_разница_с_числами_JSON');
const publishedRows = rows.map(row => {
  const values = publishedIndexes.map(i => row[i]);
  values.splice(comparisonIndex, 0, meshComparisons.get(row[0]));
  return values;
});

const workbook = Workbook.create();
const sheet = workbook.worksheets.add('Проверки');
const matrix = [publishedHeaders, ...publishedRows];
const range = sheet.getRangeByIndexes(0, 0, matrix.length, publishedHeaders.length);
range.values = matrix;
workbook.recalculate();
// CSV has no native formatting; author the matrix with Artifact Tool, then
// serialize its verified values as RFC 4180 records (CSV export is undocumented).
const authored = range.values.map((row, ri) => row.map((value, ci) => {
  const expected = matrix[ri][ci];
  if (value instanceof Date) {
    assert.equal(value.getTime(), new Date(expected).getTime(), `Date mismatch at ${ri}/${ci}`);
    // Retain the source timestamp's microsecond precision in the plain CSV.
    return expected;
  }
  assert.equal(value, expected, `Cell mismatch at ${ri}/${ci}`);
  return value;
}));
function field(value) {
  if (value === null || value === undefined) return '';
  return '"' + String(value).replaceAll('"', '""') + '"';
}
await fs.writeFile(output, '\uFEFF' + authored.map(row => row.map(field).join(',')).join('\r\n') + '\r\n', 'utf8');
// Visual QA of the main identifying/status columns; this style is not a CSV feature.
sheet.getRange('A1:C7').format.font = { name: 'Arial', size: 10 };
sheet.getRange('A1:C1').format.fill = '#253746';
sheet.getRange('A1:C1').format.font = { name: 'Arial', size: 10, bold: true, color: '#FFFFFF' };
sheet.getRange('A1:A7').format.columnWidth = 78;
sheet.getRange('B1:C7').format.columnWidth = 35;
sheet.getRange('A1:C7').format.rowHeight = 32;
const preview = await workbook.render({ sheetName: 'Проверки', range: 'A1:C7', scale: 1, format: 'png' });
await fs.writeFile(path.join(support, 'preview.png'), new Uint8Array(await preview.arrayBuffer()));
// Review the changed mesh comparison and specification status columns.
for (const [label, first, count] of [
  ['mesh', publishedHeaders.indexOf('Fidesys_загружено_узлов'), 3],
  ['spec', publishedHeaders.indexOf('Спецификация_статус'), 4],
  ['cycle', publishedHeaders.indexOf('Fidesys_живая_модель'), 3],
]) {
  const view = sheet.getRangeByIndexes(0, first, 7, count);
  view.format.font = { name: 'Arial', size: 10 };
  view.format.columnWidth = label === 'mesh' ? 42 : 37;
  view.format.wrapText = true;
  view.format.rowHeight = 48;
  const head = sheet.getRangeByIndexes(0, first, 1, count);
  head.format.fill = '#253746';
  head.format.font = { name: 'Arial', size: 10, bold: true, color: '#FFFFFF' };
  function columnName(index) {
    let name = '';
    for (let i = index + 1; i > 0; i = Math.floor((i - 1) / 26)) name = String.fromCharCode(65 + (i - 1) % 26) + name;
    return name;
  }
  const address = `${columnName(first)}1:${columnName(first + count - 1)}7`;
  const rendered = await workbook.render({ sheetName: 'Проверки', range: address, scale: 1, format: 'png' });
  await fs.writeFile(path.join(support, `${label}_preview.png`), new Uint8Array(await rendered.arrayBuffer()));
}
console.log((await workbook.inspect({ kind: 'table', range: 'Проверки!C1:F4', tableMaxRows: 4, tableMaxCols: 4 })).ndjson);
const verification = { rows: rows.length, columns: publishedHeaders.length, removedColumns: [...removed], meshComparisonCounts, rtCounts, fiCounts, cross,
  matchedSourceHashes: names.length, delimiter: ',', encoding: 'UTF-8 with BOM',
  maxCellCharacters: Math.max(...publishedRows.flat().map(v => v == null ? 0 : String(v).length)),
  output, specStatuses: specReport?.statuses ?? null, created_utc: new Date().toISOString() };
await fs.writeFile(path.join(support, 'verification.json'), JSON.stringify(verification, null, 2) + '\n');
console.log(JSON.stringify(verification));
