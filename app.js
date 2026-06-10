/* Test de teoría Capitán de Yate — lógica de la app */
'use strict';

const MODULE_NAMES = {
  navegacion: 'Teoría de Navegación',
  meteorologia: 'Meteorología',
  ingles: 'Inglés',
};
const LETTERS = ['A', 'B', 'C', 'D'];
const FAILED_KEY = 'cy-failed-ids';

const $ = (id) => document.getElementById(id);

const state = {
  module: 'all',
  count: 20,
  deck: [],        // preguntas del test en curso
  index: 0,
  answered: false,
  results: [],     // {q, picked} — picked: 0..3 o null (saltada)
};

/* ===== falladas persistentes ===== */
function loadFailed() {
  try { return new Set(JSON.parse(localStorage.getItem(FAILED_KEY)) || []); }
  catch { return new Set(); }
}
function saveFailed(set) {
  localStorage.setItem(FAILED_KEY, JSON.stringify([...set]));
}
function markFailed(id, failed) {
  const set = loadFailed();
  if (failed) set.add(id); else set.delete(id);
  saveFailed(set);
}

/* ===== utilidades ===== */
function shuffle(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

function poolFor(module) {
  return module === 'all' ? QUESTIONS : QUESTIONS.filter((q) => q.module === module);
}

function show(screen) {
  ['screen-home', 'screen-quiz', 'screen-results'].forEach((id) =>
    $(id).classList.toggle('hidden', id !== screen));
  window.scrollTo(0, 0);
}

/* ===== pantalla de inicio ===== */
function updatePoolInfo() {
  const n = poolFor(state.module).length;
  $('pool-info').textContent = `${n} preguntas disponibles en el banco`;
}

function updateFailedButton() {
  const n = loadFailed().size;
  const btn = $('btn-review-failed');
  btn.classList.toggle('hidden', n === 0);
  btn.textContent = `Repasar falladas (${n})`;
}

function bindChoices(containerId, attr, onPick) {
  $(containerId).addEventListener('click', (e) => {
    const btn = e.target.closest('.choice');
    if (!btn) return;
    [...$(containerId).children].forEach((c) => c.classList.remove('selected'));
    btn.classList.add('selected');
    onPick(btn.dataset[attr]);
  });
}

bindChoices('module-choices', 'module', (v) => { state.module = v; updatePoolInfo(); });
bindChoices('count-choices', 'count', (v) => { state.count = v === 'all' ? Infinity : parseInt(v, 10); });

$('btn-start').addEventListener('click', () => {
  const pool = shuffle([...poolFor(state.module)]);
  startQuiz(pool.slice(0, Math.min(state.count, pool.length)));
});

$('btn-review-failed').addEventListener('click', () => {
  const failed = loadFailed();
  const pool = shuffle(QUESTIONS.filter((q) => failed.has(q.id)));
  if (pool.length) startQuiz(pool);
});

/* ===== test ===== */
function startQuiz(deck) {
  if (!deck.length) return;
  state.deck = deck;
  state.index = 0;
  state.results = [];
  show('screen-quiz');
  renderQuestion();
}

function renderQuestion() {
  const q = state.deck[state.index];
  state.answered = false;

  const badge = $('q-module');
  badge.textContent = MODULE_NAMES[q.module];
  badge.className = `module-badge mod-${q.module}`;

  $('q-progress').textContent = `Pregunta ${state.index + 1} de ${state.deck.length}`;
  const ok = state.results.filter((r) => r.picked === r.q.correct).length;
  const ko = state.results.filter((r) => r.picked !== null && r.picked !== r.q.correct).length;
  $('q-score').textContent = `✓ ${ok} · ✗ ${ko}`;
  $('q-progressbar').style.width = `${(state.index / state.deck.length) * 100}%`;

  $('q-text').textContent = q.question;

  const box = $('q-options');
  box.innerHTML = '';
  q.options.forEach((opt, i) => {
    const btn = document.createElement('button');
    btn.className = 'option';
    btn.innerHTML = `<span class="letter">${LETTERS[i]}</span><span class="text"></span>`;
    btn.querySelector('.text').textContent = opt;
    btn.addEventListener('click', () => answer(i, btn));
    box.appendChild(btn);
  });

  $('q-source').classList.add('hidden');
  $('btn-skip').classList.remove('hidden');
  $('btn-next').classList.add('hidden');
}

function answer(picked, pickedBtn) {
  if (state.answered) return;
  state.answered = true;

  const q = state.deck[state.index];
  const hit = picked === q.correct;
  state.results.push({ q, picked });
  markFailed(q.id, !hit);

  const buttons = [...$('q-options').children];
  buttons.forEach((b, i) => {
    b.classList.add('locked');
    if (i === q.correct) b.classList.add('correct');
    else if (i === picked) b.classList.add('wrong');
    else b.classList.add('dimmed');
  });
  if (hit) pickedBtn.classList.remove('dimmed');

  if (navigator.vibrate) navigator.vibrate(hit ? 15 : [40, 60, 40]);

  const src = $('q-source');
  src.textContent = `Examen ${q.examLabel} · Pregunta ${q.number}`;
  src.classList.remove('hidden');

  const ok = state.results.filter((r) => r.picked === r.q.correct).length;
  const ko = state.results.filter((r) => r.picked !== null && r.picked !== r.q.correct).length;
  $('q-score').textContent = `✓ ${ok} · ✗ ${ko}`;

  $('btn-skip').classList.add('hidden');
  const next = $('btn-next');
  next.textContent = state.index + 1 < state.deck.length ? 'Siguiente →' : 'Ver resultados';
  next.classList.remove('hidden');
}

function advance() {
  if (state.index + 1 < state.deck.length) {
    state.index++;
    renderQuestion();
  } else {
    renderResults();
  }
}

$('btn-next').addEventListener('click', advance);

$('btn-skip').addEventListener('click', () => {
  state.results.push({ q: state.deck[state.index], picked: null });
  advance();
});

$('btn-exit').addEventListener('click', () => {
  if (state.results.length === 0 || confirm('¿Salir del test? Se perderá el progreso.')) {
    goHome();
  }
});

/* ===== resultados ===== */
function renderResults() {
  const total = state.results.length;
  const ok = state.results.filter((r) => r.picked === r.q.correct).length;
  const skipped = state.results.filter((r) => r.picked === null).length;
  const ko = total - ok - skipped;
  const pct = total ? Math.round((ok / total) * 100) : 0;

  show('screen-results');
  $('r-ring').style.setProperty('--pct', pct);
  $('r-pct').textContent = `${pct}%`;
  $('r-title').textContent = pct >= 80 ? '¡Excelente!' : pct >= 60 ? '¡Buen trabajo!' : 'Sigue practicando';
  $('r-summary').textContent =
    `${ok} aciertos · ${ko} fallos${skipped ? ` · ${skipped} saltadas` : ''} de ${total} preguntas`;

  const byModule = {};
  state.results.forEach((r) => {
    const m = r.q.module;
    byModule[m] = byModule[m] || { ok: 0, total: 0 };
    byModule[m].total++;
    if (r.picked === r.q.correct) byModule[m].ok++;
  });
  $('r-modules').innerHTML = Object.entries(byModule).map(([m, s]) =>
    `<div class="module-row">
       <span class="module-badge mod-${m}">${MODULE_NAMES[m]}</span>
       <span class="stat">${s.ok} / ${s.total}</span>
     </div>`).join('');

  const failedNow = state.results.filter((r) => r.picked !== null && r.picked !== r.q.correct);
  const retry = $('btn-retry-failed');
  retry.classList.toggle('hidden', failedNow.length === 0);
  retry.textContent = `Repetir falladas (${failedNow.length})`;
  retry.onclick = () => startQuiz(shuffle(failedNow.map((r) => r.q)));
}

function goHome() {
  updatePoolInfo();
  updateFailedButton();
  show('screen-home');
}

$('btn-home').addEventListener('click', goHome);

/* ===== arranque ===== */
updatePoolInfo();
updateFailedButton();

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => navigator.serviceWorker.register('sw.js'));
}
