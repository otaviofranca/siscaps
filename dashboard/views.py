from django.shortcuts import render, redirect
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from .models import Paciente, Atendimento
import os
from django.conf import settings
from django.contrib import messages
from django.core.management import call_command
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


        descricao = CID_DICT.get(codigo_limpo, item['cid'])

        item['descricao_completa'] = f"{item['cid']} - {descricao}"


    distribuicao_sexo = Paciente.objects.filter(ativo=True).values('sexo') \
        .annotate(qtd=Count('id')).order_by('sexo')

    top_procedimentos = Atendimento.objects.values('procedimento__nome') \
        .annotate(qtd=Count('id')) \
        .order_by('-qtd')[:5]
    
    producao_mensal = Atendimento.objects.annotate(mes=TruncMonth('data')) \
        .values('mes').annotate(qtd=Count('id')).order_by('mes') 
    
    dados_formatados = []
    for item in producao_mensal:
        if item['mes']:
            dados_formatados.append({
                'mes': item['mes'].strftime('%m/%Y'),
                'qtd': item['qtd']
            })

    dados_sexo = list(distribuicao_sexo) 

    context = {
        "usuarios_ativos": usuarios_ativos,

        "pacientes_rua": pacientes_rua,         
        "pacientes_alcool_droga": pacientes_alcool_droga,
        "top_cids": top_cids,                    
        "top_procedimentos": top_procedimentos,
        "dados_grafico": dados_formatados,
        "dados_sexo": dados_sexo                 
    }

    return render(request, 'dashboard.html', context)

def importar_raas(request):
    if request.method == 'POST' and request.FILES.get('arquivo_xls'):
        arquivo = request.FILES['arquivo_xls']
        
        if not arquivo.name.endswith(('.xls', '.xlsx')):
            messages.error(request, 'Formato de arquivo inválido. Use .xls ou .xlsx')
            return redirect('dashboard')
        caminho_destino = os.path.join(settings.BASE_DIR, 'dados_caps.xls')

        try:
            with open(caminho_destino, 'wb+') as destino:
                for chunk in arquivo.chunks():
                    destino.write(chunk)
            call_command('importar_xlsx')
            messages.success(request, 'Importação bem sucedida')
        except Exception as e:
            messages.error(request, f'Erro ao importar dados: {str(e)}')
    return redirect('dashboard')        
