-- ============================================
-- 🤖 BLOX FRUITS BOT SCANNER COMPLETO
-- Sistema de detecção de frutas + comunicação com dashboard
-- ============================================

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local HttpService = game:GetService("HttpService")
local TeleportService = game:GetService("TeleportService")
local MarketplaceService = game:GetService("MarketplaceService")
local Workspace = game:GetService("Workspace")
local StarterGui = game:GetService("StarterGui")

-- =========== CONFIGURAÇÃO ===========
local BOT_NAME = Players.LocalPlayer.Name
local DASHBOARD_URL = "http://localhost:5000"  -- URL do seu Replit
local DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1458473913183899871/zYl2Z0fyeDnBJblnSMJy53N6rC47xxJietRwHKriODetqU5FeOXpBVQgSnkvE5RFWiaT"
local GAME_ID = 2753915549  -- Blox Fruits Place ID
local SCAN_DURATION = 30    -- Segundos para escanear cada server
local SWITCH_DELAY = 17     -- Segundos entre trocas de server

-- =========== LISTA DE FRUTAS ===========
local VALID_FRUITS = {
    -- COMUM
    "Rocket Fruit", "Spin Fruit", "Chop Fruit", "Spring Fruit",
    "Bomb Fruit", "Smoke Fruit", "Spike Fruit",
    -- INCOMUM
    "Flame Fruit", "Ice Fruit", "Sand Fruit", "Dark Fruit",
    "Diamond Fruit", "Light Fruit", "Ghost Fruit",
    -- RARO
    "Rubber Fruit", "Barrier Fruit", "Magma Fruit", "Quake Fruit",
    "Love Fruit", "Spider Fruit", "Sound Fruit",
    -- LENDÁRIO
    "Phoenix Fruit", "Portal Fruit", "Rumble Fruit", "Gravity Fruit",
    "Blizzard Fruit", "Eagle Fruit", "Creation Fruit", "Pain Fruit",
    -- MÍTICO
    "Dough Fruit", "Shadow Fruit", "Venom Fruit", "Control Fruit",
    "Spirit Fruit", "Leopard Fruit", "Mammoth Fruit", "T-Rex Fruit",
    "Kitsune Fruit", "Dragon Fruit", "Gas Fruit", "Yeti Fruit",
    "Tiger Fruit", "Blade Fruit"
}

-- =========== VARIÁVEIS GLOBAIS ===========
local serverJobId = game.JobId
local isScanning = true
local startTime = os.time()
local fruitsDetectedThisSession = {}
local emptyServersFound = {}
local serverScanCount = 0

-- =========== FUNÇÕES UTILITÁRIAS ===========
local function sendHttpRequest(url, data)
    pcall(function()
        local json = HttpService:JSONEncode(data)
        local success, response = pcall(function()
            return HttpService:PostAsync(url, json, Enum.HttpContentType.ApplicationJson)
        end)
        return success, response
    end)
end

local function notifyDashboard(endpoint, data)
    local url = DASHBOARD_URL .. endpoint
    sendHttpRequest(url, data)
end

local function sendDiscordNotification(embedData)
    local message = {
        ["content"] = "",
        ["embeds"] = {embedData}
    }
    sendHttpRequest(DISCORD_WEBHOOK, message)
end

-- =========== FUNÇÃO DE DETECÇÃO DE FRUTAS (SUA VERSÃO) ===========
local function scanForFruits()
    local foundFruits = {}
    
    -- Cria dicionário para busca rápida
    local fruitLookup = {}
    for _, fruit in ipairs(VALID_FRUITS) do
        fruitLookup[string.lower(fruit)] = fruit
    end
    
    -- Procura em todos os lugares possíveis
    local function searchIn(parent)
        if not parent then return end
        
        for _, obj in pairs(parent:GetDescendants()) do
            if obj:IsA("Model") or obj:IsA("Tool") then
                local objName = obj.Name
                local lowerName = string.lower(objName)
                
                -- Verifica se é uma fruta conhecida
                if fruitLookup[lowerName] then
                    table.insert(foundFruits, {
                        name = fruitLookup[lowerName],
                        position = obj:GetPivot().Position,
                        time_found = os.time()
                    })
                -- Verifica se é "Fruit" genérica
                elseif objName == "Fruit" then
                    table.insert(foundFruits, {
                        name = "Unknown Fruit",
                        position = obj:GetPivot().Position,
                        time_found = os.time()
                    })
                end
            end
        end
    end
    
    -- Lugares para procurar
    searchIn(Workspace)
    searchIn(Workspace:FindFirstChild("SeaEvent"))
    searchIn(Workspace:FindFirstChild("FruitSpawner"))
    searchIn(Workspace:FindFirstChild("Fruits"))
    
    return foundFruits
