<template>
  <div v-show="modelValue" class="modal-overlay" @click.self="$emit('update:modelValue', null)">
    <div class="modal-card industrial-modal">
      <div class="modal-header">
        <div class="header-left">
          <span class="prio-tag" :class="modelValue?.nivel">#{{ modelValue?.prioridade }}</span>
          <h2>{{ modelValue?.titulo }}</h2>
        </div>
        <button @click="$emit('update:modelValue', null)" class="btn-close">×</button>
      </div>
      
      <div v-if="modelValue" class="modal-body">
        <div class="impact-banner" :class="modelValue.nivel">
          <div class="impact-label">Impacto Financeiro Estimado:</div>
          <div class="impact-value">{{ modelValue.impacto }}</div>
        </div>

        <div class="section-label font-syne">Passos Estratégicos Para Execução:</div>
        <div class="steps-grid">
          <div v-for="(p, i) in modelValue.passos" :key="i" class="step-item">
            <div class="step-num">{{ i + 1 }}</div>
            <div class="step-text">{{ p }}</div>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button @click="$emit('update:modelValue', null)" class="btn-dismiss">Fechar Sem Resolver</button>
        <button @click="resolver" class="btn-resolve">
          <span class="icon">✓</span>
          Marcar Ação Como Resolvida
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps(['modelValue'])
const emit = defineEmits(['update:modelValue', 'resolve'])

function resolver() {
  emit('resolve')
  emit('update:modelValue', null)
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(5,7,10,0.85);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 20px;
}
.modal-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 4px;
  width: 100%;
  max-width: 520px;
  overflow: hidden;
  box-shadow: 0 32px 64px rgba(0,0,0,0.8);
  position: relative;
}
.modal-card::before {
  content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 2px; background: var(--orange);
}

.modal-header { padding: 24px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
.header-left { display: flex; align-items: center; gap: 16px; }
.header-left h2 { font-size: 16px; margin: 0; color: var(--text); text-transform: uppercase; }

.prio-tag { font-family: 'IBM Plex Mono', monospace; font-weight: 700; font-size: 11px; padding: 2px 6px; border: 1px solid; border-radius: 2px; }
.prio-tag.critico { border-color: var(--red); color: var(--red); background: var(--red-bg); }
.prio-tag.atencao { border-color: var(--yellow); color: var(--yellow); background: var(--yellow-bg); }

.btn-close { background: none; border: none; font-size: 32px; color: var(--text-3); cursor: pointer; }

.modal-body { padding: 32px; }
.impact-banner { padding: 16px; border-radius: 4px; text-align: center; margin-bottom: 32px; border-left: 4px solid; }
.impact-banner.critico { background: var(--red-bg); border-color: var(--red); }
.impact-banner.atencao { background: var(--yellow-bg); border-color: var(--yellow); }
.impact-label { font-size: 11px; color: var(--text-2); margin-bottom: 4px; text-transform: uppercase; }
.impact-value { font-family: 'IBM Plex Mono', monospace; font-size: 20px; font-weight: 700; color: var(--text); }

.section-label { font-size: 11px; color: var(--orange); margin-bottom: 20px; }
.steps-grid { display: grid; gap: 16px; }
.step-item { display: flex; gap: 16px; align-items: flex-start; }
.step-num { width: 24px; height: 24px; border: 1px solid var(--border); color: var(--text-2); display: flex; align-items: center; justify-content: center; font-family: 'IBM Plex Mono', monospace; font-size: 12px; }
.step-text { color: var(--text-2); font-size: 13px; line-height: 1.5; }

.modal-footer { padding: 24px 32px 32px; display: flex; gap: 16px; }
.btn-dismiss { flex: 1; background: transparent; border: 1px solid var(--border); color: var(--text-3); padding: 12px; cursor: pointer; }
.btn-resolve { flex: 2; background: var(--orange); color: white; border: none; padding: 12px; font-weight: 700; text-transform: uppercase; cursor: pointer; }
</style>
