# Monitoramento-de-MITM-via-eBPF

Passo-a-passo para o experimento básico

1. "docker compose up -d" para subir o ambiente de teste
2. "docker exec -it attacker-10.9.0.99 bash" para abrir o atacante
3. "sysctl -w net.ipv4.ip_forward=1" no ambiente do atacante
4. "arpspoof -i eth0 -t 10.9.0.5 10.9.0.6" para fazer o ataque
5. verificações do ataque podem ser feitas no servidor e na vítima conforme apresentado no slide
6. rodar os códigos de controle de ataque com permissão sudo
    sudo python3 ebpf_mitm_expulsao.py
    
    ou 

    sudo python3 falco_responder.py

7. verificação no atacante de tentativas de ataque