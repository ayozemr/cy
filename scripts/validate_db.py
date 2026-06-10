#!/usr/bin/env python3
"""Valida la base de datos de preguntas (data/questions.json).

Comprueba:
- numero de preguntas por examen (30: 10 navegacion + 10 meteorologia + 10 ingles)
- cada pregunta tiene exactamente 4 opciones no vacias
- cada pregunta tiene exactamente 1 respuesta correcta (indice 0..3)
- se excluyeron las preguntas 11-20 (calculos)
- coherencia numero de pregunta <-> modulo
- texto sin artefactos de extraccion
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'questions.json')

EXPECTED_MODULE = {}
for n in range(1, 11):
    EXPECTED_MODULE[n] = 'navegacion'
for n in range(21, 31):
    EXPECTED_MODULE[n] = 'meteorologia'
for n in range(31, 41):
    EXPECTED_MODULE[n] = 'ingles'

ARTIFACT_RE = re.compile(r'[<>=]|\.{6,}|\s{2,}')


def main():
    with open(DB, encoding='utf-8') as f:
        questions = json.load(f)

    errors = []
    warnings = []

    ids = Counter(q['id'] for q in questions)
    for qid, c in ids.items():
        if c > 1:
            errors.append(f'id duplicado: {qid} ({c} veces)')

    per_exam = defaultdict(list)
    for q in questions:
        per_exam[q['exam']].append(q)

    print(f'Examenes: {len(per_exam)}')
    print(f'Preguntas totales: {len(questions)}\n')

    print(f'{"Examen":<10} {"total":>5} {"naveg":>5} {"meteo":>5} {"ingles":>6}')
    for exam in sorted(per_exam):
        qs = per_exam[exam]
        mods = Counter(q['module'] for q in qs)
        line = f'{exam:<10} {len(qs):>5} {mods["navegacion"]:>5} {mods["meteorologia"]:>5} {mods["ingles"]:>6}'
        print(line)
        if len(qs) != 30:
            errors.append(f'{exam}: {len(qs)} preguntas (esperadas 30)')
        for mod, expected in [('navegacion', 10), ('meteorologia', 10), ('ingles', 10)]:
            if mods[mod] != expected:
                errors.append(f'{exam}: {mods[mod]} preguntas de {mod} (esperadas {expected})')

        nums = sorted(q['number'] for q in qs)
        excluded = [n for n in nums if 11 <= n <= 20]
        if excluded:
            errors.append(f'{exam}: contiene preguntas de calculos (11-20): {excluded}')
        expected_nums = list(range(1, 11)) + list(range(21, 41))
        if nums != expected_nums:
            errors.append(f'{exam}: numeros inesperados {sorted(set(nums) ^ set(expected_nums))}')

    for q in questions:
        qid = q['id']
        if len(q['options']) != 4:
            errors.append(f'{qid}: {len(q["options"])} opciones')
        if any(not o.strip() for o in q['options']):
            errors.append(f'{qid}: opcion vacia')
        if q['correct'] is None:
            errors.append(f'{qid}: sin respuesta correcta')
        elif not (isinstance(q['correct'], int) and 0 <= q['correct'] <= 3):
            errors.append(f'{qid}: correct fuera de rango: {q["correct"]}')
        if not q['question'].strip():
            errors.append(f'{qid}: enunciado vacio')
        if len(q['question']) < 12:
            warnings.append(f'{qid}: enunciado muy corto: "{q["question"]}"')
        if EXPECTED_MODULE.get(q['number']) != q['module']:
            errors.append(f'{qid}: numero {q["number"]} con modulo {q["module"]}')
        for txt in [q['question']] + q['options']:
            m = ARTIFACT_RE.search(txt)
            if m:
                warnings.append(f'{qid}: posible artefacto {m.group()!r} en: "{txt[:60]}"')

    # estadistica de repeticion (informativa): misma pregunta en varios examenes
    norm = Counter(re.sub(r'\W+', '', q['question'].lower()) for q in questions)
    repeated = sum(1 for c in norm.values() if c > 1)
    print(f'\nEnunciados unicos: {len(norm)} (de {len(questions)}); {repeated} enunciados aparecen en mas de un examen')

    dist = Counter(q['correct'] for q in questions)
    print(f'Distribucion de correctas a/b/c/d: {dist.get(0,0)}/{dist.get(1,0)}/{dist.get(2,0)}/{dist.get(3,0)}')

    print(f'\n=== ERRORES ({len(errors)}) ===')
    print('\n'.join(errors) if errors else 'ninguno')
    print(f'\n=== AVISOS ({len(warnings)}) ===')
    print('\n'.join(warnings[:40]) if warnings else 'ninguno')
    if len(warnings) > 40:
        print(f'... y {len(warnings) - 40} avisos mas')

    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
