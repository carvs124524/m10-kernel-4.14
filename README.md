# Linux 4.14.336 para o Multilaser M10 (SC9863A / s9863a1h10)

Árvore pública do kernel Linux 4.14 para o tablet **Multilaser M10 NB805/SO0G**
(SoC Unisoc/Spreadtrum **SC9863A**, placa **s9863a1h10**, também conhecida como
SharkL3).

Esta árvore parte do BSP público **SharkL3 4.14.133** publicado em
[`strongtz/linux-sprd`](https://github.com/strongtz/linux-sprd) e foi atualizada
para a última versão da série 4.14.y, **4.14.336**.

> O BSP público é compatível com a família SharkL3/SC9863A, mas **não é o fonte
> exato** que a Multilaser usou no M10. O DTB e os periféricos do M10 devem ser
> validados no aparelho. Este repositório não inclui blobs proprietários,
> firmware de modem/WiFi nem o Android vendor.

## Estado

- Versão: **4.14.336** (última 4.14.y; a série foi encerrada em janeiro de 2024).
- Base: BSP SharkL3 4.14.133, commit `d834a127a` do `strongtz/linux-sprd`.
- Atualização: merge de `v4.14.336` sobre o BSP, com os conflitos de hardware
  resolvidos a favor do BSP onde a interface upstream mudou.
- Build: validado do zero com Android Clang 9.0.3 r353983c + GCC 4.9 do BSP e a
  configuração stock do M10. `Image` de 16.621.584 bytes, SHA-256
  `3e7f785f32fb9635924fd4bedc024dd3fc5b41f5a92097574511eea0c4c6a1c9`
  (release `m10-4.14.336-r2`).
- Boot no hardware: o kernel 4.14.336 **boota até o Android userspace e o ADB**
  no M10, usando o ramdisk/DTB stock e um `boot.img` reassinado com a chave AVB
  original.
- **Limitação atual:** os módulos vendor stock (GPU PowerVR `pvrsrvkm.ko`,
  WiFi `sprdwl_ng.ko`, touch `gslX680.ko`, Bluetooth, câmera) são binários
  compilados para 4.14.133. O `module_layout` do BSP público é
  `0x32781cf7`; o dos módulos stock é `0xa45272df`. Mesmo revertendo o campo
  novo de `struct module` da 4.14.336, o ABI não fecha — o BSP público não é o
  fonte exato do kernel stock. Por isso o Android completo (UI, GPU, WiFi,
  touch) continua no **kernel stock 4.14.133**.
- O release **`m10-4.14.336`** antigo tem um bug de restauração dupla de pilha
  no `entry.S` e não deve ser usado. Use **`m10-4.14.336-r2`**.

## Histórico

```
v4.14.133                 Linux 4.14.133 vanilla
m10-bsp-4.14.133          Import do BSP SharkL3 + ajustes de build
v4.14.336                 Linux 4.14.336 vanilla
main                      Merge Linux 4.14.336 no BSP do M10
                          + fix do entry.S
                          + tentativa de ABI de struct module
m10-4.14.336-r2           Build limpo do kernel corrigido
```

O merge preserva o ABI/implementação do BSP nos subsistemas que o Android e os
drivers do SC9863A usam (binder, F2FS, fscrypt, xfrm `if_id`, MUSB, MMC, USB
gadget, serial SPRD, scheduler/EAS, display/power). Os arquivos de núcleo
(arch, mm, net, tracing, random, HID) recebem o lado estável da 4.14.336.
Os detalhes e as exceções estão em `Documentation/m10/STABLE-UPDATE.md`.

## Compilação

O toolchain não é versionado (é grande). Use o Android Clang 9.0.3 r353983c e
os pré-compilados GCC 4.9 do BSP, ou adapte `CC`/`CROSS_COMPILE`:

```bash
export TOOLCHAIN=/caminho/para/toolchain   # contém clang-r353983c, gcc-aarch64-4.9, gcc-arm-4.9
./build-m10.sh
```

O script usa `arch/arm64/configs/m10_s9863a1h10_defconfig` e gera
`../build-m10-4.14/arch/arm64/boot/Image`.

Build manual:

```bash
make O=../build-m10-4.14 ARCH=arm64 \
  CC=clang CLANG_TRIPLE=aarch64-linux-gnu- \
  CROSS_COMPILE=aarch64-linux-android- \
  CROSS_COMPILE_ARM32=arm-linux-androideabi- \
  m10_s9863a1h10_defconfig
make O=../build-m10-4.14 ARCH=arm64 ... -j2 Image
```

## Escopo e limitações

- O kernel não contém os HALs vendor do Android 10 (ION/gralloc/HWC,
  keymaster/TEE etc.). Eles continuam necessários para a GSI/Android.
- Os módulos vendor stock são binários 4.14.133 e dependem do ABI do kernel
  stock. O BSP público não é ABI-idêntico; não carregue esses `.ko` no 4.14.336
  sem o fonte/config exato do vendor, sob risco de corromper `struct module`.
- O DTB do M10, a calibração do painel/touch e o `boot.img` não fazem parte
  desta árvore; use os artefatos do projeto de bring-up.
- Não grave `boot` sem backup e sem conferir os hashes de rollback.
- A série 4.14 está EOL; esta árvore é uma atualização de estabilidade, não um
  substituto para um kernel moderno.

## Licença

O kernel é distribuído sob **GPL-2.0**; veja `COPYING`. O BSP importado mantém
os créditos e avisos originais da Unisoc/Spreadtrum e dos autores de cada
arquivo. Partes do BSP podem ter licenças compatíveis específicas; verifique o
cabeçalho de cada arquivo.
