# Build do kernel 4.14.336 do M10

## Toolchain usado na validação

- Android Clang **9.0.3 r353983c** (`clang-r353983c`)
- GCC pré-compilado **4.9** para `aarch64-linux-android-` e
  `arm-linux-androideabi-`
- `make`, `bc`, `flex`, `bison`, `libssl-dev`, `libelf-dev`, `libyaml-dev`

O toolchain é o mesmo usado pelo BSP 4.14.133. Ele não está neste repositório
por tamanho; aponte `TOOLCHAIN` para o diretório que contém
`clang-r353983c`, `gcc-aarch64-4.9`, `gcc-arm-4.9` e `host`.

## Configuração

`arch/arm64/configs/m10_s9863a1h10_defconfig` é a configuração usada no
bring-up (baseada na config stock do pass9), com SDHCR11, MUSB SPRD, DRM SPRD,
touchscreen FocalTech, F2FS, binder/ashmem, pstore, etc.

A config real do kernel stock do aparelho (`/proc/config.gz`) é praticamente
a mesma; a única diferença encontrada foi `CONFIG_CHARGER_SC2721=y`, um driver
que não existe no BSP público. O build do 4.14.336 usa a defconfig acima e
`olddefconfig` resolve os símbolos novos.

## Comando reproduzível

```bash
export TOOLCHAIN=/caminho/para/toolchain
JOBS=2 ./build-m10.sh
```

O script:

1. exporta o PATH do Clang/GCC do BSP;
2. copia a defconfig para o diretório de saída;
3. roda `olddefconfig`;
4. compila `Image`;
5. imprime o SHA-256.

## Build manual

```bash
out=../build-m10-4.14
export PATH="$TOOLCHAIN/host/usr/bin:$TOOLCHAIN/clang-r353983c/bin:$TOOLCHAIN/gcc-aarch64-4.9/bin:$TOOLCHAIN/gcc-arm-4.9/bin:$PATH"

make O="$out" ARCH=arm64 \
  CC=clang CLANG_TRIPLE=aarch64-linux-gnu- \
  CROSS_COMPILE=aarch64-linux-android- \
  CROSS_COMPILE_ARM32=arm-linux-androideabi- \
  HOSTCFLAGS="-Wall -Wmissing-prototypes -Wstrict-prototypes -O2 -std=gnu89 -fcommon" \
  m10_s9863a1h10_defconfig

make O="$out" ARCH=arm64 \
  CC=clang CLANG_TRIPLE=aarch64-linux-gnu- \
  CROSS_COMPILE=aarch64-linux-android- \
  CROSS_COMPILE_ARM32=arm-linux-androideabi- \
  HOSTCFLAGS="-Wall -Wmissing-prototypes -Wstrict-prototypes -O2 -std=gnu89 -fcommon" \
  -j2 Image
```

`HOSTCFLAGS` com `-fcommon` é necessário para compilar o kbuild antigo com
GCCs modernos do host. O Clang 9 do BSP é obrigatório para o código ARM64
antigo do vendor.

## Resultado da validação

- `Image`: `3e7f785f32fb9635924fd4bedc024dd3fc5b41f5a92097574511eea0c4c6a1c9`
- tamanho: `16621584` bytes (16 MB)
- versão: `4.14.336+` (o `+` é o localversion do build; o código é 4.14.336)
- config: `m10_s9863a1h10_defconfig`
- toolchain: Android Clang 9.0.3 r353983c + GCC 4.9
- build: limpo, completo, sem erros

O build completo do zero levou cerca de 30 minutos numa Codespace de 2 vCPU.
Builds incrementais (mudança de um arquivo + link) levam 1–2 minutos.
