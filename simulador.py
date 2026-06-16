import streamlit as st
import pandas as pd
import numpy as np
import datetime
import math

# Configuração da Página
st.set_page_config(page_title="Simulador e Controladoria de Imóvel", page_icon="🏢", layout="wide")

st.title("🏢 Plataforma de Gestão Imobiliária")
st.markdown("Planeje a compra e controle o fluxo de caixa real durante o período de obras.")
st.divider()

# --- 1. MODO DE OPERAÇÃO E PERFIL (Barra lateral) ---
st.sidebar.header("1. Modo de Operação")
modo_app = st.sidebar.radio(
    "O que você deseja fazer?",
    ["🎯 Simulador (Pré-Assinatura)", "📊 Controladoria (Pós-Assinatura)"]
)

st.sidebar.markdown("---")
st.sidebar.header("2. Configurações Gerais")
perfil = st.sidebar.radio(
    "👤 Selecione o Perfil", 
    ["Cenário Vinicius & Ju", "Cenário João & Mari"]
)

# Definindo os valores padrão
if perfil == "Cenário Vinicius & Ju":
    default_imovel = 717000.0
    default_entrada = 55000.0
    default_mensal_const = 0.0  
    default_meses_chaves = 30      
    default_renda = 14868.0
    default_prazo = 308          
    default_taxa = 11.19         
    opcoes_amortizacao = ["SAC"]
else:
    default_imovel = 437000.0      
    default_entrada = 65000.0      
    default_mensal_const = 0.0     
    default_meses_chaves = 39      
    default_renda = 7500.0
    default_prazo = 420          
    default_taxa = 7.93          
    opcoes_amortizacao = ["PRICE", "SAC"]

# Variáveis globais para compartilhar entre os módulos
taxa_mensal = (default_taxa / 100) / 12  
saldo_necessario = default_imovel - default_entrada

