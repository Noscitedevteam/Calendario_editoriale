# Noscite Calendar

**Tool SaaS per la generazione automatica di piani editoriali destinato alle PMI**

---

## Panoramica

Noscite Calendar è una piattaforma web che consente alle Piccole e Medie Imprese di creare automaticamente piani editoriali per i social media, sfruttando l'intelligenza artificiale per generare contenuti personalizzati e ottimizzati.

Il sistema analizza il brand, genera buyer personas specifiche, e produce calendari editoriali completi per LinkedIn, Instagram e Facebook, con post pronti per la pubblicazione.

---

## Architettura

### Stack Tecnologico

| Layer | Tecnologia |
|-------|------------|
| **Frontend** | React + Vite, Tailwind CSS, Zustand (state management) |
| **Backend** | FastAPI (Python), SQLAlchemy ORM |
| **Database** | PostgreSQL |
| **AI Services** | Anthropic Claude (generazione contenuti), Perplexity (trend e analisi URL), OpenAI (generazione immagini) |
| **Queue** | Redis + Celery (task asincroni) |
| **Deploy** | VPS Linux privato |

### Struttura Progetto

```
/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # Endpoint REST
│   │   │   ├── auth.py          # Autenticazione JWT
│   │   │   ├── brands.py        # CRUD brand
│   │   │   ├── projects.py      # CRUD progetti/calendari
│   │   │   ├── posts.py         # Gestione post
│   │   │   └── generation.py    # Endpoints generazione AI
│   │   ├── models/              # Modelli SQLAlchemy
│   │   │   ├── user.py          # User, Organization
│   │   │   ├── brand.py         # Brand, BrandDocument
│   │   │   ├── project.py       # Project (calendario)
│   │   │   └── post.py          # Post singoli
│   │   ├── services/            # Logica business
│   │   │   ├── claude_service.py      # Integrazione Claude AI
│   │   │   ├── perplexity_service.py  # Analisi trend/URL
│   │   │   ├── openai_service.py      # Generazione immagini
│   │   │   ├── persona_analyzer.py    # Analisi buyer personas
│   │   │   ├── url_analyzer.py        # Estrazione contesto da URL
│   │   │   └── calendar_generator.py  # Orchestrazione generazione
│   │   └── core/
│   │       ├── config.py        # Configurazione env
│   │       ├── database.py      # Connessione DB
│   │       └── security.py      # Auth/JWT utilities
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── pages/               # Pagine React
│   │   │   ├── Dashboard.jsx    # Home con lista brand
│   │   │   ├── BrandDetail.jsx  # Dettaglio brand + progetti
│   │   │   ├── ProjectWizard.jsx # Wizard creazione calendario
│   │   │   └── ProjectDetail.jsx # Calendario + editor post
│   │   ├── components/          # Componenti riutilizzabili
│   │   │   ├── PostEditModal.jsx
│   │   │   ├── BuyerPersonasStep.jsx
│   │   │   └── GenerationProgress.jsx
│   │   ├── services/api.js      # Client API Axios
│   │   └── store/               # Zustand stores
│   │       ├── authStore.js
│   │       └── dataStore.js
│   └── package.json
```

---

## Funzionalità Principali

### 1. Gestione Multi-Brand

Ogni organizzazione può gestire più brand, ciascuno con:

- Nome e settore di appartenenza
- Tone of voice (formale, informale, tecnico, amichevole)
- Valori del brand
- Style guide personalizzata
- Documenti di riferimento caricati

### 2. Wizard di Creazione Calendario

Processo guidato in 6 step:

1. **Brief** - Nome progetto, obiettivi, target audience
2. **Piattaforme** - Selezione canali (LinkedIn, Instagram, Facebook) e frequenza post
3. **Content Pillars** - Temi/argomenti da trattare (suggerimenti AI-based)
4. **Riferimenti** - URL da analizzare, competitor da monitorare
5. **Buyer Personas** - Generazione automatica AI con possibilità di rigenerazione con feedback
6. **Conferma** - Riepilogo e avvio generazione

### 3. Generazione AI-Powered

Il sistema utilizza Claude AI per:

- **Analisi buyer personas** basate su brief, settore, e URL di riferimento
- **Scheduling ottimizzato** per piattaforma (giorni e orari migliori)
- **Generazione post completi** con: contenuto, hashtag, content type, visual suggestion, CTA
- **Rigenerazione singolo post** su richiesta utente con prompt personalizzato
- **Generazione batch** per campagne specifiche

