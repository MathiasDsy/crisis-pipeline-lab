import { ref, computed, onMounted, onUnmounted } from "vue"
import { fetchAllTweets } from "../api/tweetsApi"
import type { SidebarItem } from "../types/sidebar"

export function useTweets() {
  const tweets = ref<any[]>([])
  const selectedTweetId = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  let intervalId: number | null = null

  const selectedTweet = computed(() => {
    return tweets.value.find(t => t.id === selectedTweetId.value) ?? null
  })

  async function loadTweets(silent = false) {
    if (!silent) loading.value = true
    error.value = null

    try {
      tweets.value = await fetchAllTweets()

      if (tweets.value.length > 0 && !selectedTweetId.value) {
        selectedTweetId.value = tweets.value[0].id
      }
    } catch (err: any) {
      error.value = err.message ?? "Unknown error"
    } finally {
      if (!silent) loading.value = false
    }
  }

  function selectTweet(tweetId: string) {
    selectedTweetId.value = tweetId
  }

  onMounted(() => {
    loadTweets()

    intervalId = window.setInterval(() => {
      loadTweets(true)
    }, 3000)
  })

  onUnmounted(() => {
    if (intervalId !== null) {
      clearInterval(intervalId)
    }
  })

  const tweetSidebarItems = computed<SidebarItem[]>(() =>
    tweets.value.map(run => ({
      id: run.id,
      title: run.text,
      subtitle: run.config,
      description: run.blocked_at
        ? `Blocked at ${run.blocked_at}`
        : undefined,

      status: run.status,
      statusLabel: run.status.toUpperCase(),

      blockedAt: run.blocked_at,

      searchText: [
        run.text,
        run.config,
        run.status,
        run.blocked_at
      ].filter(Boolean).join(" ").toLowerCase(),

      meta: [
        { label: "Config", value: run.config }
      ],

      raw: run
    }))
  )



  return {
    tweets,
    tweetSidebarItems,
    selectedTweet,
    selectedTweetId,
    loading,
    error,
    loadTweets,
    selectTweet,
  }



}