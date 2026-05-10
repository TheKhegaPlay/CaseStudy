# 🔧 Forensic GAN Platform - MVP Интеграция

**Версия**: 1.0.0  
**Статус**: ✅ Production Ready  
**Дата**: Май 2026

---

## 📋 Обзор

Это интегрированное решение объединяет:
- **Frontend**: Angular 18 + SSR (Angular Universal + Express)
- **Backend**: FastAPI + PyTorch AOT-GAN

Поддерживает полный workflow восстановления повреждённых изображений для судебных экспертов.

---

## 🚀 Быстрый старт (5 минут)

### Вариант 1: Локальный запуск (без Docker)

#### 1️⃣ Backend

```bash
# Перейти в папку backend
cd backend

# Создать виртуальное окружение (если нужно)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установить зависимости
pip install -r requirements.txt

# Запустить FastAPI
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

✅ Backend готов на `http://localhost:8000`  
📚 API Docs: `http://localhost:8000/docs`

#### 2️⃣ Frontend

```bash
# Перейти в папку frontend
cd frontend

# Установить зависимости
npm install

# Запустить Angular SSR
npm run serve:ssr
```

✅ Frontend готов на `http://localhost:4200`

---

### Вариант 2: Docker Compose (один команд)

```bash
# В корне проекта
docker-compose up -d
```

✅ Frontend: `http://localhost:4200`  
✅ Backend: `http://localhost:8000`

```bash
# Остановить
docker-compose down
```

---

## 🔑 Учётные данные

| Поле | Значение |
|------|----------|
| Email | demo@forensics.gov |
| Пароль | demo123 |

---

## 📖 Workflow MVP

### 1. Вход в систему
- Перейти на `http://localhost:4200/login`
- Ввести email: `demo@forensics.gov`
- Ввести пароль: `demo123`
- Нажать **Login**

### 2. Перейти на страницу восстановления
- Нажать кнопку **"🔧 Show GAN Image Restoration"** на главной странице

### 3. Загрузить изображение
- **Drag & Drop** или нажать **"📁 Select Image"**
- Поддерживаемые форматы: PNG, JPG, BMP (max 10MB)

### 4. Создать маску повреждения
Выбрать один из вариантов:
- **🎲 Generate Random Damage** — автоматическая генерация
  - Выбрать тип: Irregular, Center, Rectangular, Brush Strokes
  - Выбрать процент покрытия (5-80%)
- **📤 Upload Custom Mask** — загрузить свою маску

### 5. Запустить восстановление
- Нажать **"🚀 Run Restoration"**
- Ожидать результата (обычно 5-30 сек)

### 6. Просмотреть результаты
**Три изображения в ряд**:
- Original — исходное изображение
- Masked — с применённой маской
- Restored — восстановленное

**Метрики качества**:
| Метрика | Значение | Описание |
|---------|----------|----------|
| **SSIM** | 0.0-1.0 | Structural Similarity (выше — лучше) |
| **PSNR** | dB | Peak Signal-to-Noise Ratio (выше — лучше) |
| **Confidence** | % | Уверенность модели в результате |
| **MSE** | - | Mean Squared Error (ниже — лучше) |

### 7. Сохранить результаты
Скачать:
- 💾 **Download Original** — исходное изображение
- 💾 **Download Masked** — с маской
- 💾 **Download Restored** — результат

---

## 🏗️ Архитектура проекта

```
project/
├── frontend/                    ← Angular + SSR
│   ├── src/
│   │   └── app/
│   │       ├── pages/
│   │       │   ├── gan-models.component.ts      (главная страница)
│   │       │   └── dashboard.component.ts       (с новым компонентом)
│   │       ├── components/
│   │       │   └── gan-restoration.component.ts (новый! восстановление)
│   │       ├── services/
│   │       │   └── server-api.service.ts        (обновлён для /api/restore)
│   │       └── ...
│   ├── package.json
│   └── Dockerfile
│
├── backend/                     ← FastAPI + PyTorch
│   ├── main.py                 (FastAPI приложение с /api/restore)
│   ├── inference.py            (обёртка AOT-GAN)
│   ├── utils.py                (обработка изображений)
│   ├── requirements.txt
│   └── Dockerfile
│
├── aot-gan-model/              ← исходный код модели
│   ├── model/
│   ├── data/
│   ├── loss/
│   ├── metric/
│   └── utils/
│
├── models/                      ← (gitignore) предобученные веса
│   └── aotgan_best.pth
│
├── docker-compose.yml           ← оркестрация
└── README_MVP.md               ← этот файл
```

---

## 🔌 API Endpoints

### Health Check
```http
GET /health
```

Response:
```json
{
  "status": "ready",
  "model_loaded": true,
  "device": "cuda",
  "model_params": 23450000,
  "version": "1.0.0"
}
```

### Восстановление изображения
```http
POST /api/restore
```