### 4. Calendario Interattivo

Visualizzazione mensile dei post programmati con:

- Filtri per piattaforma
- Selezione multipla per operazioni batch
- Drag & drop (futuro)
- Editing inline
- Preview post per piattaforma

### 5. Analisi Contesto Esterno

Tramite Perplexity AI:

- **Trend di settore** in tempo reale
- **Analisi URL** di riferimento per estrarre tone of voice e messaggi chiave
- **Analisi competitor** per benchmark contenuti

---

## Modelli Dati

### Organization
Entità principale che raggruppa utenti e brand.

### User
Utenti con autenticazione JWT, associati a un'organizzazione.

### Brand
Rappresenta un brand aziendale con le sue caratteristiche distintive.

### Project (Calendario)
Un piano editoriale con periodo, piattaforme, frequenza, buyer personas generate.

**Campi principali:**
- `start_date`, `end_date` - Periodo del piano
- `platforms` - Lista piattaforme attive
- `posts_per_week` - Frequenza per piattaforma
- `content_pillars` - Temi da trattare
- `buyer_personas` - Personas generate da AI (JSON)
- `status` - draft, generating, review, approved, published

### Post
Singolo contenuto programmato.

**Campi principali:**
- `platform` - linkedin, instagram, facebook
- `scheduled_date`, `scheduled_time` - Programmazione
- `content` - Testo del post
- `hashtags` - Lista hashtag
- `pillar` - Tema/argomento
- `post_type` - educational, inspirational, promotional, engagement
- `visual_suggestion` - Suggerimento per visual
- `cta` - Call to action
- `status` - draft, scheduled, published

---

## API Endpoints Principali

### Autenticazione
- `POST /api/auth/login` - Login
- `POST /api/auth/register` - Registrazione
- `GET /api/auth/me` - Profilo utente

### Brand
- `GET/POST /api/brands/` - Lista/Crea
- `GET/PUT/DELETE /api/brands/{id}` - Singolo brand

### Progetti
- `GET/POST /api/projects/` - Lista/Crea
- `GET/PUT/DELETE /api/projects/{id}` - Singolo progetto

### Post
- `GET /api/posts/project/{id}` - Lista post per progetto
- `PATCH /api/posts/{id}` - Aggiorna post
- `POST /api/posts/manual` - Crea post manuale
- `POST /api/posts/generate-ai` - Genera post AI per campagna
- `POST /api/posts/batch-delete` - Elimina multipli
- `POST /api/posts/batch-replace` - Rigenera multipli

### Generazione AI
- `POST /api/generate/personas/{id}` - Genera buyer personas
- `POST /api/generate/personas/{id}/regenerate` - Rigenera con feedback
- `POST /api/generate/calendar/{id}` - Avvia generazione calendario
- `GET /api/generate/status/{id}` - Stato generazione (polling)
- `POST /api/generate/regenerate-post/{id}` - Rigenera singolo post
- `POST /api/generate/image-prompt/{id}` - Genera prompt per immagine

---

## Roadmap

### Fase 1 - Attuale ✅
Creazione automatica piani editoriali:
- Wizard guidato
- Generazione AI buyer personas
- Calendario con post completi
- Editing e rigenerazione post

### Fase 2 - Pianificata
Pubblicazione automatica e integrazioni:
- Integrazione API social (LinkedIn, Instagram, Facebook)
- Pubblicazione automatica programmata
- Integrazione CRM (HubSpot, Salesforce)
- Tracking engagement
- Profilazione utente avanzata
- Analytics e reporting

---

## Configurazione

### Variabili d'Ambiente (.env)

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/noscite

# Security
SECRET_KEY=your-secret-key
ALGORITHM=HS256

# AI APIs
ANTHROPIC_API_KEY=sk-ant-...
PERPLEXITY_API_KEY=pplx-...
OPENAI_API_KEY=sk-...

# App
DEBUG=True
CORS_ORIGINS=http://localhost:3000
```

### Installazione

```bash
# Backend
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

---

## Note Tecniche

- **Generazione in background**: I calendari vengono generati in thread separati per non bloccare le request
- **Batching intelligente**: I post vengono generati in batch per gestire periodi lunghi
- **Polling status**: Il frontend fa polling dell'endpoint status per mostrare il progresso
- **JWT Auth**: Token con scadenza 24h, refresh automatico
- **Multi-tenancy**: Isolamento dati per organizzazione

---

## Licenza

Proprietario - Tutti i diritti riservati
