#!/usr/bin/env bash
# Deploy a GitHub Pages: sube el CACHE_VERSION del service worker (para forzar
# actualizacion en clientes con la PWA instalada), commitea y pushea.
# Uso:  ./deploy.sh ["mensaje de commit opcional"]
set -euo pipefail

# Situarse en la raiz del repo (donde vive este script)
cd "$(dirname "$0")"

SW="sw.js"

# Extraer la version actual del cache: cy-quiz-vN
current=$(grep -oE "cy-quiz-v[0-9]+" "$SW" | head -1)
if [ -z "$current" ]; then
  echo "Error: no se encontro CACHE_VERSION (cy-quiz-vN) en $SW" >&2
  exit 1
fi

# Calcular la siguiente version
num=${current##*-v}
next=$((num + 1))
new="cy-quiz-v${next}"

# Reemplazo portable (mac/linux) sin depender de 'sed -i'
tmp=$(mktemp)
sed "s/${current}/${new}/" "$SW" > "$tmp" && mv "$tmp" "$SW"
echo "CACHE_VERSION: ${current} -> ${new}"

# Commit + push de todo lo pendiente
msg="${1:-Deploy: bump cache a ${new}}"
git add -A
git commit -m "$msg"
git push

echo "OK · Deploy lanzado (${new})"
