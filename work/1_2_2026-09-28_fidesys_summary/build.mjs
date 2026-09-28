import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import path from 'node:path';
import { Workbook } from '@oai/artifact-tool';

const here = path.dirname(new URL(import.meta.url).pathname);
const output = path.join(here, '../1_2_2026-09-28_fidesys_roundtrip.csv');
const report = JSON.parse(await fs.readFile(path.join(here, 'results.json'), 'utf8'));
const headers = ['Файл', 'Roundtrip_статус', 'JSON_статус', 'Число_различий',
  'Разделы_различий', 'Пути_различий', 'Описание_различий', 'Различия_JSON',
  'Импорт_завершён', 'Экспорт_завершён', 'Ошибки_импорта', 'Ошибки_экспорта',
  'Предупреждения_импорта', 'Предупреждения_экспорта', 'Ошибка_выходного_FC',
  'Узлов_вход', 'Узлов_импорт', 'Узлов_выход', 'Элементов_вход', 'Элементов_импорт',
  'Элементов_выход', 'Счётчики_совпадают'];
const kinds = { added: 'Добавлено', removed: 'Удалено', value_changed: 'Изменено значение',
  type_changed: 'Изменён тип', length_changed: 'Изменена длина массива' };
const show = value => JSON.stringify(value);
function description(d) {
  const kind = kinds[d.kind] ?? d.kind;
  if (d.kind === 'added') return `${d.path}: ${kind} ${show(d.after)}`;
  if (d.kind === 'removed') return `${d.path}: ${kind} ${show(d.before)}`;
  return `${d.path}: ${kind}, ${show(d.before)} → ${show(d.after)}` +
    (d.kind === 'type_changed' ? ` (${d.before_type} → ${d.after_type})` : '');
}
const rows = report.files.map(r => {
  const ds = r.differences;
  return [r.file, r.status, r.json_status, ds?.length ?? null,
    [...new Set((ds ?? []).map(d => d.path.split('/')[1] || '$'))].join(' | '),
    [...new Set((ds ?? []).map(d => d.path))].join(' | '),
    (ds ?? []).map(description).join('\n'), ds === null ? '' : JSON.stringify(ds),
    r.import_done ? 'Да' : 'Нет', r.export_done ? 'Да' : 'Нет',
    r.import_errors.join('\n'), r.export_errors.join('\n'),
    r.import_warnings.join('\n'), r.export_warnings.join('\n'), r.output_error,
    ...r.counts, r.counts_equal];
});
assert.equal(rows.length, 1130);
assert.equal(new Set(rows.map(r => r[0])).size, 1130);
assert.ok(rows.every(r => r.length === headers.length));
const workbook = Workbook.create();
const sheet = workbook.worksheets.add('Fidesys roundtrip');
const matrix = [headers, ...rows];
const range = sheet.getRangeByIndexes(0, 0, matrix.length, headers.length);
range.values = matrix;
workbook.recalculate();
const values = range.values;
assert.deepEqual(values, matrix);
// CSV has no styles or formulas. Serialize the verified Artifact Tool values as RFC 4180.
const field = v => v === null ? '' : '"' + String(v).replaceAll('"', '""') + '"';
await fs.writeFile(output, '\uFEFF' + values.map(row => row.map(field).join(',')).join('\r\n') + '\r\n');

// Compact QA view with representative rows; not a second deliverable.
const qa = workbook.worksheets.add('Просмотр');
const sample = [rows.find(r => r[1] === 'Пройден'), rows.find(r => r[1] === 'Расхождения JSON'),
  rows.find(r => r[1] === 'Ошибка импорта'), rows.find(r => r[1] === 'Импорт не завершён')];
assert.ok(sample.every(Boolean));
qa.getRange('A1:D5').values = [headers.slice(0, 4), ...sample.map(r => r.slice(0, 4))];
qa.getRange('A1:D5').format.font = {name: 'Arial', size: 11};
qa.getRange('A1:D5').format.wrapText = true;
qa.getRange('A1:D5').format.rowHeight = 44;
qa.getRange('A1:A5').format.columnWidth = 66;
qa.getRange('B1:C5').format.columnWidth = 30;
qa.getRange('D1:D5').format.columnWidth = 21;
qa.getRange('A1:D1').format.fill = '#253746';
qa.getRange('A1:D1').format.font = {name: 'Arial', size: 11, bold: true, color: '#FFFFFF'};
workbook.recalculate();
const png = await workbook.render({sheetName: 'Просмотр', range: 'A1:D5', scale: 1, format: 'png'});
await fs.writeFile(path.join(here, 'preview.png'), new Uint8Array(await png.arrayBuffer()));
console.log((await workbook.inspect({kind: 'table', range: 'Просмотр!A1:D5', tableMaxRows: 5, tableMaxCols: 4})).ndjson);
console.log(JSON.stringify({rows: rows.length, columns: headers.length, counts: report.counts, output}));
