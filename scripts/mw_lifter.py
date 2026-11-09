"""Project-local corrections for the shared pcrecomp lifter.

1. x87: FCOM/FUCOM/FTST update the x87 status word, not integer EFLAGS. MW's
   0x81CDC6 sound routine schedules CMP channel,-1; FUCOMPP; JNE: replacing
   the CMP flags sends the all-channel sentinel through a single-channel write,
   overwriting its effects callback at voice+0x118 with a floating-point gain.
   Keep the integer lazy flags until TEST/SAHF explicitly transfers the status.

2. XADD / CMPXCHG (dword): MW's reference-counting/scheduler code around
   0x834DA4-0x835812 uses LOCK XADD and LOCK CMPXCHG, which the shared lifter
   does not implement (the guest stopped at boot: "Instruction unsupported at
   0x00834e2d: lock xadd"). The LOCK prefix is dropped as it is for LOCK INC:
   lifted code runs under one machine lock, so the plain operation is exact.
   Flags are produced exactly as ADD (xadd) and CMP eax,dst (cmpxchg) do.
"""
from lift32 import Lifter as BaseLifter

_X87_COMPARES = {'fcom', 'fcomp', 'fcompp', 'fucom', 'fucomp', 'fucompp', 'ftst'}


class Lifter(BaseLifter):
    def _lift_instruction(self, insn):
        m = insn.mnemonic
        if m.startswith('lock'):
            m = m[4:].strip() or (insn.op_str.split() or [''])[0]
        ops = insn.operands if insn.operands else []
        if m in ('xadd', 'cmpxchg') and len(ops) == 2 and ops[0].size == 4 and ops[1].size == 4:
            return self._lift_atomic(insn, m, ops)
        if insn.mnemonic not in _X87_COMPARES:
            return super()._lift_instruction(insn)
        state, seq = self._flag_state, self._flag_seq
        lines = super()._lift_instruction(insn)
        self._flag_state, self._flag_seq = state, seq
        return [line for line in lines
                if line != '_flag_a = (uint32_t)_fpu_cmp; _flag_b = 0;']

    def _lift_atomic(self, insn, m, ops):
        comment = f"/* 0x{insn.address:08X}: {insn.mnemonic} {insn.op_str} */"
        lines = []
        if m == 'xadd':
            # tmp = dst; dst = dst + src; src = tmp   (flags of dst + src)
            a = self._fmt_read(ops[0])
            b = self._fmt_read(ops[1])
            lines.append(self._flag_capture(a, b, 32))
            lines.append("_cf = (uint32_t)((uint32_t)(_flag_a + _flag_b) < (uint32_t)_flag_a);")
            lines.append(f"{{ uint32_t _xa = {a}; uint32_t _xb = {b}; "
                         f"{self._fmt_write(ops[0], '_xa + _xb')}; "
                         f"{self._fmt_write(ops[1], '_xa')}; }} {comment}")
            self._flag_state = ('add', "_flag_a, _flag_b")
            self._flag_seq += 1
        else:
            # cmpxchg dst, src: flags of eax - dst; if equal dst = src, else eax = dst
            a = self._fmt_read(ops[0])
            b = self._fmt_read(ops[1])
            lines.append(f"/* cmp eax, {a} */ {comment}")
            lines.append(self._flag_capture("eax", a, 32))
            lines.append("_cf = (uint32_t)CMP_B(_flag_a, _flag_b);")
            lines.append(f"{{ uint32_t _cd = {a}; uint32_t _cs = {b}; "
                         f"if (eax == _cd) {{ {self._fmt_write(ops[0], '_cs')}; }} else {{ eax = _cd; }} }}")
            self._flag_state = ('cmp', "_flag_a, _flag_b")
            self._flag_seq += 1
        return lines
