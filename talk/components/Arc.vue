<script setup lang="ts">
// The workflow arc. `active` lights up steps (1-based); `size="lg"` is the full-slide version.
const props = withDefaults(defineProps<{ active?: number[]; size?: "sm" | "lg" }>(), {
  active: () => [],
  size: "sm",
})
const steps = [
  { icon: "📖", label: "story" },
  { icon: "🎲", label: "priors" },
  { icon: "🔮", label: "prior predictive" },
  { icon: "⚙️", label: "sample" },
  { icon: "🔁", label: "posterior predictive" },
  { icon: "🎯", label: "coverage" },
  { icon: "🛠️", label: "expand" },
]
const isOn = (i: number) => props.active.length === 0 || props.active.includes(i + 1)
</script>

<template>
  <div v-if="size === 'lg'" class="flex items-stretch justify-center gap-3 mt-8">
    <template v-for="(s, i) in steps" :key="s.label">
      <div
        class="flex flex-col items-center justify-center w-28 py-5 rounded-xl border"
        :class="isOn(i) ? 'bg-gray-800/60 border-emerald-500/70 text-white' : 'bg-gray-900/40 border-gray-800 text-gray-600'"
      >
        <div class="text-4xl">{{ s.icon }}</div>
        <div class="mt-3 text-sm text-center leading-tight">{{ s.label }}</div>
      </div>
      <div v-if="i < steps.length - 1" class="self-center text-2xl text-gray-600">→</div>
      <div v-else class="self-center text-3xl bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-indigo-500 font-bold">↻</div>
    </template>
  </div>

  <div v-else class="flex items-center justify-center gap-2 mt-12">
    <template v-for="(s, i) in steps" :key="s.label">
      <div
        class="px-3 py-1.5 rounded-full text-sm border"
        :class="isOn(i) ? 'bg-gradient-to-r from-emerald-500 to-indigo-500 border-transparent text-white font-bold' : 'bg-gray-900/40 border-gray-800 text-gray-600'"
      >
        {{ s.icon }} {{ s.label }}
      </div>
      <span v-if="i < steps.length - 1" class="text-gray-700">→</span>
      <span v-else class="text-emerald-400">↻</span>
    </template>
  </div>
</template>
