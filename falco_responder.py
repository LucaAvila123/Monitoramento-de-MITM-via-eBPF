#!/usr/bin/env python3
import subprocess
import os
import signal
import sys
import time

def kill_process_by_name(process_name, contextual_message="🎯 ANULAÇÃO"):
    """Localiza o processo no host e o encerra imediatamente."""
    try:
        result = subprocess.run(["pgrep", "-f", process_name], stdout=subprocess.PIPE, text=True)
        pids = result.stdout.strip().split("\n")
        
        killed_any = False
        for pid_str in pids:
            if pid_str:
                pid = int(pid_str)
                if pid != os.getpid():  # Evita suicídio do script Python
                    os.kill(pid, signal.SIGKILL)
                    print(f"   ↳ {contextual_message}: PID {pid} ({process_name}) foi neutralizado.")
                    killed_any = True
        return killed_any
    except Exception as e:
        print(f"   ↳ ⚠️ Erro ao tentar encerrar processo: {e}")
        return False

def monitor_falco_preventivo():
    print("🛡️  [SISTEMA DE MITIGAÇÃO PROATIVA] Ativado.")
    
    # --- PASSO NOVO: SANITIZAÇÃO INICIAL ---
    print("🔍 [VARREDURA] Procurando por ataques ativos que já estavam rodando...")
    houve_limpeza = kill_process_by_name("arpspoof", contextual_message="🧹 LIMPEZA INICIAL")
    if not houve_limpeza:
        print("   ↳ Nenhum ataque pré-existente encontrado. Sistema limpo.")
    
    print("\n🚀 Iniciando monitoramento em tempo real via Falco (Pré-Rede)...")
    print("💡 Aguardando novas tentativas de execução...\n")
    
    # stdbuf -oL impede o buffer de bloco; --tail 0 ignora o passado no log do Falco
    cmd = ["stdbuf", "-oL", "docker", "logs", "-f", "--tail", "0", "falco"]
    
    process = subprocess.Popen(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        text=True
    )

    for line in iter(process.stdout.readline, ""):
        line_lower = line.lower()
        
        # Captura novas inicializações do binário malicioso
        if "arpspoof" in line_lower and ("execve" in line_lower or "executing binary" in line_lower):
            
            print(f"\n⚡ [ALERTA DE PRÉ-ATAQUE DETECTADO VIA FALCO]:")
            print(f"   ↳ {line.strip()[:130]}...")
            print(f"🚨 [REAÇÃO PREVENTIVA]: Tentativa de nova execução interceptada!")
            
            sucesso = kill_process_by_name("arpspoof", contextual_message="🎯 BLOQUEIO EM TEMPO REAL")
            
            if not sucesso:
                # Margem de segurança de milissegundos para o escalonador do Kernel
                time.sleep(0.01)
                kill_process_by_name("arpspoof", contextual_message="🎯 BLOQUEIO EM TEMPO REAL (REINSPEÇÃO)")

            print("-" * 85)
            sys.stdout.flush()

if __name__ == "__main__":
    try:
        monitor_falco_preventivo()
    except KeyboardInterrupt:
        print("\n👋 Monitoramento preventivo encerrado.")