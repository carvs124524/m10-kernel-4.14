# Linux 4.14.336 para o Multilaser M10 (SC9863A / s9863a1h10)

Árvore pública do kernel Linux 4.14 para o tablet **Multilaser M10 NB805/SO0G**
(SoC Unisoc/Spreadtrum **SC9863A**, placa **s9863a1h10**, SharkL3).

Parte do BSP público **SharkL3 4.14.133** (`strongtz/linux-sprd`) e foi
atualizada para **4.14.336+**, com os subsistemas vendor importantes
restaurados para o comportamento stock.

> O BSP público não é o fonte exato da Multilaser. O DTB e os periféricos do
> M10 devem ser validados no aparelho. Este repositório não inclui blobs
> proprietários, firmware vendor nem o Android.

## Estado (release `m10-4.14.336-r3`)

- Versão: `4.14.336+` (`Image` `0e3756bcebce0b213a7699cebe2cf36ebbc5ac045773f490de946b5c8b1929cb`,
  16.556.048 bytes).
- **Android 11 boota completo** no M10 (`sys.boot_completed=1`), com
  SurfaceFlinger, GPU PowerVR (`pvrsrvkm`), touch `gslX680`, WiFi/BT/câmera/
  sensores e os 13 módulos vendor carregados.
- **GPU/clock**: restaurados `drivers/devfreq`, `drivers/base/power/opp`,
  `drivers/cpufreq`, `kernel/sched` (EAS) e `drivers/dma-buf`/`ION` do BSP.
  A GPU usa o governor stock (`simple_ondemand`, 256/384/550 MHz); não há
  Magisk nem frequência fixa.
- **WiFi**: o módulo `sprdwl_ng` carrega, mas o host SDIO `mmc2`
  (`20400000.sdio`) **não detecta o cartão** (`card=NULL`) nem no boot nem no
  rescan. O `sprd_sdhcr11`/SDIO do BSP público difere do host vendor stock;
  sem o fonte exato do host, o WiFi continua no **kernel stock 4.14.133**.
- `entry.S` corrigido (restauração dupla de SP) e `__wake_up_pollfree`
  mantido com o `wait.c` vendor.
- Config stock do aparelho (`/proc/config.gz`) é a base; KASAN **off**;
  a única diferença é `CONFIG_CHARGER_SC2721=y`, driver ausente no BSP.

## Módulos vendor

Os `.ko` de `/mnt/vendor/socko` são binários 4.14.133. O layout de
`struct module` do módulo e do nosso kernel é **idêntico** (896 bytes, mesmos
offsets, confirmado com `pahole`). Para carregar:

1. use o `Module.symvers` do release;
2. rode `scripts/m10-patch-vendor-ko.py` nos seus módulos (CRCs + vermagic);
3. instale os `.ko` patchados em `/mnt/vendor/socko` e reinicie.

Os módulos proprietários não são distribuídos neste repositório.

## Releases

- **`m10-4.14.336-r3`** — kernel atual (vendor restore + fix SDIO/DIAG;
  WiFi limitado ao stock).
- `m10-4.14.336-r2` — kernel limpo anterior, sem o vendor restore.
- `m10-4.14.336` — **quebrado** (dupla restauração de SP no `entry.S`); não use.

## Compilação

```bash
export TOOLCHAIN=/caminho/para/toolchain
JOBS=4 ./build-m10.sh
```

O toolchain é o Android Clang 9.0.3 r353983c + GCC 4.9 do BSP. Veja
`Documentation/m10/BUILD.md`.

## Licença

GPL-2.0 (`COPYING`). O BSP mantém os créditos Unisoc/Spreadtrum; os módulos
vendor e o Android não fazem parte desta árvore.
