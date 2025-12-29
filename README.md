# Noscite Calendar - AI Editorial Calendar SaaS

Sistema SaaS per la generazione automatica di piani editoriali tramite AI.

## 🚀 Funzionalità

### Fase 1 (Attuale)
- ✅ Multi-tenant con organizzazioni
- ✅ Gestione Brand con brief, valori, tone of voice
- ✅ Analisi automatica siti web (scraping)
- ✅ Generazione Buyer Personas con AI
- ✅ Scheduling ottimizzato per piattaforma
- ✅ Frequenza post suggerita dall'AI
- ✅ Generazione contenuti multi-piattaforma (LinkedIn, Instagram, Facebook, Google Business)
- ✅ Calendario interattivo con drag & drop
- ✅ Export Excel con formattazione
- ✅ Sistema ruoli (Superuser, Admin, Editor, Viewer)
- ✅ Admin Dashboard con activity log
- ✅ Profilo utente con dati estesi

### Fase 2 (Roadmap)
- 🔄 Pubblicazione automatica via API social
- 🔄 Integrazione CRM
- 🔄 Analytics e reportistica
- 🔄 A/B testing contenuti

## 🏗️ Architettura

\`\`\`
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   Backend       │────▶│   Database      │
│   React + Vite  │     │   FastAPI       │     │   PostgreSQL    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   AI Services   │
                        │ Claude/Perplexity│
                        └─────────────────┘
\`\`\`

## 🔐 Sistema Ruoli

| Ruolo | Descrizione | Permessi |
|-------|-------------|----------|
| **Superuser** | Admin piattaforma | Vede tutto, gestisce tutte le org |
| **Admin** | Admin organizzazione | Gestisce utenti e contenuti della sua org |
| **Editor** | Creatore contenuti | Crea e modifica brand, progetti, post |
| **Viewer** | Solo lettura | Visualizza contenuti |

## 🔄 Workflow Creazione Calendario

1. **Brief** → Informazioni brand e obiettivi
2. **Piattaforme** → Selezione canali e frequenza (suggerita da AI)
3. **Contenuti** → Pillar e tipologie di contenuto
4. **Riferimenti** → URL e competitor da analizzare
5. **Target** → Generazione Buyer Personas con AI
6. **Genera** → Creazione automatica piano editoriale

## 🛠️ Stack Tecnologico

- **Frontend**: React 18, Vite, TailwindCSS, Lucide Icons
- **Backend**: Python 3.11, FastAPI, SQLAlchemy, Pydantic
- **Database**: PostgreSQL 16
- **AI**: Claude (Anthropic), Perplexity API
- **Export**: OpenPyXL (Excel)
- **Server**: Ubuntu 24, Nginx, Uvicorn, Let's Encrypt

## 📊 API Endpoints Principali

| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| POST | /api/auth/login | Login utente |
| GET | /api/auth/me | Profilo utente |
| PUT | /api/auth/profile | Aggiorna profilo |
| GET | /api/brands | Lista brand |
| GET | /api/projects | Lista progetti |
| POST | /api/generate/calendar/{id} | Genera calendario AI |
| GET | /api/export/excel/{id} | Export Excel |
| GET | /api/admin/users | Lista utenti (admin) |
| GET | /api/admin/activity | Activity log |

## 📝 URL Produzione

- **App**: https://calendar.noscite.it
- **API**: https://calendar.noscite.it/api

---

© 2024 Noscite - AI Editorial Calendar
