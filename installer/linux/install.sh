#!/usr/bin/env bash
# Instala ProteinFunc AI Desktop para el usuario actual (sin sudo).
#   ./install.sh            instala en ~/.local/opt/proteinfunc-ai
#   ./install.sh --uninstall
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREFIX="${PROTEINFUNC_PREFIX:-$HOME/.local/opt/proteinfunc-ai}"
BIN="$HOME/.local/bin"
APPS="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICONS="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/256x256/apps"

uninstall() {
    rm -rf "$PREFIX"
    rm -f "$BIN/proteinfunc-ai" "$BIN/proteinfunc-check" "$APPS/proteinfunc-ai.desktop" "$ICONS/proteinfunc-ai.png"
    command -v update-desktop-database >/dev/null && update-desktop-database "$APPS" >/dev/null 2>&1 || true
    echo "ProteinFunc AI Desktop se desinstaló. El historial se conserva en ~/.local/share/USIL-Bioinformatica/ProteinFuncAI/."
}

if [[ "${1:-}" == "--uninstall" ]]; then
    uninstall
    exit 0
fi

if [[ ! -x "$HERE/ProteinFuncAI/ProteinFuncAI" ]]; then
    echo "No se encontró ProteinFuncAI/ junto a este script. Extrae el archivo .tar.gz completo." >&2
    exit 1
fi

echo "Instalando en $PREFIX …"
rm -rf "$PREFIX"
mkdir -p "$PREFIX" "$BIN" "$APPS" "$ICONS"
cp -a "$HERE/ProteinFuncAI/." "$PREFIX/"
cp "$HERE/icon.png" "$ICONS/proteinfunc-ai.png"
ln -sf "$PREFIX/ProteinFuncAI" "$BIN/proteinfunc-ai"
ln -sf "$PREFIX/proteinfunc-check" "$BIN/proteinfunc-check"

cat > "$APPS/proteinfunc-ai.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=ProteinFunc AI Desktop
Comment=Predicción local de funciones GO de proteínas
Exec="$PREFIX/ProteinFuncAI"
Icon=proteinfunc-ai
Terminal=false
Categories=Science;Biology;Education;
DESKTOP
command -v update-desktop-database >/dev/null && update-desktop-database "$APPS" >/dev/null 2>&1 || true

# Librerías gráficas del sistema que Qt necesita y no se pueden incluir en el paquete.
# Se lee la caché una sola vez: con «ldconfig -p | grep -q» y pipefail, grep cierra la
# tubería al encontrar la librería, ldconfig recibe SIGPIPE y daba falsos «faltantes».
missing=()
cache="$( (ldconfig -p || /sbin/ldconfig -p) 2>/dev/null || true)"
if [[ -n "$cache" ]]; then
    for lib in libEGL.so.1 libGL.so.1 libxkbcommon.so.0 libxkbcommon-x11.so.0 libxcb-cursor.so.0 libfontconfig.so.1; do
        grep -qF "$lib" <<<"$cache" || missing+=("$lib")
    done
fi
if (( ${#missing[@]} )); then
    echo
    echo "Aviso: faltan librerías del sistema: ${missing[*]}"
    echo "  Debian/Ubuntu: sudo apt install libegl1 libgl1 libxkbcommon-x11-0 libxcb-cursor0 libfontconfig1"
    echo "  Fedora:        sudo dnf install mesa-libEGL mesa-libGL libxkbcommon-x11 xcb-util-cursor fontconfig"
    echo "  Arch:          sudo pacman -S --needed mesa libxkbcommon-x11 xcb-util-cursor fontconfig"
fi

echo
echo "Verificando el modelo (sin conexión)…"
if "$PREFIX/proteinfunc-check" >/tmp/proteinfunc-check.log 2>&1; then
    echo "  Correcto: paquete verificado y predicción de ejemplo realizada."
else
    echo "  La verificación falló. Detalle en /tmp/proteinfunc-check.log"
fi

echo
echo "Listo. Abre «ProteinFunc AI Desktop» desde el menú de aplicaciones o ejecuta: proteinfunc-ai"
[[ ":$PATH:" == *":$BIN:"* ]] || echo "(Añade $BIN a tu PATH para usar el comando proteinfunc-ai.)"
