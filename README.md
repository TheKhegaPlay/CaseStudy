# ForensicRestore — Intelligent Forensic Platform

**MVP of an Intelligent Forensic Platform based on GAN models for the restoration of damaged digital evidence**

Web-приложение, позволяющее судебным экспертам загружать повреждённые изображения, применять маски повреждений и восстанавливать их с помощью предобученной модели **AOT-GAN**.

---

## 🎯 Project Overview

**ForensicRestore** — это минимально жизнеспособный продукт (MVP), разработанный в рамках магистерской диссертации и курса *Software Development Case Studies* (Astana IT University).

**Цель MVP**: проверить гипотезу о применимости GAN-моделей (конкретно AOT-GAN) для восстановления повреждённых цифровых доказательств в криминалистике.

### Основной функционал
- Аутентификация судебного эксперта
- Загрузка повреждённого изображения (drag & drop)
- Генерация синтетического повреждения (random mask)
- Восстановление изображения с помощью AOT-GAN
- Side-by-side сравнение: Original | Masked | Restored
- Отображение метрик качества (SSIM, PSNR, Confidence Score)
- Принятие/отклонение результата экспертом

---

## 🛠 Tech Stack

### Frontend
- Angular 18 + Angular Universal (SSR)
- TypeScript, RxJS, Angular Material
- Tailwind CSS (forensic-themed UI)

### Backend
- FastAPI (Python)
- PyTorch + AOT-GAN (pre-trained model)
- Pillow + OpenCV (image processing)

### Other
- JWT Authentication
- SQLite (metadata)
- CORS enabled

---

## 📋 Prerequisites

- Node.js 20+
- Python 3.10+
- Git
- (Опционально) CUDA 11.8+ и GPU для ускорения инференса

---

## 🚀 Installation & Setup

### 1. Клонирование репозитория

```bash
git clone https://github.com/TheKhegaPlay/GAN-main.git ForensicRestore
cd ForensicRestore