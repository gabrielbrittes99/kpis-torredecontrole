<template>
    <div class="map-wrapper" :class="{ 'is-loading': loading }">
        <div v-if="loading" class="map-overlay-loading">
            <div class="spinner"></div>
            <span>Carregando mapa...</span>
        </div>
        <div ref="mapRef" class="map-container"></div>

        <!-- Legend -->
        <div class="map-legend" v-if="!loading && data.length > 0">
            <div class="legend-title">Preço Médio (R$/L)</div>
            <div class="legend-bar">
                <div
                    class="legend-gradient"
                    :style="{ background: gradientStyle }"
                ></div>
            </div>
            <div class="legend-labels">
                <span>R$ {{ scale.min.toFixed(2) }}</span>
                <span>R$ {{ scale.max.toFixed(2) }}</span>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from "vue";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

const props = defineProps({
    data: { type: Array, default: () => [] },
    loading: { type: Boolean, default: false },
    color: { type: String, default: "#C41230" }, // Gritsch Red by default
});

const mapRef = ref(null);
let map = null;
let geojsonLayer = null;
let geojsonData = null;

const scale = ref({ min: 0, max: 1 });

// CSS Gradient for legend
const gradientStyle = computed(() => {
    return `linear-gradient(to right, ${getColorIntensity(scale.value.min, scale.value.min, scale.value.max)}, ${getColorIntensity(scale.value.max, scale.value.min, scale.value.max)})`;
});

function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result
        ? {
              r: parseInt(result[1], 16),
              g: parseInt(result[2], 16),
              b: parseInt(result[3], 16),
          }
        : { r: 196, g: 18, b: 48 };
}

const updateScale = () => {
    if (!props.data || props.data.length === 0) {
        scale.value = { min: 0, max: 1 };
        return;
    }
    const precos = props.data.map((d) => d.preco_medio).filter((v) => v > 0);
    if (precos.length === 0) {
        scale.value = { min: 0, max: 1 };
        return;
    }
    scale.value = { min: Math.min(...precos), max: Math.max(...precos) };
};

const getColorIntensity = (val, min, max) => {
    if (!val) return "#f8fafc"; // vazio
    if (min === max) return props.color;
    let pct = (val - min) / (max - min);

    const rgb = hexToRgb(props.color);
    const bg = 255;
    const alpha = 0.15 + 0.85 * pct; // 15% to 100% opacity
    const r = Math.round(bg + (rgb.r - bg) * alpha);
    const g = Math.round(bg + (rgb.g - bg) * alpha);
    const b = Math.round(bg + (rgb.b - bg) * alpha);
    return `rgb(${r}, ${g}, ${b})`;
};

function initMap() {
    if (map) return;

    map = L.map(mapRef.value, {
        center: [-14.235, -51.925],
        zoom: 4,
        zoomControl: false,
        scrollWheelZoom: false,
        dragging: false,
        doubleClickZoom: false,
        attributionControl: false,
    });

    fetch("/brazil-states.json")
        .then((r) => r.json())
        .then((json) => {
            geojsonData = json;
            renderGeojson();
        });
}

