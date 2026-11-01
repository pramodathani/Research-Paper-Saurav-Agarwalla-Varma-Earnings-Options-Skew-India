/* Asymmetric uncertainty around earnings in India: companion page.
   Reads data/snapshot.json once, keeps the chosen specification in the URL
   hash and redraws every live table and chart when it changes. */
'use strict';

const COLOURS = {
  blue: '#4285f4',
  red: '#ea4335',
  yellow: '#fbbc05',
  green: '#34a853',
  grey: '#9aa0a6',
  dark: '#202124',
};
const FONT = "'Times New Roman', Tinos, 'Liberation Serif', serif";
const TERCILES = [
  ['1', 'Large negative surprise', COLOURS.red],
  ['2', 'Small surprise', COLOURS.grey],
  ['3', 'Large positive surprise', COLOURS.blue],
];
const REGRESSION_LAYOUT = [
  ['Table 6', 'Smile from the quadratic fit, n = 1', ['(1)', '(2)'], ['RR-IV', 'P/C', 'ATM-IV']],
  ['Table 7', 'Smile from the quadratic fit, n = 2 and 3', ['n=2', 'n=3'], ['RR-IV', 'P/C', 'ATM-IV']],
  ['Table 8', 'Moneyness-bucket smile, n = 1', ['(1)', '(2)'], ['Alt RR-IV', 'P/C', 'Alt ATM-IV']],
  ['Table 9', 'Moneyness-bucket smile, n = 2 and 3', ['n=2', 'n=3'], ['Alt RR-IV', 'P/C', 'Alt ATM-IV']],
];
const CONTROL_NAMES = ['beta', 'momentum', 'size', 'bhar'];
const CONTROL_LABELS = { beta: 'Beta', momentum: 'Momentum', size: 'Size', bhar: 'BHAR(−10, −2)' };

const state = {
  sample: 'main',
  smile: 'main',
  surprise: 'sue',
  pc: 'contracts',
  se: 'classical',
  signal: 'RR-IV',
  period: '2015-2019',
  costs: 'gross',
};
let snapshot = null;
const charts = {};

/* ---------- small helpers ---------- */

function el(id) {
  return document.getElementById(id);
}

function fmt(value, digits) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '';
  }
  return value.toFixed(digits).replace('-', '−');
}

function stars(t) {
  if (t === null || t === undefined) {
    return '';
  }
  const size = Math.abs(t);
  if (size >= 2.576) {
    return '***';
  }
  if (size >= 1.96) {
    return '**';
  }
  if (size >= 1.645) {
    return '*';
  }
  return '';
}

function negativeClass(value) {
  return value !== null && value !== undefined && value < 0 ? ' class="negative"' : '';
}

/* ---------- the specification ---------- */

function readHash() {
  const hash = window.location.hash.replace('#', '');
  if (!hash) {
    return;
  }
  hash.split('&').forEach((part) => {
    const [key, value] = part.split('=');
    if (key in state && value !== undefined) {
      state[key] = decodeURIComponent(value);
    }
  });
}

function writeHash() {
  const hash = Object.keys(state).map((key) => `${key}=${encodeURIComponent(state[key])}`).join('&');
  history.replaceState(null, '', `#${hash}`);
}

function runKey() {
  if (state.sample === 'extension') {
    return 'extension';
  }
  return snapshot.runs[state.smile] ? state.smile : 'main';
}

function regressionKey() {
  if (state.surprise === 'alternative') {
    return 'alternative_contracts';
  }
  return state.pc === 'value' ? 'sue_value' : 'sue_contracts';
}

