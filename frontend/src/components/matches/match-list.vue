<template>
  <div class="mt-4">
    <h3 class="text-xl font-bold mb-4">Wedstrijden</h3>

    <div v-if="matches.length === 0" class="text-gray-400">
      Geen wedstrijden geselecteerd.
    </div>

    <MatchItem
      v-for="(m, i) in matches"
      :key="i"
      :home="m.thuisteam"
      :away="m.uitteam"
      :homeLogo="m.thuisteamlogo"
      :awayLogo="m.uitteamlogo"
      :time="m.aanvangstijd"

      :competitiesoort="m.competitiesoort"
      :klasse="m.klasse"
      :scheidsrechter="m.scheidsrechter"

      :kleedkamerThuis="m.kleedkamerthuisteam"
      :kleedkamerUit="m.kleedkameruitteam"
      :kleedkamerScheids="m.kleedkamerscheidsrechter"
    />


  </div>
</template>

<script setup>
// ─────────────────────────────────────────────────────────────────────────────
// File:    src/components/matches/match-list.vue
// Author:  MatchPlan
// Purpose: Renders the list of matches for the selected date using MatchItem.
//          Shows a placeholder message when no matches are available.
//
// Props:
//   matches  — array of match objects from the Sportlink API (required)
// ─────────────────────────────────────────────────────────────────────────────
import MatchItem from './match-item.vue'

defineProps({
  matches: { type: Array, required: true },
})
</script>
