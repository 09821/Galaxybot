#!/usr/bin/env python3
"""
BOT MASTER CONTROLLER - Replit Dashboard
Gerencia múltiplos bots Roblox e dashboard web
"""

import json
import time
import threading
import requests
from flask import Flask, render_template, jsonify, request
from datetime import datetime
import logging

# Configuração
app = Flask(__name__)
WEBHOOK_URL = "https://discord.com/api/webhooks/1458473913183899871/zYl2Z0fyeDnBJblnSMJy53N6rC47xxJietRwHKriODetqU5FeOXpBVQgSnkvE5RFWiaT"
ROBLOX_COOKIE = "_|WARNING:-DO-NOT-SHARE-THIS.--Sharing-this-will-allow-someone-to-log-in-as-you-and-to-steal-your-ROBUX-and-items.|_CAEaAhADIhwKBGR1aWQSFDE3ODQ5NDM1NDI0MzM2MjgzMDE3KAM.c_et606jCb9UwfLYbIPMXjA_UBNkQvwmk4uEjUh3rcVNBWVJorJPdXFkKG9j6M0wQ_BJcMSJe9NE2PfQK0O-GfP0MtgGDi0C52x1QsQ93BegQAfGduQBLffRWVyW8Hf2L2bJr6JMdo6AKREs0jjb1YNwdD7fa3sm-dyoR0aHBngVHlHGU9PoAWLbvLhiiosev_WDuhEvTe0zO56BaOAgjVUb3pSDhq4ofGQodzY7toI5zgSxJakGa78FHnUA48I-ghRP_4TMTCGpbfL4zREjI62SSK5tCKPFcbz-mX0_Dl78SmgYupA9u1WqWi4FKYPUn8_il4KiRxPJuP1WOxLeaPUqMWaNy2lf07BBSjCtcj5m6SbSE6JD1ND_N2W-TEE9YzzYzWc72B5J6LM4ThYNXgCO-Kw_aI4Nc805rkIOpFDnJNHCWCsEx4uqI5ir3EnnXYpDI-ctZ4GLu-tJmFMfiEZmMBsmpFHC2tkNDE4mwKL_ZwmCxNi31pUntVyHpYEuA9oQ2dz7iHFi07uhQIlYCJ0y9Sv7LngMjtGv2MnFHG5bGOG1JhiowpT96AqucbZsnrzMd_244jA813c9-WeDtRxW46c0eb7SVy1-dhEYXTaw73CSRcuDK659fnbrOaAbQ5rQ-e5-5TDBkmMhpG1vvdXRZKTjx7HTaWTGGzpGR2i_SE1MKYlEhXiZkmiCrPU9yDMZDcouhI6_1BijvE-eQNMRYFGq4ySeWe7Qx2a_zPWEiVCfGgUom702T6SvyWPRUQq4yLa3DrZw5qgkUWtgkW7FPAL7v0LkWeUNoxl9z2yn5SqU"

# Estado do sistema
bots = {
    "main_bot": {
        "name": "ScannerBot_Alt",
        "status": "offline",
        "current_server": None,
        "player_count": 0,
        "last_update": None,
        "fruits_found": [],
        "scan_stats": {
            "servers_scanned": 0,
            "fruits_detected": 0,
            "empty_servers_found": 0
        }
    }
}

# Banco de dados em memória
detected_fruits_db = []
empty_servers_db = []

# ==================== FUNÇÕES DISCORD ====================
def send_discord_notification(content, embed_data=None):
    """Envia notificação para Discord"""
    try:
        message = {
            "content": content,
            "embeds": [embed_data] if embed_data else []
        }
        
        headers = {"Content-Type": "application/json"}
        response = requests.post(WEBHOOK_URL, json=message, headers=headers, timeout=5)
        
        if response.status_code == 204:
            print("✅ Notificação enviada para Discord")
            return True
        else:
            print(f"❌ Erro Discord: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao enviar Discord: {e}")
        return False

def notify_bot_online(bot_name, game_name, server_id, player_count):
    """Notifica quando bot ficar online"""
    embed = {
        "title": "🤖 BOT ONLINE!",
        "description": "@everyone @here **Scanner iniciado!**",
        "color": 65280,  # Verde
        "fields": [
            {
                "name": "👤 Nome da Conta",
                "value": bot_name,
                "inline": True
            },
            {
                "name": "🎮 Nome do Jogo",
                "value": game_name,
                "inline": True
            },
            {
                "name": "👥 Jogadores no Server",
                "value": str(player_count),
                "inline": True
            }
        ],
        "footer": {
            "text": f"Blox Fruits Scanner • {datetime.now().strftime('%H:%M:%S')}"
        }
    }
    
    return send_discord_notification("", embed)

