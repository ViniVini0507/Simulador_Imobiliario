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

    # MOTOR DE CÁLCULO INTERNO
    taxa_mensal = (taxa_juros_anual / 100) / 12  
    saldo_necessario = valor_imovel - entrada_inicial

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

    col_res1, col_res2, col_res3 = st.columns(3)
    col_res1.metric("Saldo Financiado (Banco)", f"R$ {saldo_financiado:,.2f}")

    if perfil == "Cenário João & Mari":
        col_res2.metric("GAP Construtora (Buraco)", f"R$ {gap_construtora:,.2f}")
        col_res3.metric("Nova Parcela Const. (Sem INCC)", f"R$ {mensal_construtora_calculada:,.2f}")
    else:
        col_res2.metric("GAP Construtora (Descoberto)", f"R$ {gap_construtora:,.2f}")
        col_res3.metric("Teto Evolução Obra", f"R$ {teto_obra:,.2f}")
        
    st.info(f"💡 A 1ª parcela do financiamento na entrega das chaves ({sistema_amortizacao}) será de **R$ {parcela_banco_inicial:,.2f}**.")

    # CONSTRUTOR DO DATAFRAME PRÉ-CHAVES (Com carência)
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

    st.header("4. Planejamento de Amortização Extraordinária")
    meta_amortizacao = st.slider("Quanto abater do saldo devedor nas chaves? (R$)", min_value=0, max_value=int(saldo_devedor_chaves), step=5000, value=50000)

    if meta_amortizacao > 0:
        if sistema_amortizacao == "SAC":
            amortizacao_mensal = saldo_devedor_chaves / prazo_financiamento
            taxa_juros_mensal = 0.009521 
            reducao_parcela = (meta_amortizacao / prazo_financiamento) + (meta_amortizacao * taxa_juros_mensal)
            nova_primeira_parcela = parcela_banco_inicial - reducao_parcela
            
            st.success(f"📉 **Alternativa - Reduzir Valor:** A parcela cai de R$ {parcela_banco_inicial:,.2f} para **R$ {nova_primeira_parcela:,.2f}**.")
            
            if amortizacao_mensal > 0:
                parcelas_reduzidas = int(meta_amortizacao / amortizacao_mensal)
                anos_reduzidos = parcelas_reduzidas / 12
                st.success(f"⏳ **Alternativa - Reduzir Prazo:** Quita aproximadamente **{parcelas_reduzidas} parcelas** (redução de **{anos_reduzidos:.1f} anos**).")
                
        elif sistema_amortizacao == "PRICE":
            novo_saldo_devedor = saldo_devedor_chaves - meta_amortizacao
            if (novo_saldo_devedor * taxa_mensal) >= parcela_banco_inicial:
                st.error("Erro: O novo saldo devedor gera juros maiores que a parcela atual.")
            else:
                novo_prazo = -math.log(1 - (novo_saldo_devedor * taxa_mensal) / parcela_banco_inicial) / math.log(1 + taxa_mensal)
                novo_prazo_meses = int(round(novo_prazo))
                meses_economizados = int(prazo_financiamento) - novo_prazo_meses
                anos_economizados = meses_economizados / 12
                
                st.success(f"⏳ **Efeito do Aporte (Foco em Prazo):** Ao injetar R$ {meta_amortizacao:,.2f}, seu saldo cai para R$ {novo_saldo_devedor:,.2f}.")
                st.success(f"🚀 **Resultado:** Mantendo a parcela cravada de R$ {parcela_banco_inicial:,.2f}, você elimina **{meses_economizados} meses** de dívida (cerca de **{anos_economizados:.1f} anos a menos** pagando juros ao banco).")

    st.divider()

    st.subheader("5. Simulação de Orçamento: Poupança x Obra")
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
    col_res_otm1.metric("Renda Líquida nas Chaves", f"R$ {renda_projetada_chaves:,.2f}", f"+ R$ {renda_projetada_chaves - renda_casal:,.2f} no salário mensal")
    col_res_otm2.metric("Soma de PLR/13º (Durante a Obra)", f"R$ {total_extra_acumulado:,.2f}", "Dinheiro livre para usar como estratégia")
    col_res_otm3.metric("Peso do Mês Crítico (Mês Final)", f"{comprometimento_pico_projetado:.1f}% da Renda", f"{comprometimento_pico_projetado - comprometimento_pico_atual:.1f}% de alívio vs. Cenário Base", delta_color="inverse")

    if gap_construtora > 0:
        st.success(f"💡 **Estratégia Tática:** Você terá acumulado **R$ {total_extra_acumulado:,.2f}** em receitas extras. Como há um GAP de **R$ {gap_construtora:,.2f}** com a construtora, use esses bônus anuais para antecipar as parcelas de trás para frente, ganhando desconto de juros. Guarde a sobra para abater a Caixa nas chaves.")
    else:
        st.success(f"💡 **Estratégia Tática:** Você terá acumulado **R$ {total_extra_acumulado:,.2f}** em receitas extras. Como o seu GAP está zerado, guarde 100% desse valor e use como uma 'pancada' de amortização no saldo devedor da Caixa logo na entrega das chaves.")