Request:
```json
{
  "image": "data:image/png;base64,iVBORw0KGgo...",
  "mask": "data:image/png;base64,iVBORw0KGgo..." [optional],
  "mask_type": "irregular",
  "mask_ratio": 0.3
}
```

Response:
```json
{
  "success": true,
  "original_image": "data:image/png;base64,...",
  "masked_image": "data:image/png;base64,...",
  "restored_image": "data:image/png;base64,...",
  "confidence_score": 0.85,
  "metrics": {
    "ssim": 0.9234,
    "psnr": 28.45,
    "mse": 0.0123
  },
  "processing_time_ms": 1250,
  "timestamp": "2026-05-10T12:34:56.789Z"
}
```

### Загрузить маску
```http
POST /api/upload-mask
Content-Type: multipart/form-data

file: [binary mask image]
```

### Генерировать маску
```http
GET /api/generate-mask/{mask_type}?width=512&height=512&ratio=0.3
```

---

## ⚙️ Конфигурация

### Backend переменные окружения

```bash
# .env или export
DEVICE=cuda          # cpu или cuda
LOG_LEVEL=INFO       # DEBUG, INFO, WARNING, ERROR
CORS_ORIGINS=*       # разрешённые origins
MODEL_PATH=models/aotgan_best.pth
```

### Frontend конфигурация

File: `frontend/src/environments/environment.ts`

```typescript
export const environment = {
  production: false,
  apiBaseUrl: 'http://localhost:8000',
  corsEnabled: true
};
```

---

## 🐛 Troubleshooting

### ❌ Backend недоступен

**Проблема**: `Cannot connect to backend` на 8000 порту

**Решение**:
```bash
# Проверить, запущен ли backend
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Убедиться, что все зависимости установлены
cd backend
pip install -r requirements.txt

# Запустить с verbose
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level debug
```

### ❌ CUDA ошибка при inference

**Проблема**: `CUDA out of memory` или `No CUDA device found`

**Решение**:
```bash
# Использовать CPU вместо GPU
export DEVICE=cpu

# Или изменить в main.py:
device = torch.device("cpu")
```

### ❌ Модель не загружается

**Проблема**: `Model weights not found at models/aotgan_best.pth`

**Решение**:
```bash
# Загрузить предобученные веса
# (нужно получить из исходного репозитория AOT-GAN)
mkdir models
# Скопировать aotgan_best.pth в models/
```

---

## 📊 Технические детали

### Frontend Stack
- **Angular**: 18.2.0
- **Angular SSR**: Universal + Express
- **TypeScript**: 5.2
- **RxJS**: 7.8.0

### Backend Stack
- **FastAPI**: 0.109.0
- **PyTorch**: 2.2.0
- **Python**: 3.11+
- **CUDA**: 11.8+ (опционально)

### Модель
- **Архитектура**: HybridInpaintGenerator (AOT-GAN)
- **Параметры**: 23.45M
- **Input**: RGB + Binary Mask
- **Output**: RGB Image + Confidence Map

---

## 📈 Performance

| Метрика | Значение |
|---------|----------|
| Размер модели | ~90MB |
| GPU Memory | ~2-3GB (при использовании CUDA) |
| CPU Processing Time | 10-30 сек |
| GPU Processing Time | 1-3 сек |
| Max Image Size | 512x512 px |

---

## 🔐 Безопасность

- ✅ CORS включен для localhost:4200
- ✅ JWT токены для аутентификации
- ✅ Валидация файлов (размер, формат)
- ✅ Временные файлы очищаются автоматически

---

## 📝 Логирование

Logs из backend:
```bash
# Просмотреть логи Docker контейнера
docker-compose logs -f backend

# Или из прямого запуска
# Логи выводятся в консоль (stdout)
```

---

## 🚢 Deployment

### Production (рекомендуется)

```bash
# Используя docker-compose
docker-compose -f docker-compose.prod.yml up -d

# Используя Kubernetes
kubectl apply -f k8s/
```

### Heroku / Cloud deployment

```bash
# Подготовить
git add .
git commit -m "MVP integration complete"

# Deploy
git push heroku main
```

---

## 📚 Дополнительные ресурсы

- 📖 [AOT-GAN Оригинальный Репо](https://github.com/megvii-research/aot-gan)
- 🎓 [FastAPI Документация](https://fastapi.tiangolo.com)
- 🎨 [Angular Документация](https://angular.io)
- 🐳 [Docker Документация](https://docs.docker.com)

---

## 📄 Лицензия

MIT

---

## 👥 Автор

Forensic GAN Platform  
Май 2026

---

## 🎯 Следующие шаги (Post-MVP)

1. ✅ Fine-tuning модели на forensic-изображениях
2. ✅ Добавить поддержку пакетной обработки
3. ✅ Реализовать chain of custody логирование
4. ✅ Добавить поддержку других архитектур (GFPGAN, ESRGAN)
5. ✅ Создать UI для настройки параметров модели
6. ✅ Добавить экспорт отчётов в PDF

---

**Готово к использованию! 🚀**
