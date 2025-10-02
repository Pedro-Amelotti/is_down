function createSystemCard(system, status = 'loading') {
            const card = document.createElement('div');
            card.className = `system-card ${status}`;
            card.innerHTML = `
                <div class="system-name">${system.name}</div>
                <div class="system-status">${status.toUpperCase()}</div>
                <a href="${system.url}" target="_blank" class="system-url">Link</a>
                <div class="system-timestamp"></div>
                ${status === 'loading' ? '<div class="loading-bar"></div>' : ''}
            `;
            return card;
        }

        async function updateSystemStatus(card, system) {
            try {
                const response = await fetch(`/system_status/?url=${encodeURIComponent(system.url)}&name=${encodeURIComponent(system.name)}`);
                const data = await response.json();

                // Converte a string de status para uma classe CSS válida (ex: "NOT FOUND" -> "not-found")
                const statusClass = data.status.toLowerCase().replace(/\s+/g, '-');

                card.className = `system-card ${statusClass}`;
                card.querySelector('.system-status').textContent = data.status;
                card.querySelector('.system-timestamp').textContent = `Última verificação: ${data.checked_at}`;
                const loadingBar = card.querySelector('.loading-bar');
                if (loadingBar) {
                    loadingBar.remove();
                }
            
            } catch (error) {
                card.className = 'system-card down';
                card.querySelector('.system-status').textContent = 'ERRO';
            }
        }

        async function loadSystems() {
            const container = document.getElementById('main-container');
            try {
                const response = await fetch('/systems_list/');
                const servers = await response.json();

                container.innerHTML = ''; // Limpa o container antes de adicionar os painéis
            
                for (const serverName in servers) {
                    const systems = servers[serverName];

                    // Cria o painel para o servidor
                    const panel = document.createElement('div');
                    panel.className = 'systems-panel';
                
                    // Adiciona o título do servidor
                    const title = document.createElement('h2');
                    title.className = 'server-title';
                    title.textContent = serverName;
                    panel.appendChild(title);

                    // Adiciona o container de filtros
                    const filterContainer = document.createElement('div');
                    filterContainer.className = 'filter-container';
                    filterContainer.innerHTML = `
                        <input type="text" id="searchInput-${serverName}" onkeyup="filterSystems('${serverName}')" placeholder="Buscar por nome...">
                        <button onclick="filterByStatus('down', '${serverName}')">DOWN</button>
                        <button onclick="filterByStatus('forbidden', '${serverName}')">FORBIDDEN</button>
                        <button onclick="filterByStatus('', '${serverName}')">Limpar</button>
                    `;
                    panel.appendChild(filterContainer);
                
                    // Cria a grade de sistemas
                    const grid = document.createElement('div');
                    grid.className = 'systems-grid';
                    grid.id = `systems-grid-${serverName}`;
                    panel.appendChild(grid);
                
                    // Adiciona o painel completo ao container principal
                    container.appendChild(panel);

                    // Popula a grade com os sistemas
                    if (systems.length > 0) {
                        systems.forEach(system => {
                            const card = createSystemCard(system);
                            grid.appendChild(card);
                            updateSystemStatus(card, system);
                        });
                    } else {
                        grid.innerHTML = '<div>Nenhum sistema para monitorar neste servidor.</div>';
                    }
                }
            } catch (error) {
                container.innerHTML = '<div class="system-card down">Erro ao carregar a lista de servidores</div>';
            }
        }

        function filterSystems(serverName) {
            const input = document.getElementById(`searchInput-${serverName}`);
            const filter = input.value.toUpperCase();
            const grid = document.getElementById(`systems-grid-${serverName}`);
            const cards = grid.getElementsByClassName('system-card');

            for (let i = 0; i < cards.length; i++) {
                const name = cards[i].getElementsByClassName('system-name')[0];
                if (name.innerHTML.toUpperCase().indexOf(filter) > -1) {
                    cards[i].style.display = "";
                } else {
                    cards[i].style.display = "none";
                }
            }
        }

        function filterByStatus(status, serverName) {
            const grid = document.getElementById(`systems-grid-${serverName}`);
            const cards = grid.getElementsByClassName('system-card');

            for (let i = 0; i < cards.length; i++) {
                if (status === '' || cards[i].classList.contains(status)) {
                    cards[i].style.display = "";
                } else {
                    cards[i].style.display = "none";
                }
            }
        }

        loadSystems();
        setInterval(loadSystems, 60000);