# =====================================================================
# MÓDULO 2: CONTROLADORIA (PÓS-ASSINATURA)
# =====================================================================
else:
    st.header("📊 Painel de Controle Ativo da Obra")
    st.markdown("Atualize os dados mensalmente conforme os boletos reais chegarem para recalcular sua rota.")
    
    # Busca o GAP inicial planejado baseado no perfil para servir de teto teórico inicial
    if perfil == "Cenário Vinicius & Ju":
        teto_aprovado = 636300.00
        gap_teorico_inicial = max(0, default_imovel - default_entrada - teto_aprovado)
        meses_totais = default_meses_chaves
    else:
        gap_teorico_inicial = max(0, default_imovel - default_entrada - 298000.00)
        meses_totais = default_meses_chaves

    st.subheader("1. O Raio-X do Mês")
    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
    
    with col_ctrl1:
        mes_atual = st.number_input("Mês Atual da Obra", min_value=1, max_value=int(meses_totais), value=1, step=1)
        meses_restantes = meses_totais - mes_atual
    with col_ctrl2:
        saldo_real_const = st.number_input("Saldo Devedor c/ Construtora Atualizado (R$)", min_value=0.0, value=float(gap_teorico_inicial), step=1000.0)
    with col_ctrl3:
        eo_paga_mes = st.number_input("Boleto Evolução de Obra Caixa neste Mês (R$)", min_value=0.0, value=0.0, step=100.0)

    # Recalculando a rota da construtora
    if meses_restantes > 0:
        nova_parcela_const = saldo_real_const / meses_restantes
    else:
        nova_parcela_const = saldo_real_const # Último mês paga tudo

    custo_real_mes = nova_parcela_const + eo_paga_mes

    col_res_ctrl1, col_res_ctrl2, col_res_ctrl3 = st.columns(3)
    col_res_ctrl1.metric("Parcela Construtora Recalculada", f"R$ {nova_parcela_const:,.2f}", "Diluindo o saldo pelos meses restantes", delta_color="off")
    col_res_ctrl2.metric("Evolução de Obra Real", f"R$ {eo_paga_mes:,.2f}", "Custo bancário do mês", delta_color="off")
    col_res_ctrl3.metric("Seu Esforço de Caixa Total", f"R$ {custo_real_mes:,.2f}", "Total a desembolsar neste mês", delta_color="inverse")

    st.progress(int((mes_atual / meses_totais) * 100), text=f"Progresso da Obra: {mes_atual} de {meses_totais} meses concluídos")
    st.divider()

    st.subheader("2. Laboratório de Antecipação de Parcelas")
    
    if perfil == "Cenário Vinicius & Ju":
        st.markdown("Caiu um dinheiro extra? Simule o abatimento no saldo da construtora de trás para frente (**Taxa Fixa 0,5% a.m.**).")
    else:
        st.markdown("Caiu um dinheiro extra? Simule o abatimento no saldo da construtora para **fugir da inflação (INCC)**.")
    
    aporte_extra = st.number_input("Valor do Aporte Extra (PLR, Bônus, etc) (R$)", min_value=0.0, value=0.0, step=1000.0)
    
    if aporte_extra > 0:
        if aporte_extra >= saldo_real_const:
            st.success("🎉 **Quitação Total!** Esse aporte elimina 100% do seu GAP com a construtora. A partir do próximo mês, você paga APENAS a Evolução de Obra da Caixa.")
        else:
            novo_saldo_const = saldo_real_const - aporte_extra
            parcela_aliviada = novo_saldo_const / meses_restantes
            
            col_ant1, col_ant2 = st.columns(2)
            col_ant1.info(f"📉 **Efeito no Bolso:** Sua parcela mensal da construtora cai de R$ {nova_parcela_const:,.2f} para **R$ {parcela_aliviada:,.2f}** pelo resto da obra.")
            
            if perfil == "Cenário Vinicius & Ju":
                # Estimativa de economia de juros de 0.5% a.m. exclusiva para Vinicius & Ju
                economia_juros = aporte_extra * 0.005 * (meses_restantes / 2)
                col_ant2.success(f"💰 **Economia de Juros:** Ao antecipar, você deixa de pagar aproximadamente **R$ {economia_juros:,.2f}** de juros puros (0,5% a.m.) para a construtora.")
            else:
                # O ganho do João Pedro é blindar o dinheiro contra o INCC
                col_ant2.success("🛡️ **Fuga do INCC:** Ao antecipar esse valor, você 'congela' essa parte da dívida e blinda seu dinheiro contra os reajustes mensais da inflação da construção civil.")

