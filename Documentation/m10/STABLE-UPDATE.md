# Atualização para Linux 4.14.336

## Estratégia

BSP SharkL3 4.14.133 importado sobre a vanilla 4.14.133; vanilla 4.14.336 em
ramo separado; merge tridimensional com a 4.14.133 como base. Depois do merge,
os subsistemas que o vendor stock usa foram restaurados do BSP para manter o
comportamento de hardware.

## Conflitos e correções principais

- Merge inicial: 75 arquivos em conflito; núcleo estável aceito, ABI do BSP
  preservada em binder/F2FS/fscrypt/xfrm/MUSB/MMC/USB/SPRD/scheduler/display.
- `entry.S`: o merge manteve **duas** restaurações de SP no `kernel_exit`;
  corrigido (commit `3ab1b6ae0`). Sem isso o userspace chegava a `init` e
  morria.
- `f2fs`, `HID`, `sysrq`, `configfs`, `u_ether`, `UAPI xfrm`: restaurados do
  BSP quando a 4.14.336 mudou structs/APIs do vendor.
- `wait.c`: mantido do BSP (scheduler vendor) + `__wake_up_pollfree` e
  `poll.h` da 4.14.336 para linkar `signalfd`/`binder`.

## Restauração vendor (clock/desempenho)

O merge 4.14.336 alterou o comportamento esperado pelos módulos stock. Foram
restaurados do BSP:

- `drivers/devfreq` + `include/linux/devfreq.h` (GPU/DDR)
- `drivers/base/power/opp` + `include/linux/pm_opp.h` (OPP)
- `drivers/cpufreq` + `include/linux/cpufreq.h` (CPU)
- `kernel/sched` (EAS vendor)
- `drivers/dma-buf` + headers (fences do `pvrsrvkm`)
- `drivers/staging/android/ion` (gralloc)
- `drivers/mmc`/`include/linux/mmc` (SDIO/eMMC)

A GPU usa o governor stock `simple_ondemand` (256/384/550 MHz); o teste de UI
mostrou 10,76% de utilização média em 256 MHz, sem frequência fixa/Magisk.

## Módulos vendor

Os `.ko` stock são 4.14.133. O `struct module` do módulo e do kernel tem o
**mesmo layout** (896 bytes, mesmos offsets; `pahole`). O `module_layout` CRC
difere por detalhe de genksyms, mas o layout é compatível. Solução no kernel
público:

1. `scripts/m10-patch-vendor-ko.py` reescreve os CRCs de `__versions` com o
   `Module.symvers` do kernel e troca o vermagic para `4.14.336+` (a seção
   `.modinfo` é anexada ao fim do `.ko`);
2. instalar os `.ko` patchados em `/mnt/vendor/socko` (rw) e reiniciar.

Os 13 módulos carregam: `pvrsrvkm`, `gslX680`, `sprdwl_ng`, `sprdbt_tty`,
`sprd_camera`, `sprd_sensor`, `sprd_cpp`, `sprd_fm`, `sprd_flash_drv`,
`flash_ic_*`, `tcs3430`, `chipone_fp`. Os arquivos proprietários não são
distribuídos.

## WiFi

O módulo `sprdwl_ng` carrega, mas o host SDIO `mmc2` (`20400000.sdio`) não
enumera o cartão: `scan: card=(null) rescan_disable=0`; o `mmc_detect_change`
roda, mas o cartão não responde. O host `sprd_sdhcr11`/SDIO do BSP público não
é o host vendor exato do M10. Sem o fonte exato do host, o WiFi continua no
**kernel stock 4.14.133**.

## Validação no hardware

- Kernel `4.14.336+ #4`; Android 11 com `sys.boot_completed=1`.
- Todos os 13 módulos vendor carregados; GPU/touch/UI funcionando.
- GPU em 256 MHz ociosa (governor stock), 10,76% de utilização em swipe;
  sem Magisk.
- WiFi falha na enumeração SDIO (`mmc2` card NULL); stock 4.14.133 para WiFi.
- Boot stock restaurado/verificado (`11fa8c2d…`) para rollback.

## Limitações

- WiFi apenas no stock 4.14.133 (host SDIO vendor não público).
- Os arquivos restaurados do BSP não recebem os patches estáveis da 4.14.336
  na mesma região; o comportamento vendor foi priorizado.
- O BSP público não é o fonte exato da Multilaser.