function setupControls() {
  const bindings = {
    'control-sample': 'sample',
    'control-smile': 'smile',
    'control-surprise': 'surprise',
    'control-pc': 'pc',
    'control-se': 'se',
    'control-signal': 'signal',
    'control-period': 'period',
    'control-costs': 'costs',
  };
  const smile = el('control-smile');
  Array.from(smile.options).forEach((option) => {
    if (!snapshot.runs[option.value]) {
      option.disabled = true;
      option.textContent += ' (building)';
    }
  });
  Object.entries(bindings).forEach(([id, key]) => {
    const control = el(id);
    control.value = state[key];
    control.addEventListener('change', () => {
      state[key] = control.value;
      writeHash();
      if (['signal', 'period', 'costs'].includes(key)) {
        drawTrading();
      } else {
        drawLive();
      }
    });
  });
}

function describeSpecification() {
  const run = snapshot.runs[runKey()];
  el('control-smile').disabled = state.sample === 'extension';
  const parts = [snapshot.run_labels[runKey()]];
  parts.push(`${run.events.toLocaleString('en-IN')} events of ${run.firms} firms`);
  parts.push(state.surprise === 'sue' ? 'SUE' : 'SUE scaled over 12 quarters');
  parts.push(state.pc === 'contracts' ? 'P/C in contracts' : 'P/C in notional value');
  parts.push(state.se === 'classical' ? 'classical standard errors' : 'standard errors clustered by firm');
  let note = '';
  if (state.surprise === 'alternative' && state.pc === 'value') {
    note = ' The alternative SUE is shown with P/C in contracts.';
  }
  if (state.sample === 'extension') {
    note += ' The smile variants exist for 2015–2019 only.';
  }
  el('spec-summary').innerHTML = parts.join(' · ') + '.' + note;
}

/* ---------- charts ---------- */

function chart(id) {
  if (!charts[id]) {
    charts[id] = echarts.init(el(id), null, { renderer: 'svg' });
    window.addEventListener('resize', () => charts[id].resize());
  }
  return charts[id];
}

function narrow() {
  return window.innerWidth < 600;
}

function baseOption() {
  return {
    textStyle: { fontFamily: FONT, fontSize: 13, color: COLOURS.dark },
    grid: { left: 52, right: 18, top: narrow() ? 64 : 40, bottom: 42 },
    legend: { top: 0, itemGap: 28, textStyle: { fontFamily: FONT, fontSize: 13 } },
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' }, textStyle: { fontFamily: FONT } },
  };
}

function eventAxis(offsets) {
  return {
    type: 'category',
    data: offsets.map((o) => (o > 0 ? `+${o}` : String(o))),
    name: 'Trading days from the announcement',
    nameLocation: 'middle',
    nameGap: 28,
    axisTick: { show: false },
  };
}

function valueAxis(digits) {
  return {
    type: 'value',
    scale: true,
    splitLine: { lineStyle: { color: '#e8eaed' } },
    axisLabel: { formatter: (v) => fmt(v, digits) },
  };
}

function dayZeroLine() {
  return { silent: true, symbol: 'none', lineStyle: { color: COLOURS.dark, type: 'dashed', width: 1 }, data: [{ xAxis: '0' }], label: { show: false } };
}

function line(name, data, colour, width = 2) {
  return { name, type: 'line', data, showSymbol: false, lineStyle: { width, color: colour }, itemStyle: { color: colour } };
}

function paperPoints(name, offsets, points) {
  const data = offsets.map((o) => (String(o) in points ? points[String(o)] : null));
  return { name, type: 'scatter', data, symbolSize: 7, itemStyle: { color: COLOURS.dark }, z: 5 };
}

function drawFigureOne(run) {
  const f = run.figure_1;
  const offsets = f.atm_iv_normalised.offsets;
  const option = baseOption();
  option.xAxis = eventAxis(offsets);
  option.yAxis = valueAxis(2);
  option.series = [
    line('ATM-IV', f.atm_iv_normalised.mean, COLOURS.blue),
    line('IV(Δ = 0.75)', f.iv_75_normalised.mean, COLOURS.red),
    line('IV(Δ = 0.25)', f.iv_25_normalised.mean, COLOURS.green),
  ];
  option.series[0].markLine = dayZeroLine();
  chart('chart-figure-1').setOption(option, true);
}

