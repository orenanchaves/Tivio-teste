# -*- coding: utf-8 -*-
# Calendário de 2027: feriados, datas de dinheiro e ações da Tivio.
import calendar as _cal
_MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
FERIADOS = {(1, 1): "Confraternização Universal", (1, 25): "Aniversário de São Paulo", (2, 8): "Carnaval", (2, 9): "Carnaval", (2, 10): "Quarta-feira de Cinzas",
            (3, 26): "Sexta-feira Santa", (4, 21): "Tiradentes", (5, 1): "Dia do Trabalho", (5, 27): "Corpus Christi", (7, 9): "Revolução Constitucionalista (SP)",
            (9, 7): "Independência", (10, 12): "Nossa Senhora Aparecida", (11, 2): "Finados", (11, 15): "Proclamação da República", (11, 20): "Consciência Negra", (12, 25): "Natal"}
DINHEIRO = {(1, 4): "Tesouro Prefixado 2027 vence em 01/01; pagamento no primeiro dia útil",
            (2, 15): "Cupom de títulos com juros semestrais (conferir por título)",
            (1, 15): "PLR: 2ª parcela na GM de São Caetano (acordo de 2026, com metas)",
            (3, 1): "Tesouro Selic 2027 vence · Limite da 2ª parcela da PLR dos bancários (acordo atual)",
            (9, 30): "Limite da 1ª parcela da PLR dos bancários (regra de 2026, a confirmar para 2027)",
            (5, 17): "Cupom de títulos com juros semestrais: dia 15 cai no sábado (conferir por título)",
            (8, 16): "Cupom de títulos com juros semestrais: dia 15 cai no domingo (conferir por título)",
            (11, 16): "Cupom de títulos com juros semestrais: dia 15 é feriado (conferir por título)",
            (11, 30): "1ª parcela do 13º salário", (12, 20): "2ª parcela do 13º salário", (12, 31): "Último dia de aporte em PGBL para o IR do ano"}
# datas que repetem o padrão de 2026: as de 2027 ainda não saíram
ESTIMADO = {(2, 15): "PIS/Pasep: início do abono", (3, 15): "PIS/Pasep", (4, 15): "PIS/Pasep", (4, 26): "13º do INSS: início da 1ª parcela",
            (5, 17): "PIS/Pasep", (5, 25): "13º do INSS: início da 2ª parcela", (5, 31): "Restituição do IR: 1º lote", (6, 15): "PIS/Pasep",
            (6, 30): "Restituição do IR: 2º lote", (7, 15): "PIS/Pasep", (7, 30): "Restituição do IR: 3º lote", (8, 16): "PIS/Pasep: último mês",
            (8, 31): "Restituição do IR: 4º lote · Lucro do FGTS: prazo de crédito"}
NOTAS = {1: ("quente", "Dinheiro do Prefixado 2027 chegando à conta.", "Edição trimestral na 2ª ou 3ª semana."),
         2: ("quente", "PLR: em 2026, Itaú, Santander e Bradesco pagaram a 2ª parcela em 27/02, e a Vale pagou em Itabira no mesmo dia. Data de 2027 a confirmar.", "Cortes da edição. Evento antes do vencimento do Selic."),
         3: ("quente", "Vencimento do Tesouro Selic 2027 em 1º de março e último prazo da PLR dos bancos.", "Conteúdo de onde reinvestir e cortes."),
         4: ("quente", "Precatórios federais: em 2026, pagos até a 1ª quinzena de abril. 13º do INSS começa no fim do mês, se repetir a antecipação.", "Edição trimestral na 2ª ou 3ª semana."),
         5: ("", "", "Cortes e eventos."),
         6: ("", "", "Cortes e eventos."),
         7: ("", "", "Edição trimestral na 2ª ou 3ª semana."),
         8: ("", "", "Cortes e eventos."),
         9: ("quente", "PLR dos bancos: em 2026, o Itaú pagou a 1ª parcela em 24/09.", "Chamada para a próxima edição."),
         10: ("", "", "Edição trimestral na 2ª ou 3ª semana."),
         11: ("quente", "1ª parcela do 13º. Cupons de juros semestrais.", "Evento e conteúdo de previdência antes do fim do ano."),
         12: ("quente", "2ª parcela do 13º e PGBL até 31/12. Atenção: dezembro de 2024 teve resgates fortes nos fundos.", "Previdência: HGD30 e HYD60 em foco.")}

