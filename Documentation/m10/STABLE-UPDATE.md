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
        ├── 3ab1b6ae0   fix do entry.S
        └── 8eb83379b   tentativa de ABI de struct module
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

## Correção do entry.S

O merge manteve **duas** restaurações de pilha no epílogo `kernel_exit`:

- a do BSP (`ldr lr` + `add sp, #S_FRAME_SIZE`);
- a da 4.14.336, dentro dos ramos `.if \el == 0` / `.else`.

O resultado ajustava `sp` duas vezes e carregava `lr` do lugar errado em todo
retorno de exceção/syscall. O kernel chegava a `run init`, mas o userspace
morria/hangava. O commit `3ab1b6ae0` removeu o bloco duplicado; o `entry.S`
agora bate com a 4.14.336 (o bloco `CONFIG_SPRD_DEBUG` fica compilado fora no
config do M10). Depois disso o Android 4.14.336 chegou ao ADB/userspace.

## ABI dos módulos vendor

O kernel 4.14.336 boota o Android, mas os módulos vendor stock são binários
compilados para o kernel stock 4.14.133. O kernel recusa o `pvrsrvkm.ko`:

```
pvrsrvkm: disagrees about version of symbol module_layout
finit_module for "/mnt/vendor/socko/pvrsrvkm.ko" failed: Exec format error
```

Foi feita uma tentativa de compatibilidade:

- a 4.14.336 adicionou `bool using_gplonly_symbols` em `struct module`;
- o campo e os dois usos em `kernel/module.c` foram revertidos
  (`8eb83379b`), restaurando o layout 4.14.133;
- os 13 módulos vendor foram puxados de `/mnt/vendor/socko`;
- um patcher de CRCs/vermagic foi testado (`pvrsrvkm.ko`: 249 símbolos,
  129 CRCs, vermagic `4.14.336`).

Mesmo assim o `module_layout` do kernel público ficou `0x32781cf7`, enquanto o
dos módulos stock é `0xa45272df`. A config real do aparelho foi puxada de
`/proc/config.gz` e comparada com a config do pass9: são iguais, exceto
`CONFIG_CHARGER_SC2721=y` (driver ausente no BSP público). Não é CFI nem opção
de módulo; é **diferença de fonte**: o BSP público não é o kernel exato da
Multilaser. Carregar os `.ko` com CRCs forçados poderia corromper o
`__this_module` e o kernel, então a tentativa foi interrompida.

**Consequência:** UI/GPU/WiFi/touch/Bluetooth funcionam no kernel stock
4.14.133; o 4.14.336 é útil para o trabalho de kernel/display, mas não é um
substituto diário até existir o fonte/config exato do vendor ou módulos
recompilados contra ele.

## Validação

- Configuração: `arch/arm64/configs/m10_s9863a1h10_defconfig`.
- Toolchain: Android Clang 9.0.3 r353983c + GCC 4.9 do BSP.
- Build limpo do `main` corrigido: `Image` de 16.621.584 bytes, SHA-256
  `3e7f785f32fb9635924fd4bedc024dd3fc5b41f5a92097574511eea0c4c6a1c9`
  (`4.14.336+`), release `m10-4.14.336-r2`.
- Teste físico: o kernel 4.14.336 bootou o Android 11 (GSI) até o ADB; a tela
  ficou preta porque o `pvrsrvkm.ko` vendor não carrega. O boot stock foi
  restaurado e conferido (`11fa8c2d...`).
- O release antigo `m10-4.14.336` (Image `97200a0d...`) é anterior ao fix do
  `entry.S` e não deve ser usado.

## Limitações conhecidas

- Os módulos vendor stock (GPU, WiFi, touch, Bluetooth, câmera, sensor) não
  são ABI-compatíveis com o BSP público 4.14.336; a UI/Android completo
  continua no stock 4.14.133.
- Nos arquivos restaurados inteiros do BSP (HID, sysrq, configfs, u_ether,
  UAPI xfrm), os patches estáveis da 4.14.336 que tocavam a mesma região não
  foram aplicados. Eles já contêm backports do vendor.
- O BSP público não é o fonte exato da Multilaser; o DTB e os periféricos do
  M10 devem ser validados no aparelho.