function renderGeojson() {
    if (!map || !geojsonData) return;
    if (geojsonLayer) {
        map.removeLayer(geojsonLayer);
    }

    updateScale();
    const { min, max } = scale.value;
    const dataMap = new Map(props.data.map((d) => [d.uf, d]));

    geojsonLayer = L.geoJSON(geojsonData, {
        style: (feature) => {
            const uf = feature.properties.sigla;
            const stat = dataMap.get(uf);
            const val = stat ? stat.preco_medio : null;
            return {
                fillColor: getColorIntensity(val, min, max),
                weight: 1,
                opacity: 1,
                color: "#ffffff",
                fillOpacity: 1,
            };
        },
        onEachFeature: (feature, layer) => {
            const uf = feature.properties.sigla;
            const stat = dataMap.get(uf);
            if (stat) {
                const preco = `R$ ${stat.preco_medio.toFixed(3)}`;
                const litros = stat.total_litros.toLocaleString("pt-BR");
                const popupContent = `
          <div style="font-family: 'Inter', sans-serif; min-width: 140px;">
            <div style="font-weight: 700; font-size: 13px; color: #1e293b; margin-bottom: 6px; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px;">
              ${feature.properties.name} (${uf})
            </div>
            <div style="font-size: 12px; color: #475569; display: flex; justify-content: space-between; margin-bottom: 4px;">
              <span>Preço Médio:</span>
              <strong style="color: #C41230;">${preco}</strong>
            </div>
            <div style="font-size: 11px; color: #64748b; display: flex; justify-content: space-between;">
              <span>Volume:</span>
              <strong style="color: #0f172a;">${litros} L</strong>
            </div>
          </div>
        `;
                layer.bindTooltip(popupContent, {
                    sticky: true,
                    className: "custom-map-tooltip",
                });
            } else {
                layer.bindTooltip(
                    `
          <div style="font-family: 'Inter', sans-serif;">
            <strong style="color:#1e293b">${feature.properties.name}</strong><br>
            <span style="color:#94a3b8;font-size:11px;">Sem abastecimentos</span>
          </div>
        `,
                    { sticky: true, className: "custom-map-tooltip" },
                );
            }

            layer.on({
                mouseover: (e) => {
                    const l = e.target;
                    l.setStyle({ weight: 2, color: "#0f172a" });
                    if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
                        l.bringToFront();
                    }
                },
                mouseout: (e) => {
                    geojsonLayer.resetStyle(e.target);
                },
            });
        },
    }).addTo(map);

    map.fitBounds(geojsonLayer.getBounds(), { padding: [10, 10] });

    map.dragging.disable();
    map.touchZoom.disable();
    map.doubleClickZoom.disable();
    map.scrollWheelZoom.disable();
    map.boxZoom.disable();
    map.keyboard.disable();
    if (map.tap) map.tap.disable();
}

watch(
    () => props.data,
    () => {
        renderGeojson();
    },
    { deep: true },
);

watch(
    () => props.color,
    () => {
        renderGeojson();
    },
);

onMounted(() => {
    initMap();
});

onUnmounted(() => {
    if (map) {
        map.remove();
        map = null;
    }
});
</script>

<style scoped>
.map-wrapper {
    position: relative;
    width: 100%;
    min-height: 450px;
    background: #f8fafc;
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #e2e8f0;
    display: flex;
    flex-direction: column;
}
.map-container {
    width: 100%;
    flex: 1;
    background: transparent;
    min-height: 450px;
}
.map-overlay-loading {
    position: absolute;
    inset: 0;
    z-index: 1000;
    background: rgba(248, 250, 252, 0.8);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    font-size: 13px;
    font-weight: 600;
    color: #64748b;
}
.spinner {
    width: 36px;
    height: 36px;
    border: 4px solid #e2e8f0;
    border-top-color: #c41230;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}
@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

.map-legend {
    position: absolute;
    bottom: 16px;
    right: 16px;
    background: white;
    padding: 12px 16px;
    border-radius: 8px;
    box-shadow:
        0 4px 6px -1px rgba(0, 0, 0, 0.1),
        0 2px 4px -1px rgba(0, 0, 0, 0.06);
    border: 1px solid #e2e8f0;
    z-index: 400;
    min-width: 160px;
}
.legend-title {
    font-size: 11px;
    font-weight: 700;
    color: #64748b;
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.legend-bar {
    height: 8px;
    border-radius: 4px;
    background: #e2e8f0;
    margin-bottom: 6px;
    overflow: hidden;
}
.legend-gradient {
    height: 100%;
    width: 100%;
}
.legend-labels {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    font-weight: 700;
    color: #1e293b;
}
</style>

<style>
.leaflet-tooltip.custom-map-tooltip {
    background: white;
    border: 1px solid #e2e8f0;
    box-shadow:
        0 10px 15px -3px rgba(0, 0, 0, 0.1),
        0 4px 6px -2px rgba(0, 0, 0, 0.05);
    border-radius: 8px;
    padding: 12px;
    color: #0f172a;
}
.leaflet-tooltip-left.custom-map-tooltip::before {
    border-left-color: white;
}
.leaflet-tooltip-right.custom-map-tooltip::before {
    border-right-color: white;
}
</style>
