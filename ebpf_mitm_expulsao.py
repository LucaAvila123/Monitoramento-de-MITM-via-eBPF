#!/usr/bin/env python3
from bcc import BPF
import ctypes
import os
import signal
import time
import threading

# 1. Código C para pegar novos processos abrindo socket
ebpf_code = """
#include <linux/sched.h>

struct data_t {
    u32 pid;
    char comm[TASK_COMM_LEN];
};

BPF_PERF_OUTPUT(events);

TRACEPOINT_PROBE(syscalls, sys_enter_socket) {
    struct data_t data = {};
    int family = args->family;

    if (family == 17) { // AF_PACKET
        bpf_get_current_comm(&data.comm, sizeof(data.comm));
        
        if (data.comm[0] == 'a' && data.comm[1] == 'r' && data.comm[2] == 'p') {
            data.pid = bpf_get_current_pid_tgid() >> 32;
            events.perf_submit(args, &data, sizeof(data));
        }
    }
    return 0;
}
"""

class EventData(ctypes.Structure):
    _fields_ = [("pid", ctypes.c_uint32), ("comm", ctypes.c_char * 16)]

# Função para matar o PID com segurança
def terminate_pid(pid, reason):
    try:
        os.kill(pid, signal.SIGKILL)
        print(f"\n🚨 [SISTEMA DE MITIGAÇÃO DISPARADO]")
        print(f"   ↳ Gatilho:      {reason}")
        print(f"   ↳ PID no Host:  {pid}")
        print(f"   ↳ Ação Tomada:  EXPULSADO! Processo finalizado com SIGKILL no Kernel.")
        print("-" * 75)
    except ProcessLookupError:
        pass
    except PermissionError:
        print(f"❌ Erro de permissão para matar o PID {pid}")

# 2. Monitor Passivo (eBPF) via Callback
def bpf_callback(cpu, data, size):
    event = ctypes.cast(data, ctypes.POINTER(EventData)).contents
    process_name = event.comm.decode('utf-8', 'replace')
    terminate_pid(event.pid, f"Nova tentativa de socket AF_PACKET por '{process_name}'")

# 3. Varredura Ativa (Thread paralela para caçar arpspoof já em execução)
def active_hunter_thread():
    print("🔎 Caçador Proativo iniciado (varrendo processos ativos)...")
    while True:
        try:
            # Varre o diretório /proc do Linux buscando processos ativos
            for pid_dir in os.listdir('/proc'):
                if pid_dir.isdigit():
                    pid = int(pid_dir)
                    try:
                        with open(f'/proc/{pid_dir}/comm', 'r') as f:
                            comm = f.read().strip()
                        # Se encontrar o arpspoof rodando, liquida imediatamente
                        if comm.startswith("arpspoof"):
                            terminate_pid(pid, f"Processo ativo '{comm}' detectado em execução de fundo")
                    except (FileNotFoundError, ProcessLookupError, PermissionError):
                        continue
            time.sleep(0.5) # Intervalo de varredura (meio segundo)
        except Exception as e:
            print(f"Erro na varredura: {e}")

# --- Inicialização do Sistema ---
print("🛡️  SISTEMA DE DEFESA ATIVA HÍBRIDA INICIADO...")
b = BPF(text=ebpf_code)
b["events"].open_perf_buffer(bpf_callback)

# Inicia a thread de varredura ativa em background
hunter = threading.Thread(target=active_hunter_thread, daemon=True)
hunter.start()

print("🚀 Aguardando atividades maliciosas. Pressione Ctrl+C para sair.\n")

while True:
    try:
        b.perf_buffer_poll(timeout=100)
    except KeyboardInterrupt:
        print("\nSistema de defesa encerrado.")
        break