# =====================================================================
# MÓDULO 1: SIMULADOR (PRÉ-ASSINATURA)
# =====================================================================
if modo_app == "🎯 Simulador (Pré-Assinatura)":
    
    st.header("1. Parâmetros do Negócio")
    col1, col2, col3 = st.columns(3)

    with col1:
        valor_imovel = st.number_input("Valor Total do Imóvel (R$)", min_value=0.0, value=default_imovel, step=10000.0)
        entrada_inicial = st.number_input("Valor da Entrada (Aporte Inicial) (R$)", min_value=0.0, value=default_entrada, step=1000.0)
        itbi_construtora = st.radio("ITBI + Registro pagos pela construtora?", ["Sim", "Não"])

    with col2:
        mensal_construtora = st.number_input("Valor da Parcela Mensal (Pré-chaves)", min_value=0.0, value=default_mensal_const, step=100.0)
        anual_construtora = st.number_input("Valor da Parcela Anual", min_value=0.0, value=0.0, step=500.0)
        meses_ate_chaves = st.number_input("Meses até a Entrega das Chaves", min_value=1, value=default_meses_chaves, step=1)

    with col3:
        renda_casal = st.number_input("Renda Líquida Mensal", min_value=0.0, value=default_renda, step=500.0)
        prazo_financiamento = st.number_input("Prazo do Financiamento (Meses)", min_value=1, value=default_prazo, step=12)
        taxa_juros_anual = st.number_input("Taxa de Juros Anual do Financiamento (%)", min_value=0.0, value=default_taxa, step=0.1)
        valor_condominio = st.number_input("Valor do Condomínio", min_value=0.0, value=0.0, step=50.0)

    sistema_amortizacao = st.sidebar.selectbox(
        "Sistema de Amortização", opcoes_amortizacao,
        help="SAC: parcelas decrescentes (amortização constante). PRICE: parcelas fixas no início."
    )

    if renda_casal <= 0:
        st.warning("⚠️ Insira a renda líquida mensal informada para calcular o comprometimento.")

    st.markdown("---")
    st.header("2. Análise do Financiamento e Obra")

    if perfil == "Cenário João & Mari":
        if sistema_amortizacao == "PRICE":
            saldo_financiado = 298000.00
            parcela_banco_inicial = 2153.22 
            ultima_parcela_banco = 2153.22
        else: 
            saldo_financiado = 250000.00 
            amortizacao = saldo_financiado / prazo_financiamento
            parcela_banco_inicial = amortizacao + (saldo_financiado * taxa_mensal)
            ultima_parcela_banco = amortizacao + (amortizacao * taxa_mensal) 
            
        gap_construtora = valor_imovel - entrada_inicial - saldo_financiado
        mensal_construtora_calculada = gap_construtora / meses_ate_chaves
        teto_obra = parcela_banco_inicial
        obra_inicial = 100.00 
        
    else:
        # Cenário Vinicius & Ju
        teto_aprovado_caixa = 636300.00
        saldo_necessario_real = valor_imovel - entrada_inicial
        
        if saldo_necessario_real > teto_aprovado_caixa:
            saldo_financiado = teto_aprovado_caixa
            gap_construtora = saldo_necessario_real - teto_aprovado_caixa
        else:
            saldo_financiado = saldo_necessario_real
            gap_construtora = 0.0

        parcela_banco_inicial = 8225.12
        ultima_parcela_banco = 2109.25
        
        mensal_construtora_calculada = (gap_construtora / meses_ate_chaves) + mensal_construtora 
        teto_obra = parcela_banco_inicial
        obra_inicial = 1480.52

    saldo_devedor_chaves = saldo_financiado

   # Exibe o diagnóstico na tela (Focado 100% na fase de Obras)
    col_res1, col_res2, col_res3 = st.columns(3)

    if perfil == "Cenário João & Mari":
        col_res1.metric("GAP Construtora (Buraco)", f"R$ {gap_construtora:,.2f}")
        col_res2.metric("Parcela Construtora (Mensal)", f"R$ {mensal_construtora_calculada:,.2f}")
        col_res3.metric("Teto Evolução Obra", f"R$ {teto_obra:,.2f}")
    else:
        col_res1.metric("GAP Construtora (Descoberto)", f"R$ {gap_construtora:,.2f}")
        col_res2.metric("Parcela Mensal Construtora", f"R$ {mensal_construtora_calculada:,.2f}")
        col_res3.metric("Teto Evolução Obra", f"R$ {teto_obra:,.2f}")
        
    st.info(f"💡 A 1ª parcela do financiamento na entrega das chaves ({sistema_amortizacao}) será de **R$ {parcela_banco_inicial:,.2f}**.")
    
    # CONSTRUTOR DO DATAFRAME PRÉ-CHAVES
    meses_array = np.arange(1, int(meses_ate_chaves) + 1)
    meses_carencia_eo = 2 

    if len(meses_array) > meses_carencia_eo:
        eo_zerada = np.zeros(meses_carencia_eo)
        eo_ativa = np.linspace(obra_inicial, teto_obra, len(meses_array) - meses_carencia_eo)
        evolucao_obra_array = np.concatenate((eo_zerada, eo_ativa))
    else:
        evolucao_obra_array = np.zeros(len(meses_array))

    parcela_const_array = np.full(len(meses_array), mensal_construtora_calculada)

    df_pre_chaves = pd.DataFrame({
        'Mês': meses_array,
        'Evolução de Obra (R$)': evolucao_obra_array,
        'Parcela Construtora (R$)': parcela_const_array,
        'Custo Total Mensal (R$)': evolucao_obra_array + parcela_const_array
    })

    st.header(f"3. Financiamento Pós-Chaves ({sistema_amortizacao})")
    col4, col5, col6 = st.columns(3)
    col4.metric("Saldo Devedor a Financiar (R$)", f"R$ {saldo_devedor_chaves:,.2f}")
    col5.metric("Primeira Parcela (Exata/Aprovada)", f"R$ {parcela_banco_inicial:,.2f}")
    col6.metric("Última Parcela (Estimada)", f"R$ {ultima_parcela_banco:,.2f}")

    if renda_casal > 0:
        comprometimento_renda = (parcela_banco_inicial / renda_casal) * 100
        if comprometimento_renda > 30:
            st.warning(f"⚠️ A primeira parcela compromete {comprometimento_renda:.1f}% da renda informada. O limite dos bancos é 30% da renda bruta.")
        else:
            st.success(f"✅ Comprometimento de renda em {comprometimento_renda:.1f}%.")

    st.divider()

    # --- 4. SIMULAÇÃO DE ORÇAMENTO E POUPANÇA (MOVIDO PARA CIMA) ---
    st.subheader("4. Simulação de Orçamento: Poupança x Obra")
    col7, col8 = st.columns(2)
    with col7:
        orcamento_alvo = st.number_input("Orçamento Fixo Mensal (R$)", min_value=1000.0, value=6000.0, step=500.0)
    with col8:
        poupanca_minima = st.number_input("Piso Obrigatório de Poupança (R$)", min_value=0.0, value=1000.0, step=100.0)

    lista_poupanca = []
    lista_desembolso_real = []

    for custo in df_pre_chaves['Custo Total Mensal (R$)']:
        poupanca_projetada = orcamento_alvo - custo
        if poupanca_projetada < poupanca_minima:
            poupanca_real = poupanca_minima
            desembolso_mensal = custo + poupanca_minima
        else:
            poupanca_real = poupanca_projetada
            desembolso_mensal = orcamento_alvo
            
        lista_poupanca.append(poupanca_real)
        lista_desembolso_real.append(desembolso_mensal)

    df_pre_chaves['Poupança Gerada (R$)'] = lista_poupanca
    df_pre_chaves['Desembolso Real do Mês (R$)'] = lista_desembolso_real

    st.bar_chart(df_pre_chaves[['Custo Total Mensal (R$)', 'Poupança Gerada (R$)']])
    
    # OS TOTALIZADORES VOLTARAM AQUI
    total_poupanca_geral = df_pre_chaves['Poupança Gerada (R$)'].sum()
    total_eo_geral = df_pre_chaves['Evolução de Obra (R$)'].sum()
    total_esforco_caixa = df_pre_chaves['Desembolso Real do Mês (R$)'].sum()

    st.markdown("---")
    st.subheader("📊 Resumo Consolidado do Período de Obras")
    col_tot1, col_tot2, col_tot3 = st.columns(3)
    col_tot1.metric("Total Acumulado (Poupança)", f"R$ {total_poupanca_geral:,.2f}")
    col_tot2.metric("Total de Evolução de Obra (EO)", f"R$ {total_eo_geral:,.2f}")
    col_tot3.metric("Esforço Total de Caixa (Gasto + Poupança)", f"R$ {total_esforco_caixa:,.2f}")

    st.divider()

    # --- 5. O TRILEMA DAS CHAVES (REFORMA VS. BANCO) ---
    st.header("5. O Trilema das Chaves: Reforma x Prazo x Parcela")
    st.markdown("Chegou o dia de pegar as chaves. Aloque o seu 'Caixa Acumulado' (calculado acima) para ver qual estratégia protege mais o seu patrimônio.")

    # A INTELIGÊNCIA AQUI: O valor default puxa automaticamente o que foi poupado na Seção 4
    caixa_disponivel = st.number_input("Dinheiro Total Acumulado nas Chaves (R$)", min_value=0.0, value=float(total_poupanca_geral), step=5000.0)

    col_tril1, col_tril2 = st.columns(2)
    with col_tril1:
        reserva_reforma = st.number_input("1. Reserva Sagrada para Reforma e Móveis (R$)", min_value=0.0, max_value=float(caixa_disponivel), value=float(caixa_disponivel * 0.6), step=1000.0)
    with col_tril2:
        saldo_para_banco = caixa_disponivel - reserva_reforma
        st.metric("2. Saldo Livre para Atacar o Banco", f"R$ {saldo_para_banco:,.2f}", "Poder de fogo pós-reforma")

    if saldo_para_banco > 0:
        st.markdown(f"**Como você quer aplicar os R$ {saldo_para_banco:,.2f} na Caixa Econômica?**")
        
        estrategia_banco = st.radio(
            "Escolha a tática:", 
            ["Focar em Reduzir Prazo (Maior economia de juros a longo prazo)", "Focar em Reduzir Parcela (Maior alívio no fluxo de caixa mensal)"]
        )

        if sistema_amortizacao == "SAC":
            amortizacao_mensal_atual = saldo_devedor_chaves / prazo_financiamento
            economia_juros_direta = saldo_para_banco * taxa_mensal
            
            if "Prazo" in estrategia_banco:
                parcelas_reduzidas = int(saldo_para_banco / amortizacao_mensal_atual)
                anos_reduzidos = parcelas_reduzidas / 12
                nova_primeira_parcela = parcela_banco_inicial - economia_juros_direta
                
                st.success(f"⏳ **Efeito no Prazo:** Você arranca **{parcelas_reduzidas} meses** (cerca de **{anos_reduzidos:.1f} anos**) do seu contrato com o banco.")
                st.info(f"💡 **Brinde do SAC:** Mesmo focando em cortar o tempo, a redução da dívida faz sua 1ª parcela cair naturalmente de R$ {parcela_banco_inicial:,.2f} para **R$ {nova_primeira_parcela:,.2f}**.")
                
            else:
                novo_saldo_devedor = saldo_devedor_chaves - saldo_para_banco
                nova_amortizacao_mensal = novo_saldo_devedor / prazo_financiamento
                nova_primeira_parcela = nova_amortizacao_mensal + (novo_saldo_devedor * taxa_mensal)
                
                st.success(f"📉 **Efeito na Parcela:** Sua 1ª parcela despenca de R$ {parcela_banco_inicial:,.2f} para **R$ {nova_primeira_parcela:,.2f}**.")
                st.warning(f"⚠️ O prazo continua em {int(prazo_financiamento)} meses. Você ganha muito fôlego mensal, mas deixa de economizar centenas de milhares de reais em juros se comparado à redução de prazo.")
                
        elif sistema_amortizacao == "PRICE":
            if "Prazo" in estrategia_banco:
                novo_saldo_devedor = saldo_devedor_chaves - saldo_para_banco
                if (novo_saldo_devedor * taxa_mensal) >= parcela_banco_inicial:
                    st.error("Erro matemático: O saldo devedor gera juros maiores que a parcela.")
                else:
                    novo_prazo = -math.log(1 - (novo_saldo_devedor * taxa_mensal) / parcela_banco_inicial) / math.log(1 + taxa_mensal)
                    meses_economizados = int(prazo_financiamento) - int(round(novo_prazo))
                    st.success(f"⏳ **Efeito no Prazo:** Mantendo a parcela cravada em R$ {parcela_banco_inicial:,.2f}, você elimina **{meses_economizados} meses** de dívida (cerca de **{meses_economizados/12:.1f} anos a menos** pagando juros).")
            else:
                st.error("❌ Na Tabela PRICE, reduzir o valor da parcela é uma armadilha matemática. A velocidade de pagamento do principal cai tanto que você acaba devolvendo ao banco quase todo o lucro da amortização. Recomendamos focar estritamente na redução de prazo.")
    
    st.divider()

    st.subheader("6. Visão Dinâmica Consolidada (Matriz Anual)")
    data_inicio = datetime.date(2026, 6, 1)
    datas_reais = [data_inicio + pd.DateOffset(months=i) for i in range(int(meses_ate_chaves))]

    df_pre_chaves['Data Real'] = datas_reais
    df_pre_chaves['Ano'] = df_pre_chaves['Data Real'].dt.year
    meses_pt = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
    df_pre_chaves['Mês Nome'] = df_pre_chaves['Data Real'].dt.month.map(meses_pt)
    df_visao = df_pre_chaves[['Ano', 'Mês Nome', 'Poupança Gerada (R$)', 'Evolução de Obra (R$)', 'Custo Total Mensal (R$)']]

    anos_unicos = df_visao['Ano'].unique()
    abas = st.tabs([f"📅 {ano}" for ano in anos_unicos])

    for i, ano in enumerate(anos_unicos):
        with abas[i]:
            df_ano = df_visao[df_visao['Ano'] == ano].copy()
            df_ano = df_ano.set_index('Mês Nome')
            df_ano = df_ano.drop(columns=['Ano'])
            df_ano.loc['TOTAL DO ANO'] = df_ano.sum()
            st.dataframe(
                df_ano.style.format("R$ {:,.2f}")
                            .map(lambda _: 'font-weight: bold; background-color: #1E1E1E;', subset=pd.IndexSlice[['TOTAL DO ANO'], :]),
                use_container_width=True
            )

    st.markdown("---")
    st.header("7. Cenário Otimista: Evolução de Renda e Receitas Extras")
    col_otm1, col_otm2 = st.columns(2)
    with col_otm1:
        dissidio_anual = st.number_input("Reajuste Salarial Anual Esperado (%)", min_value=0.0, value=5.0, step=0.5)
    with col_otm2:
        receita_extra_anual = st.number_input("Receitas Extras Anuais (13º, PLR, Bônus) (R$)", min_value=0.0, value=15000.0, step=1000.0)

    anos_obra = meses_ate_chaves / 12
    renda_projetada_chaves = renda_casal * ((1 + (dissidio_anual / 100)) ** anos_obra)
    total_extra_acumulado = receita_extra_anual * anos_obra

    pico_custo_mensal = df_pre_chaves['Custo Total Mensal (R$)'].iloc[-1] if not df_pre_chaves.empty else 0
    comprometimento_pico_atual = (pico_custo_mensal / renda_casal) * 100 if renda_casal > 0 else 0
    comprometimento_pico_projetado = (pico_custo_mensal / renda_projetada_chaves) * 100 if renda_projetada_chaves > 0 else 0

    col_res_otm1, col_res_otm2, col_res_otm3 = st.columns(3)
    col_res_otm1.metric("Renda Líquida nas Chaves", f"R$ {renda_projetada_chaves:,.2f}", f"+ R$ {renda_projetada_chaves - renda_casal:,.2f} no salário")
    col_res_otm2.metric("Soma de PLR/13º (Durante a Obra)", f"R$ {total_extra_acumulado:,.2f}", "Dinheiro livre para usar como estratégia")
    col_res_otm3.metric("Peso do Mês Crítico (Mês Final)", f"{comprometimento_pico_projetado:.1f}% da Renda", f"{comprometimento_pico_projetado - comprometimento_pico_atual:.1f}% de alívio vs. Cenário Base", delta_color="inverse")


