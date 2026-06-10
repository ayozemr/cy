#!/usr/bin/env python3
"""Extrae preguntas de los examenes de Capitan de Yate (CARM Murcia).

Las respuestas correctas estan subrayadas en el PDF. El subrayado es un grafico
(linea/rectangulo fino) que se casa por posicion con los spans de texto.
Excluye las preguntas 11-20 (calculos de navegacion).
"""
import fitz
import json
import os
import re
import unicodedata

PDF_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'pdfs')
OUT_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'questions.json')
REPORT_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'extraction_report.txt')

MONTH_LABEL = {'03': 'Marzo', '04': 'Abril', '06': 'Junio', '07': 'Julio', '10': 'Octubre', '11': 'Noviembre'}

MODULES = [
    ((1, 10), 'navegacion'),
    ((11, 20), 'calculos'),   # se excluyen
    ((21, 30), 'meteorologia'),
    ((31, 40), 'ingles'),
]

# lineas transparentes (cabeceras/pies de pagina): se ignoran sin cerrar la pregunta en curso
SKIP_PATTERNS = [
    r'^Regi[oó]n de Murcia',
    r'^Consejer[ií]a',
    r'^Direcci[oó]n General',
    r'^Plaza Santo[ñn]a',
    r'http',
    r'^\d+\s*/\s*\d+$',                      # pie "2/10"
    r'^C\.?\s*Y\.?\s*[-–]?\s*Tipo',          # pie "C.Y. - Tipo 1"
    r'^CAPIT[AÁ]N',
    r'^Tipo\s*1$',
    r'CAPIT[AÁ]N DE YATE',                   # cabecera "MARZO-2026  CAPITÁN DE YATE  Tipo 1"
]
SKIP_RE = [re.compile(p, re.IGNORECASE) for p in SKIP_PATTERNS]

# separadores de seccion: cierran la pregunta en curso (el texto que sigue, p.ej. la
# introduccion de los problemas de calculo, no pertenece a ninguna pregunta)
SECTION_PATTERNS = [
    r'^M[OÓ]DULO',
    r'^Unidad te[oó]rica',
]
SECTION_RE = [re.compile(p, re.IGNORECASE) for p in SECTION_PATTERNS]

Q_RE = re.compile(r'^(\d{1,2})\s*[ºo°]?\s*[.\-]{1,3}\s*(.*)$')
OPT_RE = re.compile(r'^([a-d])[.\)]\s+(.*)$')

# correcciones puntuales de artefactos de extraccion: id -> [(texto_antiguo, texto_nuevo)]
# se aplican sobre el enunciado y las opciones ya limpias
FIXES = {
    '2022-04-q32': [('<Correction', '“Correction')],
    '2023-03-q31': [('<QUESTION. Can I have permission to use the shallow draft fairway at this time',
                     '“QUESTION. Can I have permission to use the shallow draft fairway at this time”')],
    '2023-06-q36': [('follows: = Dredging', 'follows: “Dredging'),
                    ('Wide berth requested=', 'Wide berth requested”')],
    '2023-11-q33': [('<Do I have permission to enter the fairway?"', '“Do I have permission to enter the fairway?”')],
    '2023-06-q2': [('El polo oriental. 1', 'El polo oriental.')],
}


def apply_fixes(q):
    for old, new in FIXES.get(q['id'], []):
        q['question'] = q['question'].replace(old, new)
        q['options'] = [o.replace(old, new) for o in q['options']]
    return q


def module_for(num):
    for (lo, hi), name in MODULES:
        if lo <= num <= hi:
            return name
    return None


def page_lines(page):
    """Lineas visuales de la pagina: (texto, chars_subrayados, chars_totales)."""
    underlines = []
    for d in page.get_drawings():
        r = d['rect']
        if r.height < 3.5 and r.width > 6:
            underlines.append(r)

    raw = []
    td = page.get_text('dict')
    for block in td['blocks']:
        if block['type'] != 0:
            continue
        for line in block['lines']:
            x0, y0 = line['bbox'][0], line['bbox'][1]
            text = ''
            ul_chars = 0.0
            total = 0
            for span in line['spans']:
                t = span['text']
                sx0, _, sx1, sy1 = span['bbox']
                ov = 0.0
                for r in underlines:
                    if sy1 - 5 <= r.y1 <= sy1 + 2.5:
                        ov += max(0.0, min(sx1, r.x1) - max(sx0, r.x0))
                width = max(sx1 - sx0, 0.001)
                frac = min(ov / width, 1.0)
                n = len(t.strip())
                ul_chars += frac * n
                total += n
                text += t
            text = re.sub(r'\s+', ' ', text).strip()
            if text:
                raw.append((y0, x0, text, ul_chars, total))
    raw.sort(key=lambda r: (round(r[0], 1), r[1]))
    return [(t, u, n) for _, _, t, u, n in raw]


def clean_text(s):
    s = unicodedata.normalize('NFC', s)
    s = re.sub(r'\s+', ' ', s).strip()
    # comillas tipograficas de Word mal codificadas en algunos PDF: <texto= -> "texto"
    s = re.sub(r'<([^<=>]{1,90}?)=', r'“\1”', s)
    return s


