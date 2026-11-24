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

`arch/arm64/configs/m10_s9863a1h10_defconfig` é a configuração stock do M10
(extraída do aparelho), com os símbolos que o BSP precisa: SDHCR11, MUSB SPRD,
DRM SPRD, touchscreen FocalTech, F2FS, binder/ashmem, pstore, etc.

Ela é uma configuração completa; `olddefconfig` resolve os símbolos novos da
4.14.336. O build de validação usou exatamente essa configuração.

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

- `Image`: `97200a0d60d8029be28b468f557bff1875fa45d890eac5026e5f28379f64be87`
- tamanho: `16556048` bytes (16 MB)
- config: `m10_s9863a1h10_defconfig` (stock do M10)
- toolchain: Android Clang 9.0.3 r353983c + GCC 4.9
- build: completo, sem erros
