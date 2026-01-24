// Галерея медиафайлов
let mediaGallery = [];
let currentMediaIndex = 0;
let scale = 1;
let isDragging = false;
let startX, startY, translateX = 0, translateY = 0;

function openMediaGallery(medias, startIndex = 0) {
    mediaGallery = medias;
    currentMediaIndex = startIndex;
    showCurrentMedia();
    document.getElementById('media-gallery').style.display = 'flex';
}

function showCurrentMedia() {
    const mediaContainer = document.getElementById('media-container');
    const currentMedia = mediaGallery[currentMediaIndex];
    
    // Очистка контейнера
    mediaContainer.innerHTML = '';
    
    // Проверяем тип медиафайла
    const ext = currentMedia.split('.').pop().toLowerCase();
    const isImage = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'].includes(ext);
    const isVideo = ['mp4', 'webm', 'ogg', 'mov'].includes(ext);
    
    if (isImage) {
        const img = document.createElement('img');
        img.src = '/uploads/' + currentMedia;
        img.className = 'gallery-media-item';
        img.alt = 'Media item';
        img.onload = function() {
            img.style.cursor = 'grab';
            img.addEventListener('mousedown', startDrag);
            img.addEventListener('mousemove', drag);
            img.addEventListener('mouseup', endDrag);
            img.addEventListener('mouseleave', endDrag);
            
            // Обработка двойного клика для увеличения
            img.addEventListener('dblclick', function() {
                if (scale === 1) {
                    zoomIn();
                } else {
                    resetZoom();
                }
            });
        };
        mediaContainer.appendChild(img);
    } else if (isVideo) {
        const video = document.createElement('video');
        video.src = '/uploads/' + currentMedia;
        video.controls = true;
        video.autoplay = true;
        video.className = 'gallery-media-item video';
        mediaContainer.appendChild(video);
    } else {
        // Для неподдерживаемых форматов показываем ссылку на скачивание
        const div = document.createElement('div');
        div.className = 'unsupported-media';
        div.innerHTML = '<p>Неподдерживаемый формат файла</p><a href="/uploads/' + currentMedia + '" download>Скачать файл</a>';
        mediaContainer.appendChild(div);
    }
    
    // Обновляем индикатор текущего элемента
    document.getElementById('media-counter').textContent = `${currentMediaIndex + 1} / ${mediaGallery.length}`;
    
    // Обновляем видимость кнопок навигации
    document.getElementById('prev-media-btn').style.display = currentMediaIndex > 0 ? 'block' : 'none';
    document.getElementById('next-media-btn').style.display = currentMediaIndex < mediaGallery.length - 1 ? 'block' : 'none';
}

function nextMedia() {
    if (currentMediaIndex < mediaGallery.length - 1) {
        currentMediaIndex++;
        showCurrentMedia();
    }
}

function prevMedia() {
    if (currentMediaIndex > 0) {
        currentMediaIndex--;
        showCurrentMedia();
    }
}

function closeMediaGallery() {
    document.getElementById('media-gallery').style.display = 'none';
    mediaGallery = [];
    currentMediaIndex = 0;
    scale = 1;
    translateX = 0;
    translateY = 0;
}

// Функции масштабирования
function zoomIn() {
    if (scale < 3) {
        scale += 0.25;
        applyTransform();
    }
}

function zoomOut() {
    if (scale > 0.25) {
        scale -= 0.25;
        applyTransform();
    }
}

function resetZoom() {
    scale = 1;
    translateX = 0;
    translateY = 0;
    applyTransform();
}

function applyTransform() {
    const mediaItem = document.querySelector('.gallery-media-item');
    if (mediaItem) {
        mediaItem.style.transform = `scale(${scale}) translate(${translateX}px, ${translateY}px)`;
    }
}

// Обработчики событий для перетаскивания
function startDrag(e) {
    if (scale <= 1) return; // Разрешаем перетаскивание только при увеличенном масштабе
    
    isDragging = true;
    startX = e.clientX - translateX;
    startY = e.clientY - translateY;
    e.target.style.cursor = 'grabbing';
}

function drag(e) {
    if (!isDragging) return;
    
    translateX = e.clientX - startX;
    translateY = e.clientY - startY;
    applyTransform();
}

function endDrag(e) {
    isDragging = false;
    e.target.style.cursor = 'grab';
}

// Закрытие галереи при нажатии на клавишу Escape
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && document.getElementById('media-gallery').style.display === 'flex') {
        closeMediaGallery();
    }
});

// Закрытие галереи при клике на фон
document.getElementById('media-gallery').addEventListener('click', function(e) {
    if (e.target === this) {
        closeMediaGallery();
    }
});