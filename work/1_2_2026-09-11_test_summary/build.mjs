import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { Workbook } from '@oai/artifact-tool';

const root = '/home/antonov/Base/Libs/FCModel';
const output = path.join(root, 'work/1_2_2026-09-11_test_summary.csv');
const support = path.dirname(new URL(import.meta.url).pathname);
const rtPath = 'work/1_2_2026-09-11_json_cleanup/roundtrip_results.json';
const fiPaths = [
  'work/1_2_2026-09-11_fidesys_import/results.json',
  'work/1_2_2026-09-11_json_cleanup/fidesys/results.json',
];
const retryPath = 'work/1_2_2026-09-11_fidesys_retry/results.json';
const read = async p => JSON.parse(await fs.readFile(path.join(root, p), 'utf8'));
const rt = await read(rtPath);
const rtMap = new Map(rt.files.map(r => [r.file, r]));
assert.equal(rtMap.size, rt.files.length);
const fiMap = new Map();
for (const source of fiPaths) {
  const report = await read(source);
  for (const record of report.files) fiMap.set(record.file, {
    ...record, report: source, runFinished: report.finished_utc,
  });
}
const retry = await read(retryPath);
const retries = new Map(retry.files.map(r => [r.file, r]));
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
const rtCounts = {}, fiCounts = {}, cross = {};
for (const name of names) {
  const r = rtMap.get(name), f = fiMap.get(name);
  assert.ok(f, name);
  const digest = crypto.createHash('sha256').update(await fs.readFile(path.join(corpus, name))).digest('hex');
  assert.equal(digest, r.sha256, 'Stale roundtrip: ' + name);
  assert.equal(digest, f.sha256, 'Stale Fidesys: ' + name);
  assert.equal(r.source_unchanged, true);
  assert.equal(f.source_unchanged, true);
  const done = f.completion !== null;
  const good = f.status === 'loaded_without_errors';
  assert.ok(['loaded_without_errors', 'import_error', 'incomplete'].includes(f.status));
  if (good) assert.ok(done && f.completion.errors === 0 && f.errors.length === 0);
  const fiLabel = good ? (f.warnings.length ? 'Без ошибок, с предупреждениями' : 'Без ошибок и предупреждений')
    : f.status === 'import_error' ? 'Ошибки импорта' : 'Завершение не подтверждено';
  const compare = !done ? 'Импорт Fidesys не подтверждён'
    : r.status === 'equal' ? (good ? 'Оба теста пройдены' : 'Только roundtrip пройден')
    : good ? 'Только Fidesys без ошибок' : 'Оба теста с проблемами';
  const ds = r.differences ?? [];
  const again = retries.get(name);
  if (again) assert.equal(again.sha256, digest);
  const log = path.join(path.dirname(f.report), f.log);
  await fs.access(path.join(root, log));
  const retryLog = again ? path.join(path.dirname(retryPath), again.log) : '';
  if (retryLog) await fs.access(path.join(root, retryLog));
  rows.push([
    name, rtLabels[r.status], fiLabel, compare,
    r.stage ?? '', r.error_type ?? '', r.error ?? '', r.location ?? '',
    r.status === 'error' ? null : ds.length,
    [...new Set(ds.map(d => kinds[d.kind] ?? d.kind))].sort().join(' | '),
    [...new Set(ds.map(d => d.path))].join(' | '), ds.length ? JSON.stringify(ds) : '',
    done ? f.completion.errors : null, done ? f.errors.length : null, f.errors.join(' | '),
    f.primary_errors.join(' | '), f.warnings.length, f.warnings.join(' | '), done ? 'Да' : 'Нет',
    done ? f.completion.nodes : null, done ? f.completion.elements : null,
    !done ? 'Процесс завершился до контрольного маркера без сообщения об ошибке. Успешный импорт не подтверждён.'
      : good ? (f.warnings.length ? 'Счётчик ошибок API равен нулю; предупреждения сохранены отдельно.' : 'Импорт завершён, ошибок и предупреждений нет.')
      : 'Команда импорта завершена с ошибками; модель могла загрузиться частично.',
    again ? 'Повторён последовательно: ' + again.status : '', f.duration_seconds, f.returncode,
    digest, 'data/fc_core_tests/' + name, rtPath, rt.finished_utc, f.report, f.runFinished, log, retryLog,
  ]);
  rtCounts[r.status] = (rtCounts[r.status] ?? 0) + 1;
  fiCounts[f.status] = (fiCounts[f.status] ?? 0) + 1;
  const key = r.status + ' / ' + f.status;
  cross[key] = (cross[key] ?? 0) + 1;
}
assert.deepEqual(rtCounts, { equal: 453, error: 66, different: 611 });
assert.equal(fiCounts.loaded_without_errors, 450);
assert.equal(fiCounts.import_error, 678);
assert.equal(fiCounts.incomplete, 2);

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
  const oldMatrix = await read('work/1_2_2026-09-11_spec_audit/previous_csv_matrix.json');
  assert.deepEqual(headers, oldMatrix[0]);
  assert.deepEqual(rows.map(row => row.map(value => value == null ? '' : String(value))), oldMatrix.slice(1));
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

const workbook = Workbook.create();
const sheet = workbook.worksheets.add('Проверки');
const matrix = [headers, ...rows];
const range = sheet.getRangeByIndexes(0, 0, matrix.length, headers.length);
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
if (specReport) {
  sheet.getRange('AH1:AL7').format.font = { name: 'Arial', size: 10 };
  sheet.getRange('AH1:AL1').format.fill = '#253746';
  sheet.getRange('AH1:AL1').format.font = { name: 'Arial', size: 10, bold: true, color: '#FFFFFF' };
  sheet.getRange('AH1:AH7').format.columnWidth = 60;
  sheet.getRange('AI1:AL7').format.columnWidth = 37;
  const specPreview = await workbook.render({ sheetName: 'Проверки', range: 'AH1:AL7', scale: 1, format: 'png' });
  await fs.writeFile(path.join(support, 'spec_preview.png'), new Uint8Array(await specPreview.arrayBuffer()));
}
const verification = { rows: rows.length, columns: headers.length, rtCounts, fiCounts, cross,
  matchedSourceHashes: names.length, delimiter: ',', encoding: 'UTF-8 with BOM',
  maxCellCharacters: Math.max(...rows.flat().map(v => v == null ? 0 : String(v).length)),
  output, specStatuses: specReport?.statuses ?? null, created_utc: new Date().toISOString() };
await fs.writeFile(path.join(support, 'verification.json'), JSON.stringify(verification, null, 2) + '\n');
console.log(JSON.stringify(verification));
