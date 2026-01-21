#!/usr/bin/env python3
"""
Script de diagnóstico para testar conexão serial com impressora 3D
"""

import serial
import time
import glob
import os
import sys

# Configurações
SERIAL_PORT = '/dev/ttyACM0'
SERIAL_BAUDRATE = 115200
SERIAL_TIMEOUT = 2

def list_available_ports():
    """Lista todas as portas seriais disponíveis"""
    print("\n" + "="*60)
    print("📋 PORTAS SERIAIS DISPONÍVEIS:")
    print("="*60)
    
    # Portas USB e ACM
    ports = glob.glob('/dev/tty[AU]*')
    
    if not ports:
        print("❌ Nenhuma porta serial encontrada!")
        print("\nDica: Verifique se a impressora está conectada via USB")
        return []
    
    for port in sorted(ports):
        exists = os.path.exists(port)
        readable = os.access(port, os.R_OK) if exists else False
        writable = os.access(port, os.W_OK) if exists else False
        
        status = "✓" if (readable and writable) else "⚠️"
        perms = f"R:{readable} W:{writable}"
        
        print(f"{status} {port:<20} {perms}")
    
    print()
    return ports

def check_permissions(port):
    """Verifica permissões da porta"""
    print("\n" + "="*60)
    print(f"🔒 VERIFICAÇÃO DE PERMISSÕES: {port}")
    print("="*60)
    
    if not os.path.exists(port):
        print(f"❌ Porta {port} não existe!")
        return False
    
    # Verificar leitura
    can_read = os.access(port, os.R_OK)
    print(f"{'✓' if can_read else '❌'} Permissão de leitura: {can_read}")
    
    # Verificar escrita
    can_write = os.access(port, os.W_OK)
    print(f"{'✓' if can_write else '❌'} Permissão de escrita: {can_write}")
    
    if not (can_read and can_write):
        print("\n⚠️  PROBLEMA DE PERMISSÃO DETECTADO!")
        print("\nSOLUÇÕES:")
        print("1. Adicionar usuário ao grupo dialout:")
        print(f"   sudo usermod -a -G dialout $USER")
        print("   Depois faça logout e login novamente\n")
        print("2. OU execute com sudo:")
        print(f"   sudo python3 test_serial.py\n")
        return False
    
    print("\n✓ Permissões OK!")
    return True

def test_connection(port, baudrate):
    """Testa conexão com a impressora"""
    print("\n" + "="*60)
    print(f"🔌 TESTANDO CONEXÃO")
    print("="*60)
    print(f"Porta:     {port}")
    print(f"Baudrate:  {baudrate}")
    print(f"Timeout:   {SERIAL_TIMEOUT}s")
    print()
    
    try:
        print("⏳ Abrindo porta serial...")
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=SERIAL_TIMEOUT,
            write_timeout=SERIAL_TIMEOUT,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False
        )
        
        print("✓ Porta aberta com sucesso!")
        print(f"  - Porta: {ser.port}")
        print(f"  - Baudrate: {ser.baudrate}")
        print(f"  - Aberta: {ser.is_open}")
        
        # Aguardar inicialização
        print("\n⏳ Aguardando inicialização da impressora (2s)...")
        time.sleep(2)
        
        # Limpar buffer
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        # Comandos de teste
        test_commands = [
            ('M115', 'Informações do firmware'),
            ('M105', 'Temperatura'),
            ('M114', 'Posição atual')
        ]
        
        print("\n📤 ENVIANDO COMANDOS DE TESTE:")
        print("-" * 60)
        
        for cmd, desc in test_commands:
            try:
                print(f"\n→ Enviando: {cmd} ({desc})")
                ser.write(f"{cmd}\n".encode())
                
                # Ler resposta (múltiplas linhas)
                responses = []
                start_time = time.time()
                while time.time() - start_time < 1:
                    if ser.in_waiting > 0:
                        line = ser.readline().decode('utf-8', errors='ignore').strip()
                        if line:
                            responses.append(line)
                            if 'ok' in line.lower():
                                break
                
                if responses:
                    print("← Resposta:")
                    for resp in responses:
                        print(f"  {resp}")
                else:
                    print("⚠️  Sem resposta")
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Erro ao enviar {cmd}: {e}")
        
        ser.close()
        print("\n" + "="*60)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("="*60)
        print("\n✓ A impressora está respondendo corretamente")
        print("✓ Você pode iniciar o servidor Chromasistem\n")
        return True
        
    except serial.SerialException as e:
        print(f"\n❌ ERRO SERIAL: {e}\n")
        
        if 'Permission denied' in str(e):
            print("⚠️  PROBLEMA: Sem permissão para acessar a porta")
            print("\nSOLUÇÕES:")
            print("1. Adicione seu usuário ao grupo dialout:")
            print("   sudo usermod -a -G dialout $USER")
            print("   Depois faça logout e login\n")
            print("2. OU execute com sudo:")
            print("   sudo python3 test_serial.py\n")
            
        elif 'No such file or directory' in str(e):
            print("⚠️  PROBLEMA: Porta não existe")
            print("\nSOLUÇÕES:")
            print("1. Verifique se a impressora está conectada")
            print("2. Use uma das portas listadas acima")
            print("3. Confira o cabo USB\n")
            
        elif 'Device or resource busy' in str(e):
            print("⚠️  PROBLEMA: Porta em uso por outro programa")
            print("\nSOLUÇÕES:")
            print("1. Feche o Chromasistem se estiver rodando")
            print("2. Feche OctoPrint, Pronterface ou outros programas")
            print("3. Verifique processos usando a porta:")
            print(f"   lsof {port}\n")
        
        return False
        
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {type(e).__name__}: {e}\n")
        return False

def main():
    print("\n" + "="*60)
    print("🔧 CHROMASISTEM - DIAGNÓSTICO DE CONEXÃO SERIAL")
    print("="*60)
    
    # Listar portas disponíveis
    ports = list_available_ports()
    
    # Verificar permissões da porta configurada
    if os.path.exists(SERIAL_PORT):
        check_permissions(SERIAL_PORT)
    else:
        print(f"\n⚠️  Porta configurada {SERIAL_PORT} não existe!")
        if ports:
            print(f"\n💡 Sugestão: Use uma das portas listadas acima")
            print(f"   Edite app.py e altere SERIAL_PORT para a porta correta\n")
        return
    
    # Testar conexão
    test_connection(SERIAL_PORT, SERIAL_BAUDRATE)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Teste interrompido pelo usuário\n")
        sys.exit(0)