def notify_fruits_detected(bot_name, server_id, player_count, fruits_list):
    """Notifica quando encontrar frutas"""
    if not fruits_list:
        return False
    
    # Formatando lista de frutas
    fruit_counter = {}
    for fruit in fruits_list:
        fruit_counter[fruit] = fruit_counter.get(fruit, 0) + 1
    
    fruits_text = ""
    for fruit, count in fruit_counter.items():
        fruits_text += f"• {fruit} x{count}\n"
    
    # Gerando links
    game_id = 2753915549
    mobile_link = f"roblox://placeId={game_id}&gameInstanceId={server_id}"
    pc_link = f"https://www.roblox.com/games/{game_id}/Blox-Fruits?privateServerLinkCode={server_id}"
    
    embed = {
        "title": "🍎 NOVAS FRUTAS ENCONTRADAS!",
        "description": "@everyone @here **New Fruit!**",
        "color": 16753920,  # Laranja
        "fields": [
            {
                "name": "👥 Players In Server",
                "value": str(player_count),
                "inline": True
            },
            {
                "name": "🤖 Player Detector",
                "value": bot_name,
                "inline": True
            },
            {
                "name": "🆔 Job ID",
                "value": f"`{server_id}`",
                "inline": False
            },
            {
                "name": "📱 Link Mobile",
                "value": f"[Clique Aqui]({mobile_link})",
                "inline": True
            },
            {
                "name": "💻 Link PC",
                "value": f"[Clique Aqui]({pc_link})",
                "inline": True
            },
            {
                "name": f"🍎 Fruits Detected ({len(fruits_list)})",
                "value": fruits_text[:1020] + ("..." if len(fruits_text) > 1020 else ""),
                "inline": False
            }
        ],
        "footer": {
            "text": f"Scanner Bot • {datetime.now().strftime('%H:%M:%S')}"
        }
    }
    
    return send_discord_notification("", embed)

# ==================== API ROUTES ====================
@app.route('/')
def dashboard():
    """Dashboard principal"""
    return render_template('dashboard.html', 
                         bots=bots, 
                         fruits_db=detected_fruits_db[-20:],  # Últimas 20
                         empty_servers=empty_servers_db[-10:])

@app.route('/api/bot_status')
def get_bot_status():
    """API para status do bot"""
    return jsonify(bots)

