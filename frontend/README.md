# mangalytics frontend

next.js frontend for mangalytics subscription page

## features

- beautiful subscription form with email and topic selection
- corgi mascot as friendly guide
- supabase integration for user management
- responsive design with tailwind css
- typescript for type safety

## setup

### 1. install dependencies

```bash
npm install
```

### 2. configure environment variables

create `.env.local` file:

```bash
cp .env.local.example .env.local
```

add your supabase credentials:

```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### 3. setup supabase database

run the subscriptions table migration in supabase sql editor:

```sql
CREATE TABLE IF NOT EXISTS subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT NOT NULL,
  topic TEXT NOT NULL,
  subscribed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  active BOOLEAN NOT NULL DEFAULT true,
  UNIQUE(email, topic)
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_email ON subscriptions (email);
CREATE INDEX IF NOT EXISTS idx_subscriptions_topic ON subscriptions (topic);
CREATE INDEX IF NOT EXISTS idx_subscriptions_active ON subscriptions (active);
```

### 4. run development server

```bash
npm run dev
```

open [http://localhost:3000](http://localhost:3000)

## project structure

```
frontend/
├── app/
│   ├── api/
│   │   └── subscribe/
│   │       └── route.ts          # subscription api endpoint
│   ├── globals.css               # global styles
│   ├── layout.tsx                # root layout
│   └── page.tsx                  # main subscription page
├── public/
│   ├── corgis.png               # corgi mascot
│   └── logo.png                 # mangalytics logo
├── .env.local                   # environment variables
├── package.json                 # dependencies
├── tailwind.config.ts           # tailwind configuration
└── tsconfig.json                # typescript configuration
```

## how it works

1. **user visits page**
   - sees logo, corgi mascot, and subscription form
   - enters email and selects research topic

2. **form submission**
   - data sent to `/api/subscribe` endpoint
   - validates email format
   - checks for duplicate subscriptions

3. **supabase storage**
   - creates new row in `subscriptions` table
   - stores: email, topic, timestamp, active status

4. **success feedback**
   - shows success message
   - clears form for new submission

## api endpoint

### POST /api/subscribe

**request body:**
```json
{
  "email": "user@example.com",
  "topic": "LLMs"
}
```

**success response (201):**
```json
{
  "success": true,
  "message": "subscription created successfully",
  "subscription": {
    "id": "uuid",
    "email": "user@example.com",
    "topic": "LLMs",
    "subscribed_at": "2026-01-31T14:30:00Z",
    "active": true
  }
}
```

**error responses:**

400 - missing fields:
```json
{
  "error": "email and topic are required"
}
```

400 - invalid email:
```json
{
  "error": "invalid email format"
}
```

409 - duplicate subscription:
```json
{
  "error": "email already subscribed to this topic"
}
```

## available topics

- artificial intelligence
- machine learning
- computer vision
- natural language processing
- robotics
- llms
- deep learning
- neural networks
- quantum computing
- cryptography
- computational biology
- astrophysics
- condensed matter
- high energy physics
- mathematics
- statistics
- data science

## building for production

```bash
npm run build
npm start
```

## deployment

### vercel (recommended)

1. push code to github
2. import project in vercel
3. add environment variables
4. deploy

### docker

```bash
docker build -t mangalytics-frontend .
docker run -p 3000:3000 mangalytics-frontend
```

## tech stack

- **next.js 15** - react framework
- **typescript** - type safety
- **tailwind css** - styling
- **supabase** - database and auth
- **vercel** - deployment (optional)

## customization

### change colors

edit `app/page.tsx` and tailwind classes:

```tsx
// button gradient
className="bg-gradient-to-r from-yellow-600 to-yellow-700"

// change to blue:
className="bg-gradient-to-r from-blue-600 to-blue-700"
```

### add topics

edit `ARXIV_TOPICS` array in `app/page.tsx`:

```typescript
const ARXIV_TOPICS = [
  'Your Custom Topic',
  // ... other topics
];
```

### modify layout

edit `app/page.tsx` to change structure, spacing, or add new sections

## troubleshooting

### "supabase client error"
- check `.env.local` has correct credentials
- verify supabase url and service role key

### "table does not exist"
- run migration sql in supabase dashboard
- check table name is `subscriptions`

### "image not loading"
- verify `corgis.png` and `logo.png` in `public/` folder
- check image paths in code

### "tailwind styles not working"
- restart dev server: `npm run dev`
- check `tailwind.config.ts` content paths

## integration with backend

the frontend works independently but can integrate with the mangalytics backend api:

1. **fetch subscriptions** - query supabase for users by topic
2. **trigger manga generation** - call backend `/manga` endpoint
3. **manage subscriptions** - update active status, unsubscribe

example backend integration:

```typescript
// get all active subscribers for a topic
const { data } = await supabase
  .from('subscriptions')
  .select('*')
  .eq('topic', 'LLMs')
  .eq('active', true);

// for each subscriber, generate and send manga
for (const sub of data) {
  await fetch('http://localhost:8000/manga', {
    method: 'POST',
    body: JSON.stringify({
      email: sub.email,
      topic: sub.topic,
      date: '01_31_2026'
    })
  });
}
```

## support

for issues or questions:
- check main project readme
- review supabase documentation
- verify environment variables

## license

same as main mangalytics project