end

-- =========== FUNÇÃO PARA ENCONTRAR SERVIDORES VAZIOS ===========
local function findEmptyServers()
    pcall(function()
        local url = string.format("https://games.roblox.com/v1/games/%d/servers/Public?limit=50&sortOrder=Asc", GAME_ID)
        
        local success, response = pcall(function()
            return HttpService:GetAsync(url, true)
        end)
        
        if success then
            local data = HttpService:JSONDecode(response)
            local emptyServers = {}
            
            for _, server in ipairs(data.data) do
                if server.playing <= 3 and server.id ~= serverJobId then
                    table.insert(emptyServers, {
                        id = server.id,
                        playing = server.playing,
                        ping = server.ping or 100
                    })
                end
            end
            
            -- Reportar servidores vazios para o dashboard
            for _, server in ipairs(emptyServers) do
                notifyDashboard("/api/report_empty_server", {
                    server_id = server.id,
                    player_count = server.playing,
                    ping = server.ping,
                    bot_name = BOT_NAME
                })
                
                emptyServersFound[server.id] = server
            end
            
            return emptyServers
        end
    end)
    
    return {}
end

-- =========== FUNÇÃO PARA TROCAR DE SERVIDOR ===========
local function switchToBetterServer()
    local emptyServers = findEmptyServers()
    
    if #emptyServers > 0 then
        -- Escolher o servidor com menos jogadores
        table.sort(emptyServers, function(a, b)
            return a.playing < b.playing
        end)
        
        local targetServer = emptyServers[1]
        
        print(string.format("🔄 Trocando para servidor com %d jogadores...", targetServer.playing))
        
        -- Notificar dashboard
        notifyDashboard("/api/update_bot", {
            bot_name = BOT_NAME,
            status = "changing_server",
            last_server = serverJobId,
            new_server = targetServer.id,
            reason = "seeking_empty_server"
        })
        
        -- Teleportar
        task.wait(2)
        TeleportService:TeleportToPlaceInstance(GAME_ID, targetServer.id, Players.LocalPlayer)
        return true
    end
    
    return false
end

-- =========== INICIALIZAÇÃO DO BOT ===========
local function initializeBot()
    task.wait(5)  -- Esperar carregar
    
    -- Obter informações do jogo
    local gameInfo = pcall(function()
        return MarketplaceService:GetProductInfo(game.PlaceId)
    end)
    
    local gameName = "Blox Fruits"
    if gameInfo then
        gameName = gameInfo.Name
    end
    
    -- Obter contagem de jogadores
    local playerCount = #Players:GetPlayers()
    serverJobId = game.JobId
    
    print("🤖 BOT INICIALIZADO")
    print("👤 Nome:", BOT_NAME)
    print("🎮 Jogo:", gameName)
    print("🆔 Server ID:", serverJobId)
    print("👥 Jogadores:", playerCount)
    
    -- Notificar dashboard que está online
    notifyDashboard("/api/update_bot", {
        bot_name = BOT_NAME,
        status = "online",
        game_name = gameName,
        server_id = serverJobId,
        player_count = playerCount
    })
    
    return true
end