def _mes(m):
    prim, dias = _cal.monthrange(2027, m)
    vazio = (prim + 1) % 7  # coluna começa no domingo
    cel = ["<i></i>"] * vazio
    for d in range(1, dias + 1):
        f, g, h = FERIADOS.get((m, d)), DINHEIRO.get((m, d)), ESTIMADO.get((m, d))
        cl = ("f " if f else "") + ("d " if g else "") + ("e " if h and not g else "")
        fim = "fds" if (vazio + d - 1) % 7 in (0, 6) else ""
        tit = " · ".join(x for x in (f, g, h) if x)
        cel.append(f'<span class="{cl}{fim}"' + (f' title="{tit}"' if tit else "") + f">{d}</span>")
    itens = "".join(f'<li class="lf"><b>{d}</b> {t}</li>' for (mm, d), t in sorted(FERIADOS.items()) if mm == m)
    itens += "".join(f'<li class="ld"><b>{d}</b> {t}</li>' for (mm, d), t in sorted(DINHEIRO.items()) if mm == m)
    itens += "".join(f'<li class="le"><b>{d}</b> {t}</li>' for (mm, d), t in sorted(ESTIMADO.items()) if mm == m)
    q, din, tiv = NOTAS[m]
    selo = '<span class="pill ok"><i></i>Mês de dinheiro</span>' if q else ""
    nota_d = f'<p class="nd">{din}</p>' if din else ""
    return (f'<article class="mes vidro"><header><h3>{_MESES[m-1]}</h3>{selo}</header>'
            '<div class="sem"><b>D</b><b>S</b><b>T</b><b>Q</b><b>Q</b><b>S</b><b>S</b></div>'
            f'<div class="dias">{"".join(cel)}</div><ul class="ev">{itens}</ul>{nota_d}<p class="nt">{tiv}</p></article>')

