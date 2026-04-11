// Состояние приложения
let personalities = [];
let currentPersonality = null;

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    loadPersonalities();
    setupEventListeners();
    // Случайный контент для примера
    generateRandomContent();
});

// Загрузка личностей с сервера
async function loadPersonalities() {
    try {
        const response = await fetch('/personalities');
        const data = await response.json();
        personalities = data.personalities || [];
        renderPersonalities();
        renderPantheon(); // для примера берём случайные
    } catch (error) {
        console.error('Ошибка загрузки:', error);
        // если сервер не доступен — используем демо-данные
        generateRandomContent();
    }
}

// Рендер карточек личностей
function renderPersonalities() {
    const grid = document.getElementById('personalities-grid');
    if (!grid) return;
    
    if (personalities.length === 0) {
        grid.innerHTML = '<p class="empty-state">Пока нет личностей. Создайте первую.</p>';
        return;
    }
    
    grid.innerHTML = personalities.map(p => `
        <div class="personality-card" onclick="openChat('${p.id}')">
            <div class="personality-header">
                <span class="personality-name">${p.name}</span>
                <span class="personality-tau">τ=${p.tau?.toFixed(1) || '5.0'}</span>
            </div>
            <div class="personality-stats">
                <span>k=${p.k || '1'}</span>
                <span>n=${p.n?.toFixed(1) || (p.tau * p.k).toFixed(1)}</span>
            </div>
            <div class="personality-defects">
                ${(p.defects || []).map(d => 
                    `<span class="defect-tag">${typeof d === 'string' ? d : d.name}</span>`
                ).join('')}
            </div>
        </div>
    `).join('');
}

// Рендер Пантеона (случайные для примера)
function renderPantheon() {
    const grid = document.getElementById('pantheon-grid');
    if (!grid) return;
    
    const pantheonNames = ['Анна', 'Михаил', 'Елена', 'Дмитрий', 'Татьяна', 'Алексей'];
    const pantheonYears = ['1954–2022', '1948–2021', '1963–2023', '1951–2020', '1957–2024', '1945–2022'];
    
    const randomIndices = Array.from({length: 4}, () => Math.floor(Math.random() * pantheonNames.length));
    
    grid.innerHTML = randomIndices.map(i => `
        <div class="pantheon-card" onclick="openPantheon('${pantheonNames[i]}')">
            <div class="name">${pantheonNames[i]}</div>
            <div class="dates">${pantheonYears[i]}</div>
            <div class="memory-count">${Math.floor(Math.random() * 500) + 100} воспоминаний</div>
        </div>
    `).join('');
}

// Генерация случайного контента для демо [citation:5][citation:8]
function generateRandomContent() {
    if (personalities.length === 0) {
        // Используем подход «генеративного текста» [citation:8] — наборы слов для создания случайных фраз
        const firstNames = ['Анна', 'Мария', 'Екатерина', 'Дмитрий', 'Алексей', 'Сергей', 'Ольга', 'Наталья'];
        const lastNames = ['Иванова', 'Петрова', 'Сидорова', 'Смирнов', 'Кузнецов', 'Попов', 'Васильева'];
        const tauValues = [3.2, 4.7, 5.1, 5.8, 6.3, 6.9, 7.2, 7.8, 8.4, 9.1];
        const kValues = [1, 2, 3, 4, 5, 6, 7];
        const defectPools = [
            ['любопытство', 'доверчивость'],
            ['упрямство', 'мечтательность'],
            ['осторожность', 'импульсивность'],
            ['перфекционизм', 'лень'],
            ['общительность', 'замкнутость']
        ];
        
        personalities = Array.from({length: 8}, (_, i) => {
            const firstName = firstNames[Math.floor(Math.random() * firstNames.length)];
            const lastName = lastNames[Math.floor(Math.random() * lastNames.length)];
            const tau = tauValues[Math.floor(Math.random() * tauValues.length)];
            const k = kValues[Math.floor(Math.random() * kValues.length)];
            const defects = defectPools[Math.floor(Math.random() * defectPools.length)];
            
            return {
                id: `p${String(i + 1).padStart(3, '0')}`,
                name: `${firstName} ${lastName}`,
                tau: tau,
                k: k,
                n: tau * k,
                defects: defects,
                rhythm: 0.8 + Math.random() * 1.4
            };
        });
        
        renderPersonalities();
    }
}

