#!/usr/bin/env python3
"""Genera data.js (banco de preguntas embebido) a partir de data/questions.json."""
import json
import os

ROOT = os.path.join(os.path.dirname(__file__), '..')
SRC = os.path.join(ROOT, 'data', 'questions.json')
OUT = os.path.join(ROOT, 'data.js')


def main():
    with open(SRC, encoding='utf-8') as f:
        questions = json.load(f)
    payload = json.dumps(questions, ensure_ascii=False, separators=(',', ':'))
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('const QUESTIONS=' + payload + ';\n')
    print(f'data.js: {len(questions)} preguntas, {os.path.getsize(OUT) / 1024:.0f} KB')


if __name__ == '__main__':
    main()
