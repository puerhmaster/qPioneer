# qPioneer

[![CI](https://github.com/puerhmaster/qPioneer/actions/workflows/ci.yml/badge.svg)](https://github.com/puerhmaster/qPioneer/actions)
[![Streamlit](https://static.streamlit.io/badges/qPioneer-deployed.svg)](https://share.streamlit.io/puerhmaster/qPioneer/main/qpcr_analyse_app.py)

**qPioneer** — полнофункциональное Streamlit-приложение для анализа qPCR-данных на 96/384-луночных планшетках.  
Включает:  
- Загрузку и быструю разметку данных (гены, шаблоны, репликаты).  
- QC-анализ (обнаружение выбросов по σ).  
- Нормализацию ΔCt и вычисление относительной экспрессии.  
- Статистический анализ (парные t-тесты с коррекцией Бонферрони).  
- Интерактивные boxplot и barplot с аннотациями значимости.  
- Генерацию полного отчёта в HTML и PDF.  

---

## 📥 Установка

1. **Клонируйте репозиторий**  
   ```bash
   git clone https://github.com/puerhmaster/qPioneer.git
   cd qPioneer