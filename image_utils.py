from PIL import Image
import os

def compress_image(input_path, output_path, quality=85, max_size=(1920, 1080)):
    """
    Сжимает изображение с заданным качеством и максимальным размером
    
    :param input_path: путь к исходному изображению
    :param output_path: путь для сохранения сжатого изображения
    :param quality: качество JPEG (1-100, где 100 - лучшее качество)
    :param max_size: максимальный размер изображения (ширина, высота)
    """
    with Image.open(input_path) as img:
        # Сохраняем оригинальный формат
        img_format = img.format
        
        # Преобразуем RGBA в RGB для JPEG, чтобы избежать ошибок
        if img_format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
            # Создаем изображение с белым фоном
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            
            if img.mode == 'RGBA':
                rgb_img.paste(img, mask=img.split()[-1])
            else:
                rgb_img.paste(img)
            img = rgb_img
        elif img.mode == 'P' and img_format != 'GIF':  # Для других форматов кроме GIF конвертируем из P
            img = img.convert('RGB')
        
        # Изменяем размер, если изображение больше максимального
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Определяем параметры сохранения
        save_kwargs = {
            'format': img_format,
            'optimize': True
        }
        
        if img_format == 'JPEG':
            save_kwargs['quality'] = quality
        elif img_format == 'PNG':
            # Для PNG используем уровень сжатия вместо качества
            save_kwargs['compress_level'] = int((100 - quality) / 10 * 9) if quality < 100 else 9
        elif img_format == 'GIF':
            # GIF не поддерживает качество, но мы можем оптимизировать
            pass
            
        # Сохраняем изображение
        img.save(output_path, **save_kwargs)

def process_uploaded_image(file_path, output_path=None, quality=85, max_size=(1920, 1080)):
    """
    Обрабатывает загруженное изображение: сжимает и сохраняет
    
    :param file_path: путь к загруженному файлу
    :param output_path: путь для сохранения (если None, перезаписывает исходный файл)
    :param quality: качество сжатия
    :param max_size: максимальный размер
    :return: путь к обработанному файлу
    """
    if output_path is None:
        output_path = file_path
    
    compress_image(file_path, output_path, quality, max_size)
    return output_path