-- =========== LOOP PRINCIPAL DE SCAN ===========
local function mainScanLoop()
    while isScanning do
        serverScanCount = serverScanCount + 1
        
        -- Atualizar serverJobId (pode ter mudado)
        serverJobId = game.JobId
        local playerCount = #Players:GetPlayers()
        
        print(string.format("\n🔍 Scan #%d no servidor %s", serverScanCount, string.sub(serverJobId, 1, 10) .. "..."))
        print(string.format("👥 Jogadores: %d", playerCount))
        
        -- Escanear por frutas
        local fruits = scanForFruits()
        
        if #fruits > 0 then
            print(string.format("✅ Encontradas %d frutas!", #fruits))
            
            -- Reportar frutas encontradas
            notifyDashboard("/api/report_fruits", {
                bot_name = BOT_NAME,
                server_id = serverJobId,
                player_count = playerCount,
                fruits = fruits,
                quality_score = math.max(0, 100 - (playerCount * 10))
            })
            
            -- Adicionar à lista da sessão
            for _, fruit in ipairs(fruits) do
                table.insert(fruitsDetectedThisSession, fruit)
            end
        else
            print("❌ Nenhuma fruta encontrada")
        end
        
        -- Atualizar status no dashboard
        notifyDashboard("/api/update_bot", {
            bot_name = BOT_NAME,
            status = "scanning",
            current_server = serverJobId,
            player_count = playerCount,
            last_scan = os.time(),
            total_fruits = #fruitsDetectedThisSession,
            servers_scanned = serverScanCount
        })
        
        -- Aguardar tempo de scan
        print(string.format("⏳ Aguardando %d segundos...", SCAN_DURATION))
        
        for i = SCAN_DURATION, 1, -1 do
            if not isScanning then break end
            task.wait(1)
            
            -- Atualizar contador a cada 5 segundos
            if i % 5 == 0 then
                print(string.format("   %d segundos restantes...", i))
            end
        end
        
        if not isScanning then break end
        
        -- Tentar trocar para servidor melhor (a cada 3 scans)
        if serverScanCount % 3 == 0 then
            print("🔄 Buscando servidor melhor...")
            
            if playerCount > 3 then
                local switched = switchToBetterServer()
                if switched then
                    print("✅ Servidor trocado com sucesso!")
                    task.wait(5)  -- Esperar carregar novo servidor
                else
                    print("❌ Nenhum servidor vazio encontrado")
                end
            else
                print("✅ Servidor atual já está bom (≤3 jogadores)")
            end
        end
        
        -- Pequeno delay entre ciclos
        task.wait(SWITCH_DELAY)
    end
end

-- =========== INICIALIZAÇÃO ===========
task.spawn(function()
    -- Esperar jogo carregar
    repeat task.wait(1) until Players.LocalPlayer.Character
    
    -- Inicializar bot
    local initialized = initializeBot()
    
    if initialized then
        print("\n🚀 INICIANDO SCAN LOOP...")
        mainScanLoop()
    else
        warn("❌ Falha ao inicializar bot")
    end
end)

-- =========== TRATAMENTO DE ERROS ===========
game:GetService("ScriptContext").Error:Connect(function(message, trace, script)
    warn("❌ ERRO NO BOT:", message)
    
    -- Reportar erro ao dashboard
    pcall(function()
        notifyDashboard("/api/update_bot", {
            bot_name = BOT_NAME,
            status = "error",
            error_message = string.sub(message, 1, 100),
            last_server = serverJobId
        })
    end)
end)

-- =========== COMANDOS DE CONTROLE ===========
local function executeCommand(command)
    command = string.lower(command)
    
    if command == "stop" then
        isScanning = false
        print("⏹️ Bot parando...")
        
        notifyDashboard("/api/update_bot", {
            bot_name = BOT_NAME,
            status = "stopped",
            reason = "manual_stop"
        })
        
    elseif command == "status" then
        print("\n=== STATUS DO BOT ===")
        print("Nome:", BOT_NAME)
        print("Status:", isScanning and "Scanning" or "Stopped")
        print("Server ID:", serverJobId)
        print("Scans realizados:", serverScanCount)
        print("Frutas encontradas:", #fruitsDetectedThisSession)
        print("Servidores vazios:", #emptyServersFound)
        
    elseif command == "scannow" then
        print("🔍 Scan manual iniciado...")
        local fruits = scanForFruits()
        print("Frutas encontradas:", #fruits)
        
    elseif command == "findempty" then
        print("🔍 Buscando servidores vazios...")
        local servers = findEmptyServers()
        print("Servidores vazios encontrados:", #servers)
    end
end

-- Expor função de comando para uso externo
_G.BotCommand = executeCommand

print("\n" .. string.rep("=", 50))
print("🤖 BLOX FRUITS BOT SCANNER")
print("📊 Dashboard URL:", DASHBOARD_URL)
print("👤 Bot Name:", BOT_NAME)
print("⚙️ Commands: BotCommand('stop/status/scannow/findempty')")
print(string.rep("=", 50) .. "\n")

-- Mantém o script rodando
while true do
    task.wait(1)
end