corpo_c = (cabecalho("", []) + '<div class="wrap">' + trilha(("index.html", "Início"), ("marketing.html", "Central de Marketing"), ("", "Calendário 2027"))
  + '<section class="topo-peer"><div><p class="eyebrow"><i></i>Ano todo</p><h1>Calendário <strong>2027</strong></h1>'
  + '<p class="lead">Feriados, períodos em que costuma entrar dinheiro e o que a Tivio faz em cada mês.</p></div></section>'
  + '<div class="camadas" role="group" aria-label="Mostrar no calendário">'
  + '<button type="button" data-c="f" aria-pressed="true"><i class="k-f"></i>Feriados</button>'
  + '<button type="button" data-c="d" aria-pressed="true"><i class="k-d"></i>Dinheiro</button>'
  + '<button type="button" data-c="t" aria-pressed="true"><i class="k-t"></i>Tivio</button></div>'
  + '<p class="meta-txt">Dia verde cheio é data definida. Contorno verde repete o padrão de 2026: a data de 2027 ainda não saiu.</p>'
  + '<div class="ano" id="ano">' + "".join(_mes(m) for m in range(1, 13)) + "</div>"
  + '''<h2>Quanto entrou em <strong>2026</strong></h2>
<div class="subs">
  <div class="sub vidro"><b>R$ 78,2 bi</b><span>13º do INSS, abril a junho</span></div>
  <div class="sub vidro"><b>R$ 69,7 bi</b><span>Precatórios federais, março e abril</span></div>
  <div class="sub vidro"><b>R$ 16 bi</b><span>1º lote da restituição do IR</span></div>
  <div class="sub vidro"><b>R$ 13,04 bi</b><span>Lucro do FGTS, até 31/08, na conta vinculada</span></div>
</div>
<p class="meta-txt">Valores previstos ou divulgados na imprensa. O lucro do FGTS fica na conta do Fundo e não vira saque livre. Dividendos não entraram: não há padrão mensal confiável, e eles se concentram em Petrobras e bancos. Boa parte desse dinheiro vai para o consumo, não para investimento.</p>
<h2>O que está por trás do <strong>dinheiro</strong></h2>
<div class="analise">
  <div class="vidro"><h3>Confirmado</h3><ul>
    <li>Tesouro Prefixado 2027 e Tesouro Selic 2027 têm vencimento em 01/01 e 01/03</li>
    <li>13º: até 30/11 e até 20/12</li>
    <li>PGBL: aporte até o fim do ano para deduzir no IR</li>
    <li>Dezembro de 2024 teve R$ 147,6 bi de saídas líquidas nos fundos</li>
    <li>PLR dos bancários: até 30/09 e até 1º de março, pela convenção citada em 2026</li>
  </ul></div>
  <div class="vidro"><h3>Hipótese, a validar</h3><ul>
    <li>Janeiro não tem padrão: +R$ 49,8 bi em 2024, -R$ 24,6 bi em 2023 e saída em 2025 (Anbima)</li>
    <li>PLR fora dos bancos varia por empresa e por acordo; Petrobras, Ambev, Toyota e Caixa não tiveram data encontrada</li>
    <li>Restituição, PIS/Pasep e 13º do INSS: as datas de 2027 ainda não saíram</li>
    <li>Quanto vence em cada título: pedir dados ao Tesouro e cruzar com a captação da Tivio</li>
  </ul></div>
</div>
<p class="meta-txt">Feriados nacionais, com dois de São Paulo; confirmar os municipais onde houver evento. As datas dos 16 eventos com o Itaú ainda não existem: quando definidas, entram aqui.</p>
<p class="fontes-peer"><b>Fontes</b><a href="https://www.tesourodireto.com.br/b/novo-rol-de-titulos-do-tesouro-direto-2025" target="_blank" rel="noopener">Tesouro Direto</a><a href="https://borainvestir.b3.com.br/noticias/imposto-de-renda/imposto-de-renda-2026-confira-o-calendario-de-restituicao/" target="_blank" rel="noopener">B3 Bora Investir</a><a href="https://capitalaberto.com.br/mercados/fundos-tem-captacao-liquida-negativa-em-janeiro-diz-anbima/" target="_blank" rel="noopener">Capital Aberto</a><a href="https://www.suno.com.br/noticias/fundos-de-investimento-melhor-mes-dois-anos-gpj" target="_blank" rel="noopener">Suno</a><a href="https://bancariosabc.org.br/wp-content/uploads/2026/02/NB-1197_Web.pdf" target="_blank" rel="noopener">Bancários ABC</a><a href="https://seucreditodigital.com.br/plr-santander-2026-valores-pagamento/" target="_blank" rel="noopener">PLR Santander</a><a href="https://seucreditodigital.com.br/itau-paga-plr-24-setembro-2026/" target="_blank" rel="noopener">PLR Itaú</a><a href="https://www.dgabc.com.br/Noticia/4315790/trabalhadores-da-gm-de-sao-caetano-aprovam-pr-de-r$-20-780-em-duas-parcelas" target="_blank" rel="noopener">PLR GM</a><a href="https://itabiraonline.com.br/?p=232503" target="_blank" rel="noopener">PLR Vale</a><a href="https://www.tnh1.com.br/noticia/nid/13-salario-do-inss-2026-deve-ser-pago-em-abril-e-maio-veja-datas/" target="_blank" rel="noopener">13º INSS</a><a href="https://www.cnnbrasil.com.br/economia/macroeconomia/governo-tera-que-pagar-r-697-bilhoes-em-precatorios-em-2026/" target="_blank" rel="noopener">Precatórios</a><a href="https://www.contabeis.com.br/noticias/76026/receita-preve-pagar-r-16-bi-no-1o-lote-do-ir-2026/" target="_blank" rel="noopener">Restituição</a><a href="https://www.opovo.com.br/noticias/economia/2026/07/27/amp/fgts-decide-nesta-terca-distribuicao-de-lucro-veja-detalhes.html" target="_blank" rel="noopener">FGTS</a><a href="https://diariodocomercio.com.br/financas/pis-pasep-2026-calendario/" target="_blank" rel="noopener">PIS/Pasep</a></p>
<p class="rodape">Tivio Capital · Comunicação &amp; Marketing</p></div>
<script>(function(){var a=document.getElementById('ano');[].forEach.call(document.querySelectorAll('.camadas button'),function(b){b.addEventListener('click',function(){var on=b.getAttribute('aria-pressed')!=='true';b.setAttribute('aria-pressed',on);a.classList.toggle('sem-'+b.dataset.c,!on);});});})();</script>''')
(EXTRA / "calendario.html").write_text(pagina("Calendário 2027", corpo_c, CSS_P), encoding="utf-8")
