# CLAUDE.md — Vue.js Frontend

Guide de référence pour Claude lors du développement de ce projet Vue.js.

---

## Stack & versions

- **Framework** : Vue 3 (Composition API, `<script setup>`)
- **Build** : Vite
- **Router** : Vue Router 4
- **State** : Pinia
- **HTTP** : Axios (instance centralisée)
- **Styles** : CSS modules ou SCSS par composant (pas de Tailwind sauf si déjà présent)
- **Tests** : Vitest + Vue Test Utils
- **Lint** : ESLint + Prettier

---

## Architecture des dossiers

```
src/
├── assets/              # Fichiers statiques (images, polices, icônes)
├── components/          # Composants réutilisables et génériques
│   └── ui/              # Composants purement visuels (Button, Modal, Input…)
├── composables/         # Logique réutilisable (useAuth, useFetch, useForm…)
├── layouts/             # Gabarits de page (DefaultLayout, AuthLayout…)
├── pages/               # Vues associées aux routes (une page = une route)
├── router/
│   └── index.ts         # Définition des routes, guards de navigation
├── services/            # Appels API regroupés par domaine (userService, postService…)
│   └── http.ts          # Instance Axios configurée (baseURL, interceptors)
├── stores/              # Stores Pinia (un fichier par domaine)
├── types/               # Types et interfaces TypeScript partagés
└── utils/               # Fonctions pures utilitaires (formatDate, slugify…)
```

**Règles :**
- `pages/` ne contient que des vues de routage, la logique métier est dans des composables ou des stores.
- `components/` contient des composants sans état applicatif — ils reçoivent des props et émettent des events.
- Jamais d'appel API direct dans un composant ou une page ; tout passe par `services/`.

---

## Composants

### Convention de nommage

| Contexte | Convention | Exemple |
|---|---|---|
| Fichier composant | PascalCase | `UserCard.vue` |
| Composant générique | Préfixe `App` ou `Base` | `BaseButton.vue`, `AppModal.vue` |
| Composant de page | Suffixe `Page` ou `View` | `DashboardPage.vue` |
| Composable | Préfixe `use` | `useAuth.ts` |

### Structure d'un composant

```vue
<script setup lang="ts">
// 1. Imports
// 2. Props & emits
// 3. Stores / composables
// 4. État local (ref, reactive)
// 5. Computed
// 6. Watchers
// 7. Lifecycle hooks
// 8. Méthodes
</script>

<template>
  <!-- Un seul élément racine ou fragment -->
</template>

<style scoped>
/* Styles scopés au composant */
</style>
```

### Props

- Toujours typées avec TypeScript via `defineProps<{}>()`.
- Toujours documentées avec une valeur par défaut si optionnelle via `withDefaults`.
- Nommées en camelCase dans le script, kebab-case dans le template.

```ts
// ✅ Bien
const props = withDefaults(defineProps<{
  label: string
  disabled?: boolean
  variant?: 'primary' | 'secondary'
}>(), {
  disabled: false,
  variant: 'primary',
})

// ❌ Éviter
const props = defineProps(['label', 'disabled'])
```

### Emits

Toujours déclarés explicitement avec leurs types.

```ts
const emit = defineEmits<{
  submit: [value: string]
  close: []
}>()
```

---

## Composables

Un composable encapsule de la logique réutilisable avec état.

```ts
// composables/useCounter.ts
import { ref, computed } from 'vue'

export function useCounter(initial = 0) {
  const count = ref(initial)
  const doubled = computed(() => count.value * 2)

  function increment() {
    count.value++
  }

  return { count, doubled, increment }
}
```

**Règles :**
- Retourner des `ref` non destructurées pour que la réactivité soit préservée.
- Un composable = une responsabilité unique.
- Si un composable a besoin d'accéder à un store, l'importer en interne.

---

## Stores Pinia

Un store par domaine métier.

```ts
// stores/userStore.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { userService } from '@/services/userService'
import type { User } from '@/types/user'

export const useUserStore = defineStore('user', () => {
  // State
  const currentUser = ref<User | null>(null)
  const isLoading = ref(false)

  // Getters
  const isLoggedIn = computed(() => currentUser.value !== null)

  // Actions
  async function fetchUser(id: string) {
    isLoading.value = true
    try {
      currentUser.value = await userService.getById(id)
    } finally {
      isLoading.value = false
    }
  }

  return { currentUser, isLoading, isLoggedIn, fetchUser }
})
```