@app.route('/api/update_bot', methods=['POST'])
def update_bot_status():
    """API para atualizar status do bot (chamado pelo Roblox)"""
    try:
        data = request.json
        bot_name = data.get('bot_name', 'main_bot')
        
        if bot_name not in bots:
            bots[bot_name] = {
                "name": bot_name,
                "status": "online",
                "current_server": None,
                "player_count": 0,
                "last_update": datetime.now().isoformat(),
                "fruits_found": [],
                "scan_stats": {"servers_scanned": 0, "fruits_detected": 0, "empty_servers_found": 0}
            }
        
        # Atualizar dados do bot
        for key, value in data.items():
            if key in bots[bot_name]:
                bots[bot_name][key] = value
        
        bots[bot_name]['last_update'] = datetime.now().isoformat()
        
        # Se for primeiro online, notificar Discord
        if data.get('status') == 'online' and data.get('game_name'):
            notify_bot_online(
                bot_name,
                data['game_name'],
                data.get('server_id', 'Unknown'),
                data.get('player_count', 0)
            )
        
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/report_fruits', methods=['POST'])
def report_fruits():
    """API para reportar frutas encontradas"""
    try:
        data = request.json
        
        # Adicionar ao banco de dados
        for fruit in data.get('fruits', []):
            fruit_entry = {
                **fruit,
                'bot_name': data['bot_name'],
                'server_id': data['server_id'],
                'timestamp': datetime.now().isoformat(),
                'player_count': data.get('player_count', 0)
            }
            detected_fruits_db.append(fruit_entry)
        
        # Notificar Discord
        fruits_names = [f['name'] for f in data.get('fruits', [])]
        notify_fruits_detected(
            data['bot_name'],
            data['server_id'],
            data.get('player_count', 0),
            fruits_names
        )
        
        # Atualizar estatísticas do bot
        bot_name = data.get('bot_name', 'main_bot')
        if bot_name in bots:
            bots[bot_name]['scan_stats']['fruits_detected'] += len(fruits_names)
            bots[bot_name]['scan_stats']['servers_scanned'] += 1
            bots[bot_name]['fruits_found'].extend(fruits_names)
        
        return jsonify({"status": "success", "fruits_reported": len(fruits_names)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/report_empty_server', methods=['POST'])
def report_empty_server():
    """API para reportar servidor vazio"""
    try:
        data = request.json
        
        server_info = {
            'server_id': data['server_id'],
            'player_count': data['player_count'],
            'ping': data.get('ping', 0),
            'bot_name': data.get('bot_name', 'main_bot'),
            'timestamp': datetime.now().isoformat()
        }
        
        empty_servers_db.append(server_info)
        
        # Atualizar estatísticas
        bot_name = data.get('bot_name', 'main_bot')
        if bot_name in bots:
            bots[bot_name]['scan_stats']['empty_servers_found'] += 1
        
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/get_empty_servers')
def get_empty_servers():
    """API para obter servidores vazios"""
    # Filtrar servidores com menos de 4 jogadores
    empty_servers = [s for s in empty_servers_db if s['player_count'] <= 3]
    
    # Ordenar por player_count (ascendente)
    empty_servers.sort(key=lambda x: x['player_count'])
    
    # Remover duplicados mantendo o mais recente
    unique_servers = []
    seen_ids = set()
    
    for server in reversed(empty_servers):
        if server['server_id'] not in seen_ids:
            unique_servers.append(server)
            seen_ids.add(server['server_id'])
    
    return jsonify(unique_servers[:20])  # Retorna até 20

# ==================== TEMPLATE HTML ====================
@app.route('/dashboard')
def dashboard_page():
    return '''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🤖 Blox Fruits Bot Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <script>
            async function updateDashboard() {
                const response = await fetch('/api/bot_status');
                const data = await response.json();
                
                // Atualizar status dos bots
                for (const [botName, botData] of Object.entries(data)) {
                    const botElement = document.getElementById(`bot-${botName}`);
                    if (botElement) {
                        const statusColor = botData.status === 'online' ? 'bg-green-500' : 
                                          botData.status === 'scanning' ? 'bg-yellow-500' : 'bg-red-500';
                        
                        botElement.innerHTML = `
                            <div class="bg-gray-800 rounded-lg p-4">
                                <div class="flex justify-between items-center">
                                    <div>
                                        <h3 class="text-xl font-bold text-white">${botName}</h3>
                                        <p class="text-gray-300">${botData.name}</p>
                                    </div>
                                    <div class="flex items-center space-x-2">
                                        <span class="px-3 py-1 rounded-full ${statusColor} text-white text-sm">
                                            ${botData.status.toUpperCase()}
                                        </span>
                                        <span class="text-gray-400">
                                            <i class="fas fa-clock"></i> ${new Date(botData.last_update).toLocaleTimeString()}
                                        </span>
                                    </div>
                                </div>
                                
                                <div class="mt-4 grid grid-cols-3 gap-4">
                                    <div class="bg-gray-700 rounded p-3">
                                        <p class="text-gray-400 text-sm">Server Atual</p>
                                        <p class="text-white font-mono">${botData.current_server || 'N/A'}</p>
                                    </div>
                                    <div class="bg-gray-700 rounded p-3">
                                        <p class="text-gray-400 text-sm">Jogadores</p>
                                        <p class="text-white text-2xl">${botData.player_count}</p>
                                    </div>
                                    <div class="bg-gray-700 rounded p-3">
                                        <p class="text-gray-400 text-sm">Frutas Detectadas</p>
                                        <p class="text-white text-2xl">${botData.scan_stats?.fruits_detected || 0}</p>
                                    </div>
                                </div>
                                
                                <div class="mt-4">
                                    <p class="text-gray-400 mb-2">Últimas Frutas:</p>
                                    <div class="flex flex-wrap gap-2">
                                        ${botData.fruits_found?.slice(-5).map(fruit => 
                                            `<span class="px-2 py-1 bg-purple-600 rounded text-sm">${fruit}</span>`
                                        ).join('') || '<span class="text-gray-500">Nenhuma fruta ainda</span>'}
                                    </div>
                                </div>
                            </div>
                        `;
                    }
                }
            }
            
            async function getEmptyServers() {
                const response = await fetch('/api/get_empty_servers');
                const servers = await response.json();
                
                const container = document.getElementById('empty-servers');
                if (servers.length > 0) {
                    container.innerHTML = servers.map(server => `
                        <div class="bg-gray-800 p-3 rounded mb-2">
                            <div class="flex justify-between">
                                <span class="text-white font-mono">${server.server_id.substring(0, 15)}...</span>
                                <span class="px-2 py-1 ${server.player_count === 1 ? 'bg-green-600' : 'bg-yellow-600'} rounded text-sm">
                                    ${server.player_count} jogador${server.player_count !== 1 ? 'es' : ''}
                                </span>
                            </div>
                            <div class="text-gray-400 text-sm mt-1">
                                <i class="fas fa-robot"></i> ${server.bot_name} • 
                                <i class="fas fa-clock ml-2"></i> ${new Date(server.timestamp).toLocaleTimeString()}
                            </div>
                        </div>
                    `).join('');
                } else {
                    container.innerHTML = '<p class="text-gray-500 text-center">Nenhum servidor vazio encontrado ainda</p>';
                }
            }
            
            // Atualizar a cada 5 segundos
            setInterval(updateDashboard, 5000);
            setInterval(getEmptyServers, 10000);
            
            // Carregar inicial
            document.addEventListener('DOMContentLoaded', () => {
                updateDashboard();
                getEmptyServers();
            });
        </script>
    </head>
    <body class="bg-gray-900 text-white min-h-screen">
        <div class="container mx-auto px-4 py-8">
            <header class="mb-8">
                <h1 class="text-4xl font-bold mb-2">
                    <i class="fas fa-robot"></i> Blox Fruits Bot Dashboard
                </h1>
                <p class="text-gray-400">Monitoramento em tempo real dos bots scanner</p>
            </header>
            
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Coluna 1: Status dos Bots -->
                <div class="lg:col-span-2">
                    <h2 class="text-2xl font-bold mb-4">
                        <i class="fas fa-server"></i> Status dos Bots
                    </h2>
                    <div id="bots-container">
                        <!-- Preenchido por JavaScript -->
                        <div class="text-gray-500">Carregando status dos bots...</div>
                    </div>
                </div>
                
                <!-- Coluna 2: Estatísticas -->
                <div>
                    <h2 class="text-2xl font-bold mb-4">
                        <i class="fas fa-chart-bar"></i> Estatísticas
                    </h2>
                    <div class="bg-gray-800 rounded-lg p-4 mb-6">
                        <h3 class="text-lg font-bold mb-3">Servidores Vazios</h3>
                        <div id="empty-servers" class="max-h-96 overflow-y-auto">
                            <!-- Preenchido por JavaScript -->
                        </div>
                    </div>
                    
                    <div class="bg-gray-800 rounded-lg p-4">
                        <h3 class="text-lg font-bold mb-3">Ações Rápidas</h3>
                        <div class="space-y-3">
                            <button onclick="fetch('/api/get_empty_servers').then(r => r.json()).then(console.log)" 
                                    class="w-full bg-blue-600 hover:bg-blue-700 py-2 rounded">
                                <i class="fas fa-sync-alt"></i> Buscar Servidores Vazios
                            </button>
                            <button onclick="location.reload()" 
                                    class="w-full bg-gray-700 hover:bg-gray-600 py-2 rounded">
                                <i class="fas fa-redo"></i> Atualizar Dashboard
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Últimas Frutas Detectadas -->
            <div class="mt-8">
                <h2 class="text-2xl font-bold mb-4">
                    <i class="fas fa-apple-alt"></i> Últimas Frutas Detectadas
                </h2>
                <div class="bg-gray-800 rounded-lg p-4">
                    <div id="recent-fruits" class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
                        <!-- Será preenchido pelo backend -->
                        {% for fruit in fruits_db %}
                        <div class="bg-gray-700 p-3 rounded text-center">
                            <div class="text-lg font-bold">{{ fruit.name }}</div>
                            <div class="text-sm text-gray-400">{{ fruit.bot_name }}</div>
                            <div class="text-xs text-gray-500">{{ fruit.timestamp[-8:] }}</div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
            
            <footer class="mt-8 pt-4 border-t border-gray-700 text-center text-gray-500">
                <p>🤖 Blox Fruits Bot Scanner • Dashboard v1.0 • 
                   <span id="current-time">{{ datetime.now().strftime('%H:%M:%S') }}</span>
                </p>
            </footer>
        </div>
        
        <script>
            // Atualizar hora atual
            function updateTime() {
                document.getElementById('current-time').textContent = 
                    new Date().toLocaleTimeString();
            }
            setInterval(updateTime, 1000);
            
            // Inicializar containers de bot
            const botsContainer = document.getElementById('bots-container');
            botsContainer.innerHTML = `
                {% for bot_name, bot_data in bots.items() %}
                <div id="bot-{{ bot_name }}" class="mb-4">
                    <!-- Preenchido por JavaScript -->
                </div>
                {% endfor %}
            `;
        </script>
    </body>
    </html>
    '''

# ==================== MAIN ====================
if __name__ == "__main__":
    print("🚀 Iniciando Bot Dashboard...")
    print("🌐 Dashboard disponível em: http://localhost:5000")
    print("🤖 Bot Controller pronto para receber conexões")
    
    # Iniciar servidor Flask
    app.run(host='0.0.0.0', port=5000, debug=False)