from django.shortcuts import render, redirect
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.contrib import messages
from django.core.management import call_command
from django.conf import settings

import os

from dateutil.relativedelta import relativedelta
from .models import Paciente, Atendimento
from .cids_data import CID_DICT

def dashboard_view(request):
    usuarios_ativos = Paciente.objects.filter(ativo=True).count()
    pacientes_rua = Paciente.objects.filter(ativo=True, em_situacao_rua=True).count()
    pacientes_alcool_droga = Paciente.objects.filter(ativo=True, usuario_alcool_drogas=True).count()

    top_cids = Atendimento.objects.values('cid') \
        .annotate(qtd=Count('id')) \
        .order_by('-qtd')[:5]
    
    for item in top_cids:
        codigo_limpo = str(item['cid']).replace('.', '').replace('-', '').strip().upper()
        descricao = CID_DICT.get(codigo_limpo, "Descrição não encontrada")
        item['descricao_completa'] = f"{item['cid']} - {descricao}"

    distribuicao_sexo = Paciente.objects.filter(ativo=True).values('sexo') \
        .annotate(qtd=Count('id')).order_by('sexo')

    # --- CONFIGURAÇÃO DO GRÁFICO (ÚLTIMOS 12 MESES) ---
    hoje = timezone.now().date()
    data_inicio_filtro = hoje.replace(day=1) - relativedelta(months=11)
    
    producao_mensal = Atendimento.objects.filter(
            data__gte=data_inicio_filtro,
            data__lte=hoje 
        ) \
        .annotate(mes_trunc=TruncMonth('data')) \
        .values('mes_trunc') \
        .annotate(qtd=Count('id')) \
        .order_by('mes_trunc')

    dados_formatados = []
    for item in producao_mensal:
        if item['mes_trunc']:
            dados_formatados.append({
                'mes': item['mes_trunc'].strftime('%m/%Y'),
                'qtd': item['qtd']
            })

    context = {
        "usuarios_ativos": usuarios_ativos,
        "pacientes_rua": pacientes_rua,
        "pacientes_alcool_droga": pacientes_alcool_droga,
        "top_cids": top_cids,
        "dados_grafico": dados_formatados,
        "dados_sexo": list(distribuicao_sexo)
    }

    return render(request, 'dashboard.html', context)

def importar_raas(request):
    if request.method == 'POST' and request.FILES.get('arquivo_xls'):
        arquivo = request.FILES['arquivo_xls']
        
        if not arquivo.name.endswith(('.xls', '.xlsx')):
            messages.error(request, 'Formato de arquivo inválido.')
            return redirect('dashboard')

        caminho_destino = os.path.join(settings.BASE_DIR, 'dados_caps.xls')

        try:
            with open(caminho_destino, 'wb+') as destino:
                for chunk in arquivo.chunks():
                    destino.write(chunk)
            call_command('importar_xlsx')
            messages.success(request, 'Importação concluída!')
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
            
    return redirect('dashboard')