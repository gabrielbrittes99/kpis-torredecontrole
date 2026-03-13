<template>
  <div class="alerts-container" v-if="alertas.length">
    <div v-for="a in alertas" :key="a.id" class="alert-item" :class="a.nivel">
      <div class="alert-icon">
        <span v-if="a.nivel === 'critico'">🚨</span>
        <span v-else-if="a.nivel === 'atencao'">⚠️</span>
        <span v-else>ℹ️</span>
      </div>
      <div class="alert-content">
        <div class="alert-title">{{ a.titulo }}</div>
        <div class="alert-desc">{{ a.descricao }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  alertas: { type: Array, default: () => [] }
})
</script>

<style scoped>
.alerts-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 24px;
}
.alert-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 14px 18px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--surface);
  animation: slideIn 0.3s ease-out;
}
.alert-item.critico { border-left: 4px solid var(--red); background: var(--red-bg); }
.alert-item.atencao { border-left: 4px solid var(--orange); background: var(--orange-bg); }
.alert-item.info    { border-left: 4px solid var(--blue);   background: var(--blue-bg); }

.alert-icon { font-size: 18px; margin-top: 2px; }
.alert-title { font-size: 13px; font-weight: 700; color: var(--text); margin-bottom: 2px; }
.alert-desc { font-size: 12px; color: var(--text-2); line-height: 1.4; }

@keyframes slideIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
