import pandas as pd
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from dashboard.models import Procedimento

class Command(BaseCommand):
    help = 'Importa tabela oficial (Corrige erro de valor nulo)'

    def handle(self, *args, **kwargs):
        # 1. CONFIGURAÇÃO
        COL_CODIGO = 'CODIGO'
        COL_NOME   = 'PROCEDIMENTO'
        
        NOME_ARQUIVO = 'tabela_caps.csv'
        caminho = os.path.join(settings.BASE_DIR, NOME_ARQUIVO)

        self.stdout.write(self.style.WARNING(f'Lendo arquivo: {caminho}...'))

        # 2. ABERTURA DO ARQUIVO
        try:
            if os.path.exists(caminho.replace('.csv', '.xlsx')):
                df = pd.read_excel(caminho.replace('.csv', '.xlsx'), engine='openpyxl')
            else:
                try:
                    df = pd.read_csv(caminho)
                except:
                    df = pd.read_csv(caminho, sep=';', encoding='latin-1')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao abrir: {e}'))
            return

        df.columns = df.columns.str.strip().str.upper()

        if COL_CODIGO not in df.columns:
            self.stdout.write(self.style.ERROR(f'ERRO: Coluna "{COL_CODIGO}" não encontrada.'))
            return

        self.stdout.write(self.style.SUCCESS('Iniciando importação corrigida...'))

        count_criados = 0
        count_atualizados = 0

        for index, row in df.iterrows():
            try:
                # Tratamento do Código
                raw_cod = str(row[COL_CODIGO])
                if raw_cod.endswith('.0'): raw_cod = raw_cod[:-2]
                codigo = ''.join(filter(str.isdigit, raw_cod))
                
                if not codigo: continue

                # Tratamento do Nome
                nome = str(row[COL_NOME]).strip().upper()
                if (nome == 'NAN' or nome == '') and 'DESCRICAO' in df.columns:
                    nome = str(row['DESCRICAO']).strip().upper()

                # --- A MÁGICA DA CORREÇÃO AQUI ---
                # get_or_create: Tenta pegar o existente. Se não achar, cria um NOVO com os defaults.
                obj, created = Procedimento.objects.get_or_create(
                    codigo=codigo,
                    defaults={
                        'nome': nome,
                        'valor': 0.00  # <--- OBRIGATÓRIO: Define 0.00 para novos registros
                    }
                )

                if created:
                    count_criados += 1
                else:
                    # Se já existia, atualizamos SÓ o nome (mantendo o preço antigo)
                    if obj.nome != nome:
                        obj.nome = nome
                        obj.save()
                        count_atualizados += 1

                if (count_criados + count_atualizados) % 50 == 0:
                    self.stdout.write(f'Processado: {codigo}...')

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erro linha {index}: {e}'))

        self.stdout.write(self.style.SUCCESS('='*40))
        self.stdout.write(self.style.SUCCESS(f'SUCESSO TOTAL!'))
        self.stdout.write(self.style.SUCCESS(f'Novos procedimentos criados (R$ 0,00): {count_criados}'))
        self.stdout.write(self.style.WARNING(f'Procedimentos renomeados: {count_atualizados}'))
        self.stdout.write(self.style.SUCCESS('='*40))