function drawTerciles(id, figure, digits, paper) {
  const offsets = figure.offsets;
  const option = baseOption();
  option.xAxis = eventAxis(offsets);
  option.yAxis = valueAxis(digits);
  option.series = TERCILES.filter(([key]) => figure[key]).map(([key, name, colour]) => line(name, figure[key], colour));
  if (option.series.length) {
    option.series[0].markLine = dayZeroLine();
  }
  if (paper) {
    option.series.push(paperPoints('Paper, large negative', offsets, paper));
  }
  chart(id).setOption(option, true);
}

function drawFigureFour(run) {
  const os = run.figure_4.os_ratio;
  const of = run.figure_4.of_ratio;
  const offsets = os.offsets;
  const labels = offsets.map((o) => (o > 0 ? `+${o}` : String(o)));
  const option = baseOption();
  option.grid = [
    { left: 52, right: 18, top: 50, height: '31%' },
    { left: 52, right: 18, top: '56%', height: '31%' },
  ];
  option.xAxis = [
    { type: 'category', data: labels, gridIndex: 0, axisTick: { show: false } },
    { type: 'category', data: labels, gridIndex: 1, axisTick: { show: false }, name: 'Trading days from the announcement', nameLocation: 'middle', nameGap: 28 },
  ];
  option.yAxis = [
    { ...valueAxis(1), gridIndex: 0, name: 'O/S', nameTextStyle: { fontFamily: FONT } },
    { ...valueAxis(2), gridIndex: 1, name: 'O/F', nameTextStyle: { fontFamily: FONT } },
  ];
  const paper = snapshot.paper.figure_4;
  const showPaper = state.sample === 'main';
  option.series = [
    { ...line('This study', os.mean, COLOURS.blue), xAxisIndex: 0, yAxisIndex: 0, markLine: dayZeroLine() },
    { ...line('This study', of.mean, COLOURS.blue), xAxisIndex: 1, yAxisIndex: 1, markLine: dayZeroLine() },
  ];
  if (showPaper) {
    option.series.push({ ...paperPoints('Paper', offsets, paper.os_ratio), xAxisIndex: 0, yAxisIndex: 0 });
    option.series.push({ ...paperPoints('Paper', offsets, paper.of_ratio), xAxisIndex: 1, yAxisIndex: 1 });
  }
  option.legend.data = showPaper ? ['This study', 'Paper'] : ['This study'];
  chart('chart-figure-4').setOption(option, true);
}

/* ---------- tables ---------- */

function drawTableOne() {
  const columns = snapshot.table_1;
  const head = `<thead><tr><th></th>${columns.map((c) => `<th>${c.name}</th>`).join('')}</tr></thead>`;
  const rows = [['Spot price', (c) => fmt(c.spot, 2)]];
  ['ITM', 'ATM', 'OTM'].forEach((label, i) => {
    rows.push([`${label} strike`, (c) => fmt(c.strikes[i], 2)]);
    rows.push([`${label} premium`, (c) => fmt(c.premiums[i], 2)]);
    rows.push([`${label}-IV (%)`, (c) => fmt(c.volatilities[i], 2)]);
  });
  rows.push(['RR-IV (OTM − ITM, points)', (c) => fmt(c.risk_reversal, 2)]);
  const body = rows.map(([label, value], i) => `<tr${i % 3 === 1 ? ' class="group-start"' : ''}><th>${label}</th>${columns.map((c) => `<td>${value(c)}</td>`).join('')}</tr>`).join('');
  el('table-one').innerHTML = `${head}<tbody>${body}</tbody>`;
}