// Навигация по вкладкам
function setupEventListeners() {
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const viewId = btn.dataset.view + '-view';
            document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
            document.getElementById(viewId)?.classList.add('active');
        });
    });
    
    // Создание новой личности
    document.getElementById('create-personality-btn')?.addEventListener('click', () => {
        document.getElementById('create-modal').classList.add('active');
    });
    
    // Закрытие модалок
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', () => {
            btn.closest('.modal').classList.remove('active');
        });
    });
    
    // Форма создания
    document.getElementById('create-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        
        const defects = formData.get('defects').split(',').map(d => d.trim()).filter(d => d);
        
        const newPersonality = {
            name: formData.get('name'),
            tau: parseFloat(formData.get('tau')),
            k: parseInt(formData.get('k')),
            rhythm: parseFloat(formData.get('rhythm')),
            defects: defects.map(d => ({ name: d, vector: 0.5, strength: 0.5 }))
        };
        
        try {
            const response = await fetch('/personalities', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newPersonality)
            });
            
            if (response.ok) {
                document.getElementById('create-modal').classList.remove('active');
                loadPersonalities(); // перезагружаем список
            }
        } catch (error) {
            console.error('Ошибка создания:', error);
            // для демо — просто добавим локально
            newPersonality.id = `p${String(personalities.length + 1).padStart(3, '0')}`;
            newPersonality.n = newPersonality.tau * newPersonality.k;
            personalities.push(newPersonality);
            renderPersonalities();
            document.getElementById('create-modal').classList.remove('active');
        }
    });
    
    // Отправка сообщения
    document.getElementById('chat-send')?.addEventListener('click', sendMessage);
    document.getElementById('chat-input')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
}

// Открыть чат с личностью
window.openChat = function(personalityId) {
    const personality = personalities.find(p => p.id === personalityId);
    if (!personality) return;
    
    currentPersonality = personality;
    document.getElementById('chat-personality-name').textContent = personality.name;
    document.getElementById('chat-messages').innerHTML = `
        <div class="message personality">Здравствуйте. Я — ${personality.name}. Чем могу помочь?</div>
    `;
    document.getElementById('chat-modal').classList.add('active');
};

// Отправить сообщение
async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message || !currentPersonality) return;
    
    // Добавляем сообщение пользователя
    const messagesDiv = document.getElementById('chat-messages');
    messagesDiv.innerHTML += `<div class="message user">${message}</div>`;
    input.value = '';
    
    const accessLevel = document.getElementById('chat-access-level').value;
    
    try {
        const response = await fetch(`/personalities/${currentPersonality.id}/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                question: message,
                person: accessLevel === 'relation' ? 'собеседник' : null
            })
        });
        
        const data = await response.json();
        messagesDiv.innerHTML += `<div class="message personality">${data.answer}</div>`;
    } catch (error) {
        // демо-режим
        setTimeout(() => {
            const answers = [
                "Я вспоминаю что-то связанное с этим...",
                "Это важный вопрос. Дай подумать.",
                "В моей памяти есть несколько похожих моментов.",
                "Хороший вопрос. Расскажи подробнее."
            ];
            messagesDiv.innerHTML += `<div class="message personality">${
                answers[Math.floor(Math.random() * answers.length)]
            }</div>`;
        }, 500);
    }
    
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Открыть запись в Пантеоне
window.openPantheon = function(name) {
    alert(`Пантеон: ${name}\nВы можете оставить сообщение или просто побыть в тишине.`);
};