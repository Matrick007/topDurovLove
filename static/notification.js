// static/notification.js

// Запрос разрешения на уведомления
function requestNotificationPermission() {
    if (!("Notification" in window)) {
        console.log("Браузер не поддерживает уведомления");
        return;
    }

    if (Notification.permission === "granted") {
        console.log("Разрешение на уведомления уже получено");
    } else if (Notification.permission !== "denied") {
        Notification.requestPermission().then(function (permission) {
            if (permission === "granted") {
                console.log("Разрешение на уведомления получено");
            }
        });
    }
}

// Показать уведомление
function showNotification(sender, message) {
    if (Notification.permission === "granted") {
        const notification = new Notification(`${sender} написал:`, {
            body: message,
            icon: "/static/bell.png", // иконка (опционально)
            badge: "/static/badge.png"
        });

        // Открыть чат по клику
        notification.onclick = function () {
            window.focus();
            notification.close();
        };

        // Автозакрытие через 5 сек
        setTimeout(() => notification.close(), 5000);
    }
}

// Проиграть звук
function playNotificationSound() {
    const audio = new Audio('/static/message.mp3');
    audio.play().catch(e => console.log("Не удалось проиграть звук:", e));
}

// === ФУНКЦИИ ДЛЯ ПЕРЕКЛЮЧЕНИЯ ТЕМЫ ===
function setTheme(themeName) {
    localStorage.setItem('theme', themeName);
    document.documentElement.setAttribute('data-theme', themeName);
    
    // Обновить иконку темы
    updateThemeIcon(themeName);
}

function toggleTheme() {
    if (localStorage.getItem('theme') === 'dark') {
        setTheme('light');
    } else {
        setTheme('dark');
    }
}

function updateThemeIcon(themeName) {
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        if (themeName === 'dark') {
            themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
            themeToggle.title = 'Переключить на светлую тему';
        } else {
            themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
            themeToggle.title = 'Переключить на темную тему';
        }
    }
}

// Загрузить сохраненную тему при загрузке страницы
function loadSavedTheme() {
    const savedTheme = localStorage.getItem('theme');
    
    // Если тема не сохранена, определяем системную тему
    if (savedTheme) {
        setTheme(savedTheme);
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        setTheme('dark');
    } else {
        setTheme('light');
    }
}

// Проверить системную тему при изменении
if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', event => {
        if (!localStorage.getItem('theme')) {
            setTheme(event.matches ? 'dark' : 'light');
        }
    });
}