function drawTableFive(run) {
  const labels = { atm_iv: 'ATM-IV', iv_75: 'IV(Δ = 0.75)', iv_25: 'IV(Δ = 0.25)' };
  const head = '<thead><tr><th></th><th>Pre-EA month</th><th>EA month</th><th>Post-EA month</th><th>EA − pre</th><th>EA − post</th></tr></thead>';
  const body = run.table_5.map((r, i) => {
    const p = snapshot.paper.table_5[r.parameter];
    const ours = `<tr${i ? ' class="group-start"' : ''}><th>${labels[r.parameter]}</th><td>${fmt(r.pre, 3)}</td><td>${fmt(r.ea, 3)}</td><td>${fmt(r.post, 3)}</td>`
      + `<td>${fmt(r.ea_minus_pre, 3)}<span class="t">${fmt(r.t_welch_pre, 2)} (${fmt(r.t_paired_pre, 1)})</span></td>`
      + `<td>${fmt(r.ea_minus_post, 3)}<span class="t">${fmt(r.t_welch_post, 2)} (${fmt(r.t_paired_post, 1)})</span></td></tr>`;
    const paper = state.sample === 'main'
      ? `<tr><th class="paper">&nbsp;&nbsp;paper</th><td class="paper">${fmt(p[0], 3)}</td><td class="paper">${fmt(p[1], 3)}</td><td class="paper">${fmt(p[2], 3)}</td><td class="paper">${fmt(p[3], 3)}<span class="t">${fmt(p[4], 2)}</span></td><td class="paper">${fmt(p[5], 3)}<span class="t">${fmt(p[6], 2)}</span></td></tr>`
      : '';
    return ours + paper;
  }).join('');
  const events = run.table_5[0].events;
  el('table-five').innerHTML = `${head}<tbody>${body}</tbody><caption style="caption-side:bottom;text-align:left;font-size:13px;color:#5f6368;padding-top:4px">${Math.round(events).toLocaleString('en-IN')} events with at least five fitted days in each month.</caption>`;
}

function drawTableThree(run) {
  const labels = {
    sue: 'SUE', rr_iv_1: 'RR-IV, day −1', atm_iv_1: 'ATM-IV, day −1', pc_contracts_1: 'P/C, day −1',
    rr_iv_2: 'RR-IV, day −2', atm_iv_2: 'ATM-IV, day −2', pc_contracts_2: 'P/C, day −2',
    rr_iv_3: 'RR-IV, day −3', atm_iv_3: 'ATM-IV, day −3', pc_contracts_3: 'P/C, day −3',
    beta: 'Beta', momentum: 'Momentum', size: 'Size (log ₹ million)', bhar: 'BHAR(−10, −2)',
  };
  const head = '<thead><tr><th></th><th>N</th><th>Mean</th><th>St. dev.</th><th>Median</th><th class="paper">Paper N</th><th class="paper">Paper mean</th><th class="paper">Paper st. dev.</th></tr></thead>';
  const body = run.table_3.map((r) => {
    const p = snapshot.paper.table_3[r.variable] || [null, null, null];
    const showPaper = state.sample === 'main';
    return `<tr><th>${labels[r.variable] || r.variable}</th><td>${Math.round(r.N).toLocaleString('en-IN')}</td><td>${fmt(r.mean, 3)}</td><td>${fmt(r.st_dev, 3)}</td><td>${fmt(r.median, 3)}</td>`
      + `<td class="paper">${showPaper && p[0] ? p[0].toLocaleString('en-IN') : ''}</td><td class="paper">${showPaper ? fmt(p[1], 3) : ''}</td><td class="paper">${showPaper ? fmt(p[2], 3) : ''}</td></tr>`;
  }).join('');
  el('table-three').innerHTML = `${head}<tbody>${body}</tbody>`;
}

function drawTableFour(run) {
  const names = { rr: 'RR-IV', atm: 'ATM-IV', pc: 'P/C' };
  const lookup = {};
  run.table_4.forEach((r) => {
    lookup[r.variable] = r.sue;
  });
  const head = '<thead><tr><th>Correlation with SUE</th><th>Day −1</th><th>Day −2</th><th>Day −3</th></tr></thead>';
  const body = ['rr', 'atm', 'pc'].map((k) => {
    const variable = (n) => (k === 'pc' ? `pc_contracts_${n}` : `${k}_iv_${n}`);
    const ours = `<tr class="group-start"><th>${names[k]}</th>${[1, 2, 3].map((n) => `<td>${fmt(lookup[variable(n)], 3)}</td>`).join('')}</tr>`;
    const paper = state.sample === 'main'
      ? `<tr><th class="paper">&nbsp;&nbsp;paper</th>${[1, 2, 3].map((n) => `<td class="paper">${fmt(snapshot.paper.table_4[variable(n)], 3)}</td>`).join('')}</tr>`
      : '';
    return ours + paper;
  }).join('');
  el('table-four').innerHTML = `${head}<tbody>${body}</tbody>`;
}

