#!/usr/bin/env python3
"""List catalogued "functions" that are really data decoded as code.

  find_data_functions.py <module.dll> <catalog.json> <out_exclude.json>

Some modules (d3dx9_26) hold tables and ASCII strings next to code, and the
catalog turns them into functions whose bodies decode to instructions that
user-mode MSVC output never contains (arpl, insb, bound, daa ...). Lifting them
only produces thousands of RECOMP_UNIMPL stubs and millions of useless C lines.

The result is a JSON array of VAs for run_lift.py's --exclude option:
  run_lift.py lift <module.dll> <catalog.json> <outdir> --prefix P --exclude <out_exclude.json>
"""
import collections
import json
import os
import sys

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_GRP_JUMP, CS_OP_IMM

# Never emitted by a user-mode 32-bit compiler. 3DNow!, fisttp, fcmov and
# fcomi are deliberately NOT listed: real code can contain them.
IMPOSSIBLE = {
    "arpl", "insb", "insw", "insd", "outsb", "outsw", "outsd", "bound",
    "popaw", "pushaw", "daa", "das", "aaa", "aas", "aam", "aad", "salc",
    "into", "int1", "int", "sldt", "str", "rdmsr", "lcall", "ljmp",
    "iretd", "iretw", "hlt", "cli", "sti", "bnd",
}


def main(dll, catalog, out):
    pe = pefile.PE(dll, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    img = pe.get_memory_mapped_image()
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    cat = json.load(open(catalog))
    bad, reasons, examples = set(), collections.Counter(), []
    for fd in cat["functions"]:
        starts = {b[0] for b in fd["blocks"]}
        lo, hi = fd["address"], fd["end"]
        hit = None
        for start, end, _succ, _exit in fd["blocks"]:
            for ins in md.disasm(img[start - base:end - base], start):
                if ins.mnemonic in IMPOSSIBLE:
                    hit = ins.mnemonic
                    break
                # A direct branch inside the function to an address that starts no block:
                # the lifter emits `goto L_xxx` with no label, and the C does not compile.
                if CS_GRP_JUMP in ins.groups and ins.operands and ins.operands[0].type == CS_OP_IMM:
                    t = ins.operands[0].imm
                    if lo <= t < hi and t not in starts:
                        hit = "unlabeled-" + ins.mnemonic
                        if len(examples) < 8:
                            examples.append(f"{fd['address']:08X}: {ins.address:08X} {ins.mnemonic} -> {t:08X}")
                        break
            if hit:
                break
        if hit:
            bad.add(fd["address"])
            reasons[hit] += 1
    # keep what an earlier run already excluded
    if os.path.exists(out):
        bad |= set(json.load(open(out)))
    json.dump(sorted(bad), open(out, "w"))
    print(f"[*] {len(bad)} of {len(cat['functions'])} functions excluded -> {out}")
    print("    first hit by mnemonic:", dict(reasons.most_common(12)))
    for e in examples:
        print("    e.g.", e)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
