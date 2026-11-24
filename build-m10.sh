#!/usr/bin/env bash
# Build the M10 4.14.336 kernel with the Android BSP toolchain.
set -euo pipefail

src=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
out=${OUT:-$src/../build-m10-4.14}
jobs=${JOBS:-2}
tc=${TOOLCHAIN:-}

if [[ -z "$tc" ]]; then
    echo "Uso: TOOLCHAIN=/caminho/para/toolchain $0" >&2
    echo "O diretório deve conter clang-r353983c, gcc-aarch64-4.9, gcc-arm-4.9 e host." >&2
    exit 2
fi

for d in clang-r353983c gcc-aarch64-4.9 gcc-arm-4.9; do
    [[ -d "$tc/$d" ]] || { echo "Faltou $tc/$d" >&2; exit 2; }
done

export PATH="$tc/host/usr/bin:$tc/clang-r353983c/bin:$tc/gcc-aarch64-4.9/bin:$tc/gcc-arm-4.9/bin:$PATH"
export LC_ALL=C

common=(
    ARCH=arm64
    CC=clang
    CLANG_TRIPLE=aarch64-linux-gnu-
    CROSS_COMPILE=aarch64-linux-android-
    CROSS_COMPILE_ARM32=arm-linux-androideabi-
    HOSTCFLAGS="-Wall -Wmissing-prototypes -Wstrict-prototypes -O2 -std=gnu89 -fcommon"
)

mkdir -p "$out"

make -C "$src" O="$out" "${common[@]}" m10_s9863a1h10_defconfig
make -C "$src" O="$out" "${common[@]}" -j"$jobs" Image

image="$out/arch/arm64/boot/Image"
cp -- "$out/.config" "$out/kernel.config"

python3 - "$image" <<'PY'
from pathlib import Path
import struct
import sys

with Path(sys.argv[1]).open("rb") as f:
    header = f.read(64)
if header[56:60] != b"ARM\x64":
    raise SystemExit("Image não tem o magic ARM64 esperado")
text_offset = struct.unpack_from("<Q", header, 8)[0]
if text_offset not in (0, 0x80000):
    raise SystemExit(f"text_offset inesperado no Image ARM64: {text_offset:#x}")
PY

ls -lh "$image"
sha256sum "$image"
