import pandas as pd
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from dashboard.models import Procedimento

class Command(BaseCommand):
    help = 'Importa tabela completa com detecção automática de formato'

    def handle(self, *args, **kwargs):
        # Tenta nomes prováveis (o arquivo que você tiver na pasta será usado)
        arquivos_possiveis = [
            'tabela_caps.csv',
            'tabela_caps.xlsx',
            'tabela_caps.xlsx - Reorganização de Tabela de Proc.csv'
        ]
        
        caminho = None
        for nome in arquivos_possiveis:
            temp_path = os.path.join(settings.BASE_DIR, nome)
            if os.path.exists(temp_path):
                caminho = temp_path
                break
        
        if not caminho:
            self.stdout.write(self.style.ERROR('ERRO: Nenhum arquivo de tabela encontrado na pasta do projeto.'))
            self.stdout.write('Certifique-se de que o arquivo "tabela_caps.csv" está junto do manage.py')
            return

        self.stdout.write(self.style.WARNING(f'Lendo arquivo: {caminho}'))

        # TENTATIVA 1: Ler como CSV (Várias combinações de encoding e separador)
        df = None
        combinacoes = [
            {'sep': ',', 'encoding': 'utf-8'},
            {'sep': ',', 'encoding': 'latin-1'}, # Mais provável para Excel em PT-BR
            {'sep': ';', 'encoding': 'utf-8'},
            {'sep': ';', 'encoding': 'latin-1'},
        ]

        for config in combinacoes:
            try:
                df = pd.read_csv(caminho, sep=config['sep'], encoding=config['encoding'])
                # Verifica se leu corretamente (deve ter mais de 1 coluna)
                if len(df.columns) > 1:
                    self.stdout.write(self.style.SUCCESS(f"Sucesso lendo com: {config}"))
                    break
            except:
                continue

        # TENTATIVA 2: Se tudo falhar, tenta ler como Excel verdadeiro (.xlsx)
        if df is None:
            try:
                df = pd.read_excel(caminho)
                self.stdout.write(self.style.SUCCESS("Sucesso lendo como Excel (.xlsx)"))
            except:
                self.stdout.write(self.style.ERROR('FALHA FATAL: Não foi possível ler o arquivo. Verifique se ele não está corrompido.'))
                return

        # Padroniza colunas
        df.columns = df.columns.str.strip().str.upper()
        
        # Validação básica
        if 'CODIGO' not in df.columns:
            self.stdout.write(self.style.ERROR(f'Colunas encontradas: {list(df.columns)}'))
            self.stdout.write(self.style.ERROR('A coluna CODIGO não foi encontrada.'))
            return

        count_criados = 0
        count_atualizados = 0

        self.stdout.write('Iniciando importação no banco de dados...')

        for index, row in df.iterrows():
            try:
                # Limpeza e tratamento de dados
                raw_cod = str(row['CODIGO'])
                codigo = raw_cod.replace('.', '').replace('-', '').strip()
                
                # Pula linhas vazias
                if not codigo or codigo.lower() == 'nan':
                    continue

                nome = str(row.get('PROCEDIMENTO', 'Sem Nome')).strip().upper()
                
                # Trata campos de texto para não salvar "nan" do pandas
                descricao = str(row.get('DESCRICAO', '')).strip()
                if descricao.lower() == 'nan': descricao = ''
                
                cbo = str(row.get('CBO', '')).strip()
                if cbo.lower() == 'nan': cbo = ''
                
                cid = str(row.get('CID', '')).strip()
                if cid.lower() == 'nan': cid = ''

                # Salva no banco
                obj, created = Procedimento.objects.update_or_create(
                    codigo=codigo,
                    defaults={
                        'nome': nome,
                        'valor': 0.00,
                        'descricao': descricao,
                        'cbo': cbo,
                        'cid': cid
                    }
                )

                if created:
                    count_criados += 1
                else:
                    count_atualizados += 1

                if (index + 1) % 100 == 0:
                    self.stdout.write(f'Processado {index + 1} linhas...')

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erro na linha {index}: {e}'))

        self.stdout.write(self.style.SUCCESS('='*40))
        self.stdout.write(self.style.SUCCESS(f'IMPORTAÇÃO CONCLUÍDA!'))
        self.stdout.write(f'Novos: {count_criados} | Atualizados: {count_atualizados}')