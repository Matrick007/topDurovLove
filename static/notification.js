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