def parse_exam(pdf_path):
    doc = fitz.open(pdf_path)
    lines = []
    for page in doc:
        for text, ul, total in page_lines(page):
            if any(rx.search(text) for rx in SKIP_RE):
                continue
            lines.append((text, ul, total))

    questions = []
    cur_q = None       # {'number', 'text_parts', 'options': [...]}
    cur_opt = None     # {'letter', 'parts', 'ul', 'total'}

    def close_question():
        nonlocal cur_q, cur_opt
        if cur_q is not None:
            if cur_opt is not None:
                cur_q['options'].append(cur_opt)
            if len(cur_q['options']) >= 4:
                questions.append(cur_q)
        cur_q = None
        cur_opt = None

    def looks_like_question(i):
        """Un inicio de pregunta es valido si su opcion a) aparece en las lineas
        siguientes antes que otra opcion, otra pregunta o un separador de seccion.
        Evita falsos positivos como "12.000 metros" o las filas "1 - 10" de la
        tabla de instrucciones."""
        for j in range(i + 1, min(i + 9, len(lines))):
            t = lines[j][0]
            if any(rx.search(t) for rx in SECTION_RE):
                return False
            mo = OPT_RE.match(t)
            if mo:
                return mo.group(1) == 'a'
            mq = Q_RE.match(t)
            if mq and 1 <= int(mq.group(1)) <= 40:
                return False
        return False

    for i, (text, ul, total) in enumerate(lines):
        if any(rx.search(text) for rx in SECTION_RE):
            close_question()
            continue
        mq = Q_RE.match(text)
        mo = OPT_RE.match(text)
        n_opts = (len(cur_q['options']) if cur_q else 0) + (1 if cur_opt else 0)
        # cabeceras tematicas en mayusculas entre preguntas (p.ej. "ECLIPTICA")
        if (not mq and not mo and len(text) >= 4 and not any(c.islower() for c in text)
                and (cur_q is None or n_opts >= 4)):
            close_question()
            continue
        if mq and 1 <= int(mq.group(1)) <= 40 and looks_like_question(i):
            close_question()
            cur_q = {'number': int(mq.group(1)), 'text_parts': [mq.group(2)], 'options': []}
        elif mo and cur_q is not None:
            if cur_opt is not None:
                cur_q['options'].append(cur_opt)
            cur_opt = {'letter': mo.group(1), 'parts': [mo.group(2)], 'ul': ul, 'total': total}
        elif cur_opt is not None:
            cur_opt['parts'].append(text)
            cur_opt['ul'] += ul
            cur_opt['total'] += total
        elif cur_q is not None:
            cur_q['text_parts'].append(text)
    close_question()

    return questions


def build():
    exams = sorted(f for f in os.listdir(PDF_DIR) if f.endswith('.pdf'))
    all_questions = []
    report = []
    issues = []

    for fname in exams:
        m = re.match(r'cy-(\d{4})-(\d{2})\.pdf', fname)
        if not m:
            continue
        year, month = m.group(1), m.group(2)
        exam_id = f'{year}-{month}'
        label = f'{MONTH_LABEL[month]} {year}'
        parsed = parse_exam(os.path.join(PDF_DIR, fname))

        nums = [q['number'] for q in parsed]
        report.append(f'{exam_id}: {len(parsed)} preguntas parseadas, numeros {nums[0]}-{nums[-1]}' if nums else f'{exam_id}: SIN PREGUNTAS')
        missing = [n for n in range(1, 41) if n not in nums]
        if missing:
            issues.append(f'{exam_id}: faltan numeros {missing}')
        dupes = sorted({n for n in nums if nums.count(n) > 1})
        if dupes:
            issues.append(f'{exam_id}: numeros duplicados {dupes}')

        for q in parsed:
            num = q['number']
            mod = module_for(num)
            if mod == 'calculos' or mod is None:
                continue
            opts = q['options'][:4]
            if len(q['options']) > 4:
                issues.append(f'{exam_id} q{num}: {len(q["options"])} opciones, recortado a 4')
            letters = [o['letter'] for o in opts]
            if letters != ['a', 'b', 'c', 'd']:
                issues.append(f'{exam_id} q{num}: letras {letters}')

            scores = [(o['ul'], o['ul'] / max(o['total'], 1)) for o in opts]
            best = max(range(len(opts)), key=lambda i: scores[i][0])
            best_ul, best_cov = scores[best]
            second_ul = max((scores[i][0] for i in range(len(opts)) if i != best), default=0)
            correct = None
            if best_ul >= 1.2 and best_cov >= 0.25:
                correct = best
                if second_ul > best_ul * 0.5 and second_ul >= 2.5:
                    issues.append(f'{exam_id} q{num}: subrayado ambiguo (mejor={best_ul:.1f}, segundo={second_ul:.1f})')
            else:
                issues.append(f'{exam_id} q{num}: SIN respuesta detectada (mejor subrayado {best_ul:.1f} chars, cobertura {best_cov:.2f})')

            all_questions.append(apply_fixes({
                'id': f'{exam_id}-q{num}',
                'exam': exam_id,
                'examLabel': label,
                'number': num,
                'module': mod,
                'question': clean_text(' '.join(q['text_parts'])),
                'options': [clean_text(' '.join(o['parts'])) for o in opts],
                'correct': correct,
            }))

    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_questions, f, ensure_ascii=False, indent=1)

    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report) + '\n\n=== INCIDENCIAS ===\n' + ('\n'.join(issues) if issues else 'ninguna') + '\n')

    print('\n'.join(report))
    print(f'\nTotal preguntas guardadas: {len(all_questions)}')
    print(f'\n=== INCIDENCIAS ({len(issues)}) ===')
    print('\n'.join(issues) if issues else 'ninguna')


if __name__ == '__main__':
    build()