# =====================================================================
# MÓDULO 2: CONTROLADORIA (PÓS-ASSINATURA)
# =====================================================================
else:
    st.header("📊 Painel de Controle Ativo da Obra")
    st.markdown("Atualize os dados mensalmente conforme os boletos reais chegarem para recalcular sua rota.")
    
    # SETUP BASE ORÇADA PARA COMPARAÇÃO
    if perfil == "Cenário Vinicius & Ju":
        teto_aprovado = 636300.00
        gap_teorico_inicial = max(0, default_imovel - default_entrada - teto_aprovado)
        meses_totais = default_meses_chaves
        parcela_banco_inicial = 8225.12
        obra_inicial_base = 1480.52
    else:
        teto_aprovado = 298000.00
        gap_teorico_inicial = max(0, default_imovel - default_entrada - teto_aprovado)
        meses_totais = default_meses_chaves
        parcela_banco_inicial = 2153.22
        obra_inicial_base = 100.00

    # Recriando a curva ideal (Orçada)
    meses_array_base = np.arange(1, int(meses_totais) + 1)
    if len(meses_array_base) > 2:
        eo_ativa = np.linspace(obra_inicial_base, parcela_banco_inicial, len(meses_array_base) - 2)
        eo_base = np.concatenate((np.zeros(2), eo_ativa))
    else:
        eo_base = np.zeros(len(meses_array_base))
    parcela_const_base = gap_teorico_inicial / meses_totais

    st.subheader("1. O Raio-X do Mês")
    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
    
    with col_ctrl1:
        mes_atual = st.number_input("Mês Atual da Obra", min_value=1, max_value=int(meses_totais), value=1, step=1)
        meses_restantes = meses_totais - mes_atual
    with col_ctrl2:
        saldo_real_const = st.number_input("Saldo Devedor c/ Construtora (com INCC) (R$)", min_value=0.0, value=float(gap_teorico_inicial), step=1000.0)
    with col_ctrl3:
        eo_paga_mes = st.number_input("Boleto Evolução de Obra Caixa neste Mês (R$)", min_value=0.0, value=float(eo_base[mes_atual-1]), step=100.0)

    if meses_restantes > 0:
        nova_parcela_const = saldo_real_const / meses_restantes
    else:
        nova_parcela_const = saldo_real_const 
    custo_real_mes = nova_parcela_const + eo_paga_mes

    st.progress(int((mes_atual / meses_totais) * 100), text=f"Progresso da Obra: {mes_atual} de {meses_totais} meses concluídos")
    st.divider()

    # --- NOVO: DASHBOARD REAL VS ORÇADO ---
    st.subheader("2. Dashboard Real vs. Orçado (Termômetro do Mês)")
    st.markdown("Veja se os boletos deste mês estão punindo o caixa além do planejado no simulador original.")
    
    orcado_eo_mes = eo_base[mes_atual - 1]
    orcado_const_mes = parcela_const_base
    orcado_total = orcado_eo_mes + orcado_const_mes
    
    col_dash1, col_dash2, col_dash3 = st.columns(3)
    
    # Delta inverso: Se o Real for MAIOR que o Orçado, fica vermelho (ruim). Se for menor, fica verde (bom).
    dif_eo = eo_paga_mes - orcado_eo_mes
    col_dash1.metric("Evolução de Obra (Caixa)", f"R$ {eo_paga_mes:,.2f}", f"R$ {dif_eo:,.2f} vs Orçado", delta_color="inverse")
    
    dif_const = nova_parcela_const - orcado_const_mes
    col_dash2.metric("Parcela da Construtora", f"R$ {nova_parcela_const:,.2f}", f"R$ {dif_const:,.2f} vs Orçado", delta_color="inverse")
    
    dif_total = custo_real_mes - orcado_total
    col_dash3.metric("Seu Desembolso Total", f"R$ {custo_real_mes:,.2f}", f"R$ {dif_total:,.2f} vs Orçado", delta_color="inverse")

    if dif_total > 0:
        st.error("⚠️ Atenção: A inflação (INCC) ou o ritmo da obra fizeram seu custo deste mês ficar **acima** do que você havia planejado no simulador.")
    else:
        st.success("✅ Excelente: Seu custo atual está aderente ou abaixo da nossa previsão conservadora inicial.")

    st.divider()

    # --- NOVO: O AMORTÔMETRO (GAMIFICAÇÃO) ---
    st.subheader("3. Termômetro de Aportes 🚀")
    if perfil == "Cenário Vinicius & Ju":
        st.markdown("Caiu um dinheiro extra? Simule o impacto de jogar isso na dívida (Prioridade: Construtora com taxa de 0,5% a.m. -> Depois Caixa Econômica).")
    else:
        st.markdown("Caiu um dinheiro extra? Simule o impacto de jogar isso na dívida (Prioridade: Construtora para fugir do INCC -> Depois Caixa Econômica).")
    
    aporte_extra = st.number_input("Valor do Aporte Extra (PLR, Bônus, etc) (R$)", min_value=0.0, value=0.0, step=1000.0)
    
    if aporte_extra > 0:
        if aporte_extra <= saldo_real_const:
            novo_saldo_const = saldo_real_const - aporte_extra
            parcela_aliviada = novo_saldo_const / meses_restantes
            pct_gap_pago = (aporte_extra / saldo_real_const) * 100
            
            st.progress(int(pct_gap_pago), text=f"Ataque à Construtora: {pct_gap_pago:.1f}% do saldo devedor atual foi aniquilado!")
            st.info(f"📉 **Alívio Imediato:** Sua parcela mensal da construtora cai de R$ {nova_parcela_const:,.2f} para **R$ {parcela_aliviada:,.2f}**.")
            
        else:
            sobra_pra_caixa = aporte_extra - saldo_real_const
            st.progress(100, text="Construtora 100% ELIMINADA! 🎉 O restante foi jogado para a Caixa!")
            
            st.success(f"🎯 **Ataque Duplo!** Você quitou toda a construtora, zerando sua parcela mensal com eles. A sobra de **R$ {sobra_pra_caixa:,.2f}** bateu direto no saldo da Caixa Econômica.")
            
            # Calculando impacto da sobra na Caixa
            if perfil == "Cenário Vinicius & Ju":
                 amortizacao_mensal_caixa = teto_aprovado / default_prazo
                 meses_cortados = int(sobra_pra_caixa / amortizacao_mensal_caixa)
            else:
                 if (teto_aprovado * taxa_mensal) < parcela_banco_inicial:
                     novo_p = -math.log(1 - ((teto_aprovado - sobra_pra_caixa) * taxa_mensal) / parcela_banco_inicial) / math.log(1 + taxa_mensal)
                     meses_cortados = int(default_prazo) - int(round(novo_p))
                 else:
                     meses_cortados = 0
                     
            anos_cortados = meses_cortados / 12
            st.info(f"⏳ **Bônus na Caixa:** Essa injeção extra arrancou aproximadamente **{meses_cortados} parcelas** do final do seu contrato bancário (Você comprou de volta **{anos_cortados:.1f} anos** de vida).")
            
