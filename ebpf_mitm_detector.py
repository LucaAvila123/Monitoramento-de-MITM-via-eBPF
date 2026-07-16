#!/usr/bin/env python3
from bcc import BPF
import ctypes

# Código C que usa Tracepoints estáveis do Kernel
ebpf_code = """
#include <linux/sched.h>

struct data_t {
    u32 pid;
    char comm[TASK_COMM_LEN];
    u32 family;
};

BPF_PERF_OUTPUT(events);

// Hook estável na entrada da syscall socket
TRACEPOINT_PROBE(syscalls, sys_enter_socket) {
    struct data_t data = {};
    
    // args->family extrai o valor diretamente da definição de tracepoint do kernel
    int family = args->family;

    // AF_PACKET (constante 17)
    if (family == 17) {
        data.pid = bpf_get_current_pid_tgid() >> 32;
        bpf_get_current_comm(&data.comm, sizeof(data.comm));
        data.family = family;

        events.perf_submit(args, &data, sizeof(data));
    }
    return 0;
}
"""

class EventData(ctypes.Structure):
    _fields_ = [
        ("pid", ctypes.c_uint32),
        ("comm", ctypes.c_char * 16),
        ("family", ctypes.c_uint32)
    ]

print("🛡️  Iniciando detector de MITM via eBPF Tracepoint...")
b = BPF(text=ebpf_code)

def print_event(cpu, data, size):
    # Correção: POINTER em maiúsculas
    event = ctypes.cast(data, ctypes.POINTER(EventData)).contents
    process_name = event.comm.decode('utf-8', 'replace')
    
    print(f"\n⚠️  [ALERTA DE SEGURANÇA eBPF]")
    print(f"   ↳ Detecção:    Tentativa de falsificação de rede / MITM")
    print(f"   ↳ Processo:     {process_name}")
    print(f"   ↳ PID no Host:  {event.pid}")
    print(f"   ↳ Família:      AF_PACKET (Acesso de rede de baixo nível)")
    print("-" * 60)

# O BCC mapeia automaticamente o tracepoint
b["events"].open_perf_buffer(print_event)
while True:
    try:
        b.perf_buffer_poll()
    except KeyboardInterrupt:
        print("\nDetector encerrado.")
        break