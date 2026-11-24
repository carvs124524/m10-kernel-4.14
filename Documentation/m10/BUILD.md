# Build do kernel 4.14.336 do M10

## Toolchain

- Android Clang **9.0.3 r353983c**
- GCC 4.9 `aarch64-linux-android-` / `arm-linux-androideabi-`
- `make`, `bc`, `flex`, `bison`, `libssl-dev`, `libelf-dev`, `libyaml-dev`

## Configuração

`arch/arm64/configs/m10_s9863a1h10_defconfig` (base stock do aparelho; KASAN
off). A config real do stock (`/proc/config.gz`) é praticamente igual; a única
diferença encontrada é `CONFIG_CHARGER_SC2721=y`, driver ausente no BSP
público. Veja também `Documentation/m10/stock-device.config`.

## Comando

```bash
export TOOLCHAIN=/caminho/para/toolchain
JOBS=4 ./build-m10.sh
```

O script roda `m10_s9863a1h10_defconfig`, `olddefconfig` e compila `Image`.

## Resultado validado

- `Image`: `0e3756bcebce0b213a7699cebe2cf36ebbc5ac045773f490de946b5c8b1929cb`
- tamanho: `16556048` bytes
- versão: `4.14.336+`
- `Module.symvers`: `5caa130beb122011ac6444cf72b7bef63e5ae9bb186397b70c62f548d34c28c2`
- config: `m10_s9863a1h10_defconfig`
- `module_layout`: `0x32781cf7`
- boot AVB usado no teste: `260b4873d5f976dc800225dd846abde8e7abebe94ff5d2b8150951edcff6702d`
  (stock ramdisk/DTB + AVB assinado com a chave original)

O build completo do zero levou ~10-15 min em 4 vCPU.

## Módulos vendor

Use o `Module.symvers` acima e `scripts/m10-patch-vendor-ko.py`:

```bash
python3 scripts/m10-patch-vendor-ko.py \
  --symvers Module.symvers \
  --old-version 4.14.133 \
  --new-version 4.14.336+ \
  --outdir patched \
  /caminho/para/*.ko
```

Depois copie os `.ko` patchados para `/mnt/vendor/socko` (rw) e reinicie.
Os módulos proprietários não são distribuídos.