function regressionCell(row) {
  if (!row) {
    return '<td></td>';
  }
  const t = state.se === 'classical' ? row.t_statistic : row.clustered_t_statistic;
  const beneath = state.se === 'classical' ? `(${fmt(row.standard_error, 3)})` : `[${fmt(row.clustered_t_statistic, 2)}]`;
  return `<td>${fmt(row.coefficient, 3)}${stars(t)}<span class="t">${beneath}</span></td>`;
}

function paperCell(table, column, variable) {
  const row = snapshot.paper.regressions.find((r) => r.table === table && r.column === column && r.variable === variable);
  if (!row || state.sample !== 'main') {
    return '<td class="paper"></td>';
  }
  if (row.standard_error === null) {
    const digits = variable === 'observations' ? 0 : 3;
    const text = variable === 'observations' ? Math.round(row.coefficient).toLocaleString('en-IN') : fmt(row.coefficient, digits);
    return `<td class="paper">${text}</td>`;
  }
  return `<td class="paper">${fmt(row.coefficient, 3)}${stars(row.coefficient / row.standard_error)}<span class="t">(${fmt(row.standard_error, 3)})</span></td>`;
}

function drawRegressions(run) {
  const rows = run.regressions[regressionKey()];
  const find = (table, column, variable) => rows.find((r) => r.table === table && r.column === column && r.variable === variable);
  const head = '<thead><tr><th></th><th>Column 1</th><th class="paper">Paper</th><th>Column 2</th><th class="paper">Paper</th></tr></thead>';
  const body = REGRESSION_LAYOUT.map(([table, title, columns, variables]) => {
    const columnNames = columns.map((c) => (c.startsWith('n=') ? c.replace('n=', 'n = ') : c));
    let html = `<tr class="group-start"><th colspan="5"><b>${table}</b>: ${title}, columns ${columnNames.join(' and ')}</th></tr>`;
    [...variables, ...CONTROL_NAMES].forEach((variable) => {
      html += `<tr><th>${CONTROL_LABELS[variable] || variable}</th>`;
      columns.forEach((column) => {
        html += regressionCell(find(table, column, variable)) + paperCell(table, column, variable);
      });
      html += '</tr>';
    });
    html += '<tr><th>Observations</th>';
    columns.forEach((column) => {
      const r = find(table, column, variables[0]);
      html += `<td>${r ? Math.round(r.observations).toLocaleString('en-IN') : ''}</td>${paperCell(table, column, 'observations')}`;
    });
    html += '</tr><tr><th>Adjusted R² (within)</th>';
    columns.forEach((column) => {
      const r = find(table, column, variables[0]);
      html += `<td>${r ? `${fmt(r.adjusted_r2, 3)}<span class="t">(${fmt(r.within_r2, 3)})</span>` : ''}</td>${paperCell(table, column, 'adjusted_r2')}`;
    });
    html += '</tr><tr><th>Year-quarter effects</th>';
    columns.forEach((column) => {
      const yes = column !== '(1)';
      html += `<td>${yes ? 'Yes' : 'No'}</td><td class="paper">${yes ? 'Yes' : 'No'}</td>`;
    });
    return `${html}</tr>`;
  }).join('');
  el('table-regressions').innerHTML = `${head}<tbody>${body}</tbody>`;
}

