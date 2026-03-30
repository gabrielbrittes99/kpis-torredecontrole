import re

with open('src/views/Pneus.vue', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add Ano filter
ano_filter = '''            <div class="filter-group">
              <label>Ano</label>
              <select v-model="filtroAno" @change="loadAll">
                <option value="">Todos</option>
                <option v-for="a in filtros.anos" :key="a" :value="a">{{ a }}</option>
              </select>
            </div>
            <div class="filter-group">'''
text = text.replace('<div class="filter-group">', ano_filter, 1)

# 2. Swap sections in template
text = re.sub(
    r'<!-- SEÇÃO 6: TOP PNEUS MAIS CAROS -->.*?<!-- SEÇÃO 7:', 
    '''<!-- SEÇÃO 6: GASTOS POR MÊS -->
      <section class="v-block">
        <div class="section-heading">Gastos por Mês</div>
        <div v-if="lTimeline" class="skel" style="height:300px" />
        <div v-else-if="!timeline.length" class="empty">Sem dados</div>
        <apexchart v-else type="area" height="300" :options="areaTimelineOptions" :series="areaTimelineSeries" />
      </section>

      <!-- SEÇÃO 7:''', 
    text, flags=re.DOTALL)

text = re.sub(r'<!-- SEÇÃO 8: TABELA DETALHADA -->.*?</template>', '</template>', text, flags=re.DOTALL)

# 3. Add imports
text = text.replace('fetchPneusPorTipo, fetchPneusTopCaros, fetchPneusPorPlaca,', 'fetchPneusPorTipo, fetchPneusTimeline, fetchPneusPorPlaca,')

# 4. Refs
text = text.replace('filtros = ref({ filiais: [], marcas: [], fornecedores: [], eixos: [], medidas: [] })', 'filtros = ref({ anos: [], filiais: [], marcas: [], fornecedores: [], eixos: [], medidas: [] })')
text = text.replace("const filtroFilial = ref('')", "const filtroAno = ref('')\nconst filtroFilial = ref('')")

text = text.replace('const topCaros = ref([])', 'const timeline = ref([])')
text = text.replace('const tabela = ref({ cols: [], rows: [] })', '')
text = text.replace('const lTopCaros = ref(true)', 'const lTimeline = ref(true)')
text = text.replace('const lTabela = ref(true)', '')

# Params
text = text.replace('''const params = () => ({
  filial: filtroFilial.value,
  marca: filtroMarca.value,
  fornecedor: filtroFornecedor.value,
})''', '''const params = () => ({
  ano: filtroAno.value,
  filial: filtroFilial.value,
  marca: filtroMarca.value,
  fornecedor: filtroFornecedor.value,
})''')

# 5. Load methods
text = text.replace('lTopCaros.value = true', 'lTimeline.value = true')
text = text.replace('lPlaca.value = true; lTabela.value = true', 'lPlaca.value = true')

fetch_block_old = '''    const [k, t, fm, ma, fo, ex, me, es, tc, pl, tb] = await Promise.all([
      fetchPneusKpis(p),
      fetchPneusPorTipo(p),
      fetchPneusPorFilial(p),
      fetchPneusPorMarca(p),
      fetchPneusPorFornecedor(p),
      fetchPneusPorEixo(p),
      fetchPneusPorMedida(p),
      fetchPneusPorEstado(),
      fetchPneusTopCaros({ filial: p.filial, limit: 10 }),
      fetchPneusPorPlaca({ filial: p.filial, limit: 20 }),
      fetchPneusTabela(p),
    ])'''
fetch_block_new = '''    const [k, t, fm, ma, fo, ex, me, es, tl, pl] = await Promise.all([
      fetchPneusKpis(p),
      fetchPneusPorTipo(p),
      fetchPneusPorFilial(p),
      fetchPneusPorMarca(p),
      fetchPneusPorFornecedor(p),
      fetchPneusPorEixo(p),
      fetchPneusPorMedida(p),
      fetchPneusPorEstado(p),
      fetchPneusTimeline(p),
      fetchPneusPorPlaca({ ...p, limit: 20 }),
    ])'''
text = text.replace(fetch_block_old, fetch_block_new)

text = text.replace('topCaros.value = tc', 'timeline.value = tl')
text = text.replace('porPlaca.value = pl\n    tabela.value = tb', 'porPlaca.value = pl')
text = text.replace('lTopCaros.value = false', 'lTimeline.value = false')
text = text.replace('lPlaca.value = false; lTabela.value = false', 'lPlaca.value = false')

# 6. Formatting fixes
marca_old = """xaxis: { categories: porMarca.value.map(m => m.marca), labels: { style: { fontSize: '11px' } } },
  yaxis: { labels: { formatter: v => fmtR(v) } },"""
marca_new = """xaxis: { categories: porMarca.value.map(m => m.marca), labels: { style: { fontSize: '11px' }, formatter: v => fmtR(v) } },
  yaxis: { labels: { show: true } },"""
text = text.replace(marca_old, marca_new)

medida_old = """xaxis: { categories: porMedida.value.map(m => m.medida), labels: { style: { fontSize: '11px' } } },
  yaxis: { labels: { formatter: v => Math.round(v) } },"""
medida_new = """xaxis: { categories: porMedida.value.map(m => m.medida), labels: { style: { fontSize: '11px' }, formatter: v => Math.round(v) } },
  yaxis: { labels: { show: true } },"""
text = text.replace(medida_old, medida_new)

# Timeline Options
timeline_code = """
// Donut: Estado (UF)
const donutEstadoOptions = computed(() => ({
  labels: porEstado.value.map(e => e.estado),
  legend: { position: 'bottom', fontSize: '12px' },
  colors: COLORS,
  dataLabels: { enabled: true, formatter: v => v.toFixed(1) + '%' },
}))
const donutEstadoSeries = computed(() => porEstado.value.map(e => e.valor))

// Área: Gastos por Mês
const areaTimelineOptions = computed(() => ({
  chart: { toolbar: { show: false } },
  xaxis: { categories: timeline.value.map(t => t.mes), labels: { style: { fontSize: '11px' } } },
  yaxis: { labels: { formatter: v => fmtR(v) } },
  colors: ['#C41230'],
  stroke: { curve: 'smooth', width: 2 },
  fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.4, opacityTo: 0.05, stops: [0, 90, 100] } },
  dataLabels: { enabled: false }
}))
const areaTimelineSeries = computed(() => [{ name: 'Gastos', data: timeline.value.map(t => t.valor) }])
"""
text = re.sub(r'// Donut: Estado \(UF\).*?computed\(\(\) => porEstado\.value\.map\(e => e\.valor\)\)', timeline_code, text, flags=re.DOTALL)

with open('src/views/Pneus.vue', 'w', encoding='utf-8') as f:
    f.write(text)

print('VUE FIXES COMPLETE')
