from django.shortcuts import render, redirect
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from .models import Paciente, Atendimento
import os
from django.conf import settings
from django.contrib import messages
from django.core.management import call_command

def dashboard_view(request):
    usuarios_ativos = Paciente.objects.filter(ativo=True).count()
    total_producao = Atendimento.objects.aggregate(total=Sum('procedimento__valor'))['total'] or 0
    top_procedimentos = Atendimento.objects.values('procedimento__nome') \
        .annotate(total_realizado=Count('id')) \
        .order_by('-total_realizado')[:5]
    
    producao_mensal = Atendimento.objects.annotate(mes=TruncMonth('data')) \
        .values('mes').annotate(
            qtd=Count('id')
            ).order_by('mes') 
    
    dados_formatados = []

    for item in producao_mensal:
        dados_formatados.append({
            'mes': item['mes'].strftime('%m/%Y'),
            'qtd': item['qtd']
        })

    context = {
        "usuarios_ativos": usuarios_ativos,
        "total_producao": total_producao,
        "top_procedimentos": top_procedimentos,
        "producao_mensal": producao_mensal,
        "dados_grafico": dados_formatados
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