**Règles :**
- Utiliser la syntax `setup store` (function) plutôt que Options Store.
- Jamais de logique de fetch dans les composants — toujours dans les stores ou services.
- Les stores ne se connaissent pas entre eux directement ; si nécessaire, passer par un composable.

---

## Services & HTTP

### Instance Axios

```ts
// services/http.ts
import axios from 'axios'

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 10_000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

http.interceptors.response.use(
  (res) => res,
  (error) => {
    // Gestion centralisée des erreurs (401, 500…)
    return Promise.reject(error)
  }
)
```

### Service par domaine

```ts
// services/userService.ts
import { http } from './http'
import type { User } from '@/types/user'

export const userService = {
  getById: (id: string) =>
    http.get<User>(`/users/${id}`).then((r) => r.data),

  update: (id: string, payload: Partial<User>) =>
    http.patch<User>(`/users/${id}`, payload).then((r) => r.data),
}
```

---

## Router

```ts
// router/index.ts
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/userStore'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: () => import('@/layouts/DefaultLayout.vue'),
      children: [
        {
          path: '',
          name: 'Home',
          component: () => import('@/pages/HomePage.vue'),
        },
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/pages/DashboardPage.vue'),
          meta: { requiresAuth: true },
        },
      ],
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/pages/LoginPage.vue'),
    },
  ],
})

router.beforeEach((to) => {
  const userStore = useUserStore()
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    return { name: 'Login' }
  }
})

export default router
```

**Règles :**
- Toutes les pages sont chargées en lazy-loading (`() => import(...)`).
- Les guards d'authentification sont dans le router, pas dans les composants.
- Utiliser `meta` pour enrichir les routes (titre de page, permissions, breadcrumbs…).

---

## TypeScript

- Pas de `any` sauf cas exceptionnel documenté avec un commentaire `// eslint-disable-next-line`.
- Les types partagés vivent dans `src/types/`.
- Les types de réponse API sont définis dans le même fichier ou dans `types/api.ts`.
- Préférer `interface` pour les objets, `type` pour les unions et intersections.

```ts
// types/user.ts
export interface User {
  id: string
  email: string
  displayName: string
  role: 'admin' | 'user' | 'guest'
  createdAt: string
}
```

---

## Gestion des erreurs

- Toutes les erreurs réseau sont interceptées au niveau du service ou du store — jamais swallowées en silence.
- Afficher un état d'erreur explicite dans l'UI (pas de `console.log` seul).
- Toujours gérer les trois états : `isLoading`, `data`, `error`.

```ts
// Pattern standard dans un composable ou store
const data = ref(null)
const isLoading = ref(false)
const error = ref<string | null>(null)

async function load() {
  isLoading.value = true
  error.value = null
  try {
    data.value = await someService.fetch()
  } catch (e) {
    error.value = 'Une erreur est survenue. Veuillez réessayer.'
  } finally {
    isLoading.value = false
  }
}
```

---

## Variables d'environnement

- Toutes les variables sont préfixées `VITE_` et déclarées dans un fichier `.env.example` à la racine.
- Ne jamais committer de secrets dans `.env` (ajouter `.env.local` au `.gitignore`).
- Accéder via `import.meta.env.VITE_MA_VARIABLE` — jamais via `process.env`.

---

## Tests

- Chaque composant critique a un test unitaire dans `__tests__/` à côté de lui, ou dans `src/__tests__/`.
- Les tests de composants utilisent Vue Test Utils + Vitest.
- Les stores Pinia sont testés isolément avec `setActivePinia(createPinia())`.
- Ne pas mocker ce qui peut être testé réellement.

---

## Ce que Claude doit faire

- Toujours utiliser `<script setup lang="ts">`.
- Toujours typer les props, emits, et valeurs de retour des fonctions publiques.
- Séparer la logique de la présentation : logique dans composables/stores, affichage dans les templates.
- Nommer les variables clairement (`isLoading` pas `loading`, `hasError` pas `error` pour un booléen).
- Préférer les composables aux mixins et aux `provide/inject` non typés.
- Proposer une structure de dossier si elle n'est pas encore en place.
- Signaler si une modification introduit une dépendance circulaire ou casse la séparation des responsabilités.

## Ce que Claude ne doit pas faire

- Ne pas utiliser l'Options API (sauf si base de code existante impose de l'étendre).
- Ne pas accéder à une API depuis un composant ou une page directement.
- Ne pas utiliser `ref` pour tout : préférer `reactive` pour des objets complexes quand ça clarifie le code.
- Ne pas ignorer les erreurs dans les blocs `catch`.
- Ne pas créer des composants de plus de ~250 lignes sans proposer un découpage.
