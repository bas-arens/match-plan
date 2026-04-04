<template>
  <div
    @click="toggle"
    class="bg-white dark:bg-gray-800 rounded-lg shadow px-4 py-3 mb-3 border border-brand-border dark:border-gray-700 cursor-pointer select-none"
  >

    <!-- GRID: 3 kolommen -->
    <div class="grid grid-cols-[1fr_80px_1fr] items-center">

      <!-- THUIS -->
      <div class="flex items-center space-x-3">
        <img :src="homeLogo" class="h-10 w-10 object-contain rounded" />
        <span class="font-semibold text-gray-800 dark:text-gray-100">{{ home }}</span>
      </div>

      <!-- MIDDEN: VS + Tijd -->
      <div class="flex flex-col items-center justify-center">
        <div class="text-brand-primary font-bold text-lg leading-none">VS</div>
        <div class="text-sm text-gray-600 mt-1">{{ time }}</div>
      </div>

      <!-- UIT -->
      <div class="flex items-center space-x-3 justify-end">
        <span class="font-semibold text-gray-800 dark:text-gray-100">{{ away }}</span>
        <img :src="awayLogo" class="h-10 w-10 object-contain rounded" />
      </div>

    </div>

    <!-- UITKLAPBARE DETAILS -->
    <transition name="slide">
      <div
        v-if="expanded"
        class="mt-4 p-4 bg-gray-50 dark:bg-gray-700 rounded grid grid-cols-3 gap-6"
      >

        <!-- LINKERKOLOM: THUIS INFO -->
        <div class="text-center">
          <h4 class="font-semibold text-gray-700 dark:text-gray-200 mb-2 text-center">Thuisteam</h4>


          <p><strong>Kleedkamer:</strong> {{ kleedkamerThuis }}</p>
        </div>

        <!-- MIDDENKOLOM: ALGEMEEN -->
        <div class="text-center">
          <h4 class="font-semibold text-gray-700 dark:text-gray-200 mb-2 text-center">Wedstrijdinfo</h4>

          <p><strong>Competitie:</strong> {{ competitiesoort || '—' }}</p>
          <p><strong>Klasse:</strong> {{ klasse || '—' }}</p>
          <p><strong>Scheidsrechter:</strong> {{ scheidsrechter || '—' }}</p>
          <p><strong>SR kleedkamer:</strong> {{ kleedkamerScheids }}</p>
        </div>

        <!-- RECHTERKOLOM: UIT INFO -->
        <div class="text-center">
          <h4 class="font-semibold text-gray-700 dark:text-gray-200 mb-2 text-center">Uitteam</h4>

          <p><strong>Kleedkamer:</strong> {{ kleedkamerUit }}</p>
        </div>

      </div>
    </transition>

  </div>
</template>

<script setup>
import { ref } from 'vue'

const expanded = ref(false)
const toggle = () => (expanded.value = !expanded.value)


defineProps({
  home: String,
  away: String,
  homeLogo: String,
  awayLogo: String,

  time: String,

  // wedstrijd info
  competitiesoort: String,
  klasse: String,
  scheidsrechter: String,

  // kleedkamers
  kleedkamerThuis: String,
  kleedkamerUit: String,
  kleedkamerScheids: String
})
</script>

<style scoped>
.slide-enter-from,
.slide-leave-to {
  max-height: 0;
  opacity: 0;
}

.slide-enter-to,
.slide-leave-from {
  max-height: 300px;
  opacity: 1;
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.25s ease;
}
</style>
