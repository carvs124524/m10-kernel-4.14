# Atualização para Linux 4.14.336

## Estratégia

O BSP SharkL3 4.14.133 foi importado como um commit sobre a árvore vanilla
4.14.133. A árvore vanilla 4.14.336 foi importada em um ramo separado, também
filho da 4.14.133. O merge tridimensional usa a 4.14.133 como base, de modo que
os conflitos são apenas onde o BSP e a 4.14.336 mexeram na mesma região.

```
v4.14.133
├── m10-bsp-4.14.133   (import do BSP + build fixes)
└── v4.14.336          (vanilla)
    └── merge          (main)
```

## Conflitos e resolução

O merge inicial teve **75 arquivos em conflito**. A política foi:

1. **Núcleo estável**: aceitar o lado 4.14.336 em arch/arm64, mm, net,
   tracing, HID, random, compiler/overflow, page_alloc, slub, etc.
2. **ABI/driver do BSP**: preservar o lado do BSP onde a 4.14.336 mudou a
   interface usada pelo Android ou pelo hardware:
   - xfrm `if_id`/`mark` (Android netd);
   - fscrypt/ext4;
   - binder (Android binder);
   - F2FS (backport mais novo do BSP, com prefixos `f2fs_`);
   - MUSB/SPRD DMA;
   - MMC/SDHCR11 e RPMB;
   - USB gadget (UEVENT/accessory);
   - serial SPRD;
   - scheduler/EAS do BSP;
   - display/power/DTB.
3. **Combinações quando independentes**:
   - `panic`: `CONFIG_SPRD_SYSDUMP` + `check_panic_on_warn`;
   - `process.c`: `sprd_update_cpu_usage` + `ssbs_thread_switch`;
   - `modpost`: padrão CFI do BSP + símbolos locais `.L`;
   - `slub`: KASAN SW_TAGS + `swab(ptr_addr)`;
   - `dm-verity`: AVB do BSP + `DM_TARGET_IMMUTABLE`;
   - ChaCha: API do BSP + `lib/chacha20.c` da 4.14.336 para o novo
     `random.c`.

## Correções de build

Depois do merge, a compilação revelou pontos em que o merge misturou metades
de implementações diferentes. Foram corrigidos:

- `scripts/Makefile.build`: `endif` faltante do `CC_USING_RECORD_MCOUNT`.
- `arch/arm64/kernel/traps.c`: `dump_mem` removido na 4.14.336; adotado o
  `dump_backtrace` upstream.
- `fs/f2fs`: `EFSCORRUPTED`/`EFSBADCRC` e `f2fs_get_valid_checkpoint`
  restaurados do BSP.
- `drivers/hid/hid-core.c`, `drivers/tty/sysrq.c`,
  `drivers/usb/gadget/configfs.c`, `drivers/usb/gadget/function/u_ether.c`:
  restaurados inteiros do BSP porque a 4.14.336 mudou structs/APIs usadas
  pelo vendor.
- `include/uapi/linux/xfrm.h`: restaurado do BSP para manter `XFRMA_IF_ID`.
- `nf_socket_ipv4/6`: declaração `sk` do BSP.
- `dm-bow`: `SECTOR_SIZE` protegido contra a definição nova de `blkdev.h`.
- `mmc`: `mmc_access_rpmb` restaurado.
- `xfrm_device`: função `xfrm_dev_unregister` morta removida.
- `of/fdt`: declaração `rng_seed`.
- `vsprintf`: inicialização do hash de `%p` adaptada ao novo `random.c`
  (`late_initcall` em vez do callback removido).
- `musb_host`: variável `ep` não usada removida.

## Validação

- Configuração: `arch/arm64/configs/m10_s9863a1h10_defconfig` (stock do M10).
- Toolchain: Android Clang 9.0.3 r353983c + GCC 4.9 do BSP.
- `Image`: 16 MB, SHA-256
  `97200a0d60d8029be28b468f557bff1875fa45d890eac5026e5f28379f64be87`.
- Build completo, sem erros.

## Limitações conhecidas

- **Não foi gravado/testado no tablet nesta árvore 4.14.336.** O display no
  ACK 6.18 foi validado separadamente; o boot desta árvore ainda precisa de
  teste físico e rollback de `boot`.
- Nos arquivos restaurados inteiros do BSP (HID, sysrq, configfs, u_ether,
  UAPI xfrm), os patches estáveis da 4.14.336 que tocavam a mesma região não
  foram aplicados. Eles já contêm backports do vendor e são a versão
  compatível com o hardware/Android do M10.
- O BSP público não é necessariamente o fonte exato da Multilaser; o DTB e
  os periféricos do M10 devem ser validados no aparelho.