function drawSensitivity() {
  const head = '<thead><tr><th>Variant (2015–2019)</th><th>Events</th><th>SUE events</th><th>ATM-IV EA − pre</th><th>RR-IV</th><th>P/C</th><th>ATM-IV</th><th>RR-IV n = 2</th><th>RR-IV n = 3</th><th>Alt RR-IV</th></tr></thead>';
  const pair = (value, t) => `<td>${fmt(value, 2)}${stars(t)}<span class="t">(${fmt(t, 2)})</span></td>`;
  const body = snapshot.sensitivity.map((r) => `<tr><th>${r.variant}</th><td>${Math.round(r.events).toLocaleString('en-IN')}</td><td>${Math.round(r.observations).toLocaleString('en-IN')}</td>`
    + `<td>${fmt(r.atm_ea_minus_pre, 3)}<span class="t">(${fmt(r.atm_t_welch, 2)})</span></td>`
    + pair(r.t6_rr_coefficient, r.t6_rr_t) + pair(r.t6_pc_coefficient, r.t6_pc_t) + pair(r.t6_atm_coefficient, r.t6_atm_t)
    + pair(r.t7_n2_rr_coefficient, r.t7_n2_rr_t) + pair(r.t7_n3_rr_coefficient, r.t7_n3_rr_t) + pair(r.t8_alt_rr_coefficient, r.t8_alt_rr_t)
    + '</tr>').join('');
  el('table-sensitivity').innerHTML = `${head}<tbody>${body}</tbody>`;
}

/* ---------- the trading test ---------- */

function tradingRow(signal, period, costs) {
  const name = costs === 'gross' ? 'STT 0.01% (rate in force to Sep 2024)' : costs;
  return snapshot.trading.summary.find((r) => r.signal === signal && r.period === period && r.costs === name);
}

function yearAxis(dates) {
  return {
    type: 'category',
    data: dates,
    axisTick: { show: false },
    axisLabel: {
      interval: (index) => index === 0 || dates[index].slice(0, 4) !== dates[index - 1].slice(0, 4),
      formatter: (v) => v.slice(0, 4),
    },
  };
}

function wealthAndDrawdown(values) {
  let wealth = 1;
  let peak = 1;
  const growth = [];
  const drawdown = [];
  values.forEach((v) => {
    wealth *= 1 + (v || 0);
    peak = Math.max(peak, wealth);
    growth.push(Number(wealth.toFixed(5)));
    drawdown.push(Number((wealth / peak - 1).toFixed(5)));
  });
  return { growth, drawdown };
}

function drawTrading() {
  const row = tradingRow(state.signal, state.period, state.costs);
  const gross = state.costs === 'gross';
  const prefix = gross ? 'gross' : 'net';
  const cards = [
    ['blue', 'Trades', row.trades.toLocaleString('en-IN'), `${row.days.toLocaleString('en-IN')} trading days`],
    ['red', 'Per trade, before costs', `${fmt(100 * row.mean_trade_return, 2)}%`, `hit rate ${fmt(100 * row.hit_rate, 1)}%`],
    ['yellow', gross ? 'Annual, before costs' : 'Annual, after costs', `${fmt(100 * row[`${prefix}_annual`], 1)}%`, `Newey-West t ${fmt(row[`${prefix}_nw_t`], 2)}`],
    ['green', 'Worst drawdown', `${fmt(100 * row[`${prefix}_max_drawdown`], 1)}%`, `round trip ${fmt(100 * row.round_trip_cost, 2)}%`],
  ];
  el('trade-cards').innerHTML = cards.map(([colour, label, value, sub]) => `<div class="stat-card ${colour}"><div class="label">${label}</div><div class="value">${value}</div><div class="sub">${sub}</div></div>`).join('');
  const daily = snapshot.trading.daily[state.period];
  const lines = daily.lines[state.signal];
  const values = gross ? lines.gross : lines[state.costs];
  const curves = wealthAndDrawdown(values);
  const growth = baseOption();
  growth.xAxis = yearAxis(daily.dates);
  growth.yAxis = valueAxis(2);
  growth.series = [line(gross ? 'Before costs' : 'After costs', curves.growth, gross ? COLOURS.blue : COLOURS.red, 1.5)];
  chart('chart-trade-growth').setOption(growth, true);
  const drawdown = baseOption();
  drawdown.xAxis = yearAxis(daily.dates);
  drawdown.yAxis = { type: 'value', axisLabel: { formatter: (v) => `${Math.round(v * 100)}%` }, splitLine: { lineStyle: { color: '#e8eaed' } } };
  drawdown.legend.show = false;
  drawdown.series = [{ ...line('Drawdown', curves.drawdown, COLOURS.red, 1), areaStyle: { color: 'rgba(234,67,53,0.18)' } }];
  chart('chart-trade-drawdown').setOption(drawdown, true);
  drawTradingTable();
}

