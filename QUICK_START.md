# ⚡ Quick Start - 5 Минут до Работающей Системы

## 🎯 Цель
Получить работающую Forensic GAN Platform на локальной машине за 5 минут.

---

## 📝 Предварительные требования

```bash
# 1️⃣ Проверить Python
python --version          # Должно быть 3.9+

# 2️⃣ Проверить Node.js
node --version           # Должно быть 18+
npm --version            # Любая версия

# 3️⃣ Проверить CUDA (опционально, для GPU)
nvidia-smi               # Если есть NVIDIA GPU
```

Если что-то не установлено:
- **Python**: https://python.org
- **Node.js**: https://nodejs.org

---

## 🚀 Запуск в 3 шага

### Шаг 1️⃣ - Настройка Backend (90 сек)

```bash
# Перейти в папку backend
cd backend

# Создать виртуальное окружение (первый раз)
python -m venv venv

# Активировать
source venv/bin/activate                    # Linux/Mac
# ИЛИ
venv\Scripts\activate                       # Windows

# Установить зависимости
pip install -r requirements.txt

# ✅ Готово! Остаться в этой консоли для шага 3
```

### Шаг 2️⃣ - Настройка Frontend (120 сек, в новой консоли)

```bash
# Перейти в папку frontend
cd frontend

# Установить зависимости
npm install

# ✅ Готово!
```

### Шаг 3️⃣ - Запустить оба сервиса

**Консоль 1 (Backend):**
```bash
# Убедиться, что находитесь в backend/ с активированным venv
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Ожидать:
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Консоль 2 (Frontend):**
```bash
# Убедиться, что находитесь в frontend/
npm run serve:ssr

# Ожидать:
# ✔ Server running on http://localhost:4200
```

---

## 🌐 Открыть в браузере

### 1. Перейти на главную страницу
```
http://localhost:4200
```

### 2. Вход в систему
- **Email**: demo@forensics.gov
- **Пароль**: demo123
- Нажать **Login**

### 3. На главной странице
- Найти кнопку **"🔧 Show GAN Image Restoration"**
- Нажать её

### 4. Начать восстановление!
- Загрузить фото (drag & drop или кнопка)
- Нажать **"🎲 Generate Random Damage"**
- Нажать **"🚀 Run Restoration"**
- Просмотреть результаты! ✨

---

## ✅ Проверка работоспособности

### Backend работает?
```bash
# В браузере откройте:
http://localhost:8000/health

# Должны увидеть:
{
  "status": "ready",
  "model_loaded": true,
  "device": "cpu",
  "model_params": 23450000,
  "version": "1.0.0"
}
```

### Frontend работает?
```
http://localhost:4200 → видите login страницу ✓
```

---

## ⚙️ Автоматическая настройка (опционально)

Вместо ручных шагов, можно запустить скрипт:

**Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows:**
```batch
setup.bat
```

Скрипт:
- ✅ Проверит Python и Node.js
- ✅ Создаст виртуальное окружение
- ✅ Установит все зависимости
- ✅ Выведет инструкции запуска

---

## 🐛 Если что-то не работает

### ❌ Backend ошибка "Port 8000 already in use"

```bash
# Найти процесс на порту 8000
lsof -i :8000               # Linux/Mac
netstat -ano | findstr 8000 # Windows

# Либо использовать другой порт
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
# Затем изменить в frontend конфиге на :8001
```

### ❌ Frontend ошибка "Module not found"

```bash
# Очистить node_modules и переустановить
rm -rf node_modules package-lock.json
npm install
```

### ❌ Model файл не найден

```
⚠ Model weights not found at models/aotgan_best.pth
```

Это нормально! Модель на первый запуск использует random весы. 

Для полноценного восстановления:
1. Загрузить предобученные веса из исходного репо AOT-GAN
2. Поместить в папку `models/` с именем `aotgan_best.pth`

### ❌ Backend недоступен из Frontend

Проверить CORS:
- Backend должен быть на `localhost:8000` ✓
- Frontend должен быть на `localhost:4200` ✓
- Оба должны быть запущены ✓

---

## 📊 Ожидаемые времена обработки

| Операция | Время |
|----------|-------|
| Upload изображения | < 1 сек |
| Generate маски | 1-2 сек |
| Restoration (GPU) | 1-3 сек |
| Restoration (CPU) | 10-30 сек |
| **Итого** | **~20-40 сек (CPU)** |

---

## 🔗 Полезные ссылки

| Ссылка | Назначение |
|--------|-----------|
| http://localhost:4200 | Frontend |
| http://localhost:8000 | Backend |
| http://localhost:8000/docs | API документация (Swagger) |
| http://localhost:8000/health | Backend health check |

---

## 📚 Дальше

- 📖 Подробнее: [README_MVP.md](README_MVP.md)
- 🏗️ Архитектура: [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
- 💻 API docs: http://localhost:8000/docs (после запуска backend)

---

## 🎉 Готово!

```
✅ Frontend на http://localhost:4200
✅ Backend на http://localhost:8000
✅ Вы готовы использовать Forensic GAN Platform!
```

**Начните с** → Вход → "🔧 GAN Image Restoration" → Загрузите фото → Восстанавливайте! 

Если что-то не ясно, смотрите **README_MVP.md** или **INTEGRATION_GUIDE.md**.

Успехов! 🚀