function drawTradingTable() {
  const head = '<thead><tr><th>Signal</th><th>Period</th><th>Trades</th><th>Per trade, gross</th><th>Hit rate</th><th>Annual, gross</th><th>Annual, net STT 0.01%</th><th>Annual, net STT 0.05%</th><th>Worst drawdown, net 0.01%</th></tr></thead>';
  const signals = ['RR-IV', 'P/C', 'RR-IV and P/C'];
  const periods = ['2015-2019', '2020-Mar 2025'];
  let body = '';
  signals.forEach((signal, s) => {
    periods.forEach((period, p) => {
      const low = tradingRow(signal, period, 'STT 0.01% (rate in force to Sep 2024)');
      const high = tradingRow(signal, period, 'STT 0.05% (library default, 2026 rate)');
      const chosen = signal === state.signal && period === state.period;
      body += `<tr class="${s && !p ? 'group-start' : ''}${chosen ? ' highlight' : ''}"><th>${p ? '' : signal}</th><th>${period.replace('-Mar', '–Mar ').replace('2015-2019', '2015–2019')}</th><td>${low.trades.toLocaleString('en-IN')}</td>`
        + `<td class="negative">${fmt(100 * low.mean_trade_return, 2)}%</td><td>${fmt(100 * low.hit_rate, 1)}%</td>`
        + `<td${negativeClass(low.gross_annual)}>${fmt(100 * low.gross_annual, 1)}%<span class="t">(${fmt(low.gross_nw_t, 2)})</span></td>`
        + `<td${negativeClass(low.net_annual)}>${fmt(100 * low.net_annual, 1)}%<span class="t">(${fmt(low.net_nw_t, 2)})</span></td>`
        + `<td${negativeClass(high.net_annual)}>${fmt(100 * high.net_annual, 1)}%<span class="t">(${fmt(high.net_nw_t, 2)})</span></td>`
        + `<td class="negative">${fmt(100 * low.net_max_drawdown, 1)}%</td></tr>`;
    });
  });
  el('table-trading').innerHTML = `${head}<tbody>${body}</tbody>`;
}

/* ---------- putting it together ---------- */

function drawLive() {
  const run = snapshot.runs[runKey()];
  describeSpecification();
  drawFigureOne(run);
  drawTerciles('chart-figure-2', run.figure_2, 2, null);
  drawTerciles('chart-figure-3', run.figure_3, 3, state.sample === 'main' ? snapshot.paper.figure_3 : null);
  drawTerciles('chart-figure-5', state.pc === 'value' ? run.figure_5_value : run.figure_5, 2, null);
  drawFigureFour(run);
  drawTableFive(run);
  drawTableThree(run);
  drawTableFour(run);
  drawRegressions(run);
}

function setupCitation() {
  el('copy-citation').addEventListener('click', () => {
    navigator.clipboard.writeText(el('citation-text').textContent);
    el('copy-citation').textContent = 'Copied';
  });
}

async function main() {
  const response = await fetch('data/snapshot.json');
  snapshot = await response.json();
  readHash();
  if (!snapshot.runs[state.smile]) {
    state.smile = 'main';
  }
  setupControls();
  setupCitation();
  drawTableOne();
  drawSensitivity();
  drawLive();
  drawTrading();
}

